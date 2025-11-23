"""
デュラチャログシステム - 設定管理

全ての設定を一元管理するモジュール
"""
import os
from dataclasses import dataclass
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent


@dataclass
class Config:
    """システム設定"""
    
    # BOT設定
    MAX_MONITORS: int = 20
    POLL_INTERVAL: float = 1.5
    
    # パス設定
    LOG_DIR: Path = PROJECT_ROOT / "data" / "logs"
    BACKUP_DIR: Path = PROJECT_ROOT / "data" / "backups"
    TEMPLATE_DIR: Path = PROJECT_ROOT / "templates"
    
    # Google Drive
    GOOGLE_DRIVE_ENABLED: bool = True
    GOOGLE_DRIVE_PATH: str = r"G:\マイドライブ\開発関連"
    
    # Viewer設定
    VIEWER_HOST: str = "0.0.0.0"
    VIEWER_PORT: int = 5000
    VIEWER_DEBUG: bool = False
    APP_SECRET: str = "drrrkari-log-viewer-2025"
    
    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def from_env(cls):
        """環境変数から設定を読み込み"""
        return cls(
            MAX_MONITORS=int(os.getenv("MAX_MONITORS", "20")),
            POLL_INTERVAL=float(os.getenv("POLL_INTERVAL", "1.5")),
            VIEWER_PORT=int(os.getenv("VIEWER_PORT", "5000")),
            VIEWER_DEBUG=os.getenv("DEBUG", "False").lower() == "true",
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            GOOGLE_DRIVE_PATH=os.getenv("GOOGLE_DRIVE_PATH", r"G:\マイドライブ\開発関連"),
        )


# グローバル設定インスタンス
config = Config.from_env()

# ディレクトリ存在確認・作成
config.LOG_DIR.mkdir(parents=True, exist_ok=True)
config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print("=== Configuration ===")
    print(f"MAX_MONITORS: {config.MAX_MONITORS}")
    print(f"LOG_DIR: {config.LOG_DIR}")
    print(f"VIEWER_PORT: {config.VIEWER_PORT}")
    print(f"DEBUG: {config.VIEWER_DEBUG}")
