import asyncio
from database.core import engine
from sqlalchemy import text

async def fix_telegram_id_column():
    """Изменяет тип колонки telegram_id с INTEGER на BIGINT"""
    print("🔧 Начинаем исправление типа колонки telegram_id...")

    async with engine.connect() as conn:
        # Проверяем текущий тип
        result = await conn.execute(text("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='telegram_id'
        """))
        current_type = result.scalar()
        print(f"📊 Текущий тип: {current_type}")

        if current_type != 'bigint':
            print("➕ Меняем тип на BIGINT...")
            # Изменяем тип колонки
            await conn.execute(text("""
                ALTER TABLE users 
                ALTER COLUMN telegram_id TYPE BIGINT
            """))
            await conn.commit()
            print("✅ Тип колонки успешно изменён на BIGINT!")
        else:
            print("✅ Тип колонки уже BIGINT")

        # Проверяем результат
        result = await conn.execute(text("""
            SELECT telegram_id FROM users LIMIT 1
        """))
        sample = result.scalar()
        print(f"🎉 Пример данных: {sample}")

if __name__ == "__main__":
    asyncio.run(fix_telegram_id_column())
    print("\n✅ Готово! Теперь перезапусти бота.")
