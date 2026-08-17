import asyncio
import io
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv
from PIL import Image, ImageOps
from rembg import new_session, remove

load_dotenv()

BOT_TOKEN: str = str(os.getenv("BOT_TOKEN"))
INSTAGRAM_URL: str = str(
    os.getenv("INSTAGRAM_URL", "https://instagram.com/murodovvv.686")
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

session = new_session("isnet-general-use")
subscribed_users = set()


def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 Instagram'ga obuna bo'lish", url=INSTAGRAM_URL
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Obunani tekshirish", callback_data="check_sub"
                )
            ],
        ]
    )


def get_help_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👨‍💻 Admin bilan bog'lanish",
                    url="https://t.me/umidmurodov",
                )
            ]
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id in subscribed_users:
        subscribed_users.remove(user_id)

    await message.answer(
        f"Assalomu alaykum, <b>{message.from_user.full_name}</b>! 👋\n\n"
        "⚠️ Botdan foydalanish uchun avval bizning <b>Instagram</b> sahifamizga obuna bo'ling.\n\n"
        "Obuna bo'lgach, pastdagi <b>'✅ Obunani tekshirish'</b> tugmasini bosing!",
        reply_markup=get_sub_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Nima muammo bo'lsa admin bilan bog'laning:",
        reply_markup=get_help_keyboard(),
    )


@router.callback_query(F.data == "check_sub")
async def check_subscription(call: CallbackQuery):
    subscribed_users.add(call.from_user.id)
    await call.answer("✅ Obunangiz tasdiqlandi!", show_alert=True)
    await call.message.delete()
    await call.message.answer(
        "🎉 <b>Rahmat! Botdan foydalanishingiz mumkin.</b>\n\n"
        "📸 Orqa fonini o'chirmoqchi bo'lgan <b>rasmingizni yuboring</b>!",
        parse_mode=ParseMode.HTML,
    )


def process_image_accurate(photo_bytes_val: bytes) -> bytes:
    input_image = Image.open(io.BytesIO(photo_bytes_val))
    input_image = ImageOps.exif_transpose(input_image).convert("RGBA")
    orig_size = input_image.size

    output_image = remove(input_image, session=session)

    if output_image.size != orig_size:
        output_image = output_image.resize(orig_size, Image.Resampling.LANCZOS)

    out_buffer = io.BytesIO()
    output_image.save(out_buffer, format="PNG", compress_level=0)
    return out_buffer.getvalue()


@router.message(F.photo | F.document)
async def process_photo(message: Message):
    user_id = message.from_user.id

    if user_id not in subscribed_users:
        await message.answer(
            "⚠️ Avval Instagram sahifamizga obuna bo'ling va tekshirish tugmasini bosing!",
            reply_markup=get_sub_keyboard(),
        )
        return

    status_msg = await message.answer(
        "⚡ Rasmingiz qabul qilindi, aniq va toza qirqilmoqda..."
    )

    try:
        photo_bytes = io.BytesIO()

        if message.photo:
            photo = message.photo[-1]
            await bot.download(photo.file_id, destination=photo_bytes)
        elif (
            message.document
            and message.document.mime_type
            and message.document.mime_type.startswith("image/")
        ):
            await bot.download(
                message.document.file_id, destination=photo_bytes
            )
        else:
            await status_msg.edit_text(
                "❌ Iltimos, faqat rasm formatida fayl yuboring!"
            )
            return

        loop = asyncio.get_running_loop()
        result_bytes = await loop.run_in_executor(
            None, process_image_accurate, photo_bytes.getvalue()
        )

        await status_msg.delete()

        output_file = BufferedInputFile(result_bytes, filename="result.png")

        await message.answer_photo(
            photo=output_file,
            caption="✅ <b>Orqa fon toza va sifatli o'chirildi!</b>",
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        await status_msg.edit_text(
            f"⚠️ Rasmni qayta ishlashda xatolik yuz berdi: <code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )


async def main():
    await bot.set_my_commands(
        [BotCommand(command="help", description="Yordam va Admin")]
    )
    print(">>> Bot Ishga Tushdi! <<<")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")