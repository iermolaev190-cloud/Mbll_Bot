from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.user_repo import UserRepository
from services.economy_service import EconomyService
from keyboards.inline_kb import economy_menu_kb
from keyboards.callbacks import EconomyCallback, MainMenuCallback
from config.game_config import EXCHANGE_RATES

router = Router()


class ExchangeStates(StatesGroup):
    waiting_for_amount = State()
    exchange_type = State()


@router.message(Command("economy"))
async def economy_command(message: Message, session: AsyncSession):
    """Команда для входа в экономику"""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    msg = f"""💰 *ОБМЕН ВАЛЮТ*

💰 Монеты: {user.coins:,}
💎 Кристаллы: {user.crystals}
💠 Алмазы: {user.diamonds}

💱 *Курсы обмена:*
1️⃣ {EXCHANGE_RATES['coins_to_crystals']:,}💰 = 1💎
2️⃣ {EXCHANGE_RATES['coins_and_crystals_to_diamond']['coins']:,}💰 + {EXCHANGE_RATES['coins_and_crystals_to_diamond']['crystals']}💎 = 1💠
3️⃣ {EXCHANGE_RATES['crystals_to_diamonds']}💎 = 1💠

Выбери действие:"""

    await message.answer(msg, reply_markup=economy_menu_kb())


@router.callback_query(MainMenuCallback.filter(F.action == "economy"))
async def show_economy_menu(query: CallbackQuery, session: AsyncSession):
    """Главное меню экономики"""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)

    msg = f"""💰 *ОБМЕН ВАЛЮТ*

💰 Монеты: {user.coins:,}
💎 Кристаллы: {user.crystals}
💠 Алмазы: {user.diamonds}

💱 *Курсы обмена:*
1️⃣ {EXCHANGE_RATES['coins_to_crystals']:,}💰 = 1💎
2️⃣ {EXCHANGE_RATES['coins_and_crystals_to_diamond']['coins']:,}💰 + {EXCHANGE_RATES['coins_and_crystals_to_diamond']['crystals']}💎 = 1💠
3️⃣ {EXCHANGE_RATES['crystals_to_diamonds']}💎 = 1💠

Выбери действие:"""

    await query.message.edit_text(msg, reply_markup=economy_menu_kb())
    await query.answer()


@router.callback_query(EconomyCallback.filter(F.action == "exchange_coins"))
async def exchange_coins_start(query: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начало обмена монет на кристаллы"""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)

    rate = EXCHANGE_RATES["coins_to_crystals"]
    max_amount = user.coins // rate

    await query.message.edit_text(
        f"""💰 *ОБМЕН МОНЕТ НА КРИСТАЛЛЫ*

💱 Курс: {rate:,}💰 = 1💎
💰 Твой баланс: {user.coins:,}💰
💎 Максимум: {max_amount}💎

📝 Введи количество кристаллов (от 1 до {max_amount}):"""
    )

    await state.set_state(ExchangeStates.waiting_for_amount)
    await state.update_data(exchange_type="coins_to_crystals")
    await query.answer()


@router.callback_query(EconomyCallback.filter(F.action == "exchange_complex"))
async def exchange_complex_start(query: CallbackQuery, session: AsyncSession):
    """Сложный обмен на алмаз (монеты + кристаллы)"""
    economy_service = EconomyService(session)
    user_repo = UserRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    required = EXCHANGE_RATES["coins_and_crystals_to_diamond"]

    if user.coins >= required["coins"] and user.crystals >= required["crystals"]:
        result = await economy_service.exchange_coins_crystals_to_diamond(user.id)

        if "error" in result:
            await query.answer(result.get("message", "❌ Ошибка"), show_alert=True)
            return

        await query.message.edit_text(
            f"""✅ *ОБМЕН ВЫПОЛНЕН!*

{result['message']}

💰 Новый баланс: {result['coins']:,}💰
💎 Кристаллы: {result['crystals']}
💠 Алмазы: {result['diamonds']}""",
            reply_markup=economy_menu_kb()
        )
    else:
        missing_coins = max(0, required["coins"] - user.coins)
        missing_crystals = max(0, required["crystals"] - user.crystals)

        await query.message.edit_text(
            f"""❌ *НЕДОСТАТОЧНО РЕСУРСОВ!*

💠 Нужно: {required['coins']:,}💰 + {required['crystals']}💎

💰 У тебя: {user.coins:,}💰
💎 Кристаллов: {user.crystals}

📊 Не хватает:
💰 Монет: {missing_coins:,}
💎 Кристаллов: {missing_crystals}

🌾 Заработай на ферме или в боях!""",
            reply_markup=economy_menu_kb()
        )

    await query.answer()


@router.callback_query(EconomyCallback.filter(F.action == "exchange_crystals"))
async def exchange_crystals_start(query: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начало обмена кристаллов на алмазы"""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(query.from_user.id)

    rate = EXCHANGE_RATES["crystals_to_diamonds"]
    max_amount = user.crystals // rate

    await query.message.edit_text(
        f"""💠 *ОБМЕН КРИСТАЛЛОВ НА АЛМАЗЫ*

💱 Курс: {rate}💎 = 1💠
💎 Твой баланс: {user.crystals}💎
💠 Максимум: {max_amount}💠

📝 Введи количество алмазов (от 1 до {max_amount}):"""
    )

    await state.set_state(ExchangeStates.waiting_for_amount)
    await state.update_data(exchange_type="crystals_to_diamonds")
    await query.answer()


@router.message(ExchangeStates.waiting_for_amount)
async def process_exchange_amount(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка введенного количества"""
    try:
        amount = int(message.text)
        if amount <= 0:
            await message.answer("❌ Введи положительное число!")
            return
    except ValueError:
        await message.answer("❌ Введи число!")
        return

    data = await state.get_data()
    exchange_type = data.get("exchange_type")

    user_repo = UserRepository(session)
    economy_service = EconomyService(session)

    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if exchange_type == "coins_to_crystals":
        rate = EXCHANGE_RATES["coins_to_crystals"]
        needed_coins = amount * rate

        if user.coins < needed_coins:
            max_amount = user.coins // rate
            await message.answer(
                f"❌ *Недостаточно монет!*\n\n"
                f"💰 Нужно: {needed_coins:,}\n"
                f"💵 Есть: {user.coins:,}\n"
                f"💡 Максимум: {max_amount}💎\n\n"
                f"🌾 *Введи другое количество:*"
            )
            return

        result = await economy_service.exchange_coins_to_crystals(user.id, amount)

        if "error" in result:
            await message.answer(result.get("message", "❌ Ошибка"))
            await state.clear()
            return

        await message.answer(
            f"""✅ *ОБМЕН ВЫПОЛНЕН!*

{result['message']}

💰 *Новый баланс:* {result['coins']:,}💰
💎 *Кристаллы:* {result['crystals']}
💠 *Алмазы:* {result['diamonds']}""",
            reply_markup=economy_menu_kb()
        )

    elif exchange_type == "crystals_to_diamonds":
        rate = EXCHANGE_RATES["crystals_to_diamonds"]
        needed_crystals = amount * rate

        if user.crystals < needed_crystals:
            max_amount = user.crystals // rate
            await message.answer(
                f"❌ *Недостаточно кристаллов!*\n\n"
                f"💎 Нужно: {needed_crystals}\n"
                f"✨ Есть: {user.crystals}\n"
                f"💡 Максимум: {max_amount}💠\n\n"
                f"💎 *Введи другое количество:*"
            )
            return

        result = await economy_service.exchange_crystals_to_diamonds(user.id, amount)

        if "error" in result:
            await message.answer(result.get("message", "❌ Ошибка"))
            await state.clear()
            return

        await message.answer(
            f"""✅ *ОБМЕН ВЫПОЛНЕН!*

{result['message']}

💰 *Новый баланс:* {result['coins']:,}💰
💎 *Кристаллы:* {result['crystals']}
💠 *Алмазы:* {result['diamonds']}""",
            reply_markup=economy_menu_kb()
        )

    await state.clear()