"""
Room Finder

部屋の検索と入室を担当
"""
import asyncio
from src.utils.logger import setup_logger
from .constants import LOUNGE_URL

logger = setup_logger("bot.room_finder")


class RoomFinder:
    """Handle room discovery and entry logic"""
    
    @staticmethod
    async def find_and_enter_unmanned_room(page, occupied_rooms, blacklist, bot_name):
        """Find and enter an available unmanned room
        
        Args:
            page: Playwright page object
            occupied_rooms: Set of room IDs currently occupied by other bots
            blacklist: Set of room IDs to skip
            bot_name: Name of the bot for logging
            
        Returns:
            tuple: (success: bool, room_id: str, room_name: str) or (False, None, None)
        """
        try:
            # Navigate to lounge
            await page.goto(LOUNGE_URL, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Get all room elements
            room_uls = await page.query_selector_all("ul.rooms.clearfix")
            logger.info(f"[{bot_name}] Found {len(room_uls)} room elements")
            
            available_rooms = []
            
            for i, ul in enumerate(room_uls):
                try:
                    # Check if room element is visible
                    if not await ul.is_visible():
                        continue
                    
                    # Skip full rooms
                    if await ul.query_selector("li.full") or await ul.query_selector("div.full"):
                        continue
                    
                    # Skip knock-required rooms
                    if await ul.query_selector("i.fa-hand-paper"):
                        continue
                    
                    # Get room ID
                    id_input = await ul.query_selector("input[name='id']")
                    if not id_input:
                        continue
                    
                    room_id = await id_input.get_attribute("value")
                    
                    # Skip blacklisted or occupied rooms
                    if room_id in blacklist or room_id in occupied_rooms:
                        continue
                    
                    # Get room name
                    name_el = await ul.query_selector("li.name")
                    if name_el:
                        room_name = (await name_el.inner_text()).strip()
                        available_rooms.append({"id": room_id, "name": room_name})
                        logger.info(f"[{bot_name}] Found candidate: {room_name} ({room_id})")
                        
                except Exception as e:
                    logger.error(f"[{bot_name}] Error checking room {i}: {e}")
                    continue
            
            # Debug: Log how many candidates found
            logger.info(f"[{bot_name}] Total candidates: {len(available_rooms)}")
            
            # Try to enter available rooms
            for room in available_rooms:
                # Re-check if room is still available
                if room['id'] in occupied_rooms:
                    logger.debug(f"[{bot_name}] Room {room['name']} is occupied, skipping")
                    continue
                
                logger.info(f"[{bot_name}] Attempting to enter: {room['name']} ({room['id']})")
                success = await RoomFinder._enter_room(page, room['id'], bot_name)
                if success:
                    logger.info(f"[{bot_name}] Entered: {room['name']}")
                    return True, room['id'], room['name']
            
            logger.info(f"[{bot_name}] No available rooms found")
            return False, None, None
            
        except Exception as e:
            logger.error(f"[{bot_name}] Error in find_and_enter_unmanned_room: {e}")
            return False, None, None
    
    @staticmethod
    async def _enter_room(page, room_id, bot_name):
        """Enter a specific room by room_id
        
        Args:
            page: Playwright page object
            room_id: ID of the room to enter
            bot_name: Name of the bot for logging
            
        Returns:
            bool: True if successfully entered, False otherwise
        """
        try:
            # Find the room element by ID
            room_uls = await page.query_selector_all("ul.rooms.clearfix")
            
            for ul in room_uls:
                try:
                    if not await ul.is_visible():
                        continue
                    
                    id_input = await ul.query_selector("input[name='id']")
                    if not id_input:
                        continue
                    
                    found_id = await id_input.get_attribute("value")
                    if found_id == room_id:
                        logger.info(f"[{bot_name}] Found target room {room_id} for entry")
                        
                        # Check for knock requirement
                        knock_indicator = await ul.query_selector("i.fa-hand-paper")
                        if knock_indicator:
                            logger.info(f"[{bot_name}] Knock required, skipping")
                            return False
                        
                        # Click login button
                        login_btn = await ul.query_selector("button[name='login'], input[type='submit'][name='login']")
                        if login_btn and await login_btn.is_visible():
                            logger.info(f"[{bot_name}] Clicking login button for room {room_id}")
                            await login_btn.click()
                            await asyncio.sleep(2)
                            
                            # Check for password screen
                            if await RoomFinder._check_for_password_screen(page):
                                logger.info(f"[{bot_name}] Password protected, skipping")
                                await page.goto(LOUNGE_URL, wait_until="domcontentloaded")
                                await asyncio.sleep(2)
                                return False
                            
                            # Check for connection error
                            page_content = await page.content()
                            if "接続が切れました" in page_content:
                                logger.info(f"[{bot_name}] Connection error")
                                await page.goto(LOUNGE_URL, wait_until="domcontentloaded")
                                await asyncio.sleep(2)
                                return False
                            
                            # Wait for chat room to load
                            logger.info(f"[{bot_name}] Waiting for #talks...")
                            try:
                                await page.wait_for_selector("#talks", timeout=10000)
                                logger.info(f"[{bot_name}] Successfully entered room {room_id}")
                                return True
                            except Exception as e:
                                logger.error(f"[{bot_name}] Timeout waiting for #talks: {e}")
                                return False
                        else:
                            logger.info(f"[{bot_name}] Login button not found or invisible")
                            
                except Exception as e:
                    logger.error(f"[{bot_name}] Error in _enter_room loop: {e}")
                    continue
            
            logger.info(f"[{bot_name}] Target room {room_id} not found in list")
            return False
            
        except Exception as e:
            logger.error(f"[{bot_name}] Error in _enter_room: {e}")
            return False
    
    @staticmethod
    async def _check_for_password_screen(page):
        """Check if current page is a password screen
        
        Args:
            page: Playwright page object
            
        Returns:
            bool: True if password screen detected
        """
        try:
            pwd_input = await page.query_selector("input[type='password']")
            if pwd_input:
                return True
            if "password" in page.url.lower():
                return True
            return False
        except:
            return False
