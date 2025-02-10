from aiogram import Router
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from aiogram.enums import ParseMode

from src.logger import logger

from src.database import Redis, Database
from src.aiogram.middlewares import WaitingMiddleware, CheckNewUserMiddleware
from src.config import TRIAL_PERIOD_NUM_REQ
from src.aiogram.utils import commands_text, answer_message
from src.gpt import OpenAI_API
from src.filters import ChatModeFilter

from datetime import datetime
import re


router = Router()

router.message.middleware(CheckNewUserMiddleware())
router.message.middleware(WaitingMiddleware())


@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, redis: Redis, db: Database) -> None:
    await message.answer("Можешь задавать интересующий тебя вопрос")
    

@router.message(Command('reset_conversation'), ChatModeFilter(mode="usual"))
async def reset_handler(message: Message, redis: Redis):
    await redis.clear_user_history(message.from_user.id)
    await redis.set_user_req_inactive(message.from_user.id)
    await message.answer("Диалог сброшен")

@router.message(Command('reset_conversation'), ChatModeFilter(mode="file_analyze"))
async def reset_handler(message: Message):
    text = "\n".join([
            "В данном режиме сброс истории недоступен\n",
            "*/usual\\_conversation* \\-  сбросить историю анализа документов и вернуться к обычному диалогу",
        ])
    await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)


@router.message(Command('show_dialog'), ChatModeFilter(mode="usual"))
async def show_dialog_handler(message: Message, redis: Redis):
    history = await redis.get_history(message.from_user.id)
    if not history:
        await message.answer("Диалог пуст")
        return

    for cur_message in history:
        sender = "Неизвестно кто"
        if cur_message["role"] == "user":
            sender = "Пользователь"
            mes = ""

            for cur_content in cur_message['content']:
                if cur_content.get("type") == "text":
                    mes += f"{cur_content['text']}\n\n"
                elif cur_content.get("type") == "image_url":
                    mes += "_Приложено фото_"

            await answer_message(
                md=f"*{sender}*:\n{mes}",
                message=message,
            )

        elif cur_message["role"] == "assistant":
            sender = "Бот"
            await answer_message(
                md=f"*{sender}*:\n{cur_message['content']}",
                message=message,
            )

@router.message(Command('show_dialog'), ChatModeFilter(mode="file_analyze"))
async def show_dialog_handler(message: Message):
    text = "\n".join([
            "В данном режиме показ истории недоступен\n",
            "*/usual\\_conversation* \\-  сбросить историю анализа документов и вернуться к обычному диалогу",
        ])
    await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)

@router.message(Command('help'))
async def reset_handler(message: Message, openai: OpenAI_API):
    text = "\n".join([
        "🤖 *Этот чат\\-бот взаимодействует с OpenAI API*\n",
        f"Используемая модель: `{openai.model_id}`\n",
        "Поддерживаемые форматы запросов:",
        "\\- Генерация текста",
        "\\- Анализ изображения",
        "\\- *Анализ файлов*\n",
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


@router.message(Command("file_analyze")) 
async def file_analyze_handler(message: Message, openai: OpenAI_API, redis: Redis):

    user_mode = await redis.get_user_mode(message.from_user.id)
    if user_mode == "file_analyze":
        await message.answer(
            "Ты уже в режиме `file_analyze`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    vector_store_id = await redis.get_user_vector_store_id(message.from_user.id)
    thread_id = await redis.get_user_thread_id(message.from_user.id)

    if vector_store_id is None or thread_id is None:

        vector_store_id = await openai.create_vector_store_to_user(message.from_user.id)
        await redis.set_user_vector_store_id(message.from_user.id, vector_store_id)

        thread_id: str = await openai.create_thread_for_user(vector_store_id)
        await redis.set_user_thread_id(message.from_user.id, thread_id)



    await redis.set_user_mode(message.from_user.id, "file_analyze")

    text = "\n".join([
        "Ты зашел в режим анализа документов\n",
        "Для начала пришли мне файл для анализа без подписи\\.",
        "По ходу диалога ты можешь присылать еще файлы для расширения кругозора модели\\.\n"
        "Доступные форматы файлов: `.pdf`, `.pptx`, `.docx`, `.txt` и еще множество",
        "[Все поддерживаемые форматы](https://platform.openai.com/docs/assistants/tools/file-search#supported-files) _\\(может быть недоступно в РФ\\)_\n",
        "*/usual\\_conversation* \\-  вернуться к обычному диалогу",
    ]) 

    await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)

@router.message(Command("usual_conversation")) 
async def usual_conversation_handler(message: Message, openai: OpenAI_API, redis: Redis):
    user_mode = await redis.get_user_mode(message.from_user.id)
    if user_mode == "usual":
        await message.answer(
            "Ты уже в режиме `usual_conversation`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    await redis.set_user_mode(message.from_user.id, "usual")

    thread_id = await redis.get_user_thread_id(message.from_user.id)
    if thread_id: await openai.delete_all_file_data(thread_id)

    await redis.delete_user_thread_id(message.from_user.id)
    await redis.delete_user_vector_store_id(message.from_user.id)

    await message.answer("Установлен обычный режим. Можете продолжить переписку.")


# Хэндлер для неизвестных команд
@router.message(Command(re.compile(r"^.*"))) 
async def unknown_command_handler(message: Message):
    text = "\n".join([
        "🚫 Неизвестная команда\n",
        *commands_text,
    ]) 
    await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)