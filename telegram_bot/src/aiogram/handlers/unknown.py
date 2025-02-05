from aiogram import Router, F
from aiogram.types import Message, ContentType

from src.aiogram.middlewares.middlewares import WaitingMiddleware, CheckNewUserMiddleware

from src.logger import logger


router = Router()

router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(WaitingMiddleware())

@router.message()
async def unknown(message: Message):
    await message.answer("Бот пока не умеет обрабатывать такие запросы :(")
