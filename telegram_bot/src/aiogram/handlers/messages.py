from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.enums import ParseMode

from src.config import TRIAL_PERIOD_NUM_REQ
from src.logger import logger
from src.aiogram.decorators.decorators import check_new_user

from src.database import Database
from src.aiogram.middlewares.middlewares import (
    WaitingMiddleware, 
    CheckNewUserMiddleware,
    IncrementRequestsMiddleware,
    CheckSubscriptionMiddleware,
    CheckTrialPeriodMiddleware,
    )
from src.gpt import OpenAI_API
from src.database import Redis

from src.prometheus_metrics import handler_duration, count_messages

router = Router()

# Inner Middlwares
router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(CheckTrialPeriodMiddleware())
router.message.middleware(CheckSubscriptionMiddleware())

# Inner/Outer Middlwares
router.message.middleware(WaitingMiddleware())

# Outer Middlwares
router.message.middleware(IncrementRequestsMiddleware())


@router.message(F.text)
@handler_duration.time()
async def message_handler(message: Message, db : Database, openai: OpenAI_API, redis: Redis) -> None:
    history = await redis.get_history(message.from_user.id)

    # raise ValueError("Message handle Test error")

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

    count_messages.inc()

    await message.answer(assistant_reply, parse_mode=ParseMode.MARKDOWN)


