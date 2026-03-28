import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
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
    text += f"💵 *Твои монеты:* {format_number(current_user.coins)}💰"
    
    buttons = [[InlineKeyboardButton(text="⬅️ К списку", callback_data="rating_back")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()

@router.callback_query(F.data == "rating_wins")
async def rating_wins(query: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    
    result = await session.execute(
        select(User).order_by(desc(User.battle_wins)).limit(10)
    )
    top_users = result.scalars().all()
    
    current_user = await user_repo.get_by_telegram_id(query.from_user.id)
    if not current_user:
        await query.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return
    
    current_place = await get_user_place(session, current_user.id, User.battle_wins, "battle_wins")
    
    text = "🏆 *ТОП ПО ПОБЕДАМ*\n\n"
    
    for i, user in enumerate(top_users, 1):
        medal = get_medal(i)
        name = user.first_name or f"Игрок {user.telegram_id}"
        text += f"{medal} {name} — {user.battle_wins} ⚔️\n"
    
    text += f"\n📍 *Твоё место:* #{current_place}\n"
    text += f"🏆 *Твои победы:* {current_user.battle_wins}"
    
    buttons = [[InlineKeyboardButton(text="⬅️ К списку", callback_data="rating_back")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()

@router.callback_query(F.data == "rating_battles")
async def rating_battles(query: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    
    result = await session.execute(
        select(User).order_by(desc(User.battle_wins + User.battle_losses)).limit(10)
    )
    top_users = result.scalars().all()
    
    current_user = await user_repo.get_by_telegram_id(query.from_user.id)
    if not current_user:
        await query.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return
    
    current_battles = current_user.battle_wins + current_user.battle_losses
    
    all_users = await session.execute(
        select(User).order_by(desc(User.battle_wins + User.battle_losses))
    )
    all_list = all_users.scalars().all()
    current_place = next((i for i, u in enumerate(all_list, 1) if u.id == current_user.id), 0)
    
    text = "⚔️ *ТОП ПО БОЯМ*\n\n"
    
    for i, user in enumerate(top_users, 1):
        medal = get_medal(i)
        name = user.first_name or f"Игрок {user.telegram_id}"
        total_battles = user.battle_wins + user.battle_losses
        text += f"{medal} {name} — {total_battles} ⚔️\n"
    
    text += f"\n📍 *Твоё место:* #{current_place}\n"
    text += f"⚔️ *Твои бои:* {current_battles}"
    
    buttons = [[InlineKeyboardButton(text="⬅️ К списку", callback_data="rating_back")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()

@router.callback_query(F.data == "rating_characters")
async def rating_characters(query: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    char_repo = CharacterRepository(session)
    
    all_users = await user_repo.get_all()
    user_char_counts = []
    
    for user in all_users:
        chars = await char_repo.get_by_owner(user.id)
        user_char_counts.append((user, len(chars)))
    
    user_char_counts.sort(key=lambda x: x[1], reverse=True)
    top_users = user_char_counts[:10]
    
    current_user = await user_repo.get_by_telegram_id(query.from_user.id)
    if not current_user:
        await query.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return
    
    current_count = len(await char_repo.get_by_owner(current_user.id))
    current_place = next((i for i, (u, _) in enumerate(user_char_counts, 1) if u.id == current_user.id), 0)
    
    text = "👥 *ТОП КОЛЛЕКЦИОНЕРОВ*\n\n"
    
    for i, (user, count) in enumerate(top_users, 1):
        medal = get_medal(i)
        name = user.first_name or f"Игрок {user.telegram_id}"
        text += f"{medal} {name} — {count} 👤\n"
    
    text += f"\n📍 *Твоё место:* #{current_place}\n"
    text += f"👥 *Твои персонажи:* {current_count}"
    
    buttons = [[InlineKeyboardButton(text="⬅️ К списку", callback_data="rating_back")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()

@router.callback_query(F.data == "rating_reputation")
async def rating_reputation(query: CallbackQuery, session: AsyncSession):
    if not FEATURES.get("reputation"):
        await query.answer("❌ Система репутации временно отключена", show_alert=True)
        return
    
    user_repo = UserRepository(session)
    
    result = await session.execute(
        select(User).order_by(desc(User.reputation)).limit(10)
    )
    top_users = result.scalars().all()
    
    current_user = await user_repo.get_by_telegram_id(query.from_user.id)
    if not current_user:
        await query.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return
    
    current_place = await get_user_place(session, current_user.id, User.reputation, "reputation")
    
    text = "✨ *ТОП ПО РЕПУТАЦИИ*\n\n"
    
    for i, user in enumerate(top_users, 1):
        medal = get_medal(i)
        name = user.first_name or f"Игрок {user.telegram_id}"
        text += f"{medal} {name} — {user.reputation} ✨\n"
    
    text += f"\n📍 *Твоё место:* #{current_place}\n"
    text += f"✨ *Твоя репутация:* {current_user.reputation}"
    
    buttons = [[InlineKeyboardButton(text="⬅️ К списку", callback_data="rating_back")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()

@router.callback_query(F.data == "rating_weekly")
async def rating_weekly(query: CallbackQuery, session: AsyncSession):
    week_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
    
    user_repo = UserRepository(session)
    all_users = await user_repo.get_all()
    
    weekly_stats = []
    for user in all_users:
        result = await session.execute(
            select(BattleLog).where(
                BattleLog.player_id == user.id,
                BattleLog.player_won == True,
                BattleLog.battle_date >= week_ago
            )
        )
        weekly_wins = len(result.scalars().all())
        weekly_stats.append((user, weekly_wins))
    
    weekly_stats.sort(key=lambda x: x[1], reverse=True)
    top_weekly = weekly_stats[:10]
    
    current_user = await user_repo.get_by_telegram_id(query.from_user.id)
    if not current_user:
        await query.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return
    
    current_wins = next((w for u, w in weekly_stats if u.id == current_user.id), 0)
    current_place = next((i for i, (u, _) in enumerate(weekly_stats, 1) if u.id == current_user.id), 0)
    
    text = "📈 *ТОП НЕДЕЛИ*\n\n"
    text += "Игроки с наибольшим количеством побед за последние 7 дней:\n\n"
    
    for i, (user, wins) in enumerate(top_weekly, 1):
        medal = get_medal(i)
        name = user.first_name or f"Игрок {user.telegram_id}"
        text += f"{medal} {name} — {wins} ⚔️\n"
    
    text += f"\n🎁 *НАГРАДЫ ТОП-3 НЕДЕЛИ:*\n"
    text += f"🥇 1 место: 5 💠\n"
    text += f"🥈 2 место: 3 💠\n"
    text += f"🥉 3 место: 1 💠\n\n"
    
    text += f"📍 *Твоё место:* #{current_place}\n"
    text += f"📊 *Твои победы за неделю:* {current_wins}"
    
    buttons = [[InlineKeyboardButton(text="⬅️ К списку", callback_data="rating_back")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()

@router.callback_query(F.data == "rating_back")
async def rating_back(query: CallbackQuery):
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
    
    await query.message.edit_text(
        "🏆 *ЗАЛ СЛАВЫ* 🏆\n\n"
        "Выбери категорию рейтинга:",
        reply_markup=keyboard
    )
    await query.answer()
