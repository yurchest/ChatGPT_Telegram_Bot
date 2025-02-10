from aiogram import Router
from aiogram.types import Message

from src.aiogram.middlewares import WaitingMiddleware, CheckNewUserMiddleware
from src.filters import ChatTypeFilter

router = Router()

router.message.filter(ChatTypeFilter(chat_type=["private"]))

router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(WaitingMiddleware())

@router.message()
async def unknown(message: Message):
    await message.answer("Бот пока не умеет обрабатывать такие запросы :(")
