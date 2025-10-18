@echo off
echo OBS Backup Tool GUI を起動しています...
python obs_backup_gui.py
if errorlevel 1 (
    echo.
    echo エラーが発生しました。Pythonがインストールされているか確認してください。
    pause
)