import json
import pytz

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import (
    Message, 
    LabeledPrice, 
    PreCheckoutQuery, 
    CallbackQuery, 
    Message, 
    )

from src.logger import logger

from src.database import Redis, Database
from src.aiogram.middlewares.middlewares import WaitingMiddleware 
from src.aiogram.handlers.system import get_payment_keyboard_markup

from src.config import (
    YOOKASSA_PAYMENT_TOKEN, 
    SUBSCRIPTION_PRICE_RUB, 
    SUBSCRIPTION_DURATION_MONTHS,
    EMAIL_FOR_BILL
    )


router = Router()

router.message.middleware(WaitingMiddleware())

@router.callback_query(F.data == "pay")
async def pay_callback(callback: CallbackQuery, bot: Bot, db: Database):
    await send_invoice(
        bot=bot, 
        chat_id=callback.message.chat.id,
        full_name=callback.from_user.full_name,
        user_name=callback.from_user.username
        )
    await callback.answer() # Чтобы убрать ожидание (часики)
    

@router.message(Command('pay'))
async def pay_handler(message: Message, bot: Bot, db: Database):
    if await db.is_subscription_active(message.from_user.id):
        sub_expiration_date = await db.get_sub_expiration_date(
            telegram_id=message.from_user.id, 
            user_tz="Europe/Moscow"
            )
        await message.answer(
            f"Вы уже подписаны \n"
            f"Дата окончания подписки: {sub_expiration_date.strftime("%Y-%m-%d %H:%M:%S")}\n"
            f"Но также вы можете продлить подписку",
            reply_markup=get_payment_keyboard_markup()
            )
        return

    await send_invoice(
        bot=bot, 
        chat_id=message.chat.id,
        full_name=message.from_user.full_name,
        user_name=message.from_user.username
        )

async def send_invoice(bot: Bot, chat_id: int, full_name: str, user_name: str):
    await bot.send_invoice(
        chat_id=chat_id,
        title="Оплата подписки",
        description=f"Оплата подписки Yurchest BOT на {SUBSCRIPTION_DURATION_MONTHS} месяц(ев)",
        payload="invoice",
        start_parameter="payment",
        provider_token=YOOKASSA_PAYMENT_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Оплата подписки", amount=SUBSCRIPTION_PRICE_RUB * 100)],
        provider_data=json.dumps(
            {
                "receipt": {
                        "customer" : {
                        "full_name" : f"{full_name} ({user_name})",
                        "email" : EMAIL_FOR_BILL,
                    },
                    "items":[
                        {
                            "description" : "Оплата подписки Yurchest BOT",
                            "quantity" : 1,
                            "amount" : {
                                "value" : SUBSCRIPTION_PRICE_RUB,
                                "currency" : "RUB"
                            },
                            "vat_code" : 1,
                            "payment_mode" : "full_payment",
                            "payment_subject" : "commodity"
                        }
                    ],
                    "tax_system_code" : 1
                }
            }
        )
    )

@router.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)
    logger.debug(f"(PAYMENT)\t Payment confirmed")

@router.message(F.successful_payment)
async def on_successful_payment(message: Message, db: Database):
    await message.answer(
        f"Успешно оплачено {message.successful_payment.total_amount // 100} {message.successful_payment.currency}! \
\nНомер платежа:\n{message.successful_payment.provider_payment_charge_id}",
message_effect_id="5104841245755180586",
)
    logger.debug(f"(PAYMENT)\t Successful payment")
    await db.add_payment(
        telegram_id=message.from_user.id,
        telegram_username=message.from_user.username,
        currency=message.successful_payment.currency,
        total_amount=message.successful_payment.total_amount // 100,
        telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
        provider_payment_charge_id=message.successful_payment.provider_payment_charge_id,
        invoice_payload=message.successful_payment.invoice_payload,
        is_recurring=message.successful_payment.is_recurring,
        subscription_expiration_date=message.successful_payment.subscription_expiration_date,
        is_first_recurring=message.successful_payment.is_first_recurring,
        order_info=message.successful_payment.order_info
    )
    
