import telegramify_markdown
from telegramify_markdown.customize import markdown_symbol
from telegramify_markdown.interpreters import BaseInterpreter, MermaidInterpreter
from telegramify_markdown.type import ContentTypes

from aiogram.types import Message
from aiogram.enums import ParseMode

from src.logger import logger

import asyncio


# Copied from 
# https://github.com/sudoskys/telegramify-markdown/blob/main/playground/telegramify_case.py


async def answer_message(md: str, message: Message):
    boxs = await telegramify_markdown.telegramify(
        content=md,
        interpreters_use=[BaseInterpreter(), MermaidInterpreter(session=None)],  # Render mermaid diagram
        latex_escape=True,
        normalize_whitespace=True,
        max_word_count=4090  # The maximum number of words in a single message.
    )
    for item in boxs:
        """
        Telegram имеет ограничения на количество сообщений, отправляемых за короткий промежуток времени. 
        Если сервер медленный, он может не успеть обработать несколько сообщений до того, как Telegram ограничит отправку.
        """
        asyncio.sleep(0.5)
        try:
            if item.content_type == ContentTypes.TEXT:
                await message.answer(
                    item.content,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            '''
            elif item.content_type == ContentTypes.PHOTO:
                print("PHOTO")
                """
                bot.send_sticker(
                    chat_id,
                    (item.file_name, item.file_data),
                )
                """
                bot.send_photo(
                    chat_id,
                    (item.file_name, item.file_data),
                    caption=item.caption,
                    parse_mode="MarkdownV2"
                )
            elif item.content_type == ContentTypes.FILE:
                print("FILE")
                bot.send_document(
                    chat_id,
                    (item.file_name, item.file_data),
                    caption=item.caption,
                    parse_mode="MarkdownV2"
                )
            '''
        except Exception as e:
            logger.error(f"telegramify_markdown Error: {e}")
            raise e