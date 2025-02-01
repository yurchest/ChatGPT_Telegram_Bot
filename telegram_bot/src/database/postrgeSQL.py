from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, BigInteger, func, text, DateTime
from sqlalchemy.sql import expression
from sqlalchemy.exc import SQLAlchemyError

from src.logger import logger

from src.config import SUBSCRIPTION_DURATION_MONTHS, TRIAL_PERIOD_NUM_REQ

from dateutil.relativedelta import relativedelta
from datetime import datetime
import pytz

class Base(DeclarativeBase): pass

def handle_db_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"(POSTGRE)\t Error in {func.__name__}: {e}")
            return None
    return wrapper

class User(Base):
    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True, unique=True, index=True)
    first_name = Column(String(255))
    username = Column(String(255))
    language_code = Column(String(127))
    register_date = Column(DateTime(timezone=True), server_default=func.now())
    num_requests = Column(BigInteger, default=0)
    num_input_tokens = Column(BigInteger, default=0)
    num_output_tokens = Column(BigInteger, default=0)
    sub_expiration_date = Column(DateTime(timezone=True), nullable=True)

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger)
    telegram_username = Column(String(255))
    create_date = Column(DateTime(timezone=True), server_default=func.now())
    currency = Column(String(100), nullable=False)
    total_amount = Column(Integer, nullable=False)
    telegram_payment_charge_id = Column(String, nullable=False)
    provider_payment_charge_id = Column(String, nullable=False)
    invoice_payload = Column(String, nullable=False)
    is_recurring = Column(String)
    subscription_expiration_date = Column(DateTime(timezone=True))
    is_first_recurring=Column(String)
    order_info=Column(String)

class Error(Base):
    __tablename__ = 'errors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(255))
    text = Column(String())
    file_path = Column(String())
    telegram_id = Column(BigInteger, index=True)
    create_date = Column(DateTime(timezone=True), server_default=func.now())
    traceback = Column(String())
    is_resolved = Column(Boolean, default=False)

class Database:
    def __init__(self, db_url: str):
        try:
            self.engine = create_async_engine(db_url) # echo=True
            self.SessionLocal = sessionmaker(
                bind=self.engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("(POSTGRE)\t Database connection established")
        except (SQLAlchemyError, ConnectionRefusedError) as e:
            logger.critical(f"(POSTGRE)\t Error while initializing database engine: {e}")
            self.close()
            raise


    async def create_tables_if_not_exist(self):
        """Установить соединение с базой данных и создать таблицы."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("(POSTGRE)\t POSTGRE tables created if not exist")
        except (SQLAlchemyError, ConnectionRefusedError) as e:
            logger.critical(f"(POSTGRE)\t Error while connecting to POSTGRE: {e}")
            await self.close()
            raise
            

    async def close(self):
        """Закрыть соединение с базой данных."""
        try:
            if self.engine:
                await self.engine.dispose()
                logger.info("(POSTGRE)\t POSTGRE connection closed")
        except Exception as e:
            logger.error(f"(POSTGRE)\t Error closing the POSTGRE connection: {e}")


    @handle_db_errors
    async def add_user(self, telegram_id: int, first_name: str, username: str, language_code: str):
        """Добавить пользователя в базу данных."""
        async with self.SessionLocal() as session:
            async with session.begin():
                user = User(
                    telegram_id=telegram_id,
                    first_name=first_name if first_name else None,
                    username=username if username else None,
                    language_code=language_code,
                )
                session.add(user)
                logger.info("(POSTGRE)\t User added with username: %s", username)

    @handle_db_errors
    async def is_user_exists(self, telegram_id: int) -> bool:
        """Проверить, существует ли пользователь в базе данных."""
        async with self.SessionLocal() as session:
            result = await session.execute(
                text(f"""SELECT EXISTS(SELECT 1 FROM users WHERE telegram_id = :telegram_id)"""),
                {"telegram_id": telegram_id},
            )
            return result.scalar()
    
    @handle_db_errors
    async def increment_user_requests(self, telegram_id: int):
        """Увеличить счетчик запросов пользователя."""
        async with self.SessionLocal() as session:
            async with session.begin():
                user = await session.get(User, telegram_id)
                user.num_requests += 1
                logger.debug(f"(POSTGRE)\t User {telegram_id} requests incremented")

    @handle_db_errors
    async def add_user_input_tokens(self, telegram_id: int, tokens: int):
        """Добавить входные токены пользователю."""
        async with self.SessionLocal() as session:
            async with session.begin():
                user = await session.get(User, telegram_id)
                user.num_input_tokens += tokens
                # logger.info(f"(POSTGRE)\t User {telegram_id} input tokens ({tokens}) added")

    @handle_db_errors
    async def add_user_output_tokens(self, telegram_id: int, tokens: int):
        """Добавить выходные токены пользователю."""
        async with self.SessionLocal() as session:
            async with session.begin():
                user = await session.get(User, telegram_id)
                user.num_output_tokens += tokens
                # logger.info(f"(POSTGRE)\t User {telegram_id} output tokens ({tokens}) added")

    @handle_db_errors
    async def get_num_requests(self, telegram_id: int) -> int:
        """Получить количество запросов пользователя."""
        async with self.SessionLocal() as session:
            user = await session.get(User, telegram_id)
            return user.num_requests
        
    @handle_db_errors
    async def is_user_trial(self, telegram_id: int) -> bool:
        """
        Проверка на пробный период (num_requests <= TRIAL_PERIOD_NUM_REQ)
        """
        async with self.SessionLocal() as session:
            user = await session.get(User, telegram_id)
            return user.num_requests < TRIAL_PERIOD_NUM_REQ

    @handle_db_errors
    async def is_subscription_active(self, telegram_id: int) -> bool:
        """
        Проверить, активна ли подписка пользователя.
        Если sub_expiration_date is not NULL и текущая дата меньше sub_expiration_date
        """
        async with self.SessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT sub_expiration_date > now()
                    FROM users
                    WHERE telegram_id = :telegram_id AND sub_expiration_date IS NOT NULL
                """),
                {"telegram_id": telegram_id},
            )
            return result.scalar() or False
    
    @handle_db_errors
    async def update_sub_expiration_date(self, telegram_id: int, date: DateTime):
        """Обновить дату окончания подписки пользователя."""
        async with self.SessionLocal() as session:
            async with session.begin():
                user = await session.get(User, telegram_id)
                user.sub_expiration_date = date
                logger.debug(f"(POSTGRE)\t Updated subscription expiration date for user {telegram_id}")

    @handle_db_errors
    async def get_sub_expiration_date(self, telegram_id: int, user_tz: str) -> datetime:
        """Получить дату окончания подписки пользователя."""
        async with self.SessionLocal() as session:
            user = await session.get(User, telegram_id)
            if user is None or user.sub_expiration_date is None:
                return None
            
            # Преобразуем в локальное время пользователя
            local_tz = pytz.timezone(user_tz)
            return user.sub_expiration_date.astimezone(local_tz)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Errors
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @handle_db_errors
    async def add_error(self, 
                        error_type: str,
                        error_text: str,
                        file_path: str,
                        telegram_id: int,
                        traceback: str
                        ):
        """Добавить ошибку"""
        async with self.SessionLocal() as session:
            async with session.begin():
                error = Error(
                    type = error_type,
                    text = error_text,
                    file_path = file_path,
                    telegram_id = telegram_id,
                    traceback=traceback
                )
                session.add(error)
                logger.debug(f"(POSTGRE)\t Added Error record")

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Payments
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @handle_db_errors
    async def add_payment(self, telegram_id: int, 
                          telegram_username: str, 
                          currency: str, 
                          total_amount: int, 
                          telegram_payment_charge_id: str, 
                          provider_payment_charge_id: str, 
                          invoice_payload: str, 
                          is_recurring: str, 
                          subscription_expiration_date: DateTime, 
                          is_first_recurring: str, 
                          order_info: str):
        """
        Добавить платеж в таблицу payments.
        Обновить sub_expiration_date в users 
        """
        async with self.SessionLocal() as session:
            async with session.begin():
                payment = Payment(
                    telegram_id=telegram_id,
                    telegram_username=telegram_username,
                    currency=currency,
                    total_amount=total_amount,
                    telegram_payment_charge_id=telegram_payment_charge_id,
                    provider_payment_charge_id=provider_payment_charge_id,
                    invoice_payload=invoice_payload,
                    is_recurring=is_recurring,
                    subscription_expiration_date=subscription_expiration_date,
                    is_first_recurring=is_first_recurring,
                    order_info=order_info
                )
                session.add(payment)
                logger.debug(f"(POSTGRE)\t Payment {provider_payment_charge_id} added for user: {telegram_username}")

                # Обновить sub_expiration_date (payment.create_date + SUBSCRIPTION_DURATION_MONTHS) в users
                user = await session.get(User, telegram_id)
                if user.sub_expiration_date is None or not await self.is_subscription_active(telegram_id):
                    user.sub_expiration_date = payment.create_date + relativedelta(months=SUBSCRIPTION_DURATION_MONTHS)
                else:
                    user.sub_expiration_date += relativedelta(months=SUBSCRIPTION_DURATION_MONTHS)
                logger.debug(f"(POSTGRE)\t Updated subscription expiration date for user {telegram_id}")
                

