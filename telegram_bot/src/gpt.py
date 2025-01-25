from openai import AsyncOpenAI

from src.config import OPENAI_API_KEY
from src.logger import logger

class OpenAI_API():
    def __init__(self):
        """Инициализируем OpenAI API"""
        self.model_id = "gpt-4o-mini"
        self.client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,  # This is the default and can be omitted
        )
        logger.info("(OpenAI)\t API initialized")

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
        logger.debug(f"(OpenAI)\t Get respone from OpenAI")
        return assistent_reply, role, num_in_tokens, num_out_tokens

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
    