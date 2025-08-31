@echo off
chcp 65001
echo ========================================
echo Sales SaaS アプリ起動
echo ========================================

REM 仮想環境の存在確認
if not exist "venv" (
    echo ❌ 仮想環境が見つかりません
    echo    まず setup_venv.bat を実行してください
    pause
    exit /b 1
)

REM 仮想環境有効化
echo 🔧 仮想環境を有効化しています...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ❌ 仮想環境の有効化に失敗しました
    pause
    exit /b 1
)

REM APIキー確認
if not defined OPENAI_API_KEY (
    echo ⚠️  OPENAI_API_KEYが設定されていません
    echo    .envファイルまたは環境変数を設定してください
    echo.
    echo 続行しますか？ (Y/N)
    set /p choice=
    if /i not "!choice!"=="Y" (
        echo 起動をキャンセルしました
        pause
        exit /b 1
    )
) else (
    echo ✅ OpenAI APIキーが設定されています
)

REM Streamlit起動
echo 🚀 Streamlitアプリを起動しています...
echo.
echo ブラウザで以下のURLにアクセスしてください:
echo   http://localhost:8501
echo.
echo 終了するには Ctrl+C を押してください
echo.

streamlit run "app/ui.py" --server.headless true --server.port 8501

pause
