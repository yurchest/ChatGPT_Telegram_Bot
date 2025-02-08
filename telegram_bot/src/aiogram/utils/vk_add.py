import aiohttp

from src.config import VK_PIXEL_ID

from src.logger import logger



## https://top-fwz1.mail.ru/tracker?id=3610766;e=RG%3A0/start;rb_clickid=RBCLICKID

async def vk_send_pixel_event(rb_clickid: str, goal_name: str):
    """Отправляет событие (цель) в Mail.ru Pixel"""

    # Формируем URL с параметрами
    url = f"https://top-fwz1.mail.ru/tracker?id={VK_PIXEL_ID};e=RG%3A100/{goal_name};rb_clickid={rb_clickid}"
    
    # Отправка GET запроса
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            logger.debug(f"Sent {goal_name} to vk_ads")
            return await response.read()  # Читаем содержимое изображения


        
async def parse_utm(utm_str: str):
    """Разбираем UTM-метки из start-параметра"""
    utm_str = utm_str.replace("__", "&")  # Возвращаем обычный формат
    utm_params = {}

    for param in utm_str.split("&"):
        key_value = param.split("-")
        if len(key_value) == 2:
            utm_params[key_value[0]] = key_value[1]

    return utm_params