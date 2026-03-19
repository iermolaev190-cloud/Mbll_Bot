from typing import Callable, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database.repository.user_repo import UserRepository


class ActivityMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
            event: Any,
            data: dict[str, Any]
    ) -> Any:
        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id and 'session' in data:
            user_repo = UserRepository(data['session'])
            await user_repo.update_last_visit(user_id)

        return await handler(event, data)