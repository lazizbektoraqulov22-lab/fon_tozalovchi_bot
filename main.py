import os
import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    BufferedInputFile, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")
INSTAGRAM_LINK = "https://www.instagram.com/murodovvv_686"

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

async def remove_bg_official(image_bytes: bytes) -> bytes:
    if not REMOVE_BG_API_KEY:
        logging.error("REMOVE_BG_API_KEY topilmadi!")
        return None

    timeout = aiohttp.ClientTimeout(total=40)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field('image_file', image_bytes, filename='photo.jpg', content_type='image/jpeg')
        data.add_field('size', 'auto')
        
        headers = {'X-Api-Key': REMOVE_BG_API_KEY}
        
        try:
            async with session.post('https://api.remove.bg/v1.0/removebg', data=data, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    err_text = await resp.text()
                    logging.error(f"Remove.bg API xatosi [{resp.status}]: {err_text}")
        except Exception as e:
            logging.error(f"So'rovda xatolik: {e}")
            
    return None

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        "👋 **Salom! Men rasmlar fonini tozalovchi botman.**\n\n"
        "Botdan foydalanish uchun avval Instagram sahifamizga obuna bo'ling!"
    )
    await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Xabarni o'chirishda xatolik: {e}")
        
    await callback.message.answer("📸 **Ajoyib! Endi menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring.**", parse_mode="Markdown")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    status_msg = await message.answer("⚡ **Rasm foni tozalanmoqda, kuting...**", parse_mode="Markdown")
    
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        photo_bytes_io = await bot.download_file(file_info.file_path)
        photo_bytes = photo_bytes_io.read()
        
        clean_png_bytes = await remove_bg_official(photo_bytes)
        
        if clean_png_bytes:
            result_file = BufferedInputFile(clean_png_bytes, filename="no_bg.png")
            await message.answer_document(
                document=result_file, 
                caption="✅ **Rasmingiz foni muvaffaqiyatli tozalandi!**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ API xatosi. Render'da REMOVE_BG_API_KEY kiritilganini tekshiring.")
            
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Rasmni qayta ishlashda xatolik yuz berdi.")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menga faqat **rasm** yuboring!", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
