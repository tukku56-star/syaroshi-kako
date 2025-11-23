@echo off
REM Git for Windows インストールスクリプト
REM 管理者権限で実行してください

echo ========================================
echo   Git for Windows インストーラー
echo ========================================
echo.

REM wingetがインストールされているか確認
where winget >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [エラー] winget が見つかりません。
    echo.
    echo 手動インストール方法:
    echo 1. https://git-scm.com/download/win にアクセス
    echo 2. "64-bit Git for Windows Setup" をダウンロード
    echo 3. インストーラーを実行
    echo 4. デフォルト設定でインストール
    echo.
    pause
    exit /b 1
)

echo wingetを使用してGitをインストールします...
echo.

REM Gitをインストール
winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   インストール完了！
    echo ========================================
    echo.
    echo 次の手順:
    echo 1. このウィンドウを閉じる
    echo 2. 新しいPowerShellウィンドウを開く
    echo 3. "git --version" を実行して確認
    echo.
) else (
    echo.
    echo [エラー] インストールに失敗しました。
    echo.
)

pause
