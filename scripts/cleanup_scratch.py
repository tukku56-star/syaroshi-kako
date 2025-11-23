#!/usr/bin/env python
"""Organize the Antigravity scratch folder.
Creates subfolders and moves files by type.
Empty files are removed.
"""
import os
import shutil
from pathlib import Path

BASE = Path(__file__).parent

# Destination mapping: folder name -> glob patterns
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
                    print(f"⚠️  {dst} already exists – skipping {src}")
                else:
                    shutil.move(str(src), str(dst))
                    print(f"✅  Moved {src} → {dst}")

def main():
    for folder, patterns in DEST.items():
        target = BASE / folder
        ensure_dir(target)
        move_files(patterns, target)
    # Delete empty files (size == 0)
    for f in BASE.rglob("*"):
        if f.is_file() and f.stat().st_size == 0:
            print(f"🗑️  Removing empty file {f}")
            f.unlink()

if __name__ == "__main__":
    main()
