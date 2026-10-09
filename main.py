import asyncio
import sys

# Windows konsolida emojilar xatolik bermasligi uchun
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers import router


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    print("🚀 Pramida bot ishga tushmoqda...", flush=True)

    await init_db()

    bot = Bot(token=BOT_TOKEN)

    dp = Dispatcher()

    dp.include_router(router)

    print("================================", flush=True)
    print("🎓 PRAMIDA O'QUV MARKAZI", flush=True)
    print("🤖 BOT ISHGA TUSHDI", flush=True)
    print("================================", flush=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())