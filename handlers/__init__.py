from handlers.user_handlers import router as user_router
from handlers.farm_handlers import router as farm_router
from handlers.battle_handlers import router as battle_router
from handlers.market_handlers import router as market_router
from handlers.economy_handlers import router as economy_router
from handlers.rating_handlers import router as rating_router
from handlers.casino_handlers import router as casino_router
from handlers.admin_handlers import router as admin_router
from handlers.exchange_handlers import router as exchange_router
from handlers.reputation_handlers import router as reputation_router

__all__ = [
    "user_router",
    "farm_router",
    "battle_router",
    "market_router",
    "economy_router",
    "rating_router",
    "casino_router",
    "admin_router",
    "exchange_router",
    "reputation_router",
]