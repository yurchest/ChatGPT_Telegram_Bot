from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.enums import ParseMode

from src.logger import logger

from src.database import Redis, Database
from src.aiogram.middlewares.middlewares import WaitingMiddleware, CheckNewUserMiddleware
from src.config import TRIAL_PERIOD_NUM_REQ
from src.aiogram.utils import commands_text, answer_message

from datetime import datetime


router = Router()

router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(WaitingMiddleware())


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer("Можешь задавать интересующий тебя вопрос")

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
        else:
            sender = "Неизвестно кто"

        await answer_message(
            md=f"*{sender}*:\n" + cur_message['content'],
            message=message,
        )

@router.message(Command('help'))
async def reset_handler(message: Message, redis: Redis):
    text = "\n".join([
        "🤖 *Этот чат\\-бот работает на OpenAI API*\n",
        "Бот запоминает предыдущие сообщения, чтобы поддерживать связный диалог\\.",
        "Используйте /reset\\_conversation для сброса контекста\\.\n",
        *commands_text,
        "👨‍💻 *Разработчик:* [@yurchest](tg://user?id=567804607)"
    ]) 
    await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)

@router.message(Command('profile'))
async def profile_handler(message: Message, db: Database):
    user_id: int = message.from_user.id

    profile_text = (
        "Профиль\n\n"
        f"ID: {user_id}\n\n"
    )

    if await db.is_subscription_active(user_id):
        sub_type = "Есть"
        sub_expiration_date = await db.get_sub_expiration_date(
            telegram_id=user_id, 
            user_tz="Europe/Moscow"
            )
        profile_text += (
            f"Подписка: {sub_type}\n"
            f"Дата окончания\n"
            f"{sub_expiration_date}\n\n"
        )
        
    elif await db.is_user_trial(user_id):
        req_remain = TRIAL_PERIOD_NUM_REQ - await db.get_num_requests(user_id)
        profile_text += (
            f"Подписка: Пробная\n"
            f"Остаток: {req_remain} / {TRIAL_PERIOD_NUM_REQ}\n\n"
        )
    else:
        profile_text += (
            f"Подписка: Отсутствует\n"
            f"Оплатите подписку, используя /pay\n\n"
        )

    
    profile_text = [f"📌 *Профиль*\n\nID: `{user_id}`\n"]

    if await db.is_subscription_active(user_id):
        sub_expiration_date = await db.get_sub_expiration_date(
            telegram_id=user_id, user_tz="Europe/Moscow"
        )
        formatted_date = datetime.strftime(sub_expiration_date, "%Y-%m-%d %H:%M:%S")
        profile_text.append(f"*Подписка:* Активна ✅\n*Окончание:*\n`{formatted_date} (МСК)`\n")
    
    elif await db.is_user_trial(user_id):
        req_remain = TRIAL_PERIOD_NUM_REQ - await db.get_num_requests(user_id)
        profile_text.append(f"*Подписка:* Пробная 🆓\n*Осталось:* `{req_remain}/{TRIAL_PERIOD_NUM_REQ}` запросов\n")
    
    else:
        profile_text.append(f"*Подписка:* Отсутствует ❌\n💳 *Оформите подписку:* `/pay`\n")


    
    await message.answer("\n".join(profile_text), parse_mode=ParseMode.MARKDOWN_V2)


# Хэндлер для неизвестных команд
@router.message(lambda message: message.text.startswith('/'))  # Если текст начинается с "/"
async def unknown_command_handler(message: Message):
    text = "\n".join([
        "🚫 Неизвестная команда\\.\n",
        *commands_text,
    ]) 
    await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)