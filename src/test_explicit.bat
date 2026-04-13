@echo off
setlocal
:main_start
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
pushd "%SCRIPT_DIR%\.." >nul
set "ROOT_DIR=%CD%"
popd >nul
set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
if /I not "%~1"=="--no-build" (
    call "%SCRIPT_DIR%build.bat"
    if errorlevel 1 exit /b %errorlevel%
)
set AMIGA_INCLUDE_EXPLICIT_TESTS=1
"%PYTHON_EXE%" -m unittest ^
    src.tests.test_c_style ^
    src.tests.test_c99_assembler_codegen ^
    src.tests.test_generate_c99_assembler_subset ^
    src.tests.test_generate_c99_disassembler_subset ^
    src.tests.test_generate_c99_simulator_subset ^
 src.tests.test_platform_format_codegen ^
 src.tests.test_static_m68k_runtime
exit /b %errorlevel%
