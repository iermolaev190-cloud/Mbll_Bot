import asyncio
from sqlalchemy import text
from database.core import engine

async def fix_telegram_id_column():
    """Изменяет тип колонки telegram_id с INTEGER на BIGINT"""
    print("🔧 Начинаем исправление типа колонки telegram_id...")

    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='telegram_id'
        """))
        row = await result.fetchone()
        current_type = row[0] if row else None
        print(f"📊 Текущий тип: {current_type}")

        if current_type != 'bigint':
            print("➕ Меняем тип на BIGINT...")
            await conn.execute(text("""
                ALTER TABLE users 
                ALTER COLUMN telegram_id TYPE BIGINT
            """))
            await conn.commit()
            print("✅ Тип колонки успешно изменён на BIGINT!")
        else:
            print("✅ Тип колонки уже BIGINT")

        result = await conn.execute(text("SELECT telegram_id FROM users LIMIT 1"))
        row = await result.fetchone()
        if row:
            print(f"🎉 Пример данных: {row[0]}")

if __name__ == "__main__":
    asyncio.run(fix_telegram_id_column())
    print("\n✅ Готово! Теперь верни Procfile на python main.py и перезапусти бота.")
