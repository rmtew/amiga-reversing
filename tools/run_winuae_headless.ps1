[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$RomPath,

    [string]$StateDirectory = (Join-Path ([System.IO.Path]::GetTempPath()) 'amiga-reversing2\winuae'),

    [string[]]$GdbCommand = @(),

    [ValidateRange(1, 120)]
    [int]$StartupTimeoutSeconds = 45
)

$ErrorActionPreference = 'Stop'

function Get-ToolPath([string]$relativePath) {
    $path = Join-Path $PSScriptRoot "..\\$relativePath"
    return (Resolve-Path -LiteralPath $path).Path
}

function Test-GdbListener([int]$processId) {
    return [bool](Get-NetTCPConnection -State Listen -LocalPort 2345 -ErrorAction SilentlyContinue |
        Where-Object { $_.OwningProcess -eq $processId })
}

function ConvertTo-ArgumentListString([string[]]$arguments) {
    return (($arguments | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_ -replace '"', '\\"') + '"'
        }
        else {
            $_
        }
    }) -join ' ')
}

function Request-OrderlyGdbShutdown([string]$gdbPath, [string]$stateDirectory) {
    if (-not (Test-GdbListener $process.Id)) {
        return
    }
    $shutdownOut = Join-Path $stateDirectory 'gdb-shutdown.stdout.txt'
    $shutdownErr = Join-Path $stateDirectory 'gdb-shutdown.stderr.txt'
    $shutdownArgs = ConvertTo-ArgumentListString @('-q', '-batch', '-ex', 'target remote 127.0.0.1:2345', '-ex', 'kill')
    $shutdown = Start-Process -FilePath $gdbPath -ArgumentList $shutdownArgs -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $shutdownOut -RedirectStandardError $shutdownErr
    Remove-Item -LiteralPath $shutdownOut, $shutdownErr -Force -ErrorAction SilentlyContinue
    for ($second = 0; $second -lt 5; $second++) {
        if ($process.HasExited) {
            return
        }
        Start-Sleep -Seconds 1
    }
}

$emulator = Get-ToolPath 'ext\tools\winuae\windows-x64\winuae-gdb.exe'
$gdb = Get-ToolPath 'ext\tools\winuae\windows-x64\m68k-amiga-elf-gdb.exe'
$resolvedRom = (Resolve-Path -LiteralPath $RomPath).Path

if (Get-NetTCPConnection -State Listen -LocalPort 2345 -ErrorAction SilentlyContinue) {
    throw 'TCP port 2345 is already in use; stop the existing WinUAE GDB session first.'
}

New-Item -ItemType Directory -Force -Path $StateDirectory | Out-Null
$resolvedStateDirectory = (Resolve-Path -LiteralPath $StateDirectory).Path
$iniPath = Join-Path $resolvedStateDirectory 'winuae.ini'

$emulatorArgs = @(
    '-ini', $iniPath,
    '-datapath', $resolvedStateDirectory,
    '-s', 'use_gui=no',
    '-s', 'headless=yes',
    '-s', 'sound_output=none',
    '-s', 'debugging_features=gdbserver',
    '-s', "kickstart_rom_file=$resolvedRom",
    '-s', 'cpu_model=68000',
    '-s', 'cpu_compatible=true',
    '-s', 'chipset=ecs',
    '-s', 'chipmem_size=2',
    '-s', 'bogomem_size=0',
    '-s', 'fastmem_size=0'
)

$process = Start-Process -FilePath $emulator -ArgumentList (ConvertTo-ArgumentListString $emulatorArgs) -PassThru
$ready = $false

try {
    for ($second = 0; $second -lt $StartupTimeoutSeconds; $second++) {
        if ($process.HasExited) {
            throw "WinUAE exited during startup (exit code $($process.ExitCode))."
        }
        if (Test-GdbListener $process.Id) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 1
    }

    if (-not $ready) {
        throw "WinUAE did not expose its GDB listener within $StartupTimeoutSeconds seconds."
    }

    $gdbArgs = @('-q', '-batch', '-ex', 'set pagination off', '-ex', 'target remote 127.0.0.1:2345')
    foreach ($command in $GdbCommand) {
        $gdbArgs += '-ex', $command
    }
    $gdbArgs += '-ex', 'kill'
    $gdbStdout = Join-Path $resolvedStateDirectory 'gdb.stdout.txt'
    $gdbStderr = Join-Path $resolvedStateDirectory 'gdb.stderr.txt'
    $gdbProcess = Start-Process -FilePath $gdb -ArgumentList (ConvertTo-ArgumentListString $gdbArgs) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $gdbStdout -RedirectStandardError $gdbStderr
    $gdbOutput = @(
        Get-Content -LiteralPath $gdbStdout -Raw
        Get-Content -LiteralPath $gdbStderr -Raw
    ) -join [Environment]::NewLine
    Remove-Item -LiteralPath $gdbStdout, $gdbStderr -Force
    if ($gdbProcess.ExitCode -ne 0) {
        throw "GDB failed with exit code $($gdbProcess.ExitCode).`n$gdbOutput"
    }

    for ($second = 0; $second -lt 10; $second++) {
        if ($process.HasExited) {
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $process.HasExited) {
        throw 'GDB completed but WinUAE did not exit after its orderly kill request.'
    }

    [pscustomobject]@{
        status = 'ok'
        state_directory = $resolvedStateDirectory
        gdb_output = $gdbOutput.Trim()
    } | ConvertTo-Json -Depth 3
}
finally {
    if (-not $process.HasExited) {
        Request-OrderlyGdbShutdown $gdb $resolvedStateDirectory
    }
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
    }
}
