#!/usr/bin/env python3
"""
PoC Launcher - PowerShellを使わないローカルPoC実行スクリプト
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def check_dependencies():
    """依存関係の確認"""
    print("=== 依存関係チェック ===")

    required_modules = [
        'streamlit',
        'openai',
        'python-dotenv',
        'pydantic',
        'requests',
        'httpx'
    ]

    missing_modules = []
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}: OK")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module}: 見つかりません")

    return missing_modules

def check_api_keys():
    """APIキーの確認"""
    print("\n=== APIキー確認 ===")

    api_keys = {
        'OPENAI_API_KEY': 'OpenAI API',
        'CSE_API_KEY': 'Google Custom Search API (オプション)',
        'NEWSAPI_KEY': 'NewsAPI (オプション)',
        'CRM_API_KEY': 'CRM API (オプション)'
    }

    keys_status = {}
    for key, description in api_keys.items():
        value = os.getenv(key)
        if value:
            masked = value[:8] + '...' + value[-4:] if len(value) > 12 else value
            print(f"✅ {description}: 設定済み ({masked})")
            keys_status[key] = True
        else:
            print(f"⚠️  {description}: 未設定")
            keys_status[key] = False

    return keys_status

def test_internet_connection():
    """インターネット接続テスト"""
    print("\n=== インターネット接続テスト ===")

    try:
        import requests
        response = requests.get('https://api.openai.com/v1/models', timeout=10)
        if response.status_code == 401:
            print("✅ インターネット接続: OK (API認証が必要)")
            return True
        elif response.status_code == 200:
            print("✅ インターネット接続: OK")
            return True
        else:
            print(f"⚠️ インターネット接続: ステータス {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ インターネット接続エラー: {e}")
        return False
    except Exception as e:
        print(f"⚠️ 接続テストエラー: {e}")
        return False

def launch_streamlit():
    """Streamlitアプリの起動"""
    print("\n=== Streamlitアプリ起動 ===")

    try:
        app_path = Path("app/ui.py")
        if not app_path.exists():
            print(f"❌ アプリファイルが見つかりません: {app_path}")
            return False

        print(f"🚀 Streamlitを起動します: {app_path}")
        print("📱 ブラウザで http://localhost:8501 にアクセスしてください")
        print("🛑 終了するには Ctrl+C を押してください")

        # Streamlitをサブプロセスで起動
        cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
        process = subprocess.Popen(cmd, cwd=os.getcwd())

        print("✅ Streamlit起動完了"        print(f"   プロセスID: {process.pid}")

        # プロセスが終了するまで待機
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Streamlitを終了します...")
            process.terminate()
            process.wait()

        return True

    except FileNotFoundError:
        print("❌ PythonまたはStreamlitが見つかりません")
        return False
    except Exception as e:
        print(f"❌ Streamlit起動エラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("🎯 Sales SaaS ローカルPoC 開始")
    print("=" * 50)

    # 依存関係チェック
    missing = check_dependencies()
    if missing:
        print(f"\n❌ 不足しているモジュール: {missing}")
        print("pip install でインストールしてください:")
        print(f"pip install {' '.join(missing)}")
        return

    # APIキー確認
    keys_status = check_api_keys()

    # OpenAI APIキーが必須
    if not keys_status.get('OPENAI_API_KEY'):
        print("\n❌ OpenAI APIキーが設定されていません")
        print("環境変数 OPENAI_API_KEY を設定してください")
        return

    # インターネット接続テスト
    internet_ok = test_internet_connection()

    if not internet_ok:
        print("\n⚠️ インターネット接続に問題があります")
        print("オフラインモードで起動します")

    # Streamlit起動
    print("\n" + "=" * 50)
    success = launch_streamlit()

    if success:
        print("\n🎉 PoC完了！")
    else:
        print("\n❌ PoC失敗")

if __name__ == "__main__":
    main()
