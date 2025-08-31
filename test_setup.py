#!/usr/bin/env python3
"""
セットアップテストスクリプト
仮想環境と依存関係の問題を診断します
"""

import os
import sys
import subprocess
import importlib

def check_python_version():
    """Pythonバージョン確認"""
    print("=== Pythonバージョン確認 ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path[:3]}...")

def check_virtual_env():
    """仮想環境確認"""
    print("\n=== 仮想環境確認 ===")

    # venvフォルダ存在確認
    venv_exists = os.path.exists("venv")
    print(f"venvフォルダ存在: {'✅' if venv_exists else '❌'}")

    if venv_exists:
        # activateスクリプト存在確認
        activate_bat = os.path.join("venv", "Scripts", "activate.bat")
        activate_ps1 = os.path.join("venv", "Scripts", "activate.ps1")
        python_exe = os.path.join("venv", "Scripts", "python.exe")

        print(f"activate.bat存在: {'✅' if os.path.exists(activate_bat) else '❌'}")
        print(f"activate.ps1存在: {'✅' if os.path.exists(activate_ps1) else '❌'}")
        print(f"python.exe存在: {'✅' if os.path.exists(python_exe) else '❌'}")

        if os.path.exists(python_exe):
            try:
                result = subprocess.run([python_exe, "--version"], capture_output=True, text=True, timeout=10)
                print(f"venv Python version: {result.stdout.strip()}")
            except Exception as e:
                print(f"venv Python実行エラー: {e}")

def check_dependencies():
    """依存関係確認"""
    print("\n=== 依存関係確認 ===")

    # 必須モジュールチェック
    required_modules = [
        'streamlit',
        'openai',
        'python-dotenv',
        'pydantic',
        'requests'
    ]

    failed_modules = []
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}: OK")
        except ImportError as e:
            print(f"❌ {module}: 見つかりません - {e}")
            failed_modules.append(module)

    if failed_modules:
        print(f"\n⚠️ 不足モジュール: {failed_modules}")
        print("以下のコマンドでインストールしてください:")
        print(f"pip install {' '.join(failed_modules)}")
        return False

    return True

def check_env_file():
    """環境変数ファイル確認"""
    print("\n=== 環境変数確認 ===")

    env_file = ".env"
    if os.path.exists(env_file):
        print("✅ .envファイル: 存在します")

        # OPENAI_API_KEY確認（マスクして表示）
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else api_key
            print(f"✅ OPENAI_API_KEY: 設定済み ({masked})")
        else:
            print("❌ OPENAI_API_KEY: 未設定")

        # .envファイルの内容確認
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"📄 .envファイル行数: {len(lines)}")
                for line in lines[:3]:  # 最初の3行のみ表示
                    if line.strip() and not line.startswith('#'):
                        key = line.split('=')[0] if '=' in line else line.strip()
                        print(f"   設定項目: {key}")
        except Exception as e:
            print(f"⚠️ .envファイル読み込みエラー: {e}")
    else:
        print("❌ .envファイル: 見つかりません")
        print("   env.exampleからコピーしてください")

def check_app_structure():
    """アプリ構造確認"""
    print("\n=== アプリ構造確認 ===")

    required_files = [
        "app/ui.py",
        "app/pages/pre_advice.py",
        "app/pages/post_review.py",
        "app/pages/icebreaker.py",
        "requirements.txt"
    ]

    for file_path in required_files:
        exists = os.path.exists(file_path)
        print(f"{'✅' if exists else '❌'} {file_path}: {'存在' if exists else '見つかりません'}")

def main():
    """メイン実行関数"""
    print("🔍 Sales SaaS セットアップ診断")
    print("=" * 50)

    check_python_version()
    check_virtual_env()
    check_dependencies()
    check_env_file()
    check_app_structure()

    print("\n" + "=" * 50)
    print("📊 診断完了")

    # 問題のサマリー
    issues = []

    if not os.path.exists("venv"):
        issues.append("仮想環境が作成されていません")

    if not check_dependencies():
        issues.append("依存関係が不足しています")

    if not os.getenv("OPENAI_API_KEY"):
        issues.append("OPENAI_API_KEYが設定されていません")

    if issues:
        print("\n⚠️ 検出された問題:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n🔧 解決方法:")
        print("  1. setup_venv.bat を実行")
        print("  2. .envファイルにAPIキーを設定")
        print("  3. 必要に応じて依存関係を再インストール")
    else:
        print("\n✅ セットアップは正常です！")
        print("🚀 start_app.bat を実行してアプリを起動してください")

if __name__ == "__main__":
    main()
