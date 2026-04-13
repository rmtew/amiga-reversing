@echo off
setlocal
if /I "%~1"=="--lock-held" goto :shift_to_main
if not defined AMIGA_BUILD_LOCK_HELD goto :lock_wrap
:main
goto :main_start
:shift_to_main
shift
:main_start
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
pushd "%SCRIPT_DIR%\.." >nul
set "ROOT_DIR=%CD%"
popd >nul
set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
set "PRECOMMIT_PY=%SCRIPT_DIR%\scripts\run_precommit.py"
if not exist "%PRECOMMIT_PY%" set "PRECOMMIT_PY=src\scripts\run_precommit.py"
"%PYTHON_EXE%" "%PRECOMMIT_PY%"
exit /b %errorlevel%

:lock_wrap
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
pushd "%SCRIPT_DIR%\.." >nul
set "ROOT_DIR=%CD%"
popd >nul
set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
set "AMIGA_BUILD_LOCK_SCRIPT=%~f0"
set "AMIGA_BUILD_LOCK_ARGS=%*"
"%PYTHON_EXE%" "%SCRIPT_DIR%\scripts\with_build_lock.py" --batch-env
exit /b %errorlevel%
