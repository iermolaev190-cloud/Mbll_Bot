from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.user_repo import UserRepository
from database.repository.character_repo import CharacterRepository
from keyboards.callbacks import AdminCallback
from keyboards.inline_kb import admin_menu_kb
from config.settings import settings
from config.texts import UNAUTHORIZED
from datetime import datetime

router = Router()


class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()
    waiting_for_ban_reason = State()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids_list


@router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        await message.answer(UNAUTHORIZED)
        return

    user_repo = UserRepository(session)
    char_repo = CharacterRepository(session)

    all_users = await user_repo.get_all()
    total_users = len(all_users)
    banned_users = sum(1 for u in all_users if u.is_banned)
    total_chars = await char_repo.get_total_characters_count()

    total_coins = sum(u.coins for u in all_users)
    total_crystals = sum(u.crystals for u in all_users)
    total_diamonds = sum(u.diamonds for u in all_users)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    new_today = sum(1 for u in all_users if u.created_at >= today)

    stats = f"""📊 *СТАТИСТИКА БОТА*

👥 Всего игроков: {total_users}
⛔ Забанено: {banned_users}
🆕 Новых сегодня: {new_today}

💰 Монет в обороте: {total_coins:,}
💎 Кристаллов: {total_crystals:,}
💠 Алмазов: {total_diamonds:,}

👤 Всего персонажей: {total_chars}
"""

    await message.answer(stats, reply_markup=admin_menu_kb())


@router.callback_query(AdminCallback.filter(F.action == "stats"))
async def admin_stats(query: CallbackQuery, session: AsyncSession):
    if not is_admin(query.from_user.id):
        await query.answer(UNAUTHORIZED, show_alert=True)
        return

    user_repo = UserRepository(session)
    char_repo = CharacterRepository(session)

    all_users = await user_repo.get_all()
    total_users = len(all_users)
    banned_users = sum(1 for u in all_users if u.is_banned)
    total_chars = await char_repo.get_total_characters_count()

    total_coins = sum(u.coins for u in all_users)
    total_crystals = sum(u.crystals for u in all_users)
    total_diamonds = sum(u.diamonds for u in all_users)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    new_today = sum(1 for u in all_users if u.created_at >= today)

    top_users = sorted(all_users, key=lambda x: x.coins, reverse=True)[:5]
    top_text = "\n".join([f"{i + 1}. {u.first_name or u.telegram_id}: {u.coins:,}💰" for i, u in enumerate(top_users)])

    stats = f"""📊 *СТАТИСТИКА БОТА*

👥 Всего игроков: {total_users}
⛔ Забанено: {banned_users}
🆕 Новых сегодня: {new_today}

💰 Монет в обороте: {total_coins:,}
💎 Кристаллов: {total_crystals:,}
💠 Алмазов: {total_diamonds:,}

👤 Всего персонажей: {total_chars}

🏆 *Топ по монетам:*
{top_text}
"""

    await query.message.edit_text(stats, reply_markup=admin_menu_kb())
    await query.answer()


@router.callback_query(AdminCallback.filter(F.action == "give"))
async def admin_give_start(query: CallbackQuery, state: FSMContext):
    if not is_admin(query.from_user.id):
        await query.answer(UNAUTHORIZED, show_alert=True)
        return

    await query.message.edit_text(
        "💰 *ВЫДАЧА ВАЛЮТЫ*\n\n"
        "Введи Telegram ID пользователя:"
    )
    await state.set_state(AdminStates.waiting_for_user_id)
    await state.update_data(action="give")
    await query.answer()


@router.callback_query(AdminCallback.filter(F.action == "take"))
async def admin_take_start(query: CallbackQuery, state: FSMContext):
    if not is_admin(query.from_user.id):
        await query.answer(UNAUTHORIZED, show_alert=True)
        return

    await query.message.edit_text(
        "💸 *ИЗЪЯТИЕ ВАЛЮТЫ*\n\n"
        "Введи Telegram ID пользователя:"
    )
    await state.set_state(AdminStates.waiting_for_user_id)
    await state.update_data(action="take")
    await query.answer()


@router.callback_query(AdminCallback.filter(F.action == "ban"))
async def admin_ban_start(query: CallbackQuery, state: FSMContext):
    if not is_admin(query.from_user.id):
        await query.answer(UNAUTHORIZED, show_alert=True)
        return

    await query.message.edit_text(
        "🔨 *БАН ПОЛЬЗОВАТЕЛЯ*\n\n"
        "Введи Telegram ID пользователя:"
    )
    await state.set_state(AdminStates.waiting_for_user_id)
    await state.update_data(action="ban")
    await query.answer()


@router.callback_query(AdminCallback.filter(F.action == "unban"))
async def admin_unban_start(query: CallbackQuery, state: FSMContext):
    if not is_admin(query.from_user.id):
        await query.answer(UNAUTHORIZED, show_alert=True)
        return

    await query.message.edit_text(
        "🔓 *РАЗБАН ПОЛЬЗОВАТЕЛЯ*\n\n"
        "Введи Telegram ID пользователя:"
    )
    await state.set_state(AdminStates.waiting_for_user_id)
    await state.update_data(action="unban")
    await query.answer()


@router.callback_query(AdminCallback.filter(F.action == "banned_list"))
async def admin_banned_list(query: CallbackQuery, session: AsyncSession):
    if not is_admin(query.from_user.id):
        await query.answer(UNAUTHORIZED, show_alert=True)
        return

    user_repo = UserRepository(session)
    banned_users = await user_repo.get_banned_users()

    if not banned_users:
        await query.message.edit_text(
            "✅ Нет забаненных пользователей",
            reply_markup=admin_menu_kb()
        )
        await query.answer()
        return

    text = "⛔ *ЗАБАНЕННЫЕ ПОЛЬЗОВАТЕЛИ*\n\n"
    for i, user in enumerate(banned_users[:10], 1):
        reason = getattr(user, 'ban_reason', 'Не указана')
        text += f"{i}. {user.first_name or user.telegram_id}\n"
        text += f"   Причина: {reason or 'Не указана'}\n"

    await query.message.edit_text(text, reply_markup=admin_menu_kb())
    await query.answer()


# ОСНОВНАЯ ЛОГИКА
@router.message(AdminStates.waiting_for_user_id)
async def process_user_id(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка введенного ID пользователя"""
    try:
        target_telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи число!")
        return

    print(f"🔍 Поиск пользователя с TELEGRAM ID: {target_telegram_id}")

    user_repo = UserRepository(session)
    target_user = await user_repo.get_by_telegram_id(target_telegram_id)

    if not target_user:
        await message.answer(
            f"❌ Пользователь с ID {target_telegram_id} не найден!\n\n"
            f"💡 Убедись что:\n"
            f"• ID правильный\n"
            f"• Пользователь запускал бота"
        )
        await state.clear()
        return

    print(f"✅ Найден пользователь: {target_user.first_name}, внутренний ID: {target_user.id}")

    data = await state.get_data()
    action = data.get("action")

    # Сохраняем ВНУТРЕННИЙ ID пользователя
    await state.update_data(target_id=target_user.id)

    info_text = (
        f"👤 *Информация о пользователе*\n\n"
        f"📝 Имя: {target_user.first_name or 'Не указано'}\n"
        f"🆔 Telegram ID: {target_user.telegram_id}\n"
        f"🆔 Внутренний ID: {target_user.id}\n"
        f"💰 Монеты: {target_user.coins:,}\n"
        f"💎 Кристаллы: {target_user.crystals}\n"
        f"💠 Алмазы: {target_user.diamonds}\n"
        f"⛔ Статус: {'Забанен' if target_user.is_banned else 'Активен'}\n"
    )

    if action in ["give", "take"]:
        await message.answer(
            info_text + f"\n💸 Введи сумму для {'ВЫДАЧИ' if action == 'give' else 'ИЗЪЯТИЯ'}:"
        )
        await state.set_state(AdminStates.waiting_for_amount)

    elif action == "ban":
        if target_user.is_banned:
            await message.answer("❌ Пользователь уже забанен!")
            await state.clear()
            return

        await message.answer(
            info_text + "\n\n📝 Введи причину бана (или 'skip'):"
        )
        await state.set_state(AdminStates.waiting_for_ban_reason)

    elif action == "unban":
        if not target_user.is_banned:
            await message.answer("❌ Пользователь не забанен!")
            await state.clear()
            return

        result = await user_repo.unban_user(target_user.id)
        check_user = await user_repo.get_by_id(target_user.id)

        await message.answer(
            f"✅ *Пользователь разбанен!*\n\n"
            f"👤 {target_user.first_name}\n"
            f"🆔 {target_user.telegram_id}\n"
            f"⛔ Статус: {'Забанен' if check_user.is_banned else 'Активен'}",
            reply_markup=admin_menu_kb()
        )
        await state.clear()


#ОБРАБОТКА СУММЫ
@router.message(AdminStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка суммы для выдачи/изъятия"""
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи число!")
        return

    data = await state.get_data()
    target_internal_id = data.get("target_id")
    action = data.get("action")

    print(f"💰 Получена сумма: {amount} для пользователя с внутренним ID: {target_internal_id}")

    user_repo = UserRepository(session)
    target_user = await user_repo.get_by_id(target_internal_id)

    if not target_user:
        print(f"❌ ОШИБКА: Пользователь с внутренним ID {target_internal_id} не найден!")
        await message.answer("❌ Ошибка: пользователь не найден!")
        await state.clear()
        return

    print(f"✅ Найден пользователь: {target_user.first_name}")

    currency_buttons = [
        [
            InlineKeyboardButton(text="💰 Монеты", callback_data="admin_currency_coins"),
            InlineKeyboardButton(text="💎 Кристаллы", callback_data="admin_currency_crystals"),
        ],
        [
            InlineKeyboardButton(text="💠 Алмазы", callback_data="admin_currency_diamonds"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel"),
        ],
    ]

    action_text = "ВЫДАТЬ" if action == "give" else "ИЗЪЯТЬ"

    await message.answer(
        f"👤 *Пользователь:* {target_user.first_name or target_user.telegram_id}\n"
        f"💰 Текущий баланс монет: {target_user.coins:,}\n"
        f"💎 Кристаллы: {target_user.crystals}\n"
        f"💠 Алмазы: {target_user.diamonds}\n\n"
        f"Сумма: {amount} {'+' if action == 'give' else '-'}\n\n"
        f"Выбери тип валюты для {action_text.lower()}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=currency_buttons)
    )

    await state.update_data(amount=amount)


@router.message(AdminStates.waiting_for_ban_reason)
async def process_ban_reason(message: Message, state: FSMContext, session: AsyncSession):
    reason = message.text if message.text.lower() != "skip" else None

    data = await state.get_data()
    target_internal_id = data.get("target_id")

    print(f"🔍 Получен запрос на бан внутреннего ID: {target_internal_id}, причина: {reason}")

    user_repo = UserRepository(session)
    target_user = await user_repo.get_by_id(target_internal_id)

    if not target_user:
        print(f"❌ Пользователь с внутренним ID {target_internal_id} не найден!")
        await message.answer("❌ Пользователь не найден!")
        await state.clear()
        return

    result = await user_repo.ban_user(target_internal_id, reason)
    check_user = await user_repo.get_by_id(target_internal_id)

    await message.answer(
        f"✅ *Пользователь забанен!*\n\n"
        f"👤 {target_user.first_name or target_user.telegram_id}\n"
        f"📝 Причина: {reason or 'Не указана'}\n"
        f"⛔ Статус: {'Забанен' if check_user.is_banned else 'ОШИБКА!'}",
        reply_markup=admin_menu_kb()
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin_currency_"))
async def process_currency(query: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора типа валюты"""
    currency = query.data.split("_")[2]

    data = await state.get_data()
    target_internal_id = data.get("target_id")
    amount = data.get("amount")
    action = data.get("action")

    print(f"💱 Выбрана валюта: {currency}, сумма: {amount}, действие: {action}")
    print(f"🔍 Поиск пользователя с внутренним ID: {target_internal_id}")

    user_repo = UserRepository(session)
    target_user = await user_repo.get_by_id(target_internal_id)

    if not target_user:
        print(f"❌ ОШИБКА: Пользователь с внутренним ID {target_internal_id} не найден!")
        await query.answer("❌ Пользователь не найден!", show_alert=True)
        await state.clear()
        return

    print(f"✅ Найден пользователь: {target_user.first_name}")

    old_value = 0
    new_value = 0

    if action == "give":
        if currency == "coins":
            old_value = target_user.coins
            target_user.coins += amount
            new_value = target_user.coins
        elif currency == "crystals":
            old_value = target_user.crystals
            target_user.crystals += amount
            new_value = target_user.crystals
        elif currency == "diamonds":
            old_value = target_user.diamonds
            target_user.diamonds += amount
            new_value = target_user.diamonds
    else:
        if currency == "coins":
            old_value = target_user.coins
            target_user.coins = max(0, target_user.coins - amount)
            new_value = target_user.coins
        elif currency == "crystals":
            old_value = target_user.crystals
            target_user.crystals = max(0, target_user.crystals - amount)
            new_value = target_user.crystals
        elif currency == "diamonds":
            old_value = target_user.diamonds
            target_user.diamonds = max(0, target_user.diamonds - amount)
            new_value = target_user.diamonds

    await user_repo.update(target_user)

    currency_emoji = "💰" if currency == "coins" else "💎" if currency == "crystals" else "💠"
    action_word = "выдано" if action == "give" else "изъято"

    await query.message.edit_text(
        f"✅ *Операция выполнена!*\n\n"
        f"👤 Пользователь: {target_user.first_name or target_user.telegram_id}\n"
        f"💱 Действие: {action_word} {amount} {currency_emoji}\n"
        f"📊 Было: {old_value}\n"
        f"📈 Стало: {new_value}\n\n"
        f"💰 Монеты: {target_user.coins}\n"
        f"💎 Кристаллы: {target_user.crystals}\n"
        f"💠 Алмазы: {target_user.diamonds}",
        reply_markup=admin_menu_kb()
    )

    await state.clear()
    await query.answer("✅ Готово!")


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.edit_text(
        "🔧 *АДМИН ПАНЕЛЬ*\n\nОперация отменена.",
        reply_markup=admin_menu_kb()
    )
    await query.answer()