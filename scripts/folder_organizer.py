#!/usr/bin/env python
"""Folder Organizer – Antigravity 用プラグイン
自動で scratch フォルダー内のファイルを種別別サブフォルダーへ移動し、空ファイルを削除します。
既存の cleanup_scratch.py と同等の機能ですが、プラグインとして独立させています。
"""
import shutil
from pathlib import Path

BASE = Path(__file__).parent

# カテゴリ → ファイルパターン（glob）
DEST = {
    "scripts": ["*.py"],
    "screenshots": ["debug_no_rooms_*.png", "debug_page_*.png"],
    "html": ["debug_page_*.html", "login_page.html", "viewer.html"],
    "logs": ["*.txt", "*.log"],
    "binaries": ["chromedriver*.exe"],
    "docs": ["README.md", "requirements_viewer.txt"],
    "assets": ["*.png", "*.jpg", "*.svg"],
}

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def move_files(patterns, target: Path):
    for pat in patterns:
        for src in BASE.glob(pat):
            if src.is_file():
                dst = target / src.name
                if dst.exists():
                    print(f"⚠️  {dst} がすでに存在するためスキップ: {src}")
                else:
                    shutil.move(str(src), str(dst))
                    print(f"✅  {src} → {dst}")

def main():
    for folder, patterns in DEST.items():
        target = BASE / folder
        ensure_dir(target)
        move_files(patterns, target)
    # 空ファイル削除
    for f in BASE.rglob("*"):
        if f.is_file() and f.stat().st_size == 0:
            print(f"🗑️  空ファイル削除: {f}")
            f.unlink()

if __name__ == "__main__":
    main()
