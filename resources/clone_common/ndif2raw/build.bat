@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b %errorlevel%

set OUTDIR=build
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

cl /nologo /W4 /WX /std:c11 /D_CRT_SECURE_NO_WARNINGS /I . ^
    /Fe:%OUTDIR%\ndif2raw.exe ^
    ndif2raw.c appledouble.c resourcefork.c logger.c
exit /b %errorlevel%
