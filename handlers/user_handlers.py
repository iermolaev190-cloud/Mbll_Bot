from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import FarmSlot, Character
from database.repository.user_repo import UserRepository
from database.repository.battle_repo import BattleRepository
from database.repository.character_repo import CharacterRepository
from services.farm_service import FarmService
from services.passive_income_service import PassiveIncomeService
from keyboards.inline_kb import main_menu_kb, admin_menu_kb
from keyboards.callbacks import MainMenuCallback
from config.texts import *
from config.settings import settings
from config.features import FEATURES
from utils.ai_helper import get_mood_message

router = Router()

def is_private(message: Message) -> bool:
    return message.chat.type == "private"

async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str = None, first_name: str = None):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        user = await user_repo.get_or_create(telegram_id, username, first_name)
        farm_service = FarmService(session)
        await farm_service.initialize_farm(user.id)
        char_repo = CharacterRepository(session)
        await char_repo.create_character(user.id, "layla", level=1)
    return user

async def format_user_profile(user, session: AsyncSession):
    user_repo = UserRepository(session)
    top_players = await user_repo.get_top_players(100)
    ranking = next((i + 1 for i, p in enumerate(top_players) if p.id == user.id), 0)
    
    farm_result = await session.execute(select(FarmSlot).where(FarmSlot.owner_id == user.id))
    farm_slots = farm_result.scalars().all()
    occupied_slots = sum(1 for s in farm_slots if s.character_id)
    
    char_result = await session.execute(select(Character).where(Character.owner_id == user.id))
    characters = char_result.scalars().all()
    
    last_visit_str = user.last_visit.strftime("%d.%m.%Y %H:%M") if user.last_visit else "никогда"
    
    mood_text = ""
    if FEATURES.get("mood_profile"):
        user_data = {
            "battle_wins": user.battle_wins,
            "battle_losses": user.battle_losses,
            "coins": user.coins
        }
        mood = await get_mood_message(user_data)
        if mood:
            mood_text = f"\n✨ *Настроение:* {mood}\n"
    
    msg = PROFILE_MESSAGE.format(
        level=user.level,
        coins=user.coins,
        crystals=user.crystals,
        diamonds=user.diamonds,
        wins=user.battle_wins,
        losses=user.battle_losses,
        rating=ranking,
        farm_slots=occupied_slots,
        characters_count=len(characters),
        last_visit=last_visit_str,
    )
    
    msg = msg.replace("👤 *ПРОФИЛЬ*", f"👤 *ПРОФИЛЬ*{mood_text}")
    return msg

@router.message(Command("start"))
async def start_command(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username, message.from_user.first_name)
    user.last_visit = datetime.now(timezone.utc).replace(tzinfo=None)
    await UserRepository(session).update(user)
    
    if not is_private(message):
        await message.answer(
            "🤖 *MBLL FARM BOT*\n\n"
            "Бот работает! Используйте команды:\n"
            "• /profile — профиль\n"
            "• /top — топ игроков\n"
            "• /collect — собрать доход\n"
            "• /farm — ферма\n"
            "• /battle — бои\n"
            "• /market — рынок\n"
            "• /casino — казино\n"
            "• /pvp @username — вызвать на дуэль\n"
            "• /help — помощь\n\n"
            "✨ *Полный функционал доступен в личных сообщениях!*"
        )
        return
    
    msg = START_MESSAGE + "\n\n✅ Твой профиль готов!"
    await message.answer(msg, reply_markup=main_menu_kb())

@router.message(Command("profile"))
async def profile_command(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    user.last_visit = datetime.now(timezone.utc).replace(tzinfo=None)
    await user_repo.update(user)
    
    msg = await format_user_profile(user, session)
    
    if is_private(message):
        await message.answer(msg, reply_markup=main_menu_kb())
    else:
        await message.answer(msg)

@router.callback_query(MainMenuCallback.filter(F.action == "profile"))
async def show_profile_callback(query: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)
    if not user:
        user = await get_or_create_user(session, query.from_user.id, query.from_user.username, query.from_user.first_name)
    
    user.last_visit = datetime.now(timezone.utc).replace(tzinfo=None)
    await user_repo.update(user)
    
    msg = await format_user_profile(user, session)
    await query.message.edit_text(msg, reply_markup=main_menu_kb())
    await query.answer()

@router.message(Command("top"))
async def top_command(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    top = await user_repo.get_top_players(10)
    
    text = "🏆 *ТОП ИГРОКОВ*\n\n"
    for i, user in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        name = user.first_name or f"Игрок {user.telegram_id}"
        text += f"{medal} {name} — {user.coins:,}💰\n"
    
    await message.answer(text)

@router.message(Command("collect"))
async def collect_income_command(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    service = PassiveIncomeService(session)
    result = await service.collect_income(user.id)
    
    if "error" in result:
        if result["error"] == "too_soon":
            await message.answer(f"⏳ Подожди {result['seconds_left']} сек до следующего сбора!")
        else:
            await message.answer("❌ Ошибка сбора дохода!")
        return
    
    income_info = await service.calculate_income(user.id)
    
    msg = f"""💰 *ПАССИВНЫЙ ДОХОД СОБРАН!*

💵 +{result['collected']} монет за {result['hours_passed']} ч

📊 *Доход в час:* {income_info['total_per_hour']}💰
👥 *Персонажей:* {income_info['characters_count']}

💎 *Новый баланс:* {result['new_balance']}💰
"""
    
    msg += "\n📈 *По редкостям:*\n"
    for rarity, amount in income_info["by_rarity"].items():
        if amount > 0:
            emoji = "⚪" if rarity == "common" else "🟢" if rarity == "uncommon" else "🔵" if rarity == "rare" else "🟣" if rarity == "epic" else "🟡" if rarity == "legendary" else "🔴"
            msg += f"{emoji} {rarity.title()}: {amount}💰/ч\n"
    
    await message.answer(msg)

@router.message(Command("help"))
async def help_command(message: Message):
    if is_private(message):
        await message.answer(HELP_TEXT)
    else:
        await message.answer(
            "🤖 *MBLL FARM BOT - КОМАНДЫ*\n\n"
            "👤 `/profile` — твой профиль\n"
            "🏆 `/top` — топ игроков\n"
            "💰 `/collect` — собрать пассивный доход\n"
            "🌱 `/farm` — ферма\n"
            "⚔️ `/battle` — бои\n"
            "🏪 `/market` — рынок\n"
            "🎰 `/casino` — казино\n"
            "⚔️ `/pvp @username` — вызвать на дуэль\n\n"
            "✨ *Удачной игры!*"
        )

@router.callback_query(MainMenuCallback.filter(F.action == "help"))
async def show_help(query: CallbackQuery):
    await query.message.edit_text(HELP_TEXT, reply_markup=main_menu_kb())
    await query.answer()

@router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession):
    if message.from_user.id not in settings.admin_ids_list:
        await message.answer(UNAUTHORIZED)
        return
    
    user_repo = UserRepository(session)
    stats = await user_repo.get_total_stats()
    new_today = await user_repo.get_new_today()
    
    char_repo = CharacterRepository(session)
    total_chars = await char_repo.get_total_characters_count()
    
    battle_repo = BattleRepository(session)
    total_battles = await battle_repo.get_total_battles_count()
    
    msg = ADMIN_STATS.format(
        total_players=stats["total_players"],
        new_today=new_today,
        total_coins=stats["total_coins"],
        total_crystals=stats["total_crystals"],
        total_diamonds=stats["total_diamonds"],
        total_battles=total_battles,
        total_characters=total_chars,
    )
    
    await message.answer(msg, reply_markup=admin_menu_kb())
