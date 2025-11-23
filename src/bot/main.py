"""
Bot System Main Entry Point

メインエントリーポイント - ボットシステムの起動
"""
import asyncio
from src.utils.logger import setup_logger
from .bot_manager import ParallelPatrolBot

logger = setup_logger("bot.main")


def main():
    """Main entry point for the bot system"""
    logger.info("=== Bot System Starting ===")
    
    bot = ParallelPatrolBot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("\n[*] Stopping...")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
    finally:
        logger.info("=== Bot System Stopped ===")


if __name__ == "__main__":
    main()
