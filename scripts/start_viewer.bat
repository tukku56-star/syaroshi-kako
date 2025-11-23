@echo off
cd /d %~dp0\..
echo ========================================
echo   Starting Log Viewer
echo   Access: http://localhost:5000
echo ========================================
python -m src.viewer.log_viewer
pause
