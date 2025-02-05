import logging
import colorlog

import pytz
from datetime import datetime

# Устанавливаем часовой пояс Москвы
moscow_tz = pytz.timezone("Europe/Moscow")

# Кастомный time formatter для учета часового пояса
class MoscowFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, moscow_tz)
        return dt.strftime(datefmt if datefmt else "%Y-%m-%d %H:%M:%S")

def init_logger():
    # Форматтер для файла (без цветов)
    file_formatter = MoscowFormatter(
        "%(asctime)s %(levelname)s\t %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Форматтер для терминала (с цветами)
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s %(levelname)s\t %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # Создаем логгер
    logger = logging.getLogger('chatgpt_telegram_bot')
    logger.setLevel(logging.DEBUG)

    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    # Обработчик для файла (с московским временем, без цветов)
    file_handler = logging.FileHandler("logs/bot.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Логируем только INFO и выше
    file_handler.setFormatter(file_formatter)

    # Обработчик для консоли (с цветами и московским временем)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Логируем все, включая DEBUG
    console_handler.setFormatter(console_formatter)

    # Добавляем обработчики в логгер
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = init_logger()
