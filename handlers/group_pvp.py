import logging
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.user_repo import UserRepository
from database.repository.character_repo import CharacterRepository
from services.battle_engine import BattleEngine
from services.farm_service import FarmService

logger = logging.getLogger(__name__)
router = Router()

active_duels = {}

async def get_user_or_create(session: AsyncSession, user_id: int, username: str = None, first_name: str = None):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(user_id)
    if not user:
        try:
            user = await user_repo.get_or_create(user_id, username, first_name)
            if user:
                farm_service = FarmService(session)
                await farm_service.initialize_farm(user.id)
                char_repo = CharacterRepository(session)
                await char_repo.create_character(user.id, "layla", level=1)
                await session.commit()
        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя {user_id}: {e}")
            return None
    return user

@router.message(Command("pvp"))
@router.message(Command("fight"))
async def start_pvp_duel(message: Message, session: AsyncSession):
    if message.chat.type == "private":
        await message.answer("⚔️ *PvP дуэли* доступны только в группах!\n\nИспользуйте `/pvp @username` чтобы вызвать соперника.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ *Укажи соперника!*\n\nПример: `/pvp @username`")
        return
    
    target = args[1].strip()
    if target.startswith("@"):
        target = target[1:]
    
    user_repo = UserRepository(session)
    char_repo = CharacterRepository(session)
    
    attacker = await get_user_or_create(session, message.from_user.id, message.from_user.username, message.from_user.first_name)
    if not attacker:
        await message.answer("❌ Ошибка: не удалось создать профиль")
        return
    
    attacker_team = await char_repo.get_team(attacker.id)
    if len(attacker_team) < 3:
        await message.answer(f"❌ В твоей команде {len(attacker_team)}/3 персонажей. Нужно 3!")
        return
    
    defender = None
    try:
        async for member in message.chat.get_members():
            if member.user.is_bot:
                continue
            if (member.user.username and member.user.username.lower() == target.lower()) or \
               (member.user.first_name and member.user.first_name.lower() == target.lower()) or \
               str(member.user.id) == target:
                defender = await get_user_or_create(session, member.user.id, member.user.username, member.user.first_name)
                break
    except Exception as e:
        await message.answer(f"❌ Ошибка при поиске участника: {e}")
        return
    
    if not defender or defender.id == attacker.id:
        await message.answer(f"❌ Игрок {target} не найден или не играет в бота!")
        return
    
    defender_team = await char_repo.get_team(defender.id)
    if len(defender_team) < 3:
        await message.answer(f"❌ У {defender.first_name} нет полной команды (3 персонажа)!")
        return
    
    duel_id = f"{message.chat.id}_{attacker.id}_{defender.id}"
    active_duels[duel_id] = {
        "attacker": attacker.id,
        "defender": defender.id,
        "chat_id": message.chat.id,
        "status": "waiting",
        "message_id": None
    }
    
    buttons = [
        [
            InlineKeyboardButton(text="⚔️ ПРИНЯТЬ БОЙ", callback_data=f"duel_accept_{duel_id}"),
            InlineKeyboardButton(text="❌ ОТКАЗАТЬСЯ", callback_data=f"duel_decline_{duel_id}"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    sent_msg = await message.answer(
        f"⚔️ *ДУЭЛЬ!*\n\n{attacker.first_name} вызывает {defender.first_name} на бой!\n\n{defender.first_name}, прими вызов!",
        reply_markup=keyboard
    )
    active_duels[duel_id]["message_id"] = sent_msg.message_id

@router.callback_query(F.data.startswith("duel_accept_"))
async def accept_duel(query: CallbackQuery, session: AsyncSession):
    duel_id = query.data.replace("duel_accept_", "")
    duel = active_duels.get(duel_id)
    
    if not duel:
        await query.answer("❌ Дуэль уже неактивна!", show_alert=True)
        return
    
    if duel["status"] != "waiting":
        await query.answer("❌ Дуэль уже завершена!", show_alert=True)
        return
    
    if query.from_user.id != duel["defender"]:
        await query.answer("❌ Ты не тот, кого вызывали!", show_alert=True)
        return
    
    duel["status"] = "accepted"
    await query.answer("⚔️ БОЙ НАЧИНАЕТСЯ!")
    
    await query.message.edit_text("⚔️ *БОЙ ИДЁТ...*")
    
    battle_engine = BattleEngine(session)
    result = await battle_engine.start_pvp_battle(duel["attacker"], duel["defender"])
    
    if "error" in result:
        await query.message.edit_text(f"❌ Ошибка боя: {result.get('message', 'Неизвестная ошибка')}")
        del active_duels[duel_id]
        return
    
    attacker_repo = UserRepository(session)
    defender_repo = UserRepository(session)
    
    attacker = await attacker_repo.get_by_id(duel["attacker"])
    defender = await defender_repo.get_by_id(duel["defender"])
    
    if result["player_won"]:
        winner = attacker
        loser = defender
        winner_name = attacker.first_name
        loser_name = defender.first_name
    else:
        winner = defender
        loser = attacker
        winner_name = defender.first_name
        loser_name = attacker.first_name
    
    msg = f"""⚔️ *РЕЗУЛЬТАТ ДУЭЛИ* ⚔️

🏆 *ПОБЕДИТЕЛЬ:* {winner_name}
💀 *ПРОИГРАВШИЙ:* {loser_name}

💰 Награда победителю: +{result['coins']} монет
💎 Кристаллы: +{result['crystals']}

📈 Опыт начислен всем персонажам!"""
    
    if result.get("level_ups"):
        msg += "\n\n📈 *Повышение уровня:*\n" + "\n".join(result["level_ups"])
    
    await query.message.edit_text(msg)
    
    del active_duels[duel_id]

@router.callback_query(F.data.startswith("duel_decline_"))
async def decline_duel(query: CallbackQuery, session: AsyncSession):
    duel_id = query.data.replace("duel_decline_", "")
    duel = active_duels.get(duel_id)
    
    if not duel:
        await query.answer("❌ Дуэль уже неактивна!", show_alert=True)
        return
    
    if query.from_user.id != duel["defender"]:
        await query.answer("❌ Ты не тот, кого вызывали!", show_alert=True)
        return
    
    attacker_repo = UserRepository(session)
    attacker = await attacker_repo.get_by_id(duel["attacker"])
    
    await query.message.edit_text(
        f"❌ *ДУЭЛЬ ОТМЕНЕНА*\n\n{attacker.first_name} вызывал {query.from_user.first_name} на бой, но тот отказался."
    )
    
    del active_duels[duel_id]
    await query.answer("❌ Дуэль отклонена")
