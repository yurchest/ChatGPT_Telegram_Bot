from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from src.logger import logger

from src.database import Redis
from src.aiogram.middlewares.middlewares import WaitingMiddleware, CheckNewUserMiddleware



router = Router()

router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(WaitingMiddleware())

@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer("Можете задавать интересующий вас вопрос чат")

@router.message(Command('reset_conversation'))
async def reset_handler(message: Message, redis: Redis):
    await redis.clear_user_history(message.from_user.id)
    await redis.set_user_req_inactive(message.from_user.id)
    await message.answer("Диалог сброшен")


@router.message(Command('show_dialog'))
async def reset_handler(message: Message, redis: Redis):
    history = await redis.get_history(message.from_user.id)
    if not history:
        await message.answer("Диалог пуст")
        return
    for cur_message in history:
        sender = "Неизветно кто"
        if cur_message["role"] == "user":
            sender = "Пользователь"
        elif cur_message["role"] == "assistant":
            sender = "Бот"
        await message.answer(f"{sender}:\n{'-' * 30}\n{cur_message['content']}\n{'-' * 30}")

