
from functools import wraps

from src.logger import logger
from src.database import Database, Redis

from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import sys

async def on_startup(db: Database, bot: Bot):
    await db.create_tables_if_not_exist()
    # await db.create_tables()


async def on_shutdown(db: Database, redis: Redis):
    await redis.clear_all_history()
    await redis.clear_all_waitings()

    await redis.close()
    await db.close()
    


def init_error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.critical(f"Global error occurred in {func.__name__}: {e}", exc_info=False) # True
            sys.exit(1)
            return None 
    return wrapper

def get_payment_keyboard_markup():
    pay_keyboard_markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Оплатить", callback_data="pay")]
                    ]
                )
    return pay_keyboard_markup