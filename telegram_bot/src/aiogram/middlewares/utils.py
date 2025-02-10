from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from src.logger import logger
from src.prometheus_metrics import MESSAGE_RESPONSE_TIME
from src.database import Redis

import asyncio

class TimingMessageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        """
        Замеряем MESSAGE_RESPONSE_TIME
        """
        start_time = datetime.now()  # Фиксируем момент получения сообщения ботом

        result =  await handler(event, data)
        
        if isinstance(event, Message):
            # Время обработки сообщения основной логикой
            response_time = (datetime.now() - start_time).total_seconds() 
            # Время от отправки сообщения пользователем до начала основной логики
            message_latency: datetime = (start_time - event.date.replace(tzinfo=None)).total_seconds()  
            # Общее время от отправки до ответа 
            total_latency = message_latency + response_time  
            # Логируем
            logger.debug(f"(MAIN)\t\t Telegram latency: {message_latency:.3f}s, Bot processing: {response_time:.3f}s, Total: {total_latency:.3f}s")
            # Пишем в Prometheus
            MESSAGE_RESPONSE_TIME.observe(total_latency) # Отправляем в Prometheus
        
        return result
    

class WaitingMiddleware(BaseMiddleware):
    """
    Если предыдущий запрос пользователя еще обрабатывается, отправляет техническое сообщение об этом.
    Иначе выводим техническое сообщение - точки.
    В процессе запроса присваиваем активность (Redis).
    После выполнения технические сообщения удаляются.
    """ 

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
            tech_message = await event.answer("Ваш запрос обрабатывается. Пожалуйста, подождите...")
            asyncio.create_task(delete_message_when_inactive(redis, event.from_user.id, tech_message, event))
            return  # Завершаем выполнение, так как запрос уже обрабатывается
        
        
        # Отправляем техническое сообщение с точками
        tech_message = await event.answer(". . . . . .")
        # Устанавливаем флаг активности запроса пользователя
        await redis.set_user_req_active(event.from_user.id)
        # Ожидаем когда запрос станет неактивным
        asyncio.create_task(delete_message_when_inactive(redis, event.from_user.id, tech_message))
        # Вызываем следующий обработчик
        result = await handler(event, data)
        # Удаляем флаг активности запроса пользователя
        await redis.set_user_req_inactive(event.from_user.id)

        
        return result

async def delete_message_when_inactive(
            redis: Redis, 
            user_id: int,
            tech_message: TelegramObject, 
            user_message: TelegramObject = None
            ):
        """
        Ожидает, пока пользователь ждет ответа.
        """
        # Удаляем пользователское сообщение
        if user_message: await user_message.delete()

        while await redis.is_user_waiting(user_id):
            # Ожидаем пока юзеру ответит бот на предыдущее сообщение
            await asyncio.sleep(0.1)

        # Удаляем техническое сообщение
        await tech_message.delete()