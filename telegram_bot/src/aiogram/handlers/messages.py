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
    ChatHistoryMiddleware,
    TokensMiddleware,
)

from src.aiogram.utils import answer_message, split_message
from src.database import Database, Redis
from src.filters import ChatModeFilter, ChatTypeFilter
from src.gpt import OpenAI_API
from src.logger import logger


router = Router()

router.message.filter(ChatTypeFilter(chat_type=["private"]))
router.message.filter(ChatModeFilter(mode="usual"))


router.message.middleware(TimingMessageMiddleware())
router.message.middleware(WaitingMiddleware())

router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(CheckTrialPeriodMiddleware())
router.message.middleware(CheckSubscriptionMiddleware())

router.message.middleware(CheckHistoryLengthMiddleware())

# Outer Middlwares
router.message.middleware(IncrementRequestsMiddleware())
router.message.middleware(TokensMiddleware())

router.message.middleware(ChatHistoryMiddleware())

@router.message(F.text)
async def message_handler(message: Message, openai: OpenAI_API, history: list) -> None:
    user_message = {'role': 'user', 'content': []}

    # Add the text content of the message to the user message
    user_message["content"].append({
        "type": "text",
        "text": message.text,
    })

    # Get the assistant's response from OpenAI API
    response: dict = await openai.get_response(history, user_message)
    assistant_reply = response.get("assistant_reply")

    # Send the assistant's reply to the user
    await answer_message(md=assistant_reply, message=message)

    return response


@router.message(F.photo)
async def vision_handler(message: Message, bot: Bot, openai: OpenAI_API, history: list) -> None:
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
    
    # Get the assistant's response from OpenAI API
    response: dict = await openai.get_response(history, user_message)
    assistant_reply = response.get("assistant_reply")

    # Send the assistant's reply to the user
    await answer_message(md=assistant_reply, message=message)

    return response