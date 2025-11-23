import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to https://drrrkari.com/ ...")
        await page.goto("https://drrrkari.com/")
        
        print("Taking screenshot...")
        await page.screenshot(path="login_page.png")
        
        print("Saving HTML...")
        content = await page.content()
        with open("login_page.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Done.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
