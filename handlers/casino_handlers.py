import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sql_text
from database.repository.user_repo import UserRepository
from keyboards.callbacks import MainMenuCallback
from config.texts import BUTTON_BACK
from config.features import FEATURES
from utils.ai_helper import get_casino_message

router = Router()

@router.callback_query(MainMenuCallback.filter(F.action == "casino"))
async def casino_from_main(query: CallbackQuery, session: AsyncSession):
    await casino_main_menu(query.message, session, is_edit=True, user_id=query.from_user.id)
    await query.answer()

@router.message(Command("casino"))
@router.message(Command("game"))
async def casino_command(message: Message, session: AsyncSession):
    await casino_main_menu(message, session, is_edit=False, user_id=message.from_user.id)

@router.callback_query(F.data == "casino_main")
async def casino_back(query: CallbackQuery, session: AsyncSession):
    await casino_main_menu(query.message, session, is_edit=True, user_id=query.from_user.id)
    await query.answer()

async def casino_main_menu(message: Message, session: AsyncSession, is_edit: bool = False, user_id: int = None):
    target_id = user_id or message.chat.id
    result = await session.execute(
        sql_text("SELECT coins FROM users WHERE telegram_id = :tid"),
        {"tid": target_id}
    )
    coins = result.scalar() or 0
    welcome_text = ""
    if FEATURES.get("casino_talk"):
        welcome = await get_casino_message("welcome")
        if welcome:
            welcome_text = f"\n{welcome}\n"
    buttons = [
        [InlineKeyboardButton(text="🎳 БОУЛИНГ — x2", callback_data="casino_bowling")],
        [InlineKeyboardButton(text="🏀 БАСКЕТБОЛ — x3", callback_data="casino_basketball")],
        [InlineKeyboardButton(text="🎯 ДАРТС — x5", callback_data="casino_darts")],
        [InlineKeyboardButton(text="🎰 СЛОТЫ — x10", callback_data="casino_slots")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data=MainMenuCallback(action="profile").pack())],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    msg_text = f"""🎰 *LAS VEGAS CASINO* 🎰
{welcome_text}
💰 *Твой баланс:* {coins:,} монет

🎳 *БОУЛИНГ* — угадай Страйк (x2)
🏀 *БАСКЕТБОЛ* — угадай попадание (x3)
🎯 *ДАРТС* — угадай яблочко (x5)
🎰 *СЛОТЫ* — Джекпот (x10)

Выбери игру:"""
    if is_edit:
        await message.edit_text(msg_text, reply_markup=keyboard)
    else:
        await message.answer(msg_text, reply_markup=keyboard)

@router.callback_query(F.data == "casino_bowling")
async def bowling_bet(query: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)
    buttons = [
        [InlineKeyboardButton(text="500💰", callback_data="bowling_500"),
         InlineKeyboardButton(text="1,000💰", callback_data="bowling_1000")],
        [InlineKeyboardButton(text="5,000💰", callback_data="bowling_5000"),
         InlineKeyboardButton(text="10,000💰", callback_data="bowling_10000")],
        [InlineKeyboardButton(text="50,000💰", callback_data="bowling_50000"),
         InlineKeyboardButton(text="100,000💰", callback_data="bowling_100000")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="casino_main")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await query.message.edit_text(
        f"""🎳 *БОУЛИНГ*

💰 *Твой баланс:* {user.coins:,} монет
🎯 *Шанс страйка:* 35%
💵 *Выигрыш:* x2

Выбери ставку:""",
        reply_markup=keyboard
    )
    await query.answer()

@router.callback_query(F.data.startswith("bowling_"))
async def bowling_play(query: CallbackQuery, session: AsyncSession):
    bet = int(query.data.split("_")[1])
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)
    if user.coins < bet:
        await query.answer(f"❌ Недостаточно монет! Нужно: {bet}", show_alert=True)
        return
    await session.execute(
        sql_text("UPDATE users SET coins = coins - :bet WHERE telegram_id = :tg_id"),
        {"bet": bet, "tg_id": query.from_user.id}
    )
    is_strike = random.random() < 0.35
    if is_strike:
        prize = bet * 2
        await session.execute(
            sql_text("UPDATE users SET coins = coins + :prize WHERE telegram_id = :tg_id"),
            {"prize": prize, "tg_id": query.from_user.id}
        )
        win_msg = ""
        if FEATURES.get("casino_talk"):
            win_msg = await get_casino_message("win") + "\n"
        result_text = f"""🎳 *СТРАЙК!*
{win_msg}

💰 *Выигрыш:* +{prize}💰 (x2)"""
    else:
        lose_msg = ""
        if FEATURES.get("casino_talk"):
            lose_msg = await get_casino_message("lose") + "\n"
        result_text = f"""🎳 *ПРОМАХ!*
{lose_msg}

💸 *Проигрыш:* -{bet}💰"""
    await session.commit()
    buttons = [
        [InlineKeyboardButton(text="🎳 ЕЩЕ РАЗ", callback_data="casino_bowling")],
        [InlineKeyboardButton(text="🎰 В КАЗИНО", callback_data="casino_main")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await query.message.edit_text(
        f"{result_text}\n\n💰 *Баланс:* {user.coins - bet + (prize if is_strike else 0)}💰",
        reply_markup=keyboard
    )
    await query.answer()

@router.callback_query(F.data == "casino_basketball")
async def basketball_bet(query: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)
    buttons = [
        [InlineKeyboardButton(text="500💰", callback_data="basketball_500"),
         InlineKeyboardButton(text="1,000💰", callback_data="basketball_1000")],
        [InlineKeyboardButton(text="5,000💰", callback_data="basketball_5000"),
         InlineKeyboardButton(text="10,000💰", callback_data="basketball_10000")],
        [InlineKeyboardButton(text="50,000💰", callback_data="basketball_50000"),
         InlineKeyboardButton(text="100,000💰", callback_data="basketball_100000")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="casino_main")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await query.message.edit_text(
        f"""🏀 *БАСКЕТБОЛ*

💰 *Твой баланс:* {user.coins:,} монет
🎯 *Шанс попадания:* 25%
💵 *Выигрыш:* x3

Выбери ставку:""",
        reply_markup=keyboard
    )
    await query.answer()

@router.callback_query(F.data.startswith("basketball_"))
async def basketball_play(query: CallbackQuery, session: AsyncSession):
    bet = int(query.data.split("_")[1])
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)
    if user.coins < bet:
        await query.answer(f"❌ Недостаточно монет! Нужно: {bet}", show_alert=True)
        return
    await session.execute(
        sql_text("UPDATE users SET coins = coins - :bet WHERE telegram_id = :tg_id"),
        {"bet": bet, "tg_id": query.from_user.id}
    )
    is_score = random.random() < 0.25
    if is_score:
        prize = bet * 3
        await session.execute(
            sql_text("UPDATE users SET coins = coins + :prize WHERE telegram_id = :tg_id"),
            {"prize": prize, "tg_id": query.from_user.id}
        )
        win_msg = await get_casino_message("win") if FEATURES.get("casino_talk") else ""
        result_text = f"""🏀 *ГОЛ!*
{win_msg}

💰 *Выигрыш:* +{prize}💰 (x3)"""
    else:
        lose_msg = await get_casino_message("lose") if FEATURES.get("casino_talk") else ""
        result_text = f"""🏀 *ПРОМАХ!*
{lose_msg}

💸 *Проигрыш:* -{bet}💰"""
    await session.commit()
    buttons = [
        [InlineKeyboardButton(text="🏀 ЕЩЕ РАЗ", callback_data="casino_basketball")],
        [InlineKeyboardButton(text="🎰 В КАЗИНО", callback_data="casino_main")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await query.message.edit_text(
        f"{result_text}\n\n💰 *Баланс:* {user.coins - bet + (prize if is_score else 0)}💰",
        reply_markup=keyboard
    )
    await query.answer()

@router.callback_query(F.data == "casino_darts")
async def darts_bet(query: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)
    buttons = [
        [InlineKeyboardButton(text="500💰", callback_data="darts_500"),
         InlineKeyboardButton(text="1,000💰", callback_data="darts_1000")],
        [InlineKeyboardButton(text="5,000💰", callback_data="darts_5000"),
         InlineKeyboardButton(text="10,000💰", callback_data="darts_10000")],
        [InlineKeyboardButton(text="50,000💰", callback_data="darts_50000"),
         InlineKeyboardButton(text="100,000💰", callback_data="darts_100000")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="casino_main")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await query.message.edit_text(
        f"""🎯 *ДАРТС*

💰 *Твой баланс:* {user.coins:,} монет
🎯 *Шанс яблочка:* 15%
💵 *Выигрыш:* x5

Выбери ставку:""",
        reply_markup=keyboard
    )
    await query.answer()

@router.callback_query(F.data.startswith("darts_"))
async def darts_play(query: CallbackQuery, session: AsyncSession):
    bet = int(query.data.split("_")[1])
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)
    if user.coins < bet:
        await query.answer(f"❌ Недостаточно монет! Нужно: {bet}", show_alert=True)
        return
    await session.execute(
        sql_text("UPDATE users SET coins = coins - :bet WHERE telegram_id = :tg_id"),
        {"bet": bet, "tg_id": query.from_user.id}
    )
    is_bullseye = random.random() < 0.15
    if is_bullseye:
        prize = bet * 5
        await session.execute(
            sql_text("UPDATE users SET coins = coins + :prize WHERE telegram_id = :tg_id"),
            {"prize": prize, "tg_id": query.from_user.id}
        )
        win_msg = await get_casino_message("win") if FEATURES.get("casino_talk") else ""
        result_text = f"""🎯 *ЯБЛОЧКО!*
{win_msg}

💰 *Выигрыш:* +{prize}💰 (x5)"""
    else:
        lose_msg = await get_casino_message("lose") if FEATURES.get("casino_talk") else ""
        result_text = f"""🎯 *ПРОМАХ!*
{lose_msg}

💸 *Проигрыш:* -{bet}💰"""
    await session.commit()
    buttons = [
        [InlineKeyboardButton(text="🎯 ЕЩЕ РАЗ", callback_data="casino_darts")],
        [InlineKeyboardButton(text="🎰 В КАЗИНО", callback_data="casino_main")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await query.message.edit_text(
        f"{result_text}\n\n💰 *Баланс:* {user.coins - bet + (prize if is_bullseye else 0)}💰",
        reply_markup=keyboard
    )
    await query.answer()

@router.callback_query(F.data == "casino_slots")
async def slots_bet(query: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)
    buttons = [
        [InlineKeyboardButton(text="500💰", callback_data="slots_500"),
         InlineKeyboardButton(text="1,000💰", callback_data="slots_1000")],
        [InlineKeyboardButton(text="5,000💰", callback_data="slots_5000"),
         InlineKeyboardButton(text="10,000💰", callback_data="slots_10000")],
        [InlineKeyboardButton(text="50,000💰", callback_data="slots_50000"),
         InlineKeyboardButton(text="100,000💰", callback_data="slots_100000")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="casino_main")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await query.message.edit_text(
        f"""🎰 *СЛОТЫ*

💰 *Твой баланс:* {user.coins:,} монет
🎯 *Шанс джекпота:* 7%
💵 *Выигрыш:* x10

Выбери ставку:""",
        reply_markup=keyboard
    )
    await query.answer()

@router.callback_query(F.data.startswith("slots_"))
async def slots_play(query: CallbackQuery, session: AsyncSession):
    bet = int(query.data.split("_")[1])
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)
    if user.coins < bet:
        await query.answer(f"❌ Недостаточно монет! Нужно: {bet}", show_alert=True)
        return
    await session.execute(
        sql_text("UPDATE users SET coins = coins - :bet WHERE telegram_id = :tg_id"),
        {"bet": bet, "tg_id": query.from_user.id}
    )
    is_jackpot = random.random() < 0.07
    if is_jackpot:
        prize = bet * 10
        await session.execute(
            sql_text("UPDATE users SET coins = coins + :prize WHERE telegram_id = :tg_id"),
            {"prize": prize, "tg_id": query.from_user.id}
        )
        win_msg = await get_casino_message("win") if FEATURES.get("casino_talk") else ""
        result_text = f"""🎰 *ДЖЕКПОТ! 7️⃣7️⃣7️⃣*
{win_msg}

💰 *Выигрыш:* +{prize}💰 (x10)"""
    else:
        symbols = ["🍒", "🍋", "🍊", "🍇", "💎"]
        slot1 = random.choice(symbols)
        slot2 = random.choice(symbols)
        slot3 = random.choice(symbols)
        lose_msg = await get_casino_message("lose") if FEATURES.get("casino_talk") else ""
        result_text = f"""🎰 *ПОВЕЗЁТ В СЛЕДУЮЩИЙ РАЗ*
{lose_msg}
╔═══════╦═══════╦═══════╗
║   {slot1}   ║   {slot2}   ║   {slot3}   ║
╚═══════╩═══════╩═══════╝

💸 *Проигрыш:* -{bet}💰"""
    await session.commit()
    buttons = [
        [InlineKeyboardButton(text="🎰 ЕЩЕ РАЗ", callback_data="casino_slots")],
        [InlineKeyboardButton(text="🎰 В КАЗИНО", callback_data="casino_main")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await query.message.edit_text(
        f"{result_text}\n\n💰 *Баланс:* {user.coins - bet + (prize if is_jackpot else 0)}💰",
        reply_markup=keyboard
    )
    await query.answer()
