#!/usr/bin/env python3
"""
依存関係をインストールするスクリプト
"""

import subprocess
import sys
import os

def install_package(package_name, description=""):
    """パッケージをインストール"""
    try:
        print(f"📦 {description}インストール中: {package_name}")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name,
            "--quiet", "--disable-pip-version-check"
        ], capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print(f"✅ {description}インストール成功: {package_name}")
            return True
        else:
            print(f"❌ {description}インストール失敗: {package_name}")
            print(f"   エラー: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {description}インストールタイムアウト: {package_name}")
        return False
    except Exception as e:
        print(f"⚠️ {description}インストールエラー: {package_name} - {e}")
        return False

def main():
    """メイン実行関数"""
    print("🔧 依存関係インストールを開始します")
    print("=" * 50)

    # 必須パッケージ
    required_packages = [
        ("streamlit-sortables>=0.2.0", "Streamlit Sortables"),
        ("streamlit-javascript>=0.1.4", "Streamlit JavaScript"),
        ("PyYAML>=6.0", "PyYAML"),
        ("jsonschema>=4.0", "JSON Schema"),
    ]

    success_count = 0
    total_count = len(required_packages)

    for package, description in required_packages:
        if install_package(package, f"{description} - "):
            success_count += 1

    print("=" * 50)
    print(f"📊 インストール結果: {success_count}/{total_count} 成功")

    if success_count == total_count:
        print("🎉 全ての依存関係がインストールされました！")
        return True
    else:
        print("⚠️ 一部の依存関係がインストールされませんでした。")
        print("手動でインストールしてください:")
        for package, _ in required_packages:
            print(f"  pip install {package}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
