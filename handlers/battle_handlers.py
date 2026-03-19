import random
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
from services.reputation_service import ReputationService
from config.features import FEATURES

router = Router()


@router.message(Command("battle"))
async def battle_command(message: Message):
    """Прямая команда для боевой"""
    await message.answer(BATTLE_MENU, reply_markup=battle_menu_kb())


@router.callback_query(MainMenuCallback.filter(F.action == "battle"))
async def show_battle_from_main(query: CallbackQuery):
    """Из главного меню"""
    await query.message.edit_text(BATTLE_MENU, reply_markup=battle_menu_kb())
    await query.answer()


@router.callback_query(BattleCallback.filter(F.action == "menu"))
async def show_battle_menu(query: CallbackQuery):
    """Меню боевой"""
    await query.message.edit_text(BATTLE_MENU, reply_markup=battle_menu_kb())
    await query.answer()


@router.callback_query(BattleCallback.filter(F.action == "select_team"))
async def select_team(query: CallbackQuery, session: AsyncSession):
    """Выбор команды"""
    print(f"⚔️ Вход в выбор команды для пользователя {query.from_user.id}")

    character_repo = CharacterRepository(session)
    user_repo = UserRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)

    all_characters = await character_repo.get_by_owner(user.id)
    print(f"📊 Всего персонажей в БД: {len(all_characters)}")

    if not all_characters:
        await query.answer(
            "❌ У тебя нет персонажей!\n\n"
            "🌱 Вырасти их на ферме!",
            show_alert=True
        )
        return

    available_chars = []
    for char in all_characters:
        if not char.is_on_farm:
            available_chars.append(char)

    print(f"✅ Доступно для команды (не на ферме): {len(available_chars)}")

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

    await query.message.edit_text(
        msg,
        reply_markup=character_selection_kb(available_chars, current_team_ids)
    )
    await query.answer()


@router.callback_query(CharacterSelectCallback.filter())
async def toggle_character(query: CallbackQuery, callback_data: CharacterSelectCallback, session: AsyncSession):
    """Добавление/удаление персонажа из команды"""
    print(f"🔄 Переключение персонажа {callback_data.character_id}")

    character_repo = CharacterRepository(session)
    user_repo = UserRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    character = await character_repo.get_by_id(callback_data.character_id)

    if not character or character.owner_id != user.id:
        await query.answer("❌ Персонаж не найден", show_alert=True)
        return

    current_team = await character_repo.get_team(user.id)
    current_team_ids = [c.id for c in current_team]

    if callback_data.action == "add":
        if len(current_team_ids) >= 3:
            await query.answer("❌ Команда полная (макс 3)", show_alert=True)
            return

        character.is_in_team = True
        await character_repo.update(character)
        current_team_ids.append(callback_data.character_id)
        await query.answer("✅ Добавлен в команду")

    elif callback_data.action == "remove":
        if callback_data.character_id in current_team_ids:
            character.is_in_team = False
            await character_repo.update(character)
            current_team_ids.remove(callback_data.character_id)
            await query.answer("❌ Удален из команды")

    all_characters = await character_repo.get_by_owner(user.id)
    available_chars = []
    for char in all_characters:
        if not char.is_on_farm:
            available_chars.append(char)

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
        await query.message.edit_text(
            msg,
            reply_markup=character_selection_kb(available_chars, current_team_ids)
        )
    else:
        await query.message.edit_reply_markup(
            reply_markup=character_selection_kb(available_chars, current_team_ids)
        )


@router.callback_query(BattleCallback.filter(F.action == "view_team"))
async def view_team(query: CallbackQuery, session: AsyncSession):
    """Просмотр текущей команды"""
    character_repo = CharacterRepository(session)
    user_repo = UserRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    team = await character_repo.get_team(user.id)

    if not team:
        await query.answer("❌ Команда не выбрана", show_alert=True)
        return

    team_display = ""
    for i, char in enumerate(team, 1):
        char_data = get_character(char.character_type)
        team_display += f"""{i}. {RARITY_EMOJI.get(char_data.rarity, '⚪')} *{char_data.name}* L{char.level}
   ❤️ {char.current_hp}/{char.max_hp} | 🗡️ {char.base_damage} | 🛡️ {char.base_armor}
   ⚔️ Побед: {char.battle_wins} | 💀 Поражений: {char.battle_losses}

"""

    msg = f"""👥 *ТВОЯ БОЕВАЯ КОМАНДА*

{team_display}
Готов к бою! ⚔️"""

    if query.message.text != msg:
        await query.message.edit_text(msg, reply_markup=battle_menu_kb())
    else:
        await query.answer("✅ Команда уже отображается")


@router.callback_query(BattleCallback.filter(F.action == "start_pvp"))
async def start_pvp(query: CallbackQuery, session: AsyncSession):
    """PvP бой"""
    character_repo = CharacterRepository(session)
    user_repo = UserRepository(session)
    battle_engine = BattleEngine(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    team = await character_repo.get_team(user.id)

    if len(team) < 3:
        await query.answer(f"❌ В команде {len(team)}/3 персонажей. Нужно 3!", show_alert=True)
        return

    all_users = await user_repo.get_all()
    opponents = [u for u in all_users if u.id != user.id and u.id != 0]

    if not opponents:
        result = await battle_engine.start_pve_battle(user.id, "medium")
    else:
        opponent = random.choice(opponents)
        result = await battle_engine.start_pvp_battle(user.id, opponent.id)

    if "error" in result:
        await query.answer(result.get("message", "❌ Ошибка боя"), show_alert=True)
        return

    if result["player_won"]:
        msg = f"""🏆 *ПОБЕДА!*

💰 +{result['coins']} монет
💎 +{result['crystals']} кристаллов

    
"""
        if result["player_won"]:
            if FEATURES.get("reputation"):
                rep_service = ReputationService(session)
                await rep_service.add_reputation(user.id, "battle_win_pvp")

    else:
        msg = f"""💀 *ПОРАЖЕНИЕ*

💰 +{result['coins']} монет (утешение)

"""

    if result.get("level_ups"):
        msg += "\n📈 *Повышение уровня:*\n" + "\n".join(result["level_ups"])

    await query.message.edit_text(msg, reply_markup=battle_menu_kb())
    await query.answer("⚔️ Бой завершен!")


@router.callback_query(BattleCallback.filter(F.action == "start_pve"))
async def start_pve(query: CallbackQuery, session: AsyncSession):
    """PvE бой - выбор сложности"""
    character_repo = CharacterRepository(session)
    user_repo = UserRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    team = await character_repo.get_team(user.id)

    if len(team) < 3:
        await query.answer(f"❌ В команде {len(team)}/3 персонажей. Нужно 3!", show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton(text="👹 ЛЕГКО (x1)", callback_data="pve_easy")],
        [InlineKeyboardButton(text="👺 СРЕДНЕ (x1.5)", callback_data="pve_medium")],
        [InlineKeyboardButton(text="👿 СЛОЖНО (x2)", callback_data="pve_hard")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="battle_menu")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await query.message.edit_text(
        "⚔️ *ВЫБЕРИ СЛОЖНОСТЬ PvE*",
        reply_markup=keyboard
    )
    await query.answer()


@router.callback_query(F.data.startswith("pve_"))
async def start_pve_with_difficulty(query: CallbackQuery, session: AsyncSession):
    """PvE бой с выбранной сложностью"""
    difficulty = query.data.split("_")[1]

    battle_engine = BattleEngine(session)
    user_repo = UserRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    result = await battle_engine.start_pve_battle(user.id, difficulty)

    if "error" in result:
        await query.answer(result.get("message", "❌ Ошибка боя"), show_alert=True)
        return


    if result["player_won"]:
        msg = f"""🏆 *ПОБЕДА!* ({difficulty.upper()})

💰 +{result['coins']} монет
💎 +{result['crystals']} кристаллов

"""
    else:
        msg = f"""💀 *ПОРАЖЕНИЕ* ({difficulty.upper()})

💰 +{result['coins']} монет (утешение)

"""

    if result.get("level_ups"):
        msg += "\n📈 *Повышение уровня:*\n" + "\n".join(result["level_ups"])

    await query.message.edit_text(msg, reply_markup=battle_menu_kb())
    await query.answer("⚔️ Бой завершен!")