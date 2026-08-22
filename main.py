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
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")
CLIPDROP_API_KEY = os.getenv("CLIPDROP_API_KEY")

INSTAGRAM_LINK = "https://www.instagram.com/murodovvv_686"
TELEGRAM_LINK = "https://t.me/umidmurodov"

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Obuna bo'lgan foydalanuvchilar ro'yxati (xotirada saqlash)
SUBSCRIBED_USERS = set()

# 2. TUGMALAR
def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram'ga obuna bo'lish", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="✅ Obuna bo'ldim / Tekshirish", callback_data="check_sub")]
        ]
    )

def get_help_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram Admin", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="💬 Telegram Admin", url=TELEGRAM_LINK)]
        ]
    )

# 3. API ORQALI FONNI TOZALASH
async def process_remove_bg(image_bytes: bytes) -> bytes:
    timeout = aiohttp.ClientTimeout(total=45)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        if REMOVE_BG_API_KEY:
            url = "https://api.remove.bg/v1.0/removebg"
            headers = {"X-Api-Key": REMOVE_BG_API_KEY}
            data = aiohttp.FormData()
            data.add_field('image_file', image_bytes, filename='photo.jpg', content_type='image/jpeg')
            data.add_field('size', 'auto')
            
            try:
                async with session.post(url, headers=headers, data=data) as resp:
                    if resp.status == 200:
                        return await resp.read()
            except Exception as e:
                logging.error(f"Remove.bg xatosi: {e}")

        if CLIPDROP_API_KEY:
            url = "https://clipdrop-api.co/remove-background/v1"
            headers = {"x-api-key": CLIPDROP_API_KEY}
            data = aiohttp.FormData()
            data.add_field('image_file', image_bytes, filename='photo.jpg', content_type='image/jpeg')
            
            try:
                async with session.post(url, headers=headers, data=data) as resp:
                    if resp.status == 200:
                        return await resp.read()
            except Exception as e:
                logging.error(f"Clipdrop xatosi: {e}")

    return None

# 4. HANDLERLAR
@dp.message(CommandStart())
@dp.message(Command("restart"))
async def start_and_restart_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id in SUBSCRIBED_USERS:
        SUBSCRIBED_USERS.remove(user_id) # Qayta restart berganda obunani qayta so'raydi
        
    welcome_text = (
        "👋 **Salom! Men rasmlar fonini HD sifatda tozalovchi botman.**\n\n"
        "⚠️ **Botdan foydalanish uchun avval Instagram sahifamizga obuna bo'ling va pastdagi 'Tekshirish' tugmasini bosing!**"
    )
    await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    help_text = "🛠 **Yordam bo'limi**\n\nNima muammo bo'lsa admin bilan bog'laning:"
    await message.answer(help_text, reply_markup=get_help_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    SUBSCRIBED_USERS.add(user_id)
    
    await callback.answer("✅ Obuna tasdiqlandi!", show_alert=False)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(
        "📸 **Rahmat! Obuna tasdiqlandi.**\n\n"
        "Endi menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring!", 
        parse_mode="Markdown"
    )

@dp.message(F.photo | F.document)
async def handle_photo_or_document(message: types.Message):
    user_id = message.from_user.id
    
    # Obuna bo'lmagan bo'lsa rasmni qayta ishlamaydi
    if user_id not in SUBSCRIBED_USERS:
        await message.answer(
            "🛑 **Rasmga ishlov berish to'xtatildi!**\n\n"
            "Botdan foydalanish uchun avval Instagram sahifamizga obuna bo'lib, **'✅ Obuna bo'ldim / Tekshirish'** tugmasini bosing!",
            reply_markup=get_sub_keyboard(),
            parse_mode="Markdown"
        )
        return

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
        
        clean_png_bytes = await process_remove_bg(photo_bytes)
        
        if clean_png_bytes:
            result_file = BufferedInputFile(clean_png_bytes, filename="no_bg_hd.png")
            await message.answer_document(
                document=result_file, 
                caption="✅ **Rasmingiz foni muvaffaqiyatli va HD sifatda tozalandi!**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ API xatosi. Key limiti tugagan bo'lishi mumkin.")
            
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Qayta ishlashda xatolik yuz berdi.")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menga faqat **rasm** yuboring yoki menyudan /help buyrug'ini tanlang!", parse_mode="Markdown")

async def main():
    await bot.set_my_commands([
        BotCommand(command="restart", description="Botni qayta boshlash"),
        BotCommand(command="help", description="Admin bilan bog'lanish")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
