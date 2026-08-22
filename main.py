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

# 1. BOT SOZLAMALARI VA SOZLAMALAR
BOT_TOKEN = os.getenv("BOT_TOKEN")
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")
CLIPDROP_API_KEY = os.getenv("CLIPDROP_API_KEY")

# Telegram kanal va admin sozlamalari
CHANNEL_USERNAME = "@stories_686"
CHANNEL_LINK = "https://t.me/stories_686"
ADMIN_LINK = "https://t.me/umidmurodov"

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 2. REAL TELEGRAM OBUNASINI TEKSHIRISH FUNKSIYASI
async def check_user_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception as e:
        logging.error(f"Obuna tekshirishda xatlik (bot kanalda admin ekanini tekshiring): {e}")
        return False

# 3. TUGMALAR
def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ]
    )

def get_help_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Rasmiy kanal", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="💬 Admin bilan bog'lanish", url=ADMIN_LINK)]
        ]
    )

# 4. API ORQALI FONNI TOZALASH
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

# 5. HANDLERLAR
@dp.message(CommandStart())
@dp.message(Command("restart"))
async def start_and_restart_cmd(message: types.Message):
    is_sub = await check_user_sub(message.from_user.id)
    
    if is_sub:
        await message.answer(
            "👋 **Salom! Botdan foydalanishingiz mumkin.**\n\nMenga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring!", 
            parse_mode="Markdown"
        )
    else:
        welcome_text = (
            "👋 **Salom! Men rasmlar fonini HD sifatda tozalovchi botman.**\n\n"
            "⚠️ Botdan foydalanish uchun avval **Telegram kanalimizga obuna bo'ling** va 'Obunani tekshirish' tugmasini bosing!"
        )
        await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    help_text = "🛠 **Yordam bo'limi**\n\nNima muammo bo'lsa admin bilan bog'laning:"
    await message.answer(help_text, reply_markup=get_help_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    is_sub = await check_user_sub(callback.from_user.id)
    
    if is_sub:
        await callback.answer("✅ Obunangiz tasdiqlandi!", show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
            
        await callback.message.answer(
            "📸 **Rahmat! Obuna tasdiqlandi.**\n\nEndi menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring!", 
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

@dp.message(F.photo | F.document)
async def handle_photo_or_document(message: types.Message):
    is_sub = await check_user_sub(message.from_user.id)
    
    # Obuna bo'lmagan bo'lsa rasmni qayta ishlamaydi
    if not is_sub:
        await message.answer(
            "🛑 **Rasmga ishlov berilmadi!**\n\n"
            "Botdan foydalanish uchun avval Telegram kanalimizga obuna bo'lishingiz shart!",
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
                caption="✅ **Rasmingiz foni muvaffaqiyatli tozalandi!**",
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
    await message.answer("Iltimos, menga faqat **rasm** yuboring!", parse_mode="Markdown")

async def main():
    await bot.set_my_commands([
        BotCommand(command="restart", description="Botni qayta boshlash"),
        BotCommand(command="help", description="Admin bilan bog'lanish")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
