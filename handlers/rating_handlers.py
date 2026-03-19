from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database.models import User, BattleLog
from database.repository.user_repo import UserRepository
from database.repository.character_repo import CharacterRepository
from keyboards.callbacks import RatingCallback, MainMenuCallback
from config.texts import BUTTON_BACK
from datetime import datetime, timedelta, timezone

router = Router()


@router.callback_query(RatingCallback.filter(F.action == "show"))
@router.message(Command("rating"))
@router.message(Command("top"))
async def show_rating_menu(query_or_message, session: AsyncSession):
    """Показать меню выбора категории рейтинга"""

    buttons = [
        [InlineKeyboardButton(text="🏆 По победам", callback_data=RatingCallback(action="wins").pack())],
        [InlineKeyboardButton(text="💰 По богатству", callback_data=RatingCallback(action="wealth").pack())],
        [InlineKeyboardButton(text="👥 По персонажам", callback_data=RatingCallback(action="characters").pack())],
        [InlineKeyboardButton(text="⚔️ По боям", callback_data=RatingCallback(action="battles").pack())],
        [InlineKeyboardButton(text="📈 За неделю", callback_data=RatingCallback(action="weekly").pack())],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data=MainMenuCallback(action="profile").pack())],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = """🏆 *ЗАЛ СЛАВЫ*

Выбери категорию рейтинга:

• 🏆 Победы в боях
• 💰 Богатство (монеты)
• 👥 Коллекция персонажей
• ⚔️ Общее количество боёв
• 📈 Топ недели

Топ-3 получает алмазы! 💠"""

    if isinstance(query_or_message, CallbackQuery):
        await query_or_message.message.edit_text(msg, reply_markup=keyboard)
        await query_or_message.answer()
    else:
        await query_or_message.answer(msg, reply_markup=keyboard)


@router.callback_query(RatingCallback.filter(F.action == "wins"))
async def rating_wins(query: CallbackQuery, session: AsyncSession):
    """Рейтинг по победам"""
    user_repo = UserRepository(session)

    result = await session.execute(
        select(User).order_by(desc(User.battle_wins)).limit(10)
    )
    top_users = result.scalars().all()

    current_user = await user_repo.get_by_telegram_id(query.from_user.id)

    rating_text = "🏆 *ТОП ПОБЕДИТЕЛЕЙ*\n\n"

    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(top_users, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = user.first_name or f"Игрок {user.telegram_id}"
        rating_text += f"{medal} {name} — {user.battle_wins} ⚔️\n"

    all_users = await session.execute(
        select(User).order_by(desc(User.battle_wins))
    )
    all_users_list = all_users.scalars().all()

    current_rank = 1
    for i, user in enumerate(all_users_list, 1):
        if user.id == current_user.id:
            current_rank = i
            break

    rating_text += f"\n📍 Твоё место: #{current_rank}"
    rating_text += f"\n📊 Твои победы: {current_user.battle_wins}"

    buttons = [[InlineKeyboardButton(text="⬅️ К категориям", callback_data=RatingCallback(action="show").pack())]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await query.message.edit_text(rating_text, reply_markup=keyboard)
    await query.answer()


@router.callback_query(RatingCallback.filter(F.action == "wealth"))
async def rating_wealth(query: CallbackQuery, session: AsyncSession):
    """Рейтинг по богатству (монеты)"""
    user_repo = UserRepository(session)

    result = await session.execute(
        select(User).order_by(desc(User.coins)).limit(10)
    )
    top_users = result.scalars().all()

    current_user = await user_repo.get_by_telegram_id(query.from_user.id)

    rating_text = "💰 *ТОП БОГАЧЕЙ*\n\n"

    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(top_users, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = user.first_name or f"Игрок {user.telegram_id}"
        rating_text += f"{medal} {name} — {user.coins:,} 💰\n"

    all_users = await session.execute(
        select(User).order_by(desc(User.coins))
    )
    all_users_list = all_users.scalars().all()

    current_rank = 1
    for i, user in enumerate(all_users_list, 1):
        if user.id == current_user.id:
            current_rank = i
            break

    rating_text += f"\n📍 Твоё место: #{current_rank}"
    rating_text += f"\n💵 Твои монеты: {current_user.coins:,}"

    buttons = [[InlineKeyboardButton(text="⬅️ К категориям", callback_data=RatingCallback(action="show").pack())]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await query.message.edit_text(rating_text, reply_markup=keyboard)
    await query.answer()


@router.callback_query(RatingCallback.filter(F.action == "characters"))
async def rating_characters(query: CallbackQuery, session: AsyncSession):
    """Рейтинг по количеству персонажей"""
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
    current_chars = len(await char_repo.get_by_owner(current_user.id))

    rating_text = "👥 *ТОП КОЛЛЕКЦИОНЕРОВ*\n\n"

    medals = ["🥇", "🥈", "🥉"]
    for i, (user, count) in enumerate(top_users, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = user.first_name or f"Игрок {user.telegram_id}"
        rating_text += f"{medal} {name} — {count} 👤\n"

    current_rank = 1
    for i, (user, _) in enumerate(user_char_counts, 1):
        if user.id == current_user.id:
            current_rank = i
            break

    rating_text += f"\n📍 Твоё место: #{current_rank}"
    rating_text += f"\n👥 Твои персонажи: {current_chars}"

    buttons = [[InlineKeyboardButton(text="⬅️ К категориям", callback_data=RatingCallback(action="show").pack())]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await query.message.edit_text(rating_text, reply_markup=keyboard)
    await query.answer()


@router.callback_query(RatingCallback.filter(F.action == "battles"))
async def rating_battles(query: CallbackQuery, session: AsyncSession):
    """Рейтинг по общему количеству боёв"""
    user_repo = UserRepository(session)

    result = await session.execute(
        select(User).order_by(desc(User.battle_wins + User.battle_losses)).limit(10)
    )
    top_users = result.scalars().all()

    current_user = await user_repo.get_by_telegram_id(query.from_user.id)
    current_battles = current_user.battle_wins + current_user.battle_losses

    rating_text = "⚔️ *ТОП ВОИНОВ*\n\n"

    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(top_users, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = user.first_name or f"Игрок {user.telegram_id}"
        total_battles = user.battle_wins + user.battle_losses
        rating_text += f"{medal} {name} — {total_battles} ⚔️\n"

    all_users = await session.execute(
        select(User).order_by(desc(User.battle_wins + User.battle_losses))
    )
    all_users_list = all_users.scalars().all()

    current_rank = 1
    for i, user in enumerate(all_users_list, 1):
        if user.id == current_user.id:
            current_rank = i
            break

    rating_text += f"\n📍 Твоё место: #{current_rank}"
    rating_text += f"\n⚔️ Твои бои: {current_battles}"

    buttons = [[InlineKeyboardButton(text="⬅️ К категориям", callback_data=RatingCallback(action="show").pack())]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await query.message.edit_text(rating_text, reply_markup=keyboard)
    await query.answer()


@router.callback_query(RatingCallback.filter(F.action == "weekly"))
async def rating_weekly(query: CallbackQuery, session: AsyncSession):
    """Рейтинг за неделю"""
    user_repo = UserRepository(session)

    week_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)

    all_users = await user_repo.get_all()

    weekly_stats = []
    for user in all_users:
        # Победы за неделю
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
    current_weekly = next((w for u, w in weekly_stats if u.id == current_user.id), 0)

    rating_text = "📈 *ТОП НЕДЕЛИ*\n\n"
    rating_text += "Игроки с наибольшим количеством побед за последние 7 дней:\n\n"

    medals = ["🥇", "🥈", "🥉"]
    for i, (user, wins) in enumerate(top_weekly, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = user.first_name or f"Игрок {user.telegram_id}"
        rating_text += f"{medal} {name} — {wins} ⚔️\n"

    rating_text += f"""

🎁 *НАГРАДЫ ТОП-3 НЕДЕЛИ:*
🥇 1 место: 5 💠
🥈 2 место: 3 💠
🥉 3 место: 1 💠

📍 Твоё место: #{next((i for i, (u, _) in enumerate(weekly_stats, 1) if u.id == current_user.id), 0)}
📊 Твои победы за неделю: {current_weekly}"""

    buttons = [[InlineKeyboardButton(text="⬅️ К категориям", callback_data=RatingCallback(action="show").pack())]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await query.message.edit_text(rating_text, reply_markup=keyboard)
    await query.answer()