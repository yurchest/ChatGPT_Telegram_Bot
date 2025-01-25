from functools import wraps

from aiogram.types import Message
from aiogram import Bot

from src.database import Database


def check_new_user(func):
    @wraps(func)
    async def wrapper(message: Message, db: Database, *args, **kwargs):
        if not await db.is_user_exists(message.from_user.id):
            await message.answer(
                f"Привет, {message.from_user.first_name}! Я рад тебя видеть здесь! "
                f"Я - чат-бот, созданный на базе GPT. "
                f"Я могу помочь тебе в различных задачах и ответить на любые вопросы. "
                f"Просто напиши мне, что ты хочешь узнать! \n "
                f"У тебя есть тестовый режим на 50 запросов. Удачи!"
            )
            await db.add_user(
                telegram_id=message.from_user.id, 
                first_name=message.from_user.first_name, 
                username=message.from_user.username, 
                language_code=message.from_user.language_code)
        return await func(message, db, *args, **kwargs)
    return wrapper
