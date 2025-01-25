from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram import types

from src.logger import logger
from src.database import Redis, Database

import sys
import traceback

router = Router()

@router.error(F.update.message.as_("message"))
async def global_error_handler(event: types.ErrorEvent, bot: Bot, redis: Redis, db: Database):
    """
    Обработчик ошибок, которые возникли в ходе обработки запроса.
    Выводим ошибку в лог (имя функции, где произошла ошибка и саму ошибку) 
    Отправляем пользователю сообщение о том, что произошла ошибка.
    """
    error = event.exception  # Получаем объект ошибки
    update = event.update  # Получаем событие (сообщение и т. д.)

    await update.message.answer(f"Произошла непредвиденная ошибка. Свяжитесь с @yurchest \n {event.exception}")

    tb = traceback.extract_tb(error.__traceback__)
        
    filepath, lineno, func_name, line = tb[-1] 
    logger.error(
        f"Global error occurred\n{filepath}\nFunc name: {func_name}\n{error.__class__.__name__} | {error}", 
        exc_info=False)

    await db.add_error(
        error_type=str(error.__class__.__name__),
        error_text=str(error),
        file_path=filepath,
        telegram_id=update.message.from_user.id,
        traceback=traceback.format_exc()
    )

    await redis.clear_user_history(update.message.from_user.id)
    await redis.set_user_req_inactive(update.message.from_user.id)

    return True
