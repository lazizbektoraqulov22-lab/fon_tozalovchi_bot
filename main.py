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

# 1. BOT SOZLAMALARI
BOT_TOKEN = os.getenv("BOT_TOKEN")
INSTAGRAM_LINK = "https://www.instagram.com/murodovvv_686"
TELEGRAM_LINK = "https://t.me/umidmurodov"

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 2. TUGMALAR (KEYBOARDS)
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

# 3. BEPUL VA CHEKLAVSIZ API ORQALI FONNI HD OLISH
async def remove_bg_free_api(image_bytes: bytes) -> bytes:
    # Ishonchli ochiq zaxira xizmati
    url = "https://api.vocal.ai/v1/remove-bg" 
    
    timeout = aiohttp.ClientTimeout(total=45)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field('file', image_bytes, filename='photo.jpg', content_type='image/jpeg')
        
        try:
            async with session.post(url, data=data) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    # Muqobil 2-zaxira API (Clipdrop Free Gateway)
                    async with session.post("https://clipdrop-api.co/remove-background/v1", data=data) as resp2:
                        if resp2.status == 200:
                            return await resp2.read()
                        logging.error(f"API Error status: {resp.status} / {resp2.status}")
        except Exception as e:
            logging.error(f"Request error: {e}")
            
    return None

# 4. HANDLERLAR
@dp.message(CommandStart())
@dp.message(Command("restart"))
async def start_and_restart_cmd(message: types.Message):
    welcome_text = (
        "👋 **Salom! Men rasmlar fonini HD sifatda tozalovchi botman.**\n\n"
        "Botdan foydalanish uchun avval Instagram sahifamizga obuna bo'ling!"
    )
    await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    help_text = (
        "🛠 **Yordam bo'limi**\n\n"
        "Nima muammo bo'lsa admin bilan bog'laning:"
    )
    await message.answer(help_text, reply_markup=get_help_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    await callback.answer(
        "⚠️ Iltimos, avval Instagram sahifamizga kirib obuna bo'ling, so'ngra botdan foydalanishingiz mumkin!", 
        show_alert=True
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(
        "📸 **Rahmat! Endi menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring.**\n"
        "*(Sifat buzilmasligi uchun rasmni Hujjat ko'rinishida yuborishingiz ham mumkin)*", 
        parse_mode="Markdown"
    )

@dp.message(F.photo | F.document)
async def handle_photo_or_document(message: types.Message):
    status_msg = await message.answer("⚡ **Rasm foni HD sifatda tozalanmoqda, kuting...**", parse_mode="Markdown")
    
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document and message.document.mime_type.startswith("image/"):
            file_id = message.document.file_id
        else:
            await status_msg.edit_text("❌ Iltimos, faqat rasm fayli yuboring!")
            return

        file_info = await bot.get_file(file_id)
        photo_bytes_io = await bot.download_file(file_info.file_path)
        photo_bytes = photo_bytes_io.read()
        
        clean_png_bytes = await remove_bg_free_api(photo_bytes)
        
        if clean_png_bytes:
            result_file = BufferedInputFile(clean_png_bytes, filename="no_bg_hd.png")
            await message.answer_document(
                document=result_file, 
                caption="✅ **Rasmingiz foni muvaffaqiyatli va HD sifatda tozalandi!**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Qayta ishlashda xatolik yuz berdi. Qaytadan urinib ko'ring.")
            
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Qayta ishlashda xatolik yuz berdi.")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menga faqat **rasm** yuboring yoki menyudan /help buyrug'ini tanlang!", parse_mode="Markdown")

# 5. MENYU BUYRUQLARI (FAQAT RESTART VA HELP)
async def main():
    await bot.set_my_commands([
        BotCommand(command="restart", description="Botni qayta boshlash"),
        BotCommand(command="help", description="Admin bilan bog'lanish")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
