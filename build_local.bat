@echo off
echo ========================================
echo OBS Backup Tool - Local Build Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building GUI executable...
pyinstaller --onefile --windowed ^
    --name "OBS-Backup-Tool" ^
    --add-data "config.json;." ^
    --distpath ./dist ^
    --workpath ./build ^
    --specpath ./build ^
    obs_backup_gui.py

echo.
echo Building CLI executable...
pyinstaller --onefile --console ^
    --name "OBS-Backup-Tool-CLI" ^
    --distpath ./dist ^
    --workpath ./build ^
    --specpath ./build ^
    obs_backup_tool.py

echo.
echo ========================================
echo Build Complete!
echo.
echo Executables created in: dist\
echo - OBS-Backup-Tool.exe (GUI version)
echo - OBS-Backup-Tool-CLI.exe (Command line version)
echo ========================================
pause