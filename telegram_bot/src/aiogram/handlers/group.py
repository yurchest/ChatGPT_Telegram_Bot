from aiogram import Router, Bot
from aiogram.filters import Command, ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from aiogram.types import Message, ChatMemberUpdated

from src.logger import logger

from src.database import Redis, Database

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

from src.aiogram.utils import reply_message
from src.gpt import OpenAI_API
from src.filters import ChatTypeFilter


router = Router()

router.message.filter(ChatTypeFilter(chat_type=["group", "supergroup"]))

router.message.middleware(TimingMessageMiddleware())
router.message.middleware(WaitingMiddleware())
router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(CheckTrialPeriodMiddleware())
router.message.middleware(CheckSubscriptionMiddleware())
router.message.middleware(IncrementRequestsMiddleware())
router.message.middleware(TokensMiddleware())



@router.message(Command("ask"))
async def ask_handler(message: Message, openai: OpenAI_API):
    """Обработчик команды /ask в группах и супергруппах."""

    # Проверяем, указан ли вопрос после команды
    command_prefix = "/ask "
    if not message.text.startswith(command_prefix) or len(message.text) <= len(command_prefix):
        await message.answer("Пожалуйста, укажите вопрос после команды /ask.")
        return

    # Извлекаем текст вопроса
    question = message.text[len(command_prefix):].strip()

    user_message = {'role': 'user', 'content': []}
    user_message["content"].append({
        "type": "text",
        "text": question,
    })

    response: dict = await openai.get_response(conversation_history=[], user_message=user_message)
    assistant_reply = response.get("assistant_reply")
    
    await reply_message(
        md=assistant_reply,
        message=message
    )

    return response

@router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def bot_added(event: ChatMemberUpdated, bot: Bot):
    await bot.send_message("Привет работяги.\nИспользуйте /ask <вопрос>, чтобы узнать что-то новое")

# @router.message()
# async def ask_handler(message: Message):
#     await message.reply("В группах можно использовать только /ask")