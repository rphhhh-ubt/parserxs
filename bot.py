from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
import asyncio
import os
from parser import search_product, get_prices_by_stores
from excel_gen import create_excel


bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔍 Искать в Ленте")]],
        resize_keyboard=True
    )
    await message.answer(
        "Привет! Я помогу найти товары в Ленте и сравнить цены по магазинам.\n\n"
        "Нажми кнопку ниже, чтобы начать поиск.",
        reply_markup=keyboard
    )


@dp.message(F.text == "🔍 Искать в Ленте")
async def search_button_handler(message: Message):
    await message.answer("Введите название товара для поиска:")


@dp.message(F.text)
async def search_text_handler(message: Message):
    if not message.text or message.text.startswith("/"):
        return
    
    query = message.text
    status_msg = await message.answer("🔍 Ищу товары...")
    
    try:
        products = await search_product(query)
        
        if not products:
            await status_msg.edit_text("Товары не найдены. Попробуйте изменить запрос.")
            return
        
        keyboard_buttons = []
        for product in products[:10]:
            product_name = product["name"]
            volume = product.get("volume", "")
            button_text = f"{product_name}"
            if volume:
                button_text += f" {volume}"
            
            if len(button_text) > 64:
                button_text = button_text[:61] + "..."
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"product:{product['id']}"
                )
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await status_msg.edit_text(
            f"Найдено товаров: {len(products)}\nВыберите товар для получения цен:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        await status_msg.edit_text(f"Ошибка при поиске: {str(e)}")


@dp.callback_query(F.data.startswith("product:"))
async def product_callback_handler(callback: CallbackQuery):
    await callback.answer()
    
    product_id = callback.data.split(":", 1)[1]
    
    status_msg = await callback.message.edit_text("⏳ Собираю цены по магазинам...")
    
    try:
        prices = await get_prices_by_stores(product_id)
        
        if not prices:
            await status_msg.edit_text("Не удалось получить цены для этого товара.")
            return
        
        product_name = callback.message.text.split("\n")[0] if callback.message.text else "Товар"
        
        try:
            excel_data = create_excel(product_name, prices)
            
            file = BufferedInputFile(excel_data, filename=f"{product_name[:50]}.xlsx")
            
            await callback.message.answer_document(
                document=file,
                caption=f"📊 Цены для товара: {product_name}\n"
                        f"Найдено магазинов: {len(prices)}"
            )
            
            await status_msg.edit_text("✅ Готово! Файл отправлен выше.")
            
        except Exception as e:
            await status_msg.edit_text(f"Ошибка при создании Excel: {str(e)}")
            
    except Exception as e:
        await status_msg.edit_text(f"Ошибка при получении цен: {str(e)}")


async def main():
    if not os.getenv("BOT_TOKEN"):
        raise ValueError("BOT_TOKEN is required")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped")
