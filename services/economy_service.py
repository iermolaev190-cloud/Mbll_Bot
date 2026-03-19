from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.user_repo import UserRepository
from database.repository.economy_repo import EconomyRepository
from config.game_config import EXCHANGE_RATES


class EconomyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.economy_repo = EconomyRepository(session)

    async def exchange_coins_to_crystals(self, user_id: int, amount: int = 1) -> Dict:
        """
        Обмен монет на кристаллы
        :param user_id: ID пользователя
        :param amount: количество кристаллов для получения
        :return: dict с результатом
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"error": "not_found", "message": "❌ Пользователь не найден"}

        rate = EXCHANGE_RATES["coins_to_crystals"]
        required_coins = amount * rate

        if user.coins < required_coins:
            return {
                "error": "insufficient_coins",
                "need": required_coins,
                "have": user.coins,
                "message": f"❌ Недостаточно монет!\n"
                           f"💰 Нужно: {required_coins:,}\n"
                           f"💵 Есть: {user.coins:,}"
            }

        user.coins -= required_coins
        user.crystals += amount
        await self.user_repo.update(user)

        await self.economy_repo.record_transaction(
            user_id,
            "exchange_coins_to_crystals",
            "coins", required_coins,
            "crystals", amount
        )

        return {
            "success": True,
            "coins": user.coins,
            "crystals": user.crystals,
            "diamonds": user.diamonds,
            "message": f"✅ Обмен выполнен!\n"
                       f"💸 Отдано: {required_coins:,}💰\n"
                       f"✨ Получено: {amount}💎"
        }

    async def exchange_coins_crystals_to_diamond(self, user_id: int) -> Dict:
        """
        Сложный обмен: монеты + кристаллы → алмаз
        Только по 1 алмазу за раз!
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"error": "not_found", "message": "❌ Пользователь не найден"}

        required = EXCHANGE_RATES["coins_and_crystals_to_diamond"]
        required_coins = required["coins"]
        required_crystals = required["crystals"]

        if user.coins < required_coins or user.crystals < required_crystals:
            return {
                "error": "insufficient",
                "need_coins": required_coins,
                "need_crystals": required_crystals,
                "have_coins": user.coins,
                "have_crystals": user.crystals,
                "message": f"❌ Недостаточно ресурсов!\n"
                           f"💰 Нужно монет: {required_coins:,} (есть: {user.coins:,})\n"
                           f"💎 Нужно кристаллов: {required_crystals} (есть: {user.crystals})"
            }

        user.coins -= required_coins
        user.crystals -= required_crystals
        user.diamonds += 1
        await self.user_repo.update(user)

        await self.economy_repo.record_transaction(
            user_id,
            "exchange_coins_crystals_to_diamond",
            "coins_crystals", required_coins,
            "diamond", 1
        )

        return {
            "success": True,
            "coins": user.coins,
            "crystals": user.crystals,
            "diamonds": user.diamonds,
            "message": f"✅ *АЛМАЗ ПОЛУЧЕН!*\n\n"
                       f"💸 Отдано: {required_coins:,}💰 + {required_crystals}💎\n"
                       f"💠 Получено: 1💠"
        }

    async def exchange_crystals_to_diamonds(self, user_id: int, amount: int = 1) -> Dict:
        """
        Обмен кристаллов на алмазы
        :param user_id: ID пользователя
        :param amount: количество алмазов для получения
        :return: dict с результатом
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"error": "not_found", "message": "❌ Пользователь не найден"}

        rate = EXCHANGE_RATES["crystals_to_diamonds"]
        required_crystals = amount * rate

        if user.crystals < required_crystals:
            return {
                "error": "insufficient_crystals",
                "need": required_crystals,
                "have": user.crystals,
                "message": f"❌ Недостаточно кристаллов!\n"
                           f"💎 Нужно: {required_crystals}\n"
                           f"✨ Есть: {user.crystals}"
            }

        user.crystals -= required_crystals
        user.diamonds += amount
        await self.user_repo.update(user)

        await self.economy_repo.record_transaction(
            user_id,
            "exchange_crystals_to_diamonds",
            "crystals", required_crystals,
            "diamonds", amount
        )

        return {
            "success": True,
            "coins": user.coins,
            "crystals": user.crystals,
            "diamonds": user.diamonds,
            "message": f"✅ Обмен выполнен!\n"
                       f"💎 Отдано: {required_crystals}💎\n"
                       f"💠 Получено: {amount}💠"
        }

    async def get_balance(self, user_id: int) -> Optional[Dict]:
        """
        Получить баланс пользователя
        Возвращает словарь с балансом или None, если пользователь не найден
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None

        return {
            "coins": user.coins,
            "crystals": user.crystals,
            "diamonds": user.diamonds,
            "total_coins": user.coins,
            "total_crystals": user.crystals,
            "total_diamonds": user.diamonds,
        }

    async def check_exchange_possible(self, user_id: int, exchange_type: str, amount: int = 1) -> Dict:
        """
        Проверить, возможен ли обмен (без выполнения)
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"possible": False, "message": "❌ Пользователь не найден"}

        if exchange_type == "coins_to_crystals":
            rate = EXCHANGE_RATES["coins_to_crystals"]
            needed = amount * rate
            if user.coins >= needed:
                return {
                    "possible": True,
                    "needed": needed,
                    "have": user.coins,
                    "message": f"✅ Можно обменять {amount}💎 за {needed:,}💰"
                }
            else:
                return {
                    "possible": False,
                    "needed": needed,
                    "have": user.coins,
                    "message": f"❌ Нужно {needed:,}💰, есть {user.coins:,}💰"
                }

        elif exchange_type == "coins_crystals_to_diamond":
            required = EXCHANGE_RATES["coins_and_crystals_to_diamond"]
            if user.coins >= required["coins"] and user.crystals >= required["crystals"]:
                return {
                    "possible": True,
                    "needed_coins": required["coins"],
                    "needed_crystals": required["crystals"],
                    "message": f"✅ Можно получить 1💠"
                }
            else:
                return {
                    "possible": False,
                    "needed_coins": required["coins"],
                    "needed_crystals": required["crystals"],
                    "message": f"❌ Нужно {required['coins']:,}💰 + {required['crystals']}💎"
                }

        elif exchange_type == "crystals_to_diamonds":
            rate = EXCHANGE_RATES["crystals_to_diamonds"]
            needed = amount * rate
            if user.crystals >= needed:
                return {
                    "possible": True,
                    "needed": needed,
                    "have": user.crystals,
                    "message": f"✅ Можно обменять {amount}💠 за {needed}💎"
                }
            else:
                return {
                    "possible": False,
                    "needed": needed,
                    "have": user.crystals,
                    "message": f"❌ Нужно {needed}💎, есть {user.crystals}💎"
                }

        return {"possible": False, "message": "❌ Неизвестный тип обмена"}

    async def get_exchange_rates(self) -> Dict:
        """
        Получить текущие курсы обмена
        """
        return {
            "coins_to_crystals": {
                "rate": EXCHANGE_RATES["coins_to_crystals"],
                "description": f"1💎 = {EXCHANGE_RATES['coins_to_crystals']:,}💰"
            },
            "coins_and_crystals_to_diamond": {
                "coins": EXCHANGE_RATES["coins_and_crystals_to_diamond"]["coins"],
                "crystals": EXCHANGE_RATES["coins_and_crystals_to_diamond"]["crystals"],
                "description": f"1💠 = {EXCHANGE_RATES['coins_and_crystals_to_diamond']['coins']:,}💰 + {EXCHANGE_RATES['coins_and_crystals_to_diamond']['crystals']}💎"
            },
            "crystals_to_diamonds": {
                "rate": EXCHANGE_RATES["crystals_to_diamonds"],
                "description": f"1💠 = {EXCHANGE_RATES['crystals_to_diamonds']}💎"
            }
        }

    async def get_transaction_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Получить историю обменов пользователя
        """
        logs = await self.economy_repo.get_user_transactions(user_id, limit)
        history = []

        for log in logs:
            history.append({
                "id": log.id,
                "type": log.transaction_type,
                "gave": f"{log.give_amount} {log.give_resource}" if log.give_resource else None,
                "got": f"{log.receive_amount} {log.receive_resource}" if log.receive_resource else None,
                "date": log.created_at.strftime("%d.%m.%Y %H:%M")
            })

        return history