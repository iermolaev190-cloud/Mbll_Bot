from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import User
from database.repository.user_repo import UserRepository
from config.features import FEATURES, FEATURE_CONFIG
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class ReputationService:
    """Сервис для работы с репутацией"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    REPUTATION_LEVELS = {
        "low": {"min": 0, "max": 299, "name": "🟡 НОВИЧОК", "desc": "Ты только начинаешь свой путь"},
        "medium": {"min": 300, "max": 699, "name": "🟢 ПОЧЁТНЫЙ ГОСТЬ", "desc": "Тебя уже знают в гильдии"},
        "high": {"min": 700, "max": 1199, "name": "🔵 ГЕРОЙ", "desc": "О тебе слагают легенды"},
        "very_high": {"min": 1200, "max": 9999, "name": "🟣 ЛЕГЕНДА", "desc": "Твоё имя знает каждый!"},
    }

    REPUTATION_ACTIONS = {
        "farm_harvest": {"points": 5, "cooldown": 60},
        "battle_win_pvp": {"points": 20, "cooldown": 300},
        "battle_win_pve": {"points": 10, "cooldown": 300},
        "casino_win": {"points": 15, "cooldown": 60},
        "market_sell": {"points": 8, "cooldown": 60},
        "market_buy": {"points": 5, "cooldown": 60},
        "daily_login": {"points": 3, "cooldown": 86400},
        "help_other": {"points": 10, "cooldown": 3600},
    }

    async def get_reputation(self, user_id: int) -> int:
        """Получить репутацию пользователя"""
        if not FEATURES.get("reputation"):
            return 0

        user = await self.user_repo.get_by_id(user_id)
        return user.reputation if user else 0

    async def get_reputation_level(self, user_id: int) -> Dict:
        """Получить уровень репутации со всеми данными"""
        rep = await self.get_reputation(user_id)

        for level_id, level_data in self.REPUTATION_LEVELS.items():
            if level_data["min"] <= rep <= level_data["max"]:
                return {
                    "level_id": level_id,
                    "name": level_data["name"],
                    "description": level_data["desc"],
                    "reputation": rep,
                    "next_level": level_data["max"] + 1 if level_id != "very_high" else None,
                    "progress": min(100, int((rep - level_data["min"]) / (
                                level_data["max"] - level_data["min"] + 1) * 100)) if level_id != "very_high" else 100
                }

        # На всякий случай
        return {
            "level_id": "low",
            "name": "🟡 НОВИЧОК",
            "description": "Ты только начинаешь свой путь",
            "reputation": rep,
            "next_level": 300,
            "progress": min(100, int(rep / 300 * 100))
        }

    async def add_reputation(self, user_id: int, action: str, target_id: int = None) -> Dict:
        """
        Добавить репутацию за действие
        Возвращает: {"success": bool, "added": int, "new_total": int, "level_up": bool, "message": str}
        """
        if not FEATURES.get("reputation"):
            return {"success": False, "message": "Система репутации отключена"}

        if action not in self.REPUTATION_ACTIONS:
            return {"success": False, "message": "Неизвестное действие"}

        action_data = self.REPUTATION_ACTIONS[action]
        points = action_data["points"]

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден"}

        old_level = await self.get_reputation_level(user_id)

        user.reputation += points
        await self.user_repo.update(user)

        new_level = await self.get_reputation_level(user_id)

        level_up = old_level["level_id"] != new_level["level_id"]

        await self._log_reputation_action(user_id, action, points, target_id)

        return {
            "success": True,
            "added": points,
            "new_total": user.reputation,
            "level_up": level_up,
            "old_level": old_level["name"],
            "new_level": new_level["name"] if level_up else None,
            "message": f"✨ +{points} очков репутации!"
        }

    async def _log_reputation_action(self, user_id: int, action: str, points: int, target_id: int = None):
        """Записать действие в историю (для будущего использования)"""
        print(f"📊 Репутация: user={user_id}, action={action}, points={points}")

    async def get_bonuses(self, user_id: int) -> Dict:
        """Получить бонусы от текущего уровня репутации"""
        level_info = await self.get_reputation_level(user_id)
        level_id = level_info["level_id"]

        bonuses = FEATURE_CONFIG.get("reputation_bonuses", {}).get(level_id, {
            "market_discount": 0,
            "farm_bonus": 0,
            "casino_luck": 0,
            "battle_exp": 0
        })

        if level_id == "medium":
            bonuses["casino_luck"] = 5
        elif level_id == "high":
            bonuses["casino_luck"] = 10
            bonuses["battle_exp"] = 10
        elif level_id == "very_high":
            bonuses["casino_luck"] = 15
            bonuses["battle_exp"] = 20
            bonuses["special_access"] = True

        return bonuses

    async def apply_market_discount(self, user_id: int, price: int) -> int:
        """Применить скидку на рынке"""
        bonuses = await self.get_bonuses(user_id)
        discount = bonuses.get("market_discount", 0)

        if discount > 0:
            discounted = int(price * (100 - discount) / 100)
            return max(1, discounted)
        return price

    async def get_casino_luck_bonus(self, user_id: int) -> float:
        """Получить бонус к удаче в казино (в процентах)"""
        bonuses = await self.get_bonuses(user_id)
        return bonuses.get("casino_luck", 0) / 100  # 5% -> 0.05

    async def get_battle_exp_bonus(self, user_id: int) -> float:
        """Получить бонус к опыту в бою"""
        bonuses = await self.get_bonuses(user_id)
        return bonuses.get("battle_exp", 0) / 100

    async def get_reputation_top(self, limit: int = 10) -> List[Dict]:
        """Получить топ пользователей по репутации"""
        result = await self.session.execute(
            select(User).order_by(User.reputation.desc()).limit(limit)
        )
        users = result.scalars().all()

        top = []
        for user in users:
            level = await self.get_reputation_level(user.id)
            top.append({
                "name": user.first_name or f"Игрок {user.telegram_id}",
                "reputation": user.reputation,
                "level": level["name"]
            })

        return top

    async def get_reputation_status(self, user_id: int) -> str:
        """Получить красивое сообщение о репутации"""
        level_info = await self.get_reputation_level(user_id)
        bonuses = await self.get_bonuses(user_id)

        progress = level_info["progress"]
        bar_length = 10
        filled = int(progress / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        bonus_text = []
        if bonuses.get("market_discount"):
            bonus_text.append(f"💰 Скидка на рынке: {bonuses['market_discount']}%")
        if bonuses.get("farm_bonus"):
            bonus_text.append(f"🌱 Бонус на ферме: +{bonuses['farm_bonus']}%")
        if bonuses.get("casino_luck"):
            bonus_text.append(f"🎰 Удача в казино: +{bonuses['casino_luck']}%")
        if bonuses.get("battle_exp"):
            bonus_text.append(f"⚔️ Бонус опыта: +{bonuses['battle_exp']}%")

        bonuses_str = "\n".join(bonus_text) if bonus_text else "✨ Нет активных бонусов"

        return f"""🏛️ *ГИЛЬДИЯ ГЕРОЕВ*

{level_info['name']}
{level_info['description']}

📊 *Репутация:* {level_info['reputation']}
{bar} {progress}%

🎁 *Твои бонусы:*
{bonuses_str}"""