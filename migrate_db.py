import asyncio
from sqlalchemy import text
from database.core import engine

async def migrate():
    print("🔧 Запуск миграции...")
    try:
        async with engine.connect() as conn:
            print("➕ Меняем тип колонки telegram_id на BIGINT...")
            await conn.execute(text("ALTER TABLE users ALTER COLUMN telegram_id TYPE BIGINT"))
            await conn.commit()
            print("✅ Миграция выполнена успешно!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate())
