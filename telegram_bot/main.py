from src.config import TELEGRAM_BOT_TOKEN, POSTRGRES_URL, REDIS_PORT, REDIS_HOST
from src.database import Database, Redis
from src.gpt import OpenAI_API
from src.logger import logger
from src.aiogram.middlewares.middlewares import (
    DatabaseMiddleware, 
    OpenAIMiddleware, 
    RedisMiddleware, 
    )
from src.aiogram.handlers.system import on_startup, on_shutdown, init_error_handler
from src.aiogram.handlers import messages, commands, erorrs, payment

from aiogram.methods import DeleteWebhook
from aiogram import Bot, Dispatcher

import asyncio
from functools import partial

from prometheus_client import start_http_server, Summary

@init_error_handler
async def main() -> None:
    # db = Database("./database.db") # sqlite3
    db = Database(POSTRGRES_URL) # PostgreSQL
    db_middleware = DatabaseMiddleware(db)

    openai = OpenAI_API()
    openai_middleware = OpenAIMiddleware(openai)

    redis = Redis(REDIS_HOST, REDIS_PORT)
    redis_middleware = RedisMiddleware(redis)

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_routers(
        payment.router,
        commands.router,
        messages.router, 
        erorrs.router,
        )
    
    # Регистрация lifecycle-событий
    dp.startup.register(partial(on_startup, db))
    dp.shutdown.register(partial(on_shutdown, db, redis))

    dp.update.middleware(db_middleware)
    dp.update.middleware(redis_middleware)
    dp.update.middleware(openai_middleware)

    dp.errors.middleware(redis_middleware)
    dp.errors.middleware(db_middleware)
    
    
    logger.info("(MAIN)\t\t Bot has started successfully")
    
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Start up the server to expose the metrics.
    start_http_server(8000)

    asyncio.run(main())





