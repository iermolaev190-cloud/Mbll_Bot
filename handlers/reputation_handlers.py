from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from services.reputation_service import ReputationService
from keyboards.callbacks import MainMenuCallback
from keyboards.inline_kb import main_menu_kb
from config.texts import BUTTON_BACK
from config.features import FEATURES

router = Router()


@router.message(Command("reputation"))
@router.message(Command("rep"))
async def reputation_command(message: Message, session: AsyncSession):
    """Показать свою репутацию"""
    if not FEATURES.get("reputation"):
        await message.answer("❌ Система репутации временно отключена")
        return

    service = ReputationService(session)
    status = await service.get_reputation_status(message.from_user.id)

    buttons = [[InlineKeyboardButton(text=BUTTON_BACK, callback_data=MainMenuCallback(action="profile").pack())]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(status, reply_markup=keyboard)


@router.message(Command("reptop"))
async def reputation_top(message: Message, session: AsyncSession):
    """Топ по репутации"""
    if not FEATURES.get("reputation"):
        await message.answer("❌ Система репутации временно отключена")
        return

    service = ReputationService(session)
    top = await service.get_reputation_top(10)

    if not top:
        await message.answer("📊 Пока нет данных о репутации")
        return

    text = "🏆 *ТОП ПО РЕПУТАЦИИ*\n\n"
    for i, user in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {user['name']}\n   {user['level']} | {user['reputation']} очков\n"

    buttons = [[InlineKeyboardButton(text=BUTTON_BACK, callback_data=MainMenuCallback(action="profile").pack())]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "show_reputation")
async def show_reputation_callback(query: CallbackQuery, session: AsyncSession):
    """Показать репутацию из callback"""
    if not FEATURES.get("reputation"):
        await query.answer("❌ Система репутации временно отключена", show_alert=True)
        return

    service = ReputationService(session)
    status = await service.get_reputation_status(query.from_user.id)

    buttons = [[InlineKeyboardButton(text=BUTTON_BACK, callback_data=MainMenuCallback(action="profile").pack())]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await query.message.edit_text(status, reply_markup=keyboard)
    await query.answer()