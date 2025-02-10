import openai
from openai import AsyncOpenAI
import asyncio
from typing import BinaryIO

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
    async def get_response(self, conversation_history: list, user_message: dict) -> dict:
        """Асинхронный запрос к OpenAI API"""
        api_message = conversation_history + [user_message]

        chat_completion = await self.client.chat.completions.create(
            model=self.model_id,
            messages=api_message,
            max_completion_tokens=MAX_TOKENS,
        )
        logger.debug(f"(OpenAI)\t Get response from OpenAI")

        # length    - что-то недописал по причине ограничения max_completion_tokens
        # stop      - все дописал

        response = {
            "user_message": user_message,
            "assistant_reply": chat_completion.choices[0].message.content.strip(),
            "finish_reason": chat_completion.choices[0].finish_reason,
            "role": chat_completion.choices[0].message.role,
            "num_in_tokens": chat_completion.usage.prompt_tokens,
            "num_out_tokens": chat_completion.usage.completion_tokens
        }
        
        return response
    
    @handle_openai_errors
    async def add_file(self, fileIO: BinaryIO) -> str:
        file = await self.client.files.create(
            file=fileIO,
            purpose="assistants"
        )
        logger.debug(f"(OpenAI)\t File {fileIO.name} downloaded")
        return file.filename, file.id

    
    @handle_openai_errors
    async def create_vector_store_to_user(self, user_id: int) -> str:
        """Создание пустой vector_store для конкретного пользователя"""
        vector_store_name = f"Vector Store for {user_id}"
        vector_store = await self.client.beta.vector_stores.create(
            name=vector_store_name,
            file_ids=None,      # без файлов
            expires_after={
                "anchor": "last_active_at",
                "days": 1,
            },    # days
        )

        logger.debug(f"(OpenAI)\t Created vector_store: '{vector_store_name}'")
        return vector_store.id

        
    @handle_openai_errors
    async def add_file_to_vector_store(self, vector_store_id: str, file_id: str) -> str:
        """Добавление файла в vector_store"""
        file =  await self.client.beta.vector_stores.files.create_and_poll(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        logger.debug(f"(OpenAI)\t Added file to vector_store {vector_store_id}, file_id: '{file_id}'")

        return file.id

    @handle_openai_errors
    async def create_thread_for_user(self, vector_store_id: str) -> str:
        """
        Создание пустого `thread` для пользователя с привязкой к его `vector_store`
        """

        thread = await self.client.beta.threads.create(
            # messages=[ { "role": "user", "content": "How do I cancel my subscription?"} ],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store_id,]
                }
            }
        )
        logger.debug(f"(OpenAI)\t Created thread: '{thread.id}'")

        return thread.id
    
    @handle_openai_errors
    async def get_thread_response(self, user_message: str, thread_id: str) -> str:
        """Получает ответ от `thread`"""
        await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message,
        )

        run = await self.client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=OPENAI_ASSISTANT_ID
        )

        messages = [msg async for msg in self.client.beta.threads.messages.list(thread_id=thread_id, run_id=run.id)]

        if not messages:
            logger.error(f"(OpenAI)\t no messages for file analuze")
            return "Ошибка: OpenAI не вернул сообщений"
        
        message_content = messages[0].content[0].text
        annotations = message_content.annotations

        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(annotation.text, f"[{index}]")

        return message_content.value
    
    @handle_openai_errors
    async def delete_all_file_data(self, thread_id: str):
        thread = await self.client.beta.threads.retrieve(thread_id)
        vectore_store_id = thread.tool_resources.file_search.vector_store_ids[0]

        async for file in self.client.beta.vector_stores.files.list(vectore_store_id):
            await self.client.files.delete(file.id)
            logger.debug(f"(OpenAI)\t Deleted file `{file.id}`")

        await self.client.beta.vector_stores.delete(vectore_store_id)
        logger.debug(f"(OpenAI)\t Deleted vector_store `{vectore_store_id}`")

        await self.client.beta.threads.delete(thread_id)
        logger.debug(f"(OpenAI)\t Deleted thread `{thread_id}`")



    @handle_openai_errors
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

        # logger.debug(f"(OpenAI)\t messages_file: {messages}")

        if not messages:
            logger.error(f"(OpenAI)\t no messages for file analuze")
            return "Ошибка: OpenAI не вернул сообщений"

        message_content = messages[0].content[0].text
        annotations = message_content.annotations

        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(annotation.text, f"[{index}]")


        # logger.debug(f"(OpenAI)\t message_content_file: {message_content.value}")

        await self.client.beta.threads.delete(thread.id)
        await self.client.files.delete(file.id)
        

        return message_content.value


