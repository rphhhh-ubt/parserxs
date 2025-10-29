import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from playwright.async_api import async_playwright

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Welcome! I'm a bot with Playwright capabilities.\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/screenshot <url> - Take a screenshot of a URL\n"
        "/health - Check bot health"
    )


@dp.message(Command("health"))
async def cmd_health(message: Message):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
        await message.answer("✅ Bot is healthy! Playwright is working correctly.")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        await message.answer(f"❌ Health check failed: {str(e)}")


@dp.message(Command("screenshot"))
async def cmd_screenshot(message: Message):
    if not message.text or len(message.text.split()) < 2:
        await message.answer("Please provide a URL. Usage: /screenshot <url>")
        return
    
    url = message.text.split(maxsplit=1)[1]
    
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    status_msg = await message.answer("⏳ Taking screenshot...")
    
    try:
        timeout = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000"))
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu"
                ]
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                locale=os.getenv("LOCALE", "en-US")
            )
            page = await context.new_page()
            
            await page.goto(url, timeout=timeout, wait_until="networkidle")
            screenshot_bytes = await page.screenshot(full_page=False)
            
            await browser.close()
        
        await message.answer_photo(
            photo=screenshot_bytes,
            caption=f"Screenshot of {url}"
        )
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Screenshot failed for {url}: {e}")
        await status_msg.edit_text(f"❌ Failed to take screenshot: {str(e)}")


async def main():
    logger.info("Starting bot...")
    
    if not os.getenv("BOT_TOKEN"):
        logger.error("BOT_TOKEN environment variable is not set!")
        raise ValueError("BOT_TOKEN is required")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
