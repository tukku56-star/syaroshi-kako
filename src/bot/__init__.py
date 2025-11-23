"""
Bot System Package

モジュール化されたボットシステム
"""
from .bot_manager import ParallelPatrolBot
from .room_monitor import RoomMonitor
from .constants import (
    STATUS_SEARCHING,
    STATUS_IN_ROOM,
    STATUS_FAILED,
    MAX_SEARCH_RETRIES
)

__all__ = [
    'ParallelPatrolBot',
    'RoomMonitor',
    'STATUS_SEARCHING',
    'STATUS_IN_ROOM',
    'STATUS_FAILED',
    'MAX_SEARCH_RETRIES'
]

__version__ = '2.0.0'
__author__ = 'Bot System Team'
