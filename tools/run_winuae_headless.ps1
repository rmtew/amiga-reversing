[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$RomPath,

    [string]$Floppy0,

    [string]$StateDirectory,

    [string[]]$GdbCommand = @(),

    [ValidateRange(1, 120)]
    [int]$ContinueSeconds,

    [ValidateRange(1, 120)]
    [int]$LoadSegWatchSeconds,

    [string]$TargetPayloadPath,

    [string]$BreakpointAddress,

    [string]$BreakpointSourceOffset,

    [string]$ObservationMemoryAddress,

    [string]$ObservationMemoryEquals,

    [ValidateRange(1, 120)]
    [int]$BreakpointWaitSeconds = 60,

    [ValidateRange(1, 120)]
    [int]$StartupTimeoutSeconds = 45,

    [ValidateRange(1, 300)]
    [int]$GdbTimeoutSeconds = 45
)

$ErrorActionPreference = 'Stop'

if (($ContinueSeconds -or $LoadSegWatchSeconds) -and $GdbCommand.Count) {
    throw 'ContinueSeconds/LoadSegWatchSeconds cannot be combined with GdbCommand.'
}
if ($LoadSegWatchSeconds -and -not $ContinueSeconds) {
    throw 'LoadSegWatchSeconds requires ContinueSeconds.'
}
if ($TargetPayloadPath -and -not $ContinueSeconds) {
    throw 'TargetPayloadPath requires ContinueSeconds.'
}
if ($BreakpointAddress -and -not $ContinueSeconds) {
    throw 'BreakpointAddress requires ContinueSeconds.'
}
if ($BreakpointSourceOffset -and -not $ContinueSeconds) {
    throw 'BreakpointSourceOffset requires ContinueSeconds.'
}
if ($ObservationMemoryAddress -and -not $ContinueSeconds) {
    throw 'ObservationMemoryAddress requires ContinueSeconds.'
}
if ($ObservationMemoryEquals -and -not $ObservationMemoryAddress) {
    throw 'ObservationMemoryEquals requires ObservationMemoryAddress.'
}
if ($BreakpointAddress -and $BreakpointSourceOffset) {
    throw 'Specify either BreakpointAddress or BreakpointSourceOffset, not both.'
}

if ([string]::IsNullOrWhiteSpace($StateDirectory)) {
    $StateDirectory = Join-Path 'C:\tmp' (Join-Path 'amiga-reversing2\winuae\runs' ([guid]::NewGuid().ToString()))
}

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
    $shutdown = Start-Process -FilePath $gdbPath -ArgumentList $shutdownArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput $shutdownOut -RedirectStandardError $shutdownErr
    if (-not $shutdown.WaitForExit(5000)) {
        Stop-Process -Id $shutdown.Id -Force
    }
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
$resolvedFloppy0 = if ($Floppy0) { (Resolve-Path -LiteralPath $Floppy0).Path } else { $null }
$resolvedTargetPayload = if ($TargetPayloadPath) { (Resolve-Path -LiteralPath $TargetPayloadPath).Path } else { $null }

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
    '-s', 'chipset=ocs',
    '-s', 'chipmem_size=1',
    '-s', 'bogomem_size=2',
    '-s', 'fastmem_size=0',
    '-s', 'floppy_speed=800'
)
if ($resolvedFloppy0) {
    $emulatorArgs += '-s', "floppy0=$resolvedFloppy0"
}

$process = Start-Process -FilePath $emulator -ArgumentList (ConvertTo-ArgumentListString $emulatorArgs) -WindowStyle Hidden -PassThru
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

    $gdbStdout = Join-Path $resolvedStateDirectory 'gdb.stdout.txt'
    $gdbStderr = Join-Path $resolvedStateDirectory 'gdb.stderr.txt'
    if ($ContinueSeconds) {
        $python = (Get-Command py.exe -ErrorAction Stop).Source
        $sessionScript = Get-ToolPath 'tools\winuae_gdb_session.py'
        $ndk = Get-ToolPath 'knowledge\amiga_ndk_includes_parsed.json'
        $gdbArgs = @($sessionScript, '--gdb', $gdb, '--ndk', $ndk, '--continue-seconds', "$ContinueSeconds")
        if ($LoadSegWatchSeconds) {
            $gdbArgs += '--loadseg-watch-seconds', "$LoadSegWatchSeconds"
        }
        if ($resolvedTargetPayload) {
            $gdbArgs += '--target-payload', $resolvedTargetPayload
        }
        if ($BreakpointAddress) {
            $gdbArgs += '--breakpoint-address', $BreakpointAddress, '--breakpoint-wait-seconds', "$BreakpointWaitSeconds"
        }
        if ($BreakpointSourceOffset) {
            $gdbArgs += '--breakpoint-source-offset', $BreakpointSourceOffset, '--breakpoint-wait-seconds', "$BreakpointWaitSeconds"
        }
        if ($ObservationMemoryAddress) {
            $gdbArgs += '--observation-memory-address', $ObservationMemoryAddress
        }
        if ($ObservationMemoryEquals) {
            $gdbArgs += '--observation-memory-equals', $ObservationMemoryEquals
        }
        $gdbProcess = Start-Process -FilePath $python -ArgumentList (ConvertTo-ArgumentListString $gdbArgs) -WindowStyle Hidden -PassThru -RedirectStandardOutput $gdbStdout -RedirectStandardError $gdbStderr
        $gdbTimeoutMilliseconds = ($GdbTimeoutSeconds + $ContinueSeconds + $LoadSegWatchSeconds + $(if ($BreakpointAddress -or $BreakpointSourceOffset) { $BreakpointWaitSeconds } else { 0 }) + 15) * 1000
    }
    else {
        $gdbArgs = @('-q', '-batch', '-ex', 'set pagination off', '-ex', 'target remote 127.0.0.1:2345')
        foreach ($command in $GdbCommand) {
            $gdbArgs += '-ex', $command
        }
        $gdbArgs += '-ex', 'kill'
        $gdbProcess = Start-Process -FilePath $gdb -ArgumentList (ConvertTo-ArgumentListString $gdbArgs) -WindowStyle Hidden -PassThru -RedirectStandardOutput $gdbStdout -RedirectStandardError $gdbStderr
        $gdbTimeoutMilliseconds = $GdbTimeoutSeconds * 1000
    }
    if (-not $gdbProcess.WaitForExit($gdbTimeoutMilliseconds)) {
        Stop-Process -Id $gdbProcess.Id -Force
        throw "GDB did not complete within $([math]::Ceiling($gdbTimeoutMilliseconds / 1000)) seconds."
    }
    $gdbOutput = @(
        Get-Content -LiteralPath $gdbStdout -Raw
        Get-Content -LiteralPath $gdbStderr -Raw
    ) -join [Environment]::NewLine
    Remove-Item -LiteralPath $gdbStdout, $gdbStderr -Force
    $sessionObservation = $null
    if ($ContinueSeconds) {
        try {
            $sessionObservation = $gdbOutput | ConvertFrom-Json -ErrorAction Stop
        }
        catch {
            throw "Persistent GDB session did not return JSON.`n$gdbOutput"
        }
        if ($sessionObservation.status -ne 'ok') {
            throw "Persistent GDB session did not complete successfully.`n$gdbOutput"
        }
    }
    elseif ($gdbOutput -notmatch '\[Inferior 1 \(Remote target\) killed\]') {
        throw "GDB did not confirm orderly remote shutdown.`n$gdbOutput"
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
        floppy0 = $resolvedFloppy0
        target_payload = $resolvedTargetPayload
        continue_seconds = $ContinueSeconds
        loadseg_watch_seconds = $LoadSegWatchSeconds
        gdb_output = if ($ContinueSeconds) { $null } else { $gdbOutput.Trim() }
        observation = $sessionObservation
    } | ConvertTo-Json -Depth 10
}
finally {
    if (-not $process.HasExited) {
        Request-OrderlyGdbShutdown $gdb $resolvedStateDirectory
    }
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
    }
}
