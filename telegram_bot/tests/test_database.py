import pytest
from . import Database

import random

@pytest.mark.asyncio
async def test_database():
    db = Database("database.db")
    telegram_id = random.randint(1, 100000000)
    try:
        await db.connect()
        await db.add_user(telegram_id, "name", "username")
        result = await db.fetchone("SELECT * FROM Users WHERE telegram_id = ?", (telegram_id,))
    finally:
        await db.close()
    
    print(result)
    assert result[:3] == (telegram_id, "name", "username")