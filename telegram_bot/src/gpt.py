import openai
from openai import AsyncOpenAI
import asyncio

from src.config import OPENAI_API_KEY, ENVIRONMENT, MAX_TOKENS, OPENAI_ASSISTANT_ID
from src.logger import logger

def handle_openai_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"(OpenAI)\t Error in {func.__name__}: {e}")
            raise
    return wrapper

class OpenAI_API():
    def __init__(self):
        try:
            """Инициализируем OpenAI API"""
            self.model_id = "gpt-4o-mini" if ENVIRONMENT=="prod" else "gpt-4o-mini"
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
            max_completion_tokens=MAX_TOKENS,
        )
        logger.debug(f"(OpenAI)\t Get response from OpenAI")
        # logger.debug(f"(OpenAI)\t response: {response}")

        # length    - что-то недописал по причине ограничения max_completion_tokens
        # stop      - все дописал
        finish_reason: str = response.choices[0].finish_reason 

        logger.debug(f"(OpenAI)\t Finish_reason: {finish_reason}")

        role = response.choices[0].message.role
        assistent_reply = response.choices[0].message.content.strip()
        num_in_tokens = response.usage.prompt_tokens
        num_out_tokens = response.usage.completion_tokens
        
        return assistent_reply, role, num_in_tokens, num_out_tokens

    async def get_file_response(self, file_io, user_message):
        # Загружаем файл в OpenaAI
        file = await self.client.files.create(file=file_io, purpose="assistants")    

        # Создаем новый поток
        thread = await self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                    "attachments": [
                        {"file_id": file.id, "tools": [{"type": "file_search"}]}
                    ]
                }
            ]
        )

        run = await self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, 
            assistant_id=OPENAI_ASSISTANT_ID
        )
        # messages = list(self.client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
        messages = [msg async for msg in self.client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)]

        logger.debug(f"(OpenAI)\t messages_file: {messages}")

        if not messages:
            return "Ошибка: OpenAI не вернул сообщений"

        message_content = messages[0].content[0].text
        annotations = message_content.annotations

        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(annotation.text, f"[{index}]")


        logger.debug(f"(OpenAI)\t message_content_file: {message_content.value}")

        await self.client.files.delete(file.id)

        return message_content.value


