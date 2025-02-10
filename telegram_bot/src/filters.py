from typing import Union

from aiogram.filters import BaseFilter, Command
from aiogram.types import Message

from src.database import Redis


class ChatModeFilter(BaseFilter):
    def __init__(self, mode: str):
        self.mode = mode

    async def __call__(self, message: Message, redis: Redis) -> bool:
        """ Проверяет, совпадает ли режим пользователя с требуемым """
        
        # redis: Redis = data.get("redis")

        if redis is None:
            raise ValueError("Redis instance must be provided in the context data.")

        user_mode = await redis.get_user_mode(message.from_user.id)

        return user_mode == self.mode
    
class ChatTypeFilter(BaseFilter):  # [1]
    def __init__(self, chat_type: Union[str, list]): # [2]
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:  # [3]
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type