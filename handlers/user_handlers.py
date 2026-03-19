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
from services.reputation_service import ReputationService
from keyboards.inline_kb import main_menu_kb, admin_menu_kb
from keyboards.callbacks import MainMenuCallback
from config.texts import *
from config.settings import settings
from config.features import FEATURES
from utils.ai_helper import get_mood_message, get_spirit_message

router = Router()


@router.message(Command("start"))
async def start_command(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    char_repo = CharacterRepository(session)

    user = await user_repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    user.last_visit = datetime.now(timezone.utc).replace(tzinfo=None)
    await user_repo.update(user)

    farm_result = await session.execute(select(FarmSlot).where(FarmSlot.owner_id == user.id))
    farm_slots = farm_result.scalars().all()
    if len(farm_slots) == 0:
        farm_service = FarmService(session)
        await farm_service.initialize_farm(user.id)

    char_result = await session.execute(select(Character).where(Character.owner_id == user.id))
    characters = char_result.scalars().all()

    if len(characters) == 0:
        await char_repo.create_character(user.id, "layla", level=1)
        msg = START_MESSAGE + "\n\n✅ Ты получил первого персонажа: Лейла!"
        await message.answer(msg, reply_markup=main_menu_kb())
    else:
        await message.answer(START_MESSAGE, reply_markup=main_menu_kb())


@router.callback_query(MainMenuCallback.filter(F.action == "profile"))
async def show_profile(query: CallbackQuery, callback_data: MainMenuCallback, session: AsyncSession):
    user_repo = UserRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    if not user:
        await query.answer("❌ Ошибка", show_alert=True)
        return

    user.last_visit = datetime.now(timezone.utc).replace(tzinfo=None)
    await user_repo.update(user)

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

    await query.message.edit_text(msg, reply_markup=main_menu_kb())
    await query.answer()


@router.callback_query(MainMenuCallback.filter(F.action == "help"))
async def show_help(query: CallbackQuery):
    msg = HELP_TEXT
    await query.message.edit_text(msg, reply_markup=main_menu_kb())
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