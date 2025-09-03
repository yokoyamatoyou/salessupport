@echo off
chcp 65001
echo ========================================
echo Sales SaaS 仮想環境セットアップ
echo ========================================

REM Pythonの存在確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Pythonが見つかりません。Pythonをインストールしてください。
    echo    https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Pythonがインストールされています

REM 仮想環境作成
if not exist "venv" (
    echo 仮想環境を作成しています...
    python -m venv "venv"
    if errorlevel 1 (
        echo [ERROR] 仮想環境の作成に失敗しました
        pause
        exit /b 1
    )
    echo 仮想環境を作成しました
) else (
    echo 仮想環境が既に存在します
)

REM 仮想環境有効化
echo 仮想環境を有効化しています...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] 仮想環境の有効化に失敗しました
    pause
    exit /b 1
)

REM pip更新
echo pipを更新しています...
python -m pip install --upgrade pip --quiet

REM 依存関係インストール
echo 依存関係をインストールしています...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] 依存関係のインストールに失敗しました
    pause
    exit /b 1
)

echo 全ての依存関係がインストールされました

REM .envファイル作成（存在しない場合）
if not exist .env (
    if exist env.example (
        echo .envファイルをコピーしています...
        copy env.example .env
        echo .envファイルを作成しました
        echo [WARN] .envファイルのAPIキーを設定してください
    ) else (
        echo [WARN] env.exampleファイルが見つかりません
    )
)

echo.
echo ========================================
echo セットアップ完了！
echo ========================================
echo.
echo アプリを起動するには start_app.bat を実行してください
echo.
echo 仮想環境を手動で有効化する場合:
echo   call venv\Scripts\activate.bat
echo.
pause
