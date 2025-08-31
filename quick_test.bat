@echo off
chcp 65001
echo ========================================
echo Sales SaaS クイックテスト
echo ========================================

REM 仮想環境の存在確認
if exist venv (
    echo 🔧 既存の仮想環境が見つかりました
    goto :activate_venv
) else (
    echo 📦 仮想環境が見つからないため、新規作成します...
    call setup_venv.bat
    if errorlevel 1 (
        echo ❌ セットアップに失敗しました
        pause
        exit /b 1
    )
)

:activate_venv
REM 仮想環境有効化
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ❌ 仮想環境有効化に失敗しました
    pause
    exit /b 1
)

REM 基本テスト実行
echo 🧪 基本テストを実行しています...
python -c "
import sys
print('Python version:', sys.version[:5])

# 基本モジュールテスト
modules = ['streamlit', 'openai', 'pydantic']
for mod in modules:
    try:
        __import__(mod)
        print(f'✅ {mod}: OK')
    except ImportError:
        print(f'❌ {mod}: 失敗')

# OpenAI APIキー確認
import os
if os.getenv('OPENAI_API_KEY'):
    print('✅ OpenAI APIキー: 設定済み')
else:
    print('⚠️  OpenAI APIキー: 未設定')
"

echo.
echo 📊 テスト完了
echo.

REM アプリ起動確認
echo アプリを起動しますか？ (Y/N)
set /p choice=
if /i "!choice!"=="Y" (
    echo 🚀 アプリを起動しています...
    call start_app.bat
) else (
    echo テスト完了しました
    echo アプリを起動するには start_app.bat を実行してください
)

pause
