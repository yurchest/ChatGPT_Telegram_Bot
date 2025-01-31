import os
from dotenv import load_dotenv, find_dotenv
from src.logger import logger


# Загружаем  .env файл
dotenv_path = "../.env" # TODO Закоментить Удалить на проде
load_dotenv(dotenv_path)

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Выбираем API ключ в зависимости от среды
if ENVIRONMENT == "prod":
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_PROD")
    YOOKASSA_PAYMENT_TOKEN = os.getenv("YOOKASSA_PAYMENT_TOKEN_LIVE")
else:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_DEV")
    YOOKASSA_PAYMENT_TOKEN = os.getenv("YOOKASSA_PAYMENT_TOKEN_TEST")



POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

POSTRGRES_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres/{POSTGRES_DB}"

REDIS_PORT=os.getenv("REDIS_PORT")
REDIS_HOST=os.getenv("REDIS_HOST")

REDIS_USER = os.getenv("REDIS_USER")
REDIS_USER_PASSWORD = os.getenv("REDIS_USER_PASSWORD")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

TRIAL_PERIOD_NUM_REQ = int(os.getenv("TRIAL_PERIOD_NUM_REQ"))
SUBSCRIPTION_DURATION_MONTHS = int(os.getenv("SUBSCRIPTION_DURATION_MONTHS")) # IN MOTHS
SUBSCRIPTION_PRICE_RUB = int(os.getenv("SUBSCRIPTION_PRICE_RUB"))
EMAIL_FOR_BILL=os.getenv("EMAIL_FOR_BILL")

# Проверка наличия переменных окружения
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables")
if not YOOKASSA_PAYMENT_TOKEN:
    raise ValueError("YOOKASSA_PAYMENT_TOKEN is not set in the environment variables")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables")

