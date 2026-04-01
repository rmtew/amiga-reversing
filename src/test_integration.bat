@echo off
setlocal
if /I not "%~1"=="--no-build" (
    call "%~dp0build.bat"
    if errorlevel 1 exit /b %errorlevel%
)
python -m unittest discover -s src\tests_integration -p "test_*.py"
exit /b %errorlevel%
