from typing import BinaryIO
from aiogram import Router, Bot, F

from aiogram.types import Message
from aiogram.enums import ParseMode

from src.gpt import OpenAI_API
from src.database import Redis

from src.aiogram.middlewares.middlewares import (
    WaitingMiddleware, 
    CheckNewUserMiddleware,
    IncrementRequestsMiddleware,
    CheckSubscriptionMiddleware,
    CheckTrialPeriodMiddleware,
    TimingMessageMiddleware,
    CheckHistoryLengthMiddleware
    )

from src.logger import logger
from src.filters import ChatModeFilter

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


@router.message(ChatModeFilter(mode="file_analyze"), F.document)
async def file_handler(message: Message, bot: Bot, openai: OpenAI_API, redis: Redis):
     # Скачиваем изображение
    file_IO: BinaryIO = await bot.download(message.document.file_id)
    file_IO.name = message.document.file_name

    file_name, file_id = await openai.add_file(file_IO)

    vector_store_id: str = await redis.get_user_vector_store_id(message.from_user.id)

    await openai.add_file_to_vectore_store(vector_store_id, file_id)

    await message.answer(f"{file_name} успешно загружен.\nЧто желаете узнать?")

@router.message(ChatModeFilter(mode="file_analyze"), F.text)
async def message_filemode_handler(message: Message, bot: Bot, openai: OpenAI_API, redis: Redis):
    thread_id = await redis.get_user_thread_id(message.from_user.id)

    response = await openai.get_thread_response(message.text, thread_id)

    # TODO: добавить исотрию сообщений

    await answer_message(
        md=response,
        message=message
    )

