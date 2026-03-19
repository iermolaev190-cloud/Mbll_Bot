import random
import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.market_repo import MarketRepository
from database.repository.character_repo import CharacterRepository
from database.repository.user_repo import UserRepository
from services.market_service import MarketService
from services.reputation_service import ReputationService
from keyboards.inline_kb import (
    market_menu_kb, market_listings_kb, listing_detail_kb,
    sell_character_kb, sell_confirm_kb, my_listings_kb
)
from keyboards.callbacks import MarketCallback, MainMenuCallback
from config.texts import *
from config.character_config import get_character
from config.emoji import RARITY_EMOJI, ELEMENT_EMOJI
from config.game_config import MIN_MARKET_PRICE, MAX_MARKET_PRICE, MARKET_COMMISSION_PERCENT
from config.features import FEATURES
from utils.ai_helper import get_market_message


class MarketStates(StatesGroup):
    waiting_for_price = State()


router = Router()


@router.message(Command("market"))
async def market_command(message: Message):
    """Прямая команда для рынка"""
    await message.answer(MARKET_MENU, reply_markup=market_menu_kb())


@router.callback_query(MainMenuCallback.filter(F.action == "market"))
async def show_market_menu(query: CallbackQuery):
    """Главное меню рынка"""
    welcome_text = ""
    if FEATURES.get("market_talk"):
        welcome = await get_market_message("welcome")
        if welcome:
            welcome_text = f"\n{welcome}\n"

    await query.message.edit_text(f"{MARKET_MENU}{welcome_text}", reply_markup=market_menu_kb())
    await query.answer()


@router.callback_query(MarketCallback.filter(F.action == "menu"))
async def show_market_menu_cb(query: CallbackQuery):
    """Возврат в меню рынка"""
    await query.message.edit_text(MARKET_MENU, reply_markup=market_menu_kb())
    await query.answer()


@router.callback_query(MarketCallback.filter(F.action == "list"))
async def show_listings(query: CallbackQuery, callback_data: MarketCallback, session: AsyncSession):
    """Список объявлений"""
    market_service = MarketService(session)
    listings = await market_service.get_active_listings(limit=20)

    if not listings:
        gossip = ""
        if FEATURES.get("market_gossip"):
            gossip = "\n\n" + await get_market_message("gossip")
        # ========================

        await query.message.edit_text(f"🏪 Рынок пуст. Приходи позже!{gossip}", reply_markup=market_menu_kb())
        await query.answer()
        return

    gossip = ""
    if FEATURES.get("market_gossip") and random.random() < 0.3:
        gossip = "\n\n" + await get_market_message("gossip")

    await query.message.edit_text(
        f"🏪 *ДОСТУПНЫЕ ОБЪЯВЛЕНИЯ*\n\nВсего: {len(listings)}{gossip}",
        reply_markup=market_listings_kb(listings)
    )
    await query.answer()


@router.callback_query(MarketCallback.filter(F.action == "buy"))
async def show_listing_detail(query: CallbackQuery, callback_data: MarketCallback, session: AsyncSession):
    """Детали объявления"""
    market_repo = MarketRepository(session)
    character_repo = CharacterRepository(session)
    user_repo = UserRepository(session)

    listing = await market_repo.get_by_id(callback_data.listing_id)
    if not listing or listing.is_sold:
        await query.answer("❌ Объявление уже продано", show_alert=True)
        return

    character = await character_repo.get_by_id(listing.character_id)
    seller = await user_repo.get_by_id(listing.seller_id)
    char_data = get_character(character.character_type)

    msg = f"""🏪 *ОБЪЯВЛЕНИЕ #{listing.id}*

{RARITY_EMOJI.get(char_data.rarity, '⚪')} *{char_data.name}* L{character.level}
{ELEMENT_EMOJI.get(char_data.element, '🔥')} {char_data.element}

❤️ HP: {character.max_hp}
🗡️ Урон: {character.base_damage}
🛡️ Броня: {character.base_armor}

💰 Цена: {listing.price} монет
👤 Продавец: {seller.first_name or f'Player{seller.telegram_id}'}

🏷️ Комиссия 5% включена в цену"""

    await query.message.edit_text(msg, reply_markup=listing_detail_kb(listing.id))
    await query.answer()


@router.callback_query(MarketCallback.filter(F.action == "confirm_buy"))
async def confirm_purchase(query: CallbackQuery, callback_data: MarketCallback, session: AsyncSession):
    """Подтверждение покупки"""
    market_service = MarketService(session)
    user_repo = UserRepository(session)
    rep_service = ReputationService(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)

    market_repo = MarketRepository(session)
    listing = await market_repo.get_by_id(callback_data.listing_id)

    if not listing:
        await query.answer("❌ Объявление не найдено", show_alert=True)
        return

    price_with_discount = await rep_service.apply_market_discount(user.id, listing.price)

    result = await market_service.purchase_listing(user.id, callback_data.listing_id)

    if "error" in result:
        if result["error"] == "insufficient_funds":
            await query.answer(f"❌ Недостаточно монет! Нужно: {result['need']}, есть: {result['have']}",
                               show_alert=True)
        else:
            await query.answer(f"❌ {result['error']}", show_alert=True)
        return

    if FEATURES.get("reputation"):
        await rep_service.add_reputation(user.id, "market_buy")

    await query.message.edit_text(
        f"""✅ *ПОКУПКА УСПЕШНА!*

💰 Цена: {result['price']} монет
💸 Комиссия: {result['commission']} монет

🎉 Персонаж добавлен в твою коллекцию!""",
        reply_markup=market_menu_kb()
    )
    await query.answer("🎉 Покупка совершена!")


@router.callback_query(MarketCallback.filter(F.action == "sell"))
async def sell_character_menu(query: CallbackQuery, callback_data: MarketCallback, session: AsyncSession):
    """Меню продажи персонажа"""
    character_repo = CharacterRepository(session)
    user_repo = UserRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)

    all_characters = await character_repo.get_by_owner(user.id)
    available = []

    for char in all_characters:
        if not char.is_in_team and not char.is_on_farm:
            existing_listings = await MarketRepository(session).get_seller_listings(user.id)
            is_on_market = any(l.character_id == char.id for l in existing_listings if not l.is_sold)

            if not is_on_market:
                available.append(char)

    if not available:
        await query.answer(
            "❌ Нет персонажей для продажи!\n\n"
            "✅ Доступны персонажи:\n"
            "• Не в боевой команде\n"
            "• Не на ферме\n"
            "• Не в активных объявлениях",
            show_alert=True
        )
        return

    text = "💎 *ПРОДАЖА ПЕРСОНАЖА*\n\n"
    text += f"📊 Доступно для продажи: {len(available)}\n\n"
    text += "Выбери персонажа:\n"

    await query.message.edit_text(text, reply_markup=sell_character_kb(available))
    await query.answer()


@router.callback_query(MarketCallback.filter(F.action == "set_price"))
async def set_price_prompt(query: CallbackQuery, callback_data: MarketCallback, session: AsyncSession,
                           state: FSMContext):
    """Запрос цены"""
    character_repo = CharacterRepository(session)
    user_repo = UserRepository(session)
    market_service = MarketService(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    character = await character_repo.get_by_id(callback_data.character_id)
    char_data = get_character(character.character_type)

    recommended = await market_service.get_recommended_price(character.character_type, character.level)

    await query.message.edit_text(
        f"""💰 *УСТАНОВКА ЦЕНЫ*

{RARITY_EMOJI.get(char_data.rarity, '⚪')} *{char_data.name}* L{character.level}

💡 Рекомендуемая цена: {recommended} монет
💰 Твой баланс: {user.coins} монет

📏 Диапазон: {MIN_MARKET_PRICE} - {MAX_MARKET_PRICE} монет

Введи цену числом:"""
    )

    await state.set_state(MarketStates.waiting_for_price)
    await state.update_data(character_id=callback_data.character_id)
    await query.answer()


@router.message(MarketStates.waiting_for_price)
async def process_price_input(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка введенной цены"""
    try:
        price = int(message.text)
    except ValueError:
        await message.answer("❌ Введи число!")
        return

    if price < MIN_MARKET_PRICE or price > MAX_MARKET_PRICE:
        await message.answer(f"❌ Цена должна быть от {MIN_MARKET_PRICE} до {MAX_MARKET_PRICE}!")
        return

    data = await state.get_data()
    character_id = data["character_id"]

    character_repo = CharacterRepository(session)
    character = await character_repo.get_by_id(character_id)
    char_data = get_character(character.character_type)

    commission = int(price * MARKET_COMMISSION_PERCENT)
    net_price = price - commission

    await message.answer(
        f"""📋 *ПОДТВЕРДИ ПРОДАЖУ*

{RARITY_EMOJI.get(char_data.rarity, '⚪')} *{char_data.name}* L{character.level}

💰 Цена: {price} монет
💸 Комиссия (5%): {commission} монет
💵 Ты получишь: {net_price} монет

✅ Подтверди размещение объявления""",
        reply_markup=sell_confirm_kb(character_id)
    )
    await state.clear()


@router.callback_query(MarketCallback.filter(F.action == "create_listing"))
async def create_listing(query: CallbackQuery, callback_data: MarketCallback, session: AsyncSession):
    """Создание объявления"""
    market_service = MarketService(session)
    user_repo = UserRepository(session)
    character_repo = CharacterRepository(session)
    rep_service = ReputationService(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)

    text = query.message.text
    price_match = re.search(r'💰 Цена: (\d+)', text)
    if not price_match:
        await query.answer("❌ Ошибка определения цены", show_alert=True)
        return

    price = int(price_match.group(1))

    result = await market_service.create_listing(user.id, callback_data.character_id, price)

    if "error" in result:
        await query.answer(f"❌ {result['error']}", show_alert=True)
        return

    character = await character_repo.get_by_id(callback_data.character_id)
    char_data = get_character(character.character_type)

    commission = int(price * MARKET_COMMISSION_PERCENT)
    net_price = price - commission

    if FEATURES.get("reputation"):
        await rep_service.add_reputation(user.id, "market_sell")
    # ================================

    await query.message.edit_text(
        f"""✅ *ОБЪЯВЛЕНИЕ РАЗМЕЩЕНО!*

{RARITY_EMOJI.get(char_data.rarity, '⚪')} *{char_data.name}* L{character.level}

💰 Цена: {price} монет
💸 Комиссия: {commission} монет
💵 Ты получишь: {net_price} монет

📅 Объявление активно 7 дней""",
        reply_markup=market_menu_kb()
    )
    await query.answer("✅ Объявление создано!")


@router.callback_query(MarketCallback.filter(F.action == "my_listings"))
async def my_listings(query: CallbackQuery, callback_data: MarketCallback, session: AsyncSession):
    """Мои объявления"""
    market_service = MarketService(session)
    user_repo = UserRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    listings = await market_service.get_seller_listings(user.id)

    if not listings:
        await query.message.edit_text("📋 У тебя нет активных объявлений", reply_markup=market_menu_kb())
        await query.answer()
        return

    await query.message.edit_text(
        f"📋 *ТВОИ ОБЪЯВЛЕНИЯ*\n\nВсего: {len(listings)}\n\nНажми на объявление чтобы отменить:",
        reply_markup=my_listings_kb(listings)
    )
    await query.answer()


@router.callback_query(MarketCallback.filter(F.action == "cancel_listing"))
async def cancel_listing(query: CallbackQuery, callback_data: MarketCallback, session: AsyncSession):
    """Отмена объявления"""
    market_service = MarketService(session)
    user_repo = UserRepository(session)

    user = await user_repo.get_by_telegram_id(query.from_user.id)
    result = await market_service.cancel_listing(user.id, callback_data.listing_id)

    if "error" in result:
        await query.answer(f"❌ {result['error']}", show_alert=True)
        return

    listings = await market_service.get_seller_listings(user.id)

    if listings:
        await query.message.edit_text(
            f"📋 *ТВОИ ОБЪЯВЛЕНИЯ*\n\nВсего: {len(listings)}",
            reply_markup=my_listings_kb(listings)
        )
    else:
        await query.message.edit_text("📋 У тебя нет активных объявлений", reply_markup=market_menu_kb())

    await query.answer("✅ Объявление отменено")