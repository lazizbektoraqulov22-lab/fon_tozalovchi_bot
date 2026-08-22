import os
import asyncio
import logging
import aiohttp

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    BufferedInputFile, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery,
    BotCommand
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
INSTAGRAM_LINK = "https://www.instagram.com/murodovvv_686"
TELEGRAM_LINK = "https://t.me/umidmurodov"

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram'ga obuna bo'lish", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ]
    )

def get_help_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram Admin", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="💬 Telegram Admin", url=TELEGRAM_LINK)]
        ]
    )

@dp.message(CommandStart())
@dp.message(Command("restart"))
async def start_and_restart_cmd(message: types.Message):
    welcome_text = (
        "👋 **Salom! Men rasmlar fonini tozalovchi botman.**\n\n"
        "Botdan foydalanish uchun avval Instagram sahifamizga obuna bo'ling!"
    )
    await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    help_text = "🛠 **Yordam bo'limi**\n\nNima muammo bo'lsa admin bilan bog'laning:"
    await message.answer(help_text, reply_markup=get_help_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    await callback.answer("⚠️ Avval Instagram'ga obuna bo'ling!", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(
        "📸 **Rahmat! Endi menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring.**", 
        parse_mode="Markdown"
    )

@dp.message(F.photo | F.document)
async def handle_photo_or_document(message: types.Message):
    await message.answer("⚠️ Botingiz xavfsiz rejimda ishlamoqda. Rasm fonini qayta ishlash uchun Render Environment bo'limiga API kalit kiritishingiz kerak.", parse_mode="Markdown")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menyudan /help buyrug'ini tanlang!", parse_mode="Markdown")

async def main():
    await bot.set_my_commands([
        BotCommand(command="restart", description="Botni qayta boshlash"),
        BotCommand(command="help", description="Admin bilan bog'lanish")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
