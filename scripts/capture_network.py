import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Starting network capture...")
        
        # Capture XHR/Fetch requests
        page.on("request", lambda request: print(f"REQ: {request.url} DATA: {request.post_data}") if "ajax.php" in request.url else None)
        page.on("response", lambda response: print(f"RES: {response.url} STATUS: {response.status}") if "ajax.php" in response.url else None)
        
        # Login
        await page.goto("https://drrrkari.com/")
        await page.fill("input[name='name']", "NetCapture")
        await page.click("a.bb.cc")
        await page.wait_for_load_state("networkidle")
        
        # Find a room and enter
        print("Finding room...")
        rooms = await page.query_selector_all("ul.rooms.clearfix")
        for ul in rooms:
            if await ul.query_selector("li.full"): continue
            if await ul.query_selector("i.fa-hand-paper"): continue
            
            login_btn = await ul.query_selector("button[name='login']")
            if login_btn:
                print("Entering room...")
                await login_btn.click()
                try:
                    # Wait for chat to load and capture some traffic
                    await page.wait_for_selector("#talks", timeout=10000)
                    print("In room. Capturing traffic for 10 seconds...")
                    await asyncio.sleep(10)
                    break
                except:
                    print("Failed to enter, trying next...")
                    continue
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
