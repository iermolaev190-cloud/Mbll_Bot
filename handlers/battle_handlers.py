import random
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.user_repo import UserRepository
from database.repository.character_repo import CharacterRepository
from services.battle_engine import BattleEngine
from keyboards.inline_kb import battle_menu_kb, character_selection_kb
from keyboards.callbacks import BattleCallback, MainMenuCallback, CharacterSelectCallback
from config.texts import BATTLE_MENU, BUTTON_BACK
from config.character_config import get_character
from config.emoji import RARITY_EMOJI
from config.features import FEATURES
from utils.ai_helper import generate_pve_enemy
from database.utils import get_user_or_create

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("battle"))
async def battle_command(message: Message, session: AsyncSession):
    user = await get_user_or_create(session, message.from_user.id, message.from_user.username, message.from_user.first_name)
    if not user:
        await message.answer("Ошибка: не удалось создать профиль")
        return
    await message.answer(BATTLE_MENU, reply_markup=battle_menu_kb())

@router.callback_query(MainMenuCallback.filter(F.action == "battle"))
async def show_battle_from_main(query: CallbackQuery, session: AsyncSession):
    user = await get_user_or_create(session, query.from_user.id, query.from_user.username, query.from_user.first_name)
    if not user:
        await query.answer("Ошибка: пользователь не найден", show_alert=True)
        return
    await query.message.edit_text(BATTLE_MENU, reply_markup=battle_menu_kb())
    await query.answer()

@router.callback_query(BattleCallback.filter(F.action == "menu"))
async def show_battle_menu(query: CallbackQuery):
    await query.message.edit_text(BATTLE_MENU, reply_markup=battle_menu_kb())
    await query.answer()

@router.callback_query(BattleCallback.filter(F.action == "select_team"))
async def select_team(query: CallbackQuery, session: AsyncSession):
    user = await get_user_or_create(session, query.from_user.id, query.from_user.username, query.from_user.first_name)
    if not user:
        await query.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    character_repo = CharacterRepository(session)
    all_characters = await character_repo.get_by_owner(user.id)

    if not all_characters:
        await query.answer("У тебя нет персонажей!\n\nВырасти их на ферме!", show_alert=True)
        return

    available_chars = [char for char in all_characters if not char.is_on_farm]
    current_team = await character_repo.get_team(user.id)
    current_team_ids = [c.id for c in current_team]

    team_list = ""
    for char in available_chars[:12]:
        char_data = get_character(char.character_type)
        status = "✅" if char.id in current_team_ids else "⭕"
        team_list += f"{status} {RARITY_EMOJI.get(char_data.rarity, '⚪')} {char_data.name} L{char.level}\n"

    msg = f"""👥 *ВЫБОР КОМАНДЫ*

✅ - в команде | ⭕ - доступен
Выбрано: {len(current_team_ids)}/3
Всего персонажей: {len(available_chars)}

{team_list}

Нажимай на персонажей чтобы добавить/убрать их из команды."""

    await query.message.edit_text(msg, reply_markup=character_selection_kb(available_chars, current_team_ids))
    await query.answer()

@router.callback_query(CharacterSelectCallback.filter())
async def toggle_character(query: CallbackQuery, callback_data: CharacterSelectCallback, session: AsyncSession):
    user = await get_user_or_create(session, query.from_user.id, query.from_user.username, query.from_user.first_name)
    if not user:
        await query.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    character_repo = CharacterRepository(session)
    character = await character_repo.get_by_id(callback_data.character_id)

    if not character or character.owner_id != user.id:
        await query.answer("Персонаж не найден", show_alert=True)
        return

    current_team = await character_repo.get_team(user.id)
    current_team_ids = [c.id for c in current_team]

    if callback_data.action == "add":
        if len(current_team_ids) >= 3:
            await query.answer("Команда полная (макс 3)", show_alert=True)
            return

        character.is_in_team = True
        await character_repo.update(character)
        current_team_ids.append(callback_data.character_id)
        await query.answer("Добавлен в команду")

    elif callback_data.action == "remove":
        if callback_data.character_id in current_team_ids:
            character.is_in_team = False
            await character_repo.update(character)
            current_team_ids.remove(callback_data.character_id)
            await query.answer("Удален из команды")

    all_characters = await character_repo.get_by_owner(user.id)
    available_chars = [char for char in all_characters if not char.is_on_farm]

    team_list = ""
    for char in available_chars[:12]:
        char_data = get_character(char.character_type)
        status = "✅" if char.id in current_team_ids else "⭕"
        team_list += f"{status} {RARITY_EMOJI.get(char_data.rarity, '⚪')} {char_data.name} L{char.level}\n"

    msg = f"""👥 *ВЫБОР КОМАНДЫ*

✅ - в команде | ⭕ - доступен
Выбрано: {len(current_team_ids)}/3
Всего персонажей: {len(available_chars)}

{team_list}

Нажимай на персонажей чтобы добавить/убрать их из команды."""

    if query.message.text != msg:
        await query.message.edit_text(msg, reply_markup=character_selection_kb(available_chars, current_team_ids))
    else:
        await query.message.edit_reply_markup(reply_markup=character_selection_kb(available_chars, current_team_ids))

@router.callback_query(BattleCallback.filter(F.action == "view_team"))
async def view_team(query: CallbackQuery, session: AsyncSession):
    user = await get_user_or_create(session, query.from_user.id, query.from_user.username, query.from_user.first_name)
    if not user:
        await query.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    character_repo = CharacterRepository(session)
    team = await character_repo.get_team(user.id)

    if not team:
        await query.answer("Команда не выбрана", show_alert=True)
        return

    team_display = ""
    for i, char in enumerate(team, 1):
        char_data = get_character(char.character_type)
        team_display += f"{i}. {RARITY_EMOJI.get(char_data.rarity, '⚪')} *{char_data.name}* L{char.level}\n"
        team_display += f"   ❤️ {char.current_hp}/{char.max_hp} | 🗡️ {char.base_damage} | 🛡️ {char.base_armor}\n"
        team_display += f"   ⚔️ Побед: {char.battle_wins} | 💀 Поражений: {char.battle_losses}\n\n"

    msg = f"""👥 *ТВОЯ БОЕВАЯ КОМАНДА*

{team_display}
Готов к бою! ⚔️"""

    if query.message.text != msg:
        await query.message.edit_text(msg, reply_markup=battle_menu_kb())
    else:
        await query.answer("✅ Команда уже отображается")

@router.callback_query(BattleCallback.filter(F.action == "start_pvp"))
async def start_pvp(query: CallbackQuery, session: AsyncSession):
    user = await get_user_or_create(session, query.from_user.id, query.from_user.username, query.from_user.first_name)
    if not user:
        await query.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    character_repo = CharacterRepository(session)
    battle_engine = BattleEngine(session)

    team = await character_repo.get_team(user.id)
    if len(team) < 3:
        await query.answer(f"В команде {len(team)}/3 персонажей. Нужно 3!", show_alert=True)
        return

    all_users = await UserRepository(session).get_all()
    opponents = [u for u in all_users if u.id != user.id and u.id != 0]

    if not opponents:
        result = await battle_engine.start_pve_battle(user.id, "medium")
    else:
        opponent = random.choice(opponents)

        opponent_team = await character_repo.get_team(opponent.id)
        if len(opponent_team) < 3:
            await query.answer("У противника нет полной команды!", show_alert=True)
            return

        result = await battle_engine.start_pvp_battle(user.id, opponent.id)

    if "error" in result:
        await query.answer(result.get("message", "Ошибка боя"), show_alert=True)
        return

    if result["player_won"]:
        msg = "🏆 *ПОБЕДА!*\n\n"
        msg += f"💰 +{result['coins']} монет\n"
        msg += f"💎 +{result['crystals']} кристаллов\n\n"
    else:
        msg = "💀 *ПОРАЖЕНИЕ*\n\n"
        msg += f"💰 +{result['coins']} монет (утешение)\n\n"

    if result.get("level_ups"):
        msg += "\n📈 *Повышение уровня:*\n" + "\n".join(result["level_ups"])

    await query.message.edit_text(msg, reply_markup=battle_menu_kb())
    await query.answer("⚔️ Бой завершен!")

@router.callback_query(BattleCallback.filter(F.action == "start_pve"))
async def start_pve(query: CallbackQuery, session: AsyncSession):
    user = await get_user_or_create(session, query.from_user.id, query.from_user.username, query.from_user.first_name)
    if not user:
        await query.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    character_repo = CharacterRepository(session)

    team = await character_repo.get_team(user.id)
    avg_level = sum(char.level for char in team) // 3 if team else 1

    if len(team) < 3:
        await query.answer(f"В команде {len(team)}/3 персонажей. Нужно 3!", show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton(text="👹 ЛЕГКО", callback_data="pve_easy")],
        [InlineKeyboardButton(text="👺 СРЕДНЕ", callback_data="pve_medium")],
        [InlineKeyboardButton(text="👿 СЛОЖНО", callback_data="pve_hard")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="battle_menu")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    intro_text = "⚔️ *ВЫБЕРИ СЛОЖНОСТЬ PvE*"
    if FEATURES.get("smart_pve"):
        enemy = await generate_pve_enemy("medium", avg_level)
        intro_text = f"⚔️ *ВСТРЕЧАЙ ПРОТИВНИКА!*\n\n"
        intro_text += f"👤 *{enemy['name']}*\n"
        intro_text += f"🗣️ \"{enemy['talk']}\"\n"
        intro_text += f"⚠️ *Особенность:* {enemy['mechanic']}\n\n"
        intro_text += "Выбери сложность:"

    await query.message.edit_text(intro_text, reply_markup=keyboard)
    await query.answer()

@router.callback_query(F.data.startswith("pve_"))
async def start_pve_with_difficulty(query: CallbackQuery, session: AsyncSession):
    user = await get_user_or_create(session, query.from_user.id, query.from_user.username, query.from_user.first_name)
    if not user:
        await query.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    difficulty = query.data.split("_")[1]

    battle_engine = BattleEngine(session)
    character_repo = CharacterRepository(session)

    team = await character_repo.get_team(user.id)
    avg_level = sum(char.level for char in team) // 3 if team else 1

    enemy_info = ""
    if FEATURES.get("smart_pve") or FEATURES.get("battle_trash_talk"):
        enemy = await generate_pve_enemy(difficulty, avg_level)
        enemy_info = f"\n👤 *Противник:* {enemy['name']}\n🗣️ \"{enemy['talk']}\"\n"

    result = await battle_engine.start_pve_battle(user.id, difficulty)

    if "error" in result:
        await query.answer(result.get("message", "Ошибка боя"), show_alert=True)
        return

    if result["player_won"]:
        msg = f"🏆 *ПОБЕДА!* ({difficulty.upper()})\n"
        msg += enemy_info
        msg += f"\n💰 +{result['coins']} монет\n"
        msg += f"💎 +{result['crystals']} кристаллов\n\n"
    else:
        msg = f"💀 *ПОРАЖЕНИЕ* ({difficulty.upper()})\n"
        msg += enemy_info
        msg += f"\n💰 +{result['coins']} монет (утешение)\n\n"

    if result.get("level_ups"):
        msg += "\n📈 *Повышение уровня:*\n" + "\n".join(result["level_ups"])

    await query.message.edit_text(msg, reply_markup=battle_menu_kb())
    await query.answer("⚔️ Бой завершен!")
