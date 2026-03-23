from typing import Callable, Any, Awaitable
from aiogram import BaseMiddleware
from database.core import AsyncSessionLocal

class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionLocal() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()  
                return result
            except Exception as e:
                await session.rollback()  
                raise e
