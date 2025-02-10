from functools import wraps

from src.logger import logger
from src.database import Database, Redis

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import sys

async def on_startup(db: Database, bot: Bot):
    await db.create_tables_if_not_exist()

async def on_shutdown(db: Database, redis: Redis):
    await redis.clear_all_waitings()
    await redis.close()
    await db.close()
    logger.warning("(MAIN)\t\t Service stopped ...")
    logger.warning("--------------------------------------")

def init_error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.critical(f"Error init bot in {func.__name__}: {e.__class__.__name__} | {e}", exc_info=False)
            sys.exit(1)
    return wrapper

def get_payment_keyboard_markup():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить", callback_data="pay")]
        ]
    )
