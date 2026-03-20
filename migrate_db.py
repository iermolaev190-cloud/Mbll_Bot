import asyncio
from sqlalchemy import text
from database.core import engine

async def migrate():
    print("🔧 Запуск миграции...")
    async with engine.connect() as conn:
        print("➕ Меняем тип колонки telegram_id на BIGINT...")
        await conn.execute(text("ALTER TABLE users ALTER COLUMN telegram_id TYPE BIGINT"))
        await conn.commit()
        print("✅ Миграция выполнена!")

if __name__ == "__main__":
    asyncio.run(migrate())
