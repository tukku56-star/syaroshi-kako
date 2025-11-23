"""
Bot Manager

全体の管理とオーケストレーション
"""
import asyncio
import random
from playwright.async_api import async_playwright
from config import config
from src.utils.logger import setup_logger
from .constants import AVAILABLE_ICONS
from .utils import generate_random_name
from .room_monitor import RoomMonitor
from .status_manager import StatusManager

logger = setup_logger("bot.bot_manager")


class ParallelPatrolBot:
    """Main bot manager - orchestrates multiple room monitors"""
    
    def __init__(self):
        """Initialize the bot manager"""
        self.monitors = []
        self.playwright = None
        self.browser = None
        self.occupied_rooms = set()
        self.reserved_rooms = set()  # Rooms being entered (prevents race conditions)
        self.room_lock = asyncio.Lock()  # Thread-safe room operations
        
    def get_occupied_rooms(self):
        """Get set of room IDs currently occupied or reserved by bots
        
        Returns:
            set: Set of room IDs (includes both occupied and reserved)
        """
        rooms = set()
        for monitor in self.monitors:
            if monitor.in_room and monitor.room_id:
                rooms.add(monitor.room_id)
        # Include reserved rooms to prevent race conditions
        rooms.update(self.reserved_rooms)
        return rooms
    
    async def reserve_room(self, room_id):
        """Reserve a room before attempting entry (prevents duplicates)
        
        Args:
            room_id: ID of the room to reserve
            
        Returns:
            bool: True if reservation successful, False if already occupied/reserved
        """
        async with self.room_lock:
            occupied = self.get_occupied_rooms()
            if room_id in occupied:
                return False
            self.reserved_rooms.add(room_id)
            logger.debug(f"Reserved room {room_id}")
            return True
    
    async def release_reservation(self, room_id):
        """Release a room reservation (called if entry fails)
        
        Args:
            room_id: ID of the room to release
        """
        async with self.room_lock:
            self.reserved_rooms.discard(room_id)
            logger.debug(f"Released reservation for room {room_id}")
    
    async def confirm_entry(self, room_id):
        """Confirm successful room entry (removes from reserved list)
        
        Args:
            room_id: ID of the room entered
        """
        async with self.room_lock:
            self.reserved_rooms.discard(room_id)
            logger.debug(f"Confirmed entry to room {room_id}")
    
    async def start(self):
        """Start all bot monitors and status saving loop"""
        async with async_playwright() as p:
            self.playwright = p
            self.browser = await p.chromium.launch(headless=True)
            
            logger.info("[*] Getting room list...")
            
            # Prepare unique icons
            available_icons = AVAILABLE_ICONS.copy()
            random.shuffle(available_icons)
            
            # Limit monitors to available icons
            num_monitors = min(config.MAX_MONITORS, len(available_icons))
            
            # Create monitors
            tasks = []
            for i in range(num_monitors):
                bot_name = generate_random_name()
                bot_icon = available_icons.pop()
                
                monitor = RoomMonitor(
                    self.browser, 
                    bot_name, 
                    bot_icon,
                    self
                )
                self.monitors.append(monitor)
                tasks.append(asyncio.create_task(monitor.start()))
            
            logger.info(f"[*] Started {len(tasks)} monitors")
            
            # Start status saving loop
            status_task = asyncio.create_task(self._status_loop())
            
            # Wait for all tasks
            await asyncio.gather(*tasks, status_task, return_exceptions=True)
    
    async def _status_loop(self):
        """Save bot status every 5 seconds"""
        while True:
            try:
                await StatusManager.save_bot_status(self.monitors)
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in status loop: {e}")
                await asyncio.sleep(5)
