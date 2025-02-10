import asyncio
import base64
from typing import BinaryIO

from aiogram import Bot, F, Router
from aiogram.types import Message

from src.aiogram.middlewares import (
    CheckHistoryLengthMiddleware,
    CheckNewUserMiddleware,
    CheckSubscriptionMiddleware,
    CheckTrialPeriodMiddleware,
    IncrementRequestsMiddleware,
    TimingMessageMiddleware,
    WaitingMiddleware,
)

from src.aiogram.utils import answer_message, split_message
from src.database import Database, Redis
from src.filters import ChatModeFilter
from src.gpt import OpenAI_API
from src.logger import logger


router = Router()

router.message.filter(ChatModeFilter(mode="usual"))

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
async def message_handler(message: Message, db: Database, openai: OpenAI_API, redis: Redis) -> None:
    user_id = message.from_user.id
    user_message = {'role': 'user', 'content': []}

    # Add the text content of the message to the user message
    user_message["content"].append({
        "type": "text",
        "text": message.text,
    })

    # Get the user's message history from Redis
    history = await redis.get_history(user_id)
    
    # Get the assistant's response from OpenAI API
    assistant_reply, role, num_in_tokens, num_out_tokens = await openai.get_response(history, user_message)
    assistant_message = {'role': role, 'content': assistant_reply}

    # Append the user and assistant messages to the history in Redis
    await redis.append_to_history(user_id=user_id, messages=[user_message, assistant_message])
    
    # Update the user's token usage in the database
    await db.add_user_in_out_tokens(user_id, num_in_tokens, num_out_tokens)

    # Send the assistant's reply to the user
    await answer_message(md=assistant_reply, message=message)


@router.message(F.photo)
async def vision_handler(message: Message, bot: Bot, db: Database, openai: OpenAI_API, redis: Redis) -> None:
    user_id = message.from_user.id
    user_message = {'role': 'user', 'content': []}

    # If the photo has a caption, add it to the user message
    if message.caption:
        logger.debug(f"message.caption: {message.caption}")
        user_message["content"].append({"type": "text", "text": message.caption})

    # Download the photo and convert it to base64
    file_IO: BinaryIO = await bot.download(message.photo[-1])
    file_bytes = file_IO.read()
    user_message["content"].append({
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(file_bytes).decode('utf-8')}"}
    })

    # Get the user's message history from Redis
    history = await redis.get_history(user_id)
    
    # Get the assistant's response from OpenAI API
    assistant_reply, role, num_in_tokens, num_out_tokens = await openai.get_response(history, user_message)
    assistant_message = {'role': role, 'content': assistant_reply}

    # Append the user and assistant messages to the history in Redis
    await redis.append_to_history(user_id=user_id, messages=[user_message, assistant_message])
    
    # Update the user's token usage in the database
    await db.add_user_in_out_tokens(user_id, num_in_tokens, num_out_tokens)

    # Send the assistant's reply to the user
    await answer_message(md=assistant_reply, message=message)
