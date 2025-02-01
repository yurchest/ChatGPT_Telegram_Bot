import openai
from openai import AsyncOpenAI
import asyncio

from src.config import OPENAI_API_KEY
from src.logger import logger

def handle_openai_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"(OpenAI)\t Error in {func.__name__}: {e}")
            return None
    return wrapper

class OpenAI_API():
    def __init__(self):
        try:
            """Инициализируем OpenAI API"""
            self.model_id = "gpt-4o-mini"
            self.client = AsyncOpenAI(
                api_key=OPENAI_API_KEY,  # This is the default and can be omitted
            )
            self.check_task = asyncio.create_task(self.check_connection())
        except Exception as e:
            logger.error(f"(OpenAI)\t Error initializing API: {e}")
            self.client = None
            raise
    
    @classmethod
    async def create(cls):
        self = cls()
        await self.check_task  # Дожидаемся завершения задачи
        return self
    
    async def check_connection(self):
        """Проверка соединения с OpenAI API"""
        try:
            response = await self.client.models.list()
            if response:
                logger.info("(OpenAI)\t Connection successful")
                return True
        except openai.APIConnectionError as e:
            logger.error("(OpenAI)\t The server could not be reached")
            logger.error(e.__cause__)  # an underlying Exception, likely raised within httpx.
            raise
        except openai.RateLimitError as e:
            logger.error("(OpenAI)\t A 429 status code was received; we should back off a bit.")
            raise
        except openai.APIStatusError as e:
            logger.error("(OpenAI)\t Another non-200-range status code was received")
            logger.error(e.status_code)
            logger.error(e.response)
            raise
        except Exception:
            raise

    
    @handle_openai_errors
    async def get_response(self, conversation_history: list, user_message: dict):
        """Асинхронный запрос к OpenAI API"""
        api_message = conversation_history + [user_message]
        # logger.debug(f"(OpenAI)\t API message: {api_message}")
        response = await self.client.chat.completions.create(
            model=self.model_id,
            messages=api_message,
        )

        role = response.choices[0].message.role
        assistent_reply = response.choices[0].message.content.strip()
        num_in_tokens = response.usage.prompt_tokens
        num_out_tokens = response.usage.completion_tokens
        logger.debug(f"(OpenAI)\t Get response from OpenAI")
        return assistent_reply, role, num_in_tokens, num_out_tokens

    @handle_openai_errors
    async def chatgpt_conversation(self, user_text: str, conversation: list = []):
        if conversation:
            conversation.append({'role': 'user', 'content': user_text})
        else:
            conversation = [{'role': 'user', 'content': user_text}]
        response = await self._get_response(conversation)
        conversation.append({
            'role': response.choices[0].message.role,
            'content': response.choices[0].message.content.strip()
        })
        return conversation
    