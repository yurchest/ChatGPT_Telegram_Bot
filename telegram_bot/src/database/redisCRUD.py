import json
import redis.asyncio as aioredis
import asyncio
from src.logger import logger
import sys

def handle_redis_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"(Redis)\t Error in {func.__name__}: {e}")
            return None
    return wrapper

class Redis:
    def __init__(self, redis_host, redis_port):
        self.redis = aioredis.from_url(f"redis://{redis_host}:{redis_port}", db=0,decode_responses=True)
        self.check_task = asyncio.create_task(self.check_connection())

    @classmethod
    async def create(cls, redis_host, redis_port):
        self = cls(redis_host, redis_port)
        await self.check_task  # Дожидаемся завершения задачи
        return self

    async def check_connection(self):
        try:
            await self.redis.ping()
            logger.info(f"(Redis)\t Redis connection established ")
        except Exception as e:
            logger.error(f"(Redis)\t Error while checking connection: {e}")
            raise

    @handle_redis_errors
    async def close(self):
        await self.redis.aclose()
        logger.info(f"(Redis)\t Redis connection closed")

    @handle_redis_errors
    async def get_history(self, user_id):
        """Получить историю сообщений для пользователя"""
        history = await self.redis.lrange(f"history:{user_id}", 0, -1)
        return [json.loads(item) for item in history] if history else []

    @handle_redis_errors
    async def append_to_history(self, user_id, messages: list):
        """Добавить сообщение в историю (без перезаписи)"""
        await self.redis.rpush(f"history:{user_id}", *(json.dumps(message) for message in messages))
        await self.set_expiration(key=f"history:{user_id}", days=3)
        logger.debug(f"(Redis)\t Added: messages to user with id {user_id}")

    @handle_redis_errors
    async def clear_user_history(self, user_id):
        """Очистить историю сообщений для пользователя"""
        await self.redis.delete(f"history:{user_id}")
        logger.debug(f"(Redis)\t History user {user_id} cleared")

    @handle_redis_errors
    async def clear_all_history(self):
        """Очистить всю историю сообщений"""
        # Ищем все ключи по паттерну
        keys = await self.redis.keys("history:*")
        # Удаляем
        if keys: await self.redis.delete(*keys)
        # Логируем
        logger.debug(f"(Redis)\t All history cleared")

    @handle_redis_errors
    async def set_expiration(self, key: str, *, days=0.1):
        """Установить время жизни ключа в днях"""
        seconds = days * 24 * 60 * 60
        await self.redis.expire(key, seconds)
    
    @handle_redis_errors
    async def set_user_req_active(self, user_id):
        """Установить флаг user_processing:{user_id} = 1"""
        await self.redis.set(f"user_processing:{user_id}", value=1, ex=60) # expiration 60 sec
        # logger.debug(f"(Redis)\t User with id {user_id} is processing")
    
    @handle_redis_errors
    async def is_user_waiting(self, user_id):
        """Проверить, активен ли запрос пользователя"""
        return await self.redis.exists(f"user_processing:{user_id}")
    
    @handle_redis_errors
    async def set_user_req_inactive(self, user_id):
        """Установить флаг user_processing:{user_id} = 0"""
        await self.redis.delete(f"user_processing:{user_id}")
        # logger.debug(f"(Redis)\t User {user_id} requests set to inactive")

    @handle_redis_errors
    async def clear_all_waitings(self):
        """Очистить все флаги активности запроса всех пользователей"""
        # Ищем все ключи по паттерну
        keys = await self.redis.keys("user_processing:*")
        # Удаляем ключи
        if keys:await self.redis.delete(**keys)  # Правильная передача аргументов
        # Логируем
        logger.debug(f"(Redis)\t All waitings cleared")

    @handle_redis_errors
    async def get_rb_clickid(self, user_id: str):
        """Получить rb_clickid по user_id"""
        rb_clickid = await self.redis.get(f"rb_clickid:{user_id}")
        if rb_clickid: logger.debug(f"(Redis)\t rb_clickid getted for user {user_id}")
        else: logger.debug(f"(Redis)\t no rb_clickid for user {user_id}")
        return rb_clickid
    
    @handle_redis_errors
    async def update_rb_clickid_to_user(self, sha256: str, user_id: int):
        """Присваиваивает(или обновляет) rb_clickid конкретному пользователю"""
        # Получаем rb_clickid по хэшу
        rb_clickid = await self.redis.get(f"rb_clickid:{sha256}")
        if not rb_clickid:
            logger.error(f"(Redis)\t Нет хэша rb_clickid")
            return
        # Удаляем rb_clickid по хэшу (так как больше не нужен)
        await self.redis.delete(f"rb_clickid:{sha256}")
        # seconds = 10 * 24 * 60 * 60                                     # 10 дней
        # Обновляем rb_clickid для конкретного пользователя
        await self.redis.set(f"rb_clickid:{user_id}", rb_clickid)
        logger.debug(f"(Redis)\t updated rb_clickid for user {user_id}")

        
