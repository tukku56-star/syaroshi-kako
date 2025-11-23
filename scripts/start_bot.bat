@echo off
cd /d %~dp0\..
echo ========================================
echo   Starting Duracha Bot (20 monitors)
echo ========================================
python -m src.bot.main
pause
