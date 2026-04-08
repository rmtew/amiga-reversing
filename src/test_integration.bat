@echo off
setlocal
set PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=python
set AMIGA_INCLUDE_HEAVY_UNIT_TESTS=1
set INTEGRATION_MODULES=^
 src.tests_integration.test_c99_assembler_corpus_integration ^
 src.tests_integration.test_c99_disassembler_corpus_integration ^
 src.tests.test_ir_policy_dll ^
 src.tests.test_m68k_simulator_analysis ^
 src.tests_integration.test_m68k_simulator_oracle_integration ^
 src.tests_integration.test_platform_backends_integration ^
 src.tests.test_platform_backends ^
 src.tests.test_platform_disk_cli ^
 src.tests.test_platform_file_cli ^
 src.tests.test_platform_file_manifest ^
 src.tests_integration.test_platform_manifest_integration ^
 src.tests_integration.test_vasm_mmu_oracle_integration
if /I not "%~1"=="--no-build" (
    call "%~dp0build.bat"
    if errorlevel 1 exit /b %errorlevel%
)
"%PYTHON_EXE%" -m unittest %INTEGRATION_MODULES%
exit /b %errorlevel%
