@echo off
set SCRIPT_DIR=%~dp0..\scripts
if exist "python.exe" (
    python "%SCRIPT_DIR%\log_iteration_tokens.py"
) else (
    py -3 "%SCRIPT_DIR%\log_iteration_tokens.py" 2>nul || python "%SCRIPT_DIR%\log_iteration_tokens.py"
)

