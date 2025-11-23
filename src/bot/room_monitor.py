"""
Room Monitor

個別ボットの監視タスク
"""
import asyncio
from datetime import datetime
from src.utils.logger import setup_logger
from .constants import (
    LOGIN_URL,
    STATUS_SEARCHING,
    STATUS_IN_ROOM,
    STATUS_FAILED,
    MAX_SEARCH_RETRIES,
    ACTIVITY_TIMEOUT
)
from .message_saver import MessageSaver
from .room_finder import RoomFinder

logger = setup_logger("bot.room_monitor")


class RoomMonitor:
    """Individual bot monitor instance"""
    
    def __init__(self, browser, bot_name, bot_icon, parent_bot):
        """Initialize the room monitor
        
        Args:
            browser: Playwright browser instance
            bot_name: Name of the bot
            bot_icon: Icon identifier for the bot
            parent_bot: Reference to ParallelPatrolBot parent
        """
        self.browser = browser
        self.bot_name = bot_name
        self.bot_icon = bot_icon
        self.parent_bot = parent_bot
        
        # Room state
        self.room_id = None
        self.room_name = None
        self.in_room = False
        self.blacklist = set()
        
        # Runtime state
        self.context = None
        self.page = None
        self.running = True
        self.last_activity = datetime.now()
        self.activity_timeout = ACTIVITY_TIMEOUT
        
        # Status tracking
        self.current_status = STATUS_SEARCHING
        self.search_retry_count = 0
        
    async def _handle_response(self, response):
        """Handle AJAX responses for message capture"""
        try:
            if "ajax.php" in response.url:
                try:
                    data = await response.json()
                    await MessageSaver.save_ajax_data(
                        data, 
                        self.room_id, 
                        self.room_name, 
                        self.bot_name
                    )
                    self.last_activity = datetime.now()
                except Exception as e:
                    logger.error(f"[{self.bot_name}] Error processing ajax response: {e}")
        except:
            pass
    
    async def start(self):
        """Start the bot monitor - main loop"""
        try:
            # Create browser context and page
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            self.page.on("response", self._handle_response)
            
            logger.info(f"[{self.bot_name}] Starting...")
            
            # Navigate to login page
            await self.page.goto(LOGIN_URL)
            await asyncio.sleep(2)
            
            # Select icon
            try:
                icon_selector = f"img[src*='icon_{self.bot_icon}.png']"
                icon_img = await self.page.query_selector(icon_selector)
                if icon_img:
                    await icon_img.click()
                    await asyncio.sleep(0.5)
                else:
                    # Fallback to default icon
                    default_icon = await self.page.query_selector("img[src*='icon_girl.png']")
                    if default_icon:
                        await default_icon.click()
                        await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"[{self.bot_name}] Icon selection error: {e}")
            
            # Enter bot name and login
            await self.page.fill("input[name='name']", self.bot_name)
            await self.page.click("a.bb.cc")
            await asyncio.sleep(2)
            
            # Main monitoring loop
            while self.running:
                try:
                    if not self.in_room:
                        # Try to find and enter a room
                        occupied_rooms = self.parent_bot.get_occupied_rooms()
                        success, room_id, room_name = await RoomFinder.find_and_enter_unmanned_room(
                            self.page,
                            occupied_rooms,
                            self.blacklist,
                            self.bot_name,
                            self.parent_bot  # Pass parent for room reservation
                        )
                        
                        if success:
                            # Confirm successful entry
                            await self.parent_bot.confirm_entry(room_id)
                            self.in_room = True
                            self.room_id = room_id
                            self.room_name = room_name
                            self.current_status = STATUS_IN_ROOM
                            self.search_retry_count = 0
                            self.last_activity = datetime.now()
                            logger.info(f"[{self.bot_name}] Now monitoring: {room_name}")
                        else:
                            # No rooms found
                            logger.info(f"[{self.bot_name}] No available rooms found")
                            self.search_retry_count += 1
                            
                            if self.search_retry_count >= MAX_SEARCH_RETRIES:
                                logger.warning(f"[{self.bot_name}] Max retries ({MAX_SEARCH_RETRIES}) reached, marking as failed")
                                self.current_status = STATUS_FAILED
                                self.running = False
                                break
                            
                            await asyncio.sleep(5)
                    else:
                        # Check if still in room
                        if "/room/" not in self.page.url:
                            logger.info(f"[{self.bot_name}] Disconnected from room")
                            self.in_room = False
                            self.room_id = None
                            self.room_name = None
                            self.current_status = STATUS_SEARCHING
                            continue
                        
                        # Check for inactivity
                        if (datetime.now() - self.last_activity).total_seconds() > self.activity_timeout:
                            logger.info(f"[{self.bot_name}] Inactive for too long, leaving...")
                            try:
                                await self.page.click("input[name='logout']")
                            except:
                                pass
                            self.in_room = False
                            self.current_status = STATUS_SEARCHING
                            continue
                        
                        # Just wait - messages are captured via response handler
                        await asyncio.sleep(10)
                        
                except Exception as e:
                    logger.error(f"[{self.bot_name}] Loop error: {e}")
                    await asyncio.sleep(5)
                    try:
                        await self.page.reload()
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"[{self.bot_name}] Fatal error: {e}")
        finally:
            if self.context:
                await self.context.close()
            logger.info(f"[{self.bot_name}] Stopped")
