from aiogram import Router
from aiogram.types import Message

from src.aiogram.middlewares import WaitingMiddleware, CheckNewUserMiddleware

router = Router()

router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(WaitingMiddleware())

@router.message()
async def unknown(message: Message):
    await message.answer("Бот пока не умеет обрабатывать такие запросы :(")
