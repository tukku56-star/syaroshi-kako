#!/usr/bin/env python
"""Plugin Launcher – Antigravity 用簡易コンソールメニュー
インストール済みプラグイン (extensions.json に登録されたもの) を一覧表示し、
番号を入力すると対応するエントリーポイントのスクリプトを実行します。

使い方:
    cd C:\\Users\\admin\\.gemini\\antigravity\\scratch
    python plugin_launcher.py
"""
import json
import subprocess
import sys
from pathlib import Path

EXT_FILE = Path(__file__).parent / "plugins.json"

def load_plugins():
    if not EXT_FILE.is_file():
        print(f"⚠️ extensions.json が見つかりません: {EXT_FILE}")
        return []
    try:
        data = json.loads(EXT_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ JSON 読み込みエラー: {e}")
        return []
    return data

def menu(plugins):
    print("=== Antigravity Plugin Launcher ===")
    for i, p in enumerate(plugins, 1):
        print(f"{i}. {p.get('name', 'Unnamed')} – {p.get('description', '')}")
    print("0. 終了")
    try:
        choice = int(input("番号を入力してください: "))
    except ValueError:
        print("入力が無効です。終了します。")
        return None
    if choice == 0:
        return None
    if 1 <= choice <= len(plugins):
        return plugins[choice - 1]
    print("範囲外です。終了します。")
    return None

def run_plugin(plugin):
    entry = plugin.get("entry_point")
    if not entry:
        print("エントリーポイントが定義されていません")
        return
    script_path = Path(entry)
    if not script_path.is_file():
        print(f"⚠️ スクリプトが見つかりません: {script_path}")
        return
    # Windows では python で実行、拡張子が .py 以外でも python で実行できるようにする
    cmd = [sys.executable, str(script_path)]
    print(f"▶️ 実行: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 実行失敗: {e}")

def main():
    plugins = load_plugins()
    if not plugins:
        print("プラグインが登録されていません。")
        return
    while True:
        sel = menu(plugins)
        if sel is None:
            break
        run_plugin(sel)
        print("---\n")

if __name__ == "__main__":
    main()
