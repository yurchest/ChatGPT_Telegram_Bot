from aiogram import Router, F, Bot
from aiogram.types import Message, Update, ErrorEvent

from src.logger import logger
from src.database import Redis, Database

import sys
import traceback


router = Router()

@router.error()
async def global_error_handler(event: ErrorEvent, bot: Bot, redis: Redis, db: Database):
    """
    Обработчик ошибок, которые возникли в ходе обработки запроса.
    Выводим ошибку в лог (Postgre) 
    Отправляем пользователю сообщение о том, что произошла ошибка.
    """

    update: Update = event.update
    exception: Exception = event.exception

    telegram_id = None
    if update.message:
        telegram_id = update.message.from_user.id
    elif update.callback_query:
        telegram_id = update.callback_query.from_user.id


    tb = traceback.extract_tb(exception.__traceback__)
        
    filepath, lineno, func_name, line = tb[-1] 
    logger.error(
        msg=(
            f"Global error occurred\n"
            f"{filepath}\nFunc name:]\t{func_name}\n"
            f"{(lineno)}\t{line}\n"
            f"{(exception.__class__.__name__)}\t{exception}"
        ), 
        exc_info=False
        )

    # Логируем ошибку
    await db.add_error(
        error_type=str(exception.__class__.__name__),
        error_text=str(exception),
        file_path=filepath,
        telegram_id=telegram_id,
        traceback=traceback.format_exc()
    )

    # Удаляем историю сессии
    await redis.clear_user_history(telegram_id)
    await redis.set_user_req_inactive(telegram_id)

    # Уведомляем пользователя
    if telegram_id:
        await bot.send_message(
            chat_id=telegram_id,
            text=f"Произошла непредвиденная ошибка\nСвяжитесь с разработчиком(@yurchest)\nError: {exception}"
        )

    return True
