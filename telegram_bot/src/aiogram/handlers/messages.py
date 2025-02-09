
import asyncio
from typing import BinaryIO

from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.enums import ParseMode

from src.logger import logger
from src.aiogram.utils import split_message

from src.database import Database
from src.aiogram.middlewares.middlewares import (
    WaitingMiddleware, 
    CheckNewUserMiddleware,
    IncrementRequestsMiddleware,
    CheckSubscriptionMiddleware,
    CheckTrialPeriodMiddleware,
    TimingMessageMiddleware,
    CheckHistoryLengthMiddleware
    )
from src.gpt import OpenAI_API
from src.database import Redis

from src.aiogram.utils import answer_message, vk_send_pixel_event

import base64


router = Router()

# Inner/Outer Middlwares
router.message.middleware(TimingMessageMiddleware())

# Inner Middlwares
router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(CheckTrialPeriodMiddleware())
router.message.middleware(CheckSubscriptionMiddleware())

# Inner/Outer Middlwares
router.message.middleware(WaitingMiddleware())
router.message.middleware(CheckHistoryLengthMiddleware())

# Outer Middlwares
router.message.middleware(IncrementRequestsMiddleware())


@router.message(F.text | F.photo)
async def message_handler(message: Message, bot: Bot, db : Database, openai: OpenAI_API, redis: Redis) -> None:

    ## TEST
    ## ----------------------------
    # raise ValueError("1||||Message handle Test error")
    # test_mesage = 'a' * 5000
    # for message_to_send in split_message(test_mesage, with_photo=False):
    #     await message.answer(message_to_send, parse_mode=ParseMode.MARKDOWN)
    ## ----------------------------

    if await db.get_num_requests(message.from_user.id) == 0:
        await vk_send_pixel_event(redis=redis, user_id=message.from_user.id, goal_name="first_requset", cost=20)
    
    history = await redis.get_history(message.from_user.id)

    user_message = {'role': 'user', 'content': []}

    if message.photo:

        # logger.debug(f"photos: {message.photo}")

        # Приписка к изображению, если есть
        if message.caption:
            logger.debug(f"message.caption: {message.caption}")
            text_content = {
                "type": "text",
                "text": message.caption,
            }
            user_message["content"].append(text_content)

        # Скачиваем изображение
        file_IO: BinaryIO = await bot.download(message.photo[-1])
        # Преобразуем в байты
        file_bytes = file_IO.read()

        file_content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(file_bytes).decode('utf-8')}"},
        }

        user_message["content"].append(file_content)
    

    elif message.text:
        # logger.debug(f"message.text: {message.text}")
        text_content = {
            "type": "text",
            "text": message.text,
        }
        user_message["content"].append(text_content)

    # logger.debug(f"user_message {user_message}")  


    assistant_reply, role, num_in_tokens, num_out_tokens = await openai.get_response(history, user_message)
    # logger.debug(f"assistant_reply: {assistant_reply[:20]}")
    assistant_message = {'role': role, 'content': assistant_reply}

    await redis.append_to_history(
        user_id=message.from_user.id, 
        messages=[user_message, assistant_message])
    
    if num_in_tokens:
        # Добавляем входные токены пользователю
        await db.add_user_input_tokens(
            telegram_id=message.from_user.id,
            tokens=num_in_tokens
        )
    if num_out_tokens:
        # Добавляем выходные токены пользователю
        await db.add_user_output_tokens(
            telegram_id=message.from_user.id,
            tokens=num_out_tokens
        )
    
    # Работает, но это встроено в telegramify-markdown
    # for message_to_send in split_message(assistant_reply, with_photo=False):
    #     await message.answer(message_to_send, parse_mode=ParseMode.MARKDOWN)


    await answer_message(
        md=assistant_reply,
        message=message,
    )
