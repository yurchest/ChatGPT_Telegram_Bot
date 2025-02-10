from typing import BinaryIO
from aiogram import Router, Bot, F

from aiogram.types import Message
from aiogram.enums import ParseMode

from src.gpt import OpenAI_API
from src.database import Redis

from src.aiogram.middlewares import (
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
router.message.middleware(WaitingMiddleware())

# Inner Middlwares
router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(CheckTrialPeriodMiddleware())
router.message.middleware(CheckSubscriptionMiddleware())

# router.message.middleware(CheckHistoryLengthMiddleware())

# Outer Middlwares
router.message.middleware(IncrementRequestsMiddleware())


@router.message(ChatModeFilter(mode="file_analyze"), F.document)
async def file_handler(message: Message, bot: Bot, openai: OpenAI_API, redis: Redis):
    # Скачиваем изображение
    file_IO: BinaryIO = await bot.download(message.document.file_id)
    file_IO.name = message.document.file_name

    file_name, file_id = await openai.add_file(file_IO)

    vector_store_id: str = await redis.get_user_vector_store_id(message.from_user.id)

    await openai.add_file_to_vector_store(vector_store_id, file_id)

    await message.answer(f"{file_name} успешно загружен.\nЧто желаете узнать?")

@router.message(ChatModeFilter(mode="file_analyze"), F.text | F.photo)
async def message_filemode_handler(message: Message, bot: Bot, openai: OpenAI_API, redis: Redis):
    thread_id = await redis.get_user_thread_id(message.from_user.id)

    if message.photo:
        text = "\n".join([
            "В данном режиме анализ изображений недоступен\n",
            "*/usual\\_conversation* \\-  вернуться к обычному диалогу с возможностью анализировать фото",
        ])
        await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)
        return

    elif message.text:
        content = [{
            "type": "text",
            "text": message.text,
        }]


    response = await openai.get_thread_response(content, thread_id)


    await answer_message(
        md=response,
        message=message
    )

@router.message(ChatModeFilter(mode="usual"), F.document)
async def not_file_handler(message: Message):
    text = "\n".join([
            "В данном режиме анализ документов недоступен\n",
            "*/file\\_analyze* \\-  перейти в режим анализа документов",
        ])
    await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)
        