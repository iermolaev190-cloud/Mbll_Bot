from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Character
from database.repository.user_repo import UserRepository
from database.repository.farm_repo import FarmRepository
from database.repository.character_repo import CharacterRepository
from services.farm_service import FarmService
from keyboards.inline_kb import farm_menu_kb, farm_slots_kb, slot_actions_kb
from keyboards.callbacks import FarmCallback, MainMenuCallback, BattleCallback
from config.character_config import get_character
from config.emoji import RARITY_EMOJI, ELEMENT_EMOJI
from datetime import datetime, timezone
from services.reputation_service import ReputationService
from config.features import FEATURES

router = Router()


@router.message(Command("farm"))
async def farm_command(message: Message, session: AsyncSession):
    """Прямая команда для фермы"""
    await show_farm_menu_logic(message.from_user.id, message, session, is_edit=False)


@router.callback_query(MainMenuCallback.filter(F.action == "farm"))
async def show_farm_menu(query: CallbackQuery, callback_data: MainMenuCallback, session: AsyncSession):
    """Главное меню фермы"""
    await show_farm_menu_logic(query.from_user.id, query.message, session, is_edit=True)
    await query.answer()


async def show_farm_menu_logic(user_id: int, message_obj, session: AsyncSession, is_edit: bool = False):
    """Общая логика для отображения фермы"""
    user_repo = UserRepository(session)
    farm_service = FarmService(session)

    user = await user_repo.get_by_telegram_id(user_id)
    status = await farm_service.get_farm_status(user.id)

    slots_text = ""
    for slot in status["slots"]:
        if slot["is_occupied"]:
            water_emoji = "💧" if not slot.get("needs_water", False) else "⚠️"
            stage_emoji = "🥚" if slot["growth_stage"] == "seed" else "🐣" if slot["growth_stage"] == "sprout" else "🐥" if \
            slot["growth_stage"] == "teenager" else "🐔"
            slots_text += f"{stage_emoji} #{slot['slot_number']}: {slot.get('character_name', '???')} ({int(slot['progress'])}%) {water_emoji}\n"
        else:
            slots_text += f"⭕ #{slot['slot_number']}: Пусто\n"

    msg = f"""🌱 *ФЕРМА*

📊 Занято: {status['occupied_slots']}/{status['total_slots']}
💧 Требуют полива: {status['needs_water_slots']}

{slots_text}

Выбери действие:"""

    if is_edit:
        await message_obj.edit_text(msg, reply_markup=farm_menu_kb())
    else:
        await message_obj.answer(msg, reply_markup=farm_menu_kb())


@router.callback_query(FarmCallback.filter(F.action == "slots"))
async def view_farm_slots(query: CallbackQuery, callback_data: FarmCallback, session: AsyncSession):
    """Показать все грядки"""
    await query.message.edit_text("🌱 *ВЫБЕРИ ГРЯДКУ:*", reply_markup=farm_slots_kb())
    await query.answer()


@router.callback_query(FarmCallback.filter(F.action == "slot"))
async def show_slot_detail(query: CallbackQuery, callback_data: FarmCallback, session: AsyncSession):
    """Детали конкретной грядки"""
    user_repo = UserRepository(session)
    farm_repo = FarmRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    slot_id = callback_data.slot_id

    await farm_repo.update_farm_growth(user.id)

    slot = await farm_repo.get_slot(user.id, slot_id)
    if not slot:
        await query.answer("❌ Слот не найден", show_alert=True)
        return

    if not slot.character_id:
        msg = f"""🥚 *ИНКУБАТОР #{slot_id}*

⭕ *ПУСТО*
Готов к закладке яйца!

💰 *Стоимость яйца:* 5000 монет
⏰ *Время вылупления:* ~7 часов
💧 *Полив:* каждые 2 часа ускоряет рост"""

        await query.message.edit_text(
            msg,
            reply_markup=slot_actions_kb(slot_id, has_plant=False)
        )
    else:
        character = await session.get(Character, slot.character_id)
        if not character:
            await query.answer("❌ Персонаж не найден", show_alert=True)
            return

        char_data = get_character(character.character_type)

        time_left = 0
        if slot.ready_at:
            time_left = max(0, (slot.ready_at - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds() / 3600)

        time_since_water = (datetime.now(timezone.utc).replace(tzinfo=None) - slot.last_watered).total_seconds() / 3600
        needs_water = time_since_water > 2
        water_status = "⚠️ Нужен полив!" if needs_water else f"✅ {int(time_since_water)}ч назад"

        is_adult = slot.growth_stage == "adult"

        stage_emoji = "🥚" if slot.growth_stage == "seed" else "🐣" if slot.growth_stage == "sprout" else "🐥" if slot.growth_stage == "teenager" else "🐔"

        msg = f"""🥚 *ИНКУБАТОР #{slot_id}*

{stage_emoji} *{char_data.name}*
{RARITY_EMOJI.get(char_data.rarity, '⚪')} {char_data.rarity.title()}
{ELEMENT_EMOJI.get(char_data.element, '🔥')} {char_data.element}

📊 *Стадия:* {slot.growth_stage.title()} ({int(slot.stage_progress)}%)
⏰ *До вылупления:* {int(time_left)} ч
💧 *Полив:* {water_status}

❤️ HP: {character.max_hp}
🗡️ Урон: {character.base_damage}
🛡️ Броня: {character.base_armor}"""

        await query.message.edit_text(
            msg,
            reply_markup=slot_actions_kb(slot_id, has_plant=True, is_adult=is_adult, needs_water=needs_water)
        )

    await query.answer()


@router.callback_query(FarmCallback.filter(F.action == "plant"))
async def plant_seed_handler(query: CallbackQuery, callback_data: FarmCallback, session: AsyncSession):
    """Посадка яйца"""
    print(f"🥚 Посадка яйца: пользователь {query.from_user.id}, слот {callback_data.slot_id}")

    user_repo = UserRepository(session)
    farm_service = FarmService(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    slot_id = callback_data.slot_id

    EGG_PRICE = 5000

    if user.coins < EGG_PRICE:
        await query.answer(
            f"❌ Недостаточно монет!\n"
            f"💰 Нужно: {EGG_PRICE}\n"
            f"💵 Есть: {user.coins}\n"
            f"🌾 Продай персонажа или собери доход!",
            show_alert=True
        )
        return

    result, character = await farm_service.plant_on_farm(user.id, slot_id)

    if isinstance(result, str):
        await query.answer(result, show_alert=True)
        return

    user.coins -= EGG_PRICE
    await user_repo.update(user)

    char_data = get_character(character.character_type)

    msg = f"""🥚 *ЯЙЦО ПРИНЯТО В ИНКУБАТОР!*

🌟 *{char_data.name}*
{RARITY_EMOJI.get(char_data.rarity, '⚪')} {char_data.rarity.title()}
{ELEMENT_EMOJI.get(char_data.element, '🔥')} {char_data.element}

💰 *Потрачено:* {EGG_PRICE} монет
💵 *Остаток:* {user.coins} монет
⏰ *Время вылупления:* ~7 часов

💧 *Уход:* поливай каждые 2 часа для ускорения"""

    await query.message.edit_text(msg, reply_markup=farm_menu_kb())
    await query.answer("🥚 Яйцо заложено в инкубатор!")


@router.callback_query(FarmCallback.filter(F.action == "water"))
async def water_plant_handler(query: CallbackQuery, callback_data: FarmCallback, session: AsyncSession):
    """Полив растения"""
    user_repo = UserRepository(session)
    farm_service = FarmService(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    slot_id = callback_data.slot_id

    if user.coins < 10:
        await query.answer("❌ Недостаточно монет! Нужно 10💰", show_alert=True)
        return

    result = await farm_service.water_plant(user.id, slot_id)

    if result.startswith("❌") or result.startswith("⏳"):
        await query.answer(result, show_alert=True)
        return

    user.coins -= 10
    await user_repo.update(user)

    msg = f"""💧 *РАСТЕНИЕ ПОЛИТО!*

{result}
💰 *Потрачено:* 10 монет
💵 *Баланс:* {user.coins} монет

🌱 Следующий полив через 2 часа."""

    await query.message.edit_text(msg, reply_markup=farm_menu_kb())
    await query.answer("💧 Полено!")


@router.callback_query(FarmCallback.filter(F.action == "harvest"))
async def harvest_plant_handler(query: CallbackQuery, callback_data: FarmCallback, session: AsyncSession):
    """Сбор урожая"""
    print(f"🌾 Сбор урожая: пользователь {query.from_user.id}, слот {callback_data.slot_id}")

    user_repo = UserRepository(session)
    farm_service = FarmService(session)
    char_repo = CharacterRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    slot_id = callback_data.slot_id

    chars_before = await char_repo.get_by_owner(user.id)
    print(f"📊 ДО сбора: у пользователя {len(chars_before)} персонажей")

    character, result = await farm_service.harvest_plant(user.id, slot_id)

    if not character:
        await query.answer(result, show_alert=True)
        return

    chars_after = await char_repo.get_by_owner(user.id)
    print(f"📊 ПОСЛЕ сбора: у пользователя {len(chars_after)} персонажей")

    found = False
    for c in chars_after:
        if c.id == character.id:
            found = True
            print(f"✅ Персонаж {c.id} найден в коллекции! Статус: is_on_farm={c.is_on_farm}")
            break

    if not found:
        print(f"❌ Персонаж {character.id} НЕ найден в коллекции!")

    char_data = get_character(character.character_type)

    msg = f"""✨ *ПЕРСОНАЖ ВЫЛУПИЛСЯ!*

🎉 *{char_data.name}*
{RARITY_EMOJI.get(char_data.rarity, '⚪')} {char_data.rarity.title()}
{ELEMENT_EMOJI.get(char_data.element, '🔥')} {char_data.element}

📊 *Характеристики:*
❤️ HP: {character.max_hp}
🗡️ Урон: {character.base_damage}
🛡️ Броня: {character.base_armor}
⚡ Ловкость: {character.base_agility}
🧠 Интеллект: {character.base_intelligence}

👥 *Всего персонажей:* {len(chars_after)}
💡 Теперь его можно добавить в команду для боёв!"""

    buttons = [
        [InlineKeyboardButton(
            text="👥 В команду",
            callback_data=BattleCallback(action="select_team").pack()
        )],
        [InlineKeyboardButton(
            text="🌱 На ферму",
            callback_data=MainMenuCallback(action="farm").pack()
        )],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await query.message.edit_text(msg, reply_markup=keyboard)
    await query.answer("🎉 Персонаж вылупился!")

    if FEATURES.get("reputation"):
        rep_service = ReputationService(session)
        await rep_service.add_reputation(user.id, "farm_harvest")


@router.callback_query(FarmCallback.filter(F.action == "water_all"))
async def water_all_plants(query: CallbackQuery, callback_data: FarmCallback, session: AsyncSession):
    """Массовый полив"""
    user_repo = UserRepository(session)
    farm_service = FarmService(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)

    status = await farm_service.get_farm_status(user.id)

    slots_to_water = [s for s in status["slots"] if s.get("needs_water", False)]

    if not slots_to_water:
        await query.answer("✅ Все растения уже политы!", show_alert=True)
        return

    total_cost = len(slots_to_water) * 10

    if user.coins < total_cost:
        await query.answer(f"❌ Недостаточно монет! Нужно {total_cost}💰", show_alert=True)
        return

    watered_count = 0
    for slot in slots_to_water:
        result = await farm_service.water_plant(user.id, slot["slot_number"])
        if "✅" in result:
            watered_count += 1

    user.coins -= total_cost
    await user_repo.update(user)

    msg = f"""💧 *МАССОВЫЙ ПОЛИВ!*

✅ Полито растений: {watered_count}/{len(slots_to_water)}
💰 Потрачено монет: {total_cost}
💵 Новый баланс: {user.coins} монет

💡 Все растения будут расти быстрее!"""

    await query.message.edit_text(msg, reply_markup=farm_menu_kb())
    await query.answer("💧 Все полито!")