import asyncio
import logging
from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config.settings import settings
from database.core import init_db, close_db
from middlewares.database import DatabaseMiddleware
from middlewares.ban_check import BanCheckMiddleware

from handlers.user_handlers import router as user_router
from handlers.farm_handlers import router as farm_router
from handlers.battle_handlers import router as battle_router
from handlers.market_handlers import router as market_router
from handlers.economy_handlers import router as economy_router
from handlers.rating_handlers import router as rating_router
from handlers.casino_handlers import router as casino_router
from handlers.admin_handlers import router as admin_router
from handlers.exchange_handlers import router as exchange_router
from handlers.group_pvp import router as group_pvp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="profile", description="👤 Мой профиль"),
        BotCommand(command="top", description="🏆 Топ игроков"),
        BotCommand(command="collect", description="💰 Собрать доход"),
        BotCommand(command="farm", description="🌱 Ферма"),
        BotCommand(command="battle", description="⚔️ Боевая арена"),
        BotCommand(command="market", description="🏪 Рынок"),
        BotCommand(command="casino", description="🎰 Казино"),
        BotCommand(command="pvp", description="⚔️ Вызвать на дуэль (в группе)"),
        BotCommand(command="rating", description="🏆 Рейтинги"),
        BotCommand(command="help", description="❓ Помощь"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Меню команд установлено")

async def main():
    logger.info("Инициализация БД...")
    await init_db()
    logger.info("БД инициализирована")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )

    await set_commands(bot)

    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())

    dp.include_router(user_router)
    dp.include_router(farm_router)
    dp.include_router(battle_router)
    dp.include_router(market_router)
    dp.include_router(economy_router)
    dp.include_router(rating_router)
    dp.include_router(casino_router)
    dp.include_router(admin_router)
    dp.include_router(exchange_router)
    dp.include_router(group_pvp_router)

    logger.info(f"✅ Зарегистрировано роутеров: {len(dp.sub_routers)}")
    logger.info("🚀 Бот запущен!")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    finally:
        await close_db()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
