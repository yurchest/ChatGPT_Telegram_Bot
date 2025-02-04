
import asyncio

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

from src.aiogram.utils import answer_message


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


@router.message(F.text)
async def message_handler(message: Message, db : Database, openai: OpenAI_API, redis: Redis) -> None:
    history = await redis.get_history(message.from_user.id)

    ## TEST
    ## ----------------------------
    # raise ValueError("1||||Message handle Test error")
    # test_mesage = 'a' * 5000
    # for message_to_send in split_message(test_mesage, with_photo=False):
    #     await message.answer(message_to_send, parse_mode=ParseMode.MARKDOWN)
    ## ----------------------------

    user_message = {'role': 'user', 'content': message.text}
    assistant_reply, role, num_in_tokens, num_out_tokens = await openai.get_response(history, user_message)
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
    
    # # Работает, но это встроено в telegramify-markdown
    # for message_to_send in split_message(assistant_reply, with_photo=False):
    #     await message.answer(message_to_send, parse_mode=ParseMode.MARKDOWN)

    await answer_message(
        md=assistant_reply,
        message=message,
    )


