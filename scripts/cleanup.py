"""
古いログファイルとバックアップをクリーンアップ
"""
import shutil
from pathlib import Path
from datetime import datetime, timedelta


def cleanup_old_files(directory, days=7, pattern="*"):
    """指定日数より古いファイルを削除"""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"Directory not found: {directory}")
        return
    
    cutoff = datetime.now() - timedelta(days=days)
    deleted_count = 0
    
    for file in dir_path.glob(pattern):
        if file.is_file():
            if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                file.unlink()
                print(f"Deleted: {file.name}")
                deleted_count += 1
    
    print(f"\n✅ Deleted {deleted_count} files older than {days} days")


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    
    print("=== Cleanup Script ===\n")
    
    # バックアップクリーンアップ
    backup_dir = project_root / "data" / "backups"
    print(f"Cleaning backups in: {backup_dir}")
    cleanup_old_files(backup_dir, days=7, pattern="*.json")
    
    # デバッグファイルクリーンアップ
    debug_dir = project_root / "archive" / "debug_files"
    print(f"\nCleaning debug files in: {debug_dir}")
    cleanup_old_files(debug_dir, days=30, pattern="debug_*")
    
    print("\n✅ Cleanup complete!")
