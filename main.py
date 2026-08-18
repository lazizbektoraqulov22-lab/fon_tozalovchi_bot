import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
BOT_TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
async def handle(request):
    return web.Response(text="Bot faol ishlamoqda!")
async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer("Salom! Men fonni tozalovchi botman. Menga rasm yuboring!")
@dp.message()
async def echo_all(message: types.Message):
    if message.photo:
        await message.answer("Rasm qabul qilindi! Ishlov berilmoqda...")
    else:
        await message.answer("Iltimos, menga rasm yuboring!")
async def main():
    await start_dummy_server()
    await dp.start_polling(bot)
if name == "main":
    asyncio.run(main())