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
        asyncio.create_task(self.check_connection())

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
        await self.set_expiration(user_id=user_id, days=7)
        logger.debug(f"(Redis)\t Added: messages to user with id {user_id}")

    @handle_redis_errors
    async def clear_user_history(self, user_id):
        """Очистить историю сообщений для пользователя"""
        await self.redis.delete(f"history:{user_id}")
        logger.debug(f"(Redis)\t History user {user_id} cleared")

    @handle_redis_errors
    async def clear_all_history(self):
        """Очистить всю историю сообщений"""
        async for key in self.redis.scan_iter("history:*"):
            await self.redis.delete(key)
        logger.debug(f"(Redis)\t All history cleared")

    @handle_redis_errors
    async def set_expiration(self, user_id, days=0.1):
        """Установить время жизни ключа в днях"""
        seconds = days * 24 * 60 * 60
        await self.redis.expire(user_id, seconds)
    
    @handle_redis_errors
    async def set_user_req_active(self, user_id):
        """Установить флаг user_processing:{user_id} = 1"""
        await self.redis.set(f"user_processing:{user_id}", 1)
        await self.set_expiration(f"user_processing:{user_id}", days=1)
        # logger.debug(f"(Redis)\t User with id {user_id} is processing")
    
    @handle_redis_errors
    async def is_user_waiting(self, user_id):
        """Проверить, активен ли запрос пользователя"""
        # logger.debug(f"(Redis)\t User with id {user_id} is waiting")
        return await self.redis.exists(f"user_processing:{user_id}")
    
    @handle_redis_errors
    async def set_user_req_inactive(self, user_id):
        """Установить флаг user_processing:{user_id} = 0"""
        await self.redis.delete(f"user_processing:{user_id}")
        logger.debug(f"(Redis)\t User {user_id} requests set to inactive")

    @handle_redis_errors
    async def clear_all_waitings(self):
        """Очистить все флаги активности запроса всех пользователей"""
        async for key in self.redis.scan_iter("user_processing:*"):
            await self.redis.delete(key)
        logger.debug(f"(Redis)\t All waitings cleared")
