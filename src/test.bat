@echo off
setlocal
set PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=python
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
 src.tests.test_platform_disk_lib
if /I not "%~1"=="--no-build" (
    call "%~dp0build.bat"
    if errorlevel 1 exit /b %errorlevel%
)
"%~dp0build\m68k_c_unit_tests.exe"
if errorlevel 1 exit /b %errorlevel%
"%PYTHON_EXE%" -m unittest %UNIT_MODULES%
exit /b %errorlevel%
