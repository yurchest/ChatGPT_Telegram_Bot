import logging
import colorlog


def init_logger():
    logger = logging.getLogger('chatgpt_telegram_bot')
    logger.setLevel(logging.DEBUG)

    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s\t %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )

    formatter2 = colorlog.ColoredFormatter(
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
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter2)
    
    if not logger.hasHandlers():
        logger.addHandler(console_handler)


    return logger


logger = init_logger()
