@echo off
setlocal
python "%~dp0scripts\run_precommit.py"
exit /b %errorlevel%
