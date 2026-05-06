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
"%PYTHON_EXE%" -m unittest src.tests_integration.test_target_usage_manifest_integration
exit /b %errorlevel%
