@echo off
setlocal
:main_start
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
pushd "%SCRIPT_DIR%\.." >nul
set "ROOT_DIR=%CD%"
popd >nul
set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
set "C_TEST_EXE=%ROOT_DIR%\src\build\m68k_c_unit_tests.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
set UNIT_MODULES=^
 src.tests.test_c99_assembler_codegen ^
 src.tests.test_c99_assembler_corpus ^
 src.tests.test_c99_disassembler_corpus ^
 src.tests.test_c_style ^
 src.tests.test_generate_c99_assembler_subset ^
 src.tests.test_generate_c99_simulator_subset ^
 src.tests.test_m68k_simulator_abstract ^
 src.tests.test_m68k_simulator_oracle ^
 src.tests.test_platform_amiga_disk ^
 src.tests.test_platform_atari_st_disk ^
 src.tests.test_platform_disk_lib ^
 src.tests.test_target_usage_manifest
if /I not "%~1"=="--no-build" (
    call "%SCRIPT_DIR%build.bat"
    if errorlevel 1 exit /b %errorlevel%
)
"%C_TEST_EXE%"
if errorlevel 1 exit /b %errorlevel%
"%PYTHON_EXE%" -m unittest %UNIT_MODULES%
exit /b %errorlevel%
