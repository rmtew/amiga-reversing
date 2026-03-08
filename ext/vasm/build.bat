@echo off
REM Build vasm for m68k with Motorola syntax using MSVC
REM Usage: build.bat [clean]

REM Find Visual Studio
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
    echo ERROR: vswhere not found. Is Visual Studio installed?
    exit /b 1
)

REM Get VS install path
for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -property installationPath`) do set "VSINSTALL=%%i"
if not defined VSINSTALL (
    echo ERROR: No Visual Studio installation found.
    exit /b 1
)

REM Set up MSVC environment
call "%VSINSTALL%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to set up MSVC environment.
    exit /b 1
)

echo Building vasm m68k (Motorola syntax) with MSVC...

if "%1"=="clean" goto :clean

REM Create obj directory
if not exist obj mkdir obj

nmake /nologo /f Makefile.Win32 CPU=m68k SYNTAX=mot
if errorlevel 1 (
    echo BUILD FAILED
    exit /b 1
)

echo.
echo Build complete: vasmm68k_mot.exe
exit /b 0

:clean
nmake /nologo /f Makefile.Win32 CPU=m68k SYNTAX=mot clean
echo Clean complete.
exit /b 0
