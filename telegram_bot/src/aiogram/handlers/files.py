from typing import BinaryIO
from aiogram import Router, Bot, F

from aiogram.types import Message
from aiogram.enums import ParseMode

from src.gpt import OpenAI_API

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


@router.message(F.document)
async def file_handler(message: Message, bot: Bot, openai: OpenAI_API):
    logger.debug(f"message.document: {message.document}")

    logger.debug(f"message.caption: {message.caption}")

    logger.debug(f"message.text: {message.text}")

    # Путь к файлу (например, временная папка, куда загружен файл)
    # file_path = f"temp_files/{message.from_user.id}/{message.document.file_name}"
    # # Скачиваем файл на сервер
    # await message.document.download(file_path)

    
    # Скачиваем изображение
    file_IO: BinaryIO = await bot.download(message.document.file_id)
    file_IO.name = message.document.file_name

    # Обрабатываем сообщение
    user_message = "Какая информация в этом документе?" # TODO

    response = await openai.get_file_response(file_IO, user_message)

    await message.answer(response)