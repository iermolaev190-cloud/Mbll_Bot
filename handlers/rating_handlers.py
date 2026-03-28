import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from database.models import User, Character, BattleLog
from database.repository.user_repo import UserRepository
from database.repository.character_repo import CharacterRepository
from keyboards.callbacks import MainMenuCallback
from config.texts import BUTTON_BACK
from config.features import FEATURES
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)
router = Router()

def format_number(num: int) -> str:
    if num >= 1_000_000:
        return f"{num // 1_000_000}M"
    elif num >= 1_000:
        return f"{num // 1_000}K"
    return str(num)

def get_medal(place: int) -> str:
    if place == 1:
        return "🥇"
    elif place == 2:
        return "🥈"
    elif place == 3:
        return "🥉"
    return f"{place}."

async def get_user_place(session: AsyncSession, user_id: int, order_by_field, field_name: str) -> int:
    result = await session.execute(
        select(User).order_by(order_by_field.desc())
    )
    users = result.scalars().all()
    for i, user in enumerate(users, 1):
        if user.id == user_id:
            return i
    return 0

@router.message(Command("rating"))
@router.message(Command("top"))
async def rating_menu(message: Message):
    buttons = [
        [InlineKeyboardButton(text="💰 По монетам", callback_data="rating_coins")],
        [InlineKeyboardButton(text="🏆 По победам", callback_data="rating_wins")],
        [InlineKeyboardButton(text="⚔️ По боям", callback_data="rating_battles")],
        [InlineKeyboardButton(text="👥 По персонажам", callback_data="rating_characters")],
        [InlineKeyboardButton(text="✨ По репутации", callback_data="rating_reputation")],
        [InlineKeyboardButton(text="📈 За неделю", callback_data="rating_weekly")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data=MainMenuCallback(action="profile").pack())],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        "🏆 *ЗАЛ СЛАВЫ* 🏆\n\n"
        "Выбери категорию рейтинга:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "rating_coins")
async def rating_coins(query: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    
    result = await session.execute(
        select(User).order_by(desc(User.coins)).limit(10)
    )
    top_users = result.scalars().all()
    
    current_user = await user_repo.get_by_telegram_id(query.from_user.id)
    if not current_user:
        await query.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return
    
    current_place = await get_user_place(session, current_user.id, User.coins, "coins")
    
    text = "💰 *ТОП ПО БОГАТСТВУ*\n\n"
    
    for i, user in enumerate(top_users, 1):
        medal = get_medal(i)
        name = user.first_name or f"Игрок {user.telegram_id}"
        text += f"{medal} {name} — {format_number(user.coins)}💰\n"
    
    text += f"\n📍 *Твоё место:* #{current_place}\n"
    text
