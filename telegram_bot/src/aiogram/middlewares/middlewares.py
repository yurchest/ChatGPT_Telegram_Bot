import asyncio
import traceback

from aiogram import BaseMiddleware, Bot
from aiogram.types import (
    Update,
    TelegramObject,
    Message,
    )
from aiogram.enums import ParseMode

from src.database import Database
from src.gpt import OpenAI_API
from src.database import Redis
from src.config import SUBSCRIPTION_DURATION_MONTHS, TRIAL_PERIOD_NUM_REQ
from src.aiogram.handlers.system import get_payment_keyboard_markup

from src.logger import logger

class ErrorLoggingMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot, db: Database, redis: Redis):
        self.bot = bot
        self.db = db
        self.redis = redis

    async def __call__(self, handler, event: Update, data: dict):
        try:
            # Выполняем основной обработчик
            return await handler(event, data)
        except Exception as exception:
            # Получаем информацию о пользователе
            telegram_id = None
            if event.message:
                telegram_id = event.message.from_user.id
            elif event.callback_query:
                telegram_id = event.callback_query.from_user.id

            # Получаем информацию об ошибке
            tb = traceback.extract_tb(exception.__traceback__)
            filepath, lineno, func_name, line = tb[-1]

            # Логируем ошибку
            logger.error(
                f"Global error occurred\n{filepath}\nFunc name: {func_name}\n{exception.__class__.__name__} | {exception}",
                exc_info=False
            )

            # Логируем ошибку в базу данных
            await self.db.add_error(
                error_type=str(exception.__class__.__name__),
                error_text=str(exception),
                file_path=filepath,
                telegram_id=telegram_id,
                traceback=traceback.format_exc()
            )

            # Удаляем историю сессии из Redis
            if telegram_id:
                await self.redis.clear_user_history(telegram_id)
                await self.redis.set_user_req_inactive(telegram_id)

                # Уведомляем пользователя
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=f"Произошла непредвиденная ошибка\nСвяжитесь с разработчиком (@yurchest)\nError: {exception}"
                )

            # Не блокируем выполнение
            # raise exception


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

    async def __call__(self, handler, event: TelegramObject, data: dict):
        """
        Добавляет объект `db` в `data`, чтобы он был доступен в хендлерах.
        """
        data["db"] = self.db
        return await handler(event, data)
    
class OpenAIMiddleware(BaseMiddleware):
    def __init__(self, openai: OpenAI_API):
        super().__init__()
        self.openai = openai

    async def __call__(self, handler, event: TelegramObject, data: dict):
        """
        Добавляет объект `openai` в `data`, чтобы он был доступен в хендлерах.
        """
        data["openai"] = self.openai
        return await handler(event, data)
    
class RedisMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis):
        super().__init__()
        self.redis = redis

    async def __call__(self, handler, event: TelegramObject, data: dict):
        """
        Добавляет объект `redis` в `data`, чтобы он был доступен в хендлерах.
        """
        data["redis"] = self.redis
        return await handler(event, data)
    
    
class CheckNewUserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        if isinstance(event, Message):
            # Получаем объект базы данных из контекста
            db:Database= data.get("db")
            
            if db is None:
                raise ValueError("Database instance must be provided in the context data.")
        
            # Проверяем, существует ли пользователь в базе данных
            is_user_exists = await db.is_user_exists(event.from_user.id)

            if not is_user_exists:
                # Если пользователь новый, отправляем приветственное сообщение
                text = (
                    f"*Привет, {event.from_user.first_name}\\! 👋* \n\n"
                    "Я \\- *Yurchest ChatGPT Bot*, умный чат\\-бот на базе OpenAI GPT\\. "
                    "Готов помочь тебе с любыми вопросами: от написания текста до программирования\\!\n\n"
                    "🔹 *Как я могу помочь?* \n"
                    "Просто напиши свой запрос, и я постараюсь дать лучший ответ\\!\n"
                    "🔹 *Пробный период*\n"
                    f"Ты можешь бесплатно воспользоваться ботом в течение *{TRIAL_PERIOD_NUM_REQ} запросов*\\. \n"
                    f"По истечении пробного периода тебе будет предложено оплатить подписку на *{SUBSCRIPTION_DURATION_MONTHS} месяц\\(ев\\)*\n"
                    "🔹 *Основные команды:* \n"    
                    "    ⦁ */reset\\_conversation* \\- Сбросить диалог \n"
                    "    ⦁ */pay* \\- Оплатить подписку \n"
                    "    ⦁ */show\\_dialog* \\- Показать весь диалог \n"
                    "    ⦁ */help* \\- Помощь \n\n"
                    "Начнем? 😊🚀"
                )  
                
                await event.answer(text, parse_mode=ParseMode.MARKDOWN_V2)

                # Добавляем нового пользователя в базу данных
                await db.add_user(
                    telegram_id=event.from_user.id,
                    first_name=event.from_user.first_name,
                    username=event.from_user.username,
                    language_code=event.from_user.language_code
                )
            
            # Вызываем следующий обработчик
            return await handler(event, data)

class IncrementRequestsMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        result = await handler(event, data)
        if isinstance(event, Message):
            # Получаем объект базы данных из контекста
            db = data.get("db")
            
            if db is None:
                raise ValueError("Database instance must be provided in the context data.")
            
            # Увеличиваем счетчик запросов пользователя
            await db.increment_user_requests(event.from_user.id)

        # Вызываем следующий обработчик
        return result
    
class CheckTrialPeriodMiddleware(BaseMiddleware):
    """
    Если пользователь не подписан и тестовый период закончился, отправляет сообщение о подписке.
    """
    async def __call__(self, handler, event: TelegramObject, data: dict):
        if isinstance(event, Message):
            # Получаем объект базы данных из контекста
            db: Database = data.get("db")
            
            if db is None:
                raise ValueError("Database instance must be provided in the context data.")

            # Проверяем, подписан ли пользователь
            is_subscription_active = await db.is_subscription_active(event.from_user.id)

            if not is_subscription_active and not await db.is_user_trial(event.from_user.id):
                # Если пользователь не подписан и тестовый период закончился, отправляем сообщение о подписке
                await event.answer(
                    "Ваш пробный период закончился. "
                    "Для продолжения использования сервиса, пожалуйста, подпишитесь.",
                    reply_markup=get_payment_keyboard_markup()
                )
            else:
                await handler(event, data)
        else:
            await handler(event, data)

class CheckSubscriptionMiddleware(BaseMiddleware):
    """
    Если подписан и подписка закончилась, отправляет сообщение о продлении подписки.
    """
    async def __call__(self, handler, event: TelegramObject, data: dict):
        if isinstance(event, Message):
            # Получаем объект базы данных из контекста
            db: Database = data.get("db")
            
            if db is None:
                raise ValueError("Database instance must be provided in the context data.")
            
            # Проверяем, подписан ли пользователь
            is_subscription_active = await db.is_subscription_active(event.from_user.id)

            if not is_subscription_active and not await db.is_user_trial(event.from_user.id):
                # Если подписка закончилась И не пробный период, отправляем сообщение о продлении подписки
        
                await event.answer(
                    f"Ваша подписка закончилась. \n"
                    f"Для продолжения использования сервиса, пожалуйста, продлите подписку",
                    reply_markup=get_payment_keyboard_markup()
                )
                # TODO: Добавить кнопку для продления подписки
            else:
                await handler(event, data)
        else:
            await handler(event, data)

    
class WaitingMiddleware(BaseMiddleware):
    """
    Если предыдущий запрос пользователя еще обрабатывается, отправляет техническое сообщение об этом.
    Иначе выводим техническое сообщение - точки.
    В процессе запроса присваиваем активность (Redis).
    После выполнения технические сообщения удаляются.
    """
    async def delete_message_when_inactive(self, redis: Redis, 
                                           user_id: int, 
                                           tech_message: TelegramObject, 
                                           user_message: TelegramObject = None):
        """
        Ожидает, пока пользователь ждет ответа.
        """
        while await redis.is_user_waiting(user_id):
            await asyncio.sleep(0.1)

        await tech_message.delete()
        if user_message: await user_message.delete()
        

    async def __call__(self, handler, event: TelegramObject, data: dict):
        # Получаем объект базы данных из контекста
        redis: Redis = data.get("redis")

        if redis is None:
            raise ValueError("Redis instance must be provided in the context data.")

        # Проверяем, активен ли запрос пользователя
        is_user_waiting = await redis.is_user_waiting(event.from_user.id)

        tech_message = None  # Для хранения ссылки на отправленное сообщение

        
        if is_user_waiting:
            # Если запрос пользователя активен, отправляем сообщение о том, что запрос обрабатывается
            tech_message = await event.answer("Ваш запрос обрабатывается. Пожалуйста, подождите.")
            asyncio.create_task(self.delete_message_when_inactive(redis, event.from_user.id, tech_message, event))
            return  # Завершаем выполнение, так как запрос уже обрабатывается
        else:
            # Отправляем техническое сообщение с точками
            tech_message = await event.answer(". . . . . .")
            # Устанавливаем флаг активности запроса пользователя
            await redis.set_user_req_active(event.from_user.id)
            # Ожидаем когда запрос станет неактивным
            asyncio.create_task(self.delete_message_when_inactive(redis, event.from_user.id, tech_message))
            # Вызываем следующий обработчик
            result = await handler(event, data)
            # Удаляем флаг активности запроса пользователя
            await redis.set_user_req_inactive(event.from_user.id)
            return result

            



    

        

