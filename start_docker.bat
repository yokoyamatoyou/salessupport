@echo off
chcp 65001
echo ========================================
echo Sales SaaS Docker起動
echo ========================================

REM Dockerの存在確認
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Dockerが見つかりません
    echo    Docker Desktopをインストールしてください
    echo    https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo Dockerがインストールされています

REM docker-composeの存在確認
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] docker-composeが見つかりません
    echo    Docker Desktopに含まれています
    pause
    exit /b 1
)

echo docker-composeが利用可能です

REM .envファイル確認
if not exist ".env" (
    if exist env.example (
        echo .envファイルをコピーしています...
        copy env.example .env
        echo .envファイルを作成しました
        echo [WARN] .envファイルのAPIキーを設定してください
    ) else (
        echo [ERROR] .envファイルとenv.exampleが見つかりません
        echo    環境変数を手動で設定してください
    )
)

REM Dockerコンテナ起動
echo Dockerコンテナを起動しています...
echo.
echo ブラウザで以下のURLにアクセスしてください:
echo   http://localhost:8080
echo.
echo 終了するには Ctrl+C を押してください
echo.

REM バックグラウンドで起動
start /b docker-compose up --build

REM 少し待ってからステータス確認
timeout /t 5 /nobreak >nul
docker-compose ps

echo.
echo ========================================
echo Docker起動完了
echo ========================================
echo.
echo ログを確認するには: docker-compose logs -f
echo 停止するには: docker-compose down
echo.
pause
