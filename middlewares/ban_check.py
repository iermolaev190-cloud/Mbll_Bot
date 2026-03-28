from typing import Callable, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from aiogram.exceptions import TelegramForbiddenError
from database.repository.user_repo import UserRepository
from config.settings import settings

class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ) -> Any:
        user_id = None
        message_obj = None
        is_callback = False
        
        if event.message:
            user_id = event.message.from_user.id
            message_obj = event.message
            is_callback = False
            if event.message.from_user.is_bot:
                return await handler(event, data)
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
            message_obj = event.callback_query.message
            is_callback = True
        
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
                        await event.callback_query.answer("⛔ Вы забанены!", show_alert=True)
                except TelegramForbiddenError:
                    pass
                
                return
        
        return await handler(event, data)
