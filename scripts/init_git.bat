@echo off
REM Git リポジトリ初期化スクリプト

cd /d %~dp0\..

echo ========================================
echo   Git リポジトリ初期化
echo ========================================
echo.

REM Gitがインストールされているか確認
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [エラー] Gitがインストールされていません。
    echo scripts\install_git.bat を実行してください。
    pause
    exit /b 1
)

REM 既にGitリポジトリか確認
if exist ".git" (
    echo [警告] 既にGitリポジトリが初期化されています。
    pause
    exit /b 0
)

echo Git リポジトリを初期化中...
git init

echo.
echo Git設定中...
git config user.name "DurachaBotDev"
git config user.email "bot@example.com"

echo.
echo .gitignoreを作成中...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo env/
echo venv/
echo ENV/
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo *~
echo.
echo # Logs
echo data/logs/*.log
echo *.log
echo.
echo # Temporary files
echo *.tmp
echo *.bak
echo *.old
echo.
echo # Browser data
echo debug_*.png
echo debug_*.html
) > .gitignore

echo.
echo 初回コミットを作成中...
git add .
git commit -m "Initial commit: Modular bot system with 9 modules"

echo.
echo ========================================
echo   初期化完了！
echo ========================================
echo.
echo Gitコマンド早見表:
echo - git status          : 変更状況を確認
echo - git diff            : 差分を表示
echo - git checkout ファイル名 : ファイルを元に戻す
echo - git add .           : 全ての変更をステージング
echo - git commit -m "メッセージ" : コミット
echo.

pause
