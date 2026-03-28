from typing import Callable, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from aiogram.exceptions import TelegramForbiddenError
from database.repository.user_repo import UserRepository
from config.settings import settings

class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        user_id = None
        message_obj = None
        is_callback = False
        
        if isinstance(event, Message):
            user_id = event.from_user.id
            message_obj = event
            is_callback = False
            if event.from_user.is_bot:
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            message_obj = event.message
            is_callback = True
        else:
            return await handler(event, data)
        
        if not user_id:
            return await handler(event, data)
        
        if user_id in settings.admin_ids_list:
            return await handler(event, data)
        
        if 'session' in data:
            user_repo = UserRepository(data['session'])
            user = await user_repo.get_by_telegram_id(user_id)
            
            if user and getattr(user, 'is_banned', False):
                ban_message = (
                    "⛔ *ВЫ ЗАБАНЕНЫ!*\n\n"
                    f"📝 *Причина:* {getattr(user, 'ban_reason', 'Не указана') or 'Не указана'}\n"
                    "👮 *Обратитесь к администратору.*"
                )
                
                try:
                    await message_obj.answer(ban_message)
                    if is_callback:
                        await event.answer("⛔ Вы забанены!", show_alert=True)
                except TelegramForbiddenError:
                    pass
                
                return
        
        return await handler(event, data)
