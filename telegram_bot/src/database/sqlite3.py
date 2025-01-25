import aiosqlite
from src.logger import logger

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None

    async def connect(self):
        """
        Установка  соединение с базой данных.
        """
        try:
            self.connection = await aiosqlite.connect(self.db_path)
            logger.info("Database connected with path: %s", self.db_path)
        except Exception as e:
            logger.error("Error while connecting to database: %s", e)
            raise e

    async def close(self):
        """
        Закрыть соединение с базой данных.
        """
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")
        
    async def create_tables(self):
        """Create tables if they don't exist."""
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                telegram_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                username TEXT,
                language_code TEXT,
                register_date TIMESTAMP DEFAULT (DATETIME(CURRENT_TIMESTAMP, '+3 hours')),
                num_requests INTEGER DEFAULT 0,
                num_input_tokens INTEGER DEFAULT 0,
                num_output_tokens INTEGER DEFAULT 0,
                is_sub INTEGER NOT NULL DEFAULT 0,
                last_paid_date TIMESTAMP,
                last_paid_number INTEGER       
            )
        ''') # TODO: Возможно изменить  
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS Payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        ''')
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS Errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        ''')
        await self.connection.commit()
        logger.info("Created tables if they don't exist")

    async def add_user(self, telegram_id: int, first_name: str, username: str, language_code: str):
        """Add a user to the database."""
        
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                '''
                INSERT INTO Users (telegram_id, first_name, username, language_code)
                VALUES (?, ?, ?, ?)
                ''',
                (telegram_id, first_name, username, language_code)
            )
            await self.connection.commit()
        logger.info("User added with username: %s", username)

    async def is_user_exists(self, telegram_id: int) -> bool:
        """Check if the user exists in the database."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                '''
                SELECT EXISTS(SELECT 1 FROM Users WHERE telegram_id = ?)
                ''',
                (telegram_id,)
            )
            [exists] = await cursor.fetchone()
            return bool(exists)

    async def fetchone(self, query: str, parameters: tuple = ()):
        """
        Выполнить SQL-запрос и вернуть одну строку результата.
        :param query: Текст SQL-запроса.
        :param parameters: Параметры для подстановки в запрос.
        """
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, parameters)
            return await cursor.fetchone()

