from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.database import Database, Redis
from src.gpt import OpenAI_API



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