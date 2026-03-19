import random
import json
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.character_repo import CharacterRepository
from database.repository.battle_repo import BattleRepository
from database.repository.user_repo import UserRepository
from database.models import Character
from config.game_config import (
    ELEMENT_ADVANTAGE_MULTIPLIER, ELEMENT_DISADVANTAGE_MULTIPLIER,
    ARENA_REWARD_COINS, ARENA_REWARD_CRYSTALS,
    PVE_REWARD_COINS, PVE_REWARD_CRYSTALS,
    BATTLE_COOLDOWN, EXP_PER_WIN, EXP_PER_LOSS, EXP_FOR_LEVEL_UP,
    PVE_OPPONENTS, RARITY_STAT_MULTIPLIER,
)
from config.character_config import CHARACTERS
from datetime import datetime, timezone


class BattleEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.character_repo = CharacterRepository(session)
        self.battle_repo = BattleRepository(session)
        self.user_repo = UserRepository(session)

    @staticmethod
    def get_character_data(character_type: str):
        """Получить данные персонажа"""
        return CHARACTERS.get(character_type, CHARACTERS.get("forest_sprite"))

    async def start_pvp_battle(self, player_id: int, opponent_id: int = None) -> dict:
        """Начать PvP бой"""
        try:
            cooldown_ok = await self.battle_repo.check_cooldown(player_id, BATTLE_COOLDOWN)
            if not cooldown_ok:
                return {"error": "cooldown", "message": "⏳ Подожди 1 минуту перед следующим боем"}

            player_team = await self.character_repo.get_team(player_id)
            if len(player_team) < 3:
                return {"error": "incomplete_team", "message": "❌ В команде должно быть 3 персонажа"}

            if not opponent_id or opponent_id == 0:
                return await self._create_bot_battle(player_id, player_team, "pvp")

            opponent_team = await self.character_repo.get_team(opponent_id)
            if len(opponent_team) < 3:
                return await self._create_bot_battle(player_id, player_team, "pvp")

            result = await self._simulate_battle(player_team, opponent_team)

            if result["player_won"]:
                coins = ARENA_REWARD_COINS["win"]
                crystals = ARENA_REWARD_CRYSTALS["win"]
                exp = EXP_PER_WIN
            else:
                coins = ARENA_REWARD_COINS["loss"]
                crystals = ARENA_REWARD_CRYSTALS["loss"]
                exp = EXP_PER_LOSS

            player = await self.user_repo.get_by_id(player_id)
            player.coins += coins
            player.crystals += crystals

            if result["player_won"]:
                player.battle_wins += 1
            else:
                player.battle_losses += 1

            player.last_battle_time = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.user_repo.update(player)

            opponent = await self.user_repo.get_by_id(opponent_id)
            if opponent:
                if result["player_won"]:
                    opponent.battle_losses += 1
                else:
                    opponent.battle_wins += 1
                await self.user_repo.update(opponent)

            level_ups = []
            for char in player_team:
                await self.character_repo.add_experience(char.id, exp)
                await self.character_repo.add_battle_record(char.id, result["player_won"])

                if char.experience >= EXP_FOR_LEVEL_UP(char.level):
                    await self.character_repo.level_up(char.id)
                    char_data = self.get_character_data(char.character_type)
                    level_ups.append(f"⬆️ {char_data.name} достиг {char.level + 1} уровня!")

            await self.battle_repo.record_battle(
                player_id=player_id,
                opponent_id=opponent_id if opponent_id and opponent_id != 0 else None,
                player_won=result["player_won"],
                player_team=json.dumps([c.id for c in player_team]),
                opponent_team=json.dumps([c.id for c in opponent_team]) if opponent_id and opponent_id != 0 else "bot",
                coins_earned=coins,
                crystals_earned=crystals,
                is_pve=False
            )

            return {
                "success": True,
                "player_won": result["player_won"],
                "coins": coins,
                "crystals": crystals,
                "level_ups": level_ups,
                "log": result.get("log", [])
            }

        except Exception as e:
            return {"error": "battle_error", "message": f"❌ Ошибка боя: {str(e)}"}

    async def start_pve_battle(self, player_id: int, difficulty: str = "easy") -> dict:
        """Начать PvE бой"""
        try:
            cooldown_ok = await self.battle_repo.check_cooldown(player_id, BATTLE_COOLDOWN)
            if not cooldown_ok:
                return {"error": "cooldown", "message": "⏳ Подожди 1 минуту перед следующим боем"}

            player_team = await self.character_repo.get_team(player_id)
            if len(player_team) < 3:
                return {"error": "incomplete_team", "message": "❌ В команде должно быть 3 персонажа"}

            difficulty_data = PVE_OPPONENTS.get(difficulty, PVE_OPPONENTS["easy"])

            npc_team = self._create_npc_team(difficulty_data)

            result = await self._simulate_battle(player_team, npc_team)

            if result["player_won"]:
                coins = PVE_REWARD_COINS["win"]
                crystals = PVE_REWARD_CRYSTALS["win"]
                exp = EXP_PER_WIN
            else:
                coins = PVE_REWARD_COINS["loss"]
                crystals = PVE_REWARD_CRYSTALS["loss"]
                exp = EXP_PER_LOSS

            if difficulty == "medium":
                coins = int(coins * 1.5)
                crystals = int(crystals * 1.5)
                exp = int(exp * 1.2)
            elif difficulty == "hard":
                coins = coins * 2
                crystals = crystals * 2
                exp = int(exp * 1.5)

            player = await self.user_repo.get_by_id(player_id)
            player.coins += coins
            player.crystals += crystals

            if result["player_won"]:
                player.battle_wins += 1
            else:
                player.battle_losses += 1

            player.last_battle_time = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.user_repo.update(player)

            level_ups = []
            for char in player_team:
                await self.character_repo.add_experience(char.id, exp)
                await self.character_repo.add_battle_record(char.id, result["player_won"])

                if char.experience >= EXP_FOR_LEVEL_UP(char.level):
                    await self.character_repo.level_up(char.id)
                    char_data = self.get_character_data(char.character_type)
                    level_ups.append(f"⬆️ {char_data.name} достиг {char.level + 1} уровня!")

            await self.battle_repo.record_battle(
                player_id=player_id,
                opponent_id=None,
                player_won=result["player_won"],
                player_team=json.dumps([c.id for c in player_team]),
                opponent_team=json.dumps([c.character_type for c in npc_team]),
                coins_earned=coins,
                crystals_earned=crystals,
                is_pve=True,
                pve_type=difficulty
            )

            return {
                "success": True,
                "player_won": result["player_won"],
                "coins": coins,
                "crystals": crystals,
                "level_ups": level_ups,
                "difficulty": difficulty,
                "log": result.get("log", [])
            }

        except Exception as e:
            return {"error": "battle_error", "message": f"❌ Ошибка боя: {str(e)}"}

    async def _create_bot_battle(self, player_id: int, player_team: list, battle_type: str) -> dict:
        """Создать бой с ботом"""
        avg_level = sum(char.level for char in player_team) // 3

        bot_team = []
        for i in range(3):
            char_types = list(CHARACTERS.keys())
            char_type = random.choice(char_types)
            char_data = self.get_character_data(char_type)

            bot_level = max(1, avg_level - 1 + random.randint(-1, 2))

            bot_char = Character(
                owner_id=0,
                character_type=char_type,
                level=bot_level,
                max_hp=int(char_data.base_hp * RARITY_STAT_MULTIPLIER.get(char_data.rarity, 1.0) * (
                            1 + (bot_level - 1) * 0.05)),
                current_hp=int(char_data.base_hp * RARITY_STAT_MULTIPLIER.get(char_data.rarity, 1.0) * (
                            1 + (bot_level - 1) * 0.05)),
                base_damage=int(char_data.base_damage * RARITY_STAT_MULTIPLIER.get(char_data.rarity, 1.0) * (
                            1 + (bot_level - 1) * 0.05)),
                base_armor=int(char_data.base_armor * RARITY_STAT_MULTIPLIER.get(char_data.rarity, 1.0) * (
                            1 + (bot_level - 1) * 0.05)),
                base_agility=int(char_data.base_agility * RARITY_STAT_MULTIPLIER.get(char_data.rarity, 1.0) * (
                            1 + (bot_level - 1) * 0.05)),
                base_intelligence=int(
                    char_data.base_intelligence * RARITY_STAT_MULTIPLIER.get(char_data.rarity, 1.0) * (
                                1 + (bot_level - 1) * 0.05)),
            )
            bot_team.append(bot_char)

        result = await self._simulate_battle(player_team, bot_team)

        if result["player_won"]:
            coins = ARENA_REWARD_COINS["win"]
            crystals = ARENA_REWARD_CRYSTALS["win"]
            exp = EXP_PER_WIN
        else:
            coins = ARENA_REWARD_COINS["loss"]
            crystals = ARENA_REWARD_CRYSTALS["loss"]
            exp = EXP_PER_LOSS

        player = await self.user_repo.get_by_id(player_id)
        player.coins += coins
        player.crystals += crystals

        if result["player_won"]:
            player.battle_wins += 1
        else:
            player.battle_losses += 1

        player.last_battle_time = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.user_repo.update(player)

        level_ups = []
        for char in player_team:
            await self.character_repo.add_experience(char.id, exp)
            await self.character_repo.add_battle_record(char.id, result["player_won"])

            if char.experience >= EXP_FOR_LEVEL_UP(char.level):
                await self.character_repo.level_up(char.id)
                char_data = self.get_character_data(char.character_type)
                level_ups.append(f"⬆️ {char_data.name} достиг {char.level + 1} уровня!")

        return {
            "success": True,
            "player_won": result["player_won"],
            "coins": coins,
            "crystals": crystals,
            "level_ups": level_ups,
            "log": result.get("log", [])
        }

    def _create_npc_team(self, difficulty_data: dict) -> list:
        """Создать команду NPC для PvE"""
        npc_team = []
        char_types = list(CHARACTERS.keys())

        for i in range(3):
            char_type = random.choice(char_types)
            char_data = self.get_character_data(char_type)

            npc_char = Character(
                owner_id=0,
                character_type=char_type,
                level=difficulty_data["level"],
                max_hp=int(
                    char_data.base_hp * difficulty_data["multiplier"] * RARITY_STAT_MULTIPLIER.get(char_data.rarity,
                                                                                                   1.0)),
                current_hp=int(
                    char_data.base_hp * difficulty_data["multiplier"] * RARITY_STAT_MULTIPLIER.get(char_data.rarity,
                                                                                                   1.0)),
                base_damage=int(
                    char_data.base_damage * difficulty_data["multiplier"] * RARITY_STAT_MULTIPLIER.get(char_data.rarity,
                                                                                                       1.0)),
                base_armor=int(
                    char_data.base_armor * difficulty_data["multiplier"] * RARITY_STAT_MULTIPLIER.get(char_data.rarity,
                                                                                                      1.0)),
                base_agility=int(char_data.base_agility * RARITY_STAT_MULTIPLIER.get(char_data.rarity, 1.0)),
                base_intelligence=int(char_data.base_intelligence * RARITY_STAT_MULTIPLIER.get(char_data.rarity, 1.0)),
            )
            npc_team.append(npc_char)

        return npc_team

    async def _simulate_battle(self, team_a: list, team_b: list) -> dict:
        """Симуляция пошагового боя"""
        battle_log = []

        a_chars = []
        for char in team_a:
            a_chars.append({
                "id": char.id,
                "hp": char.current_hp,
                "max_hp": char.max_hp,
                "damage": char.base_damage,
                "armor": char.base_armor,
                "char_type": char.character_type,
                "name": self.get_character_data(char.character_type).name
            })

        b_chars = []
        for char in team_b:
            b_chars.append({
                "id": getattr(char, 'id', 0),
                "hp": char.current_hp if hasattr(char, 'current_hp') else char.get("hp", char.max_hp if hasattr(char,
                                                                                                                'max_hp') else 100),
                "damage": char.base_damage if hasattr(char, 'base_damage') else char.get("damage", 10),
                "armor": char.base_armor if hasattr(char, 'base_armor') else char.get("armor", 5),
                "char_type": char.character_type if hasattr(char, 'character_type') else char.get("char_type",
                                                                                                  "forest_sprite"),
                "name": self.get_character_data(
                    char.character_type if hasattr(char, 'character_type') else char.get("char_type", "forest_sprite")
                ).name
            })

        round_num = 1
        max_rounds = 20

        while a_chars and b_chars and round_num <= max_rounds:
            if a_chars and b_chars:
                attacker = random.choice(a_chars)
                defender = random.choice(b_chars)

                attacker_data = self.get_character_data(attacker["char_type"])
                defender_data = self.get_character_data(defender["char_type"])

                damage = self._calculate_damage(
                    attacker["damage"],
                    attacker_data.element,
                    defender_data.element,
                    defender["armor"]
                )

                defender["hp"] -= damage
                battle_log.append(f"⚔️ Раунд {round_num}: {attacker['name']} наносит {damage} урона {defender['name']}")

                if defender["hp"] <= 0:
                    battle_log.append(f"💀 {defender['name']} повержен!")
                    b_chars.remove(defender)

            if a_chars and b_chars:
                attacker = random.choice(b_chars)
                defender = random.choice(a_chars)

                attacker_data = self.get_character_data(attacker["char_type"])
                defender_data = self.get_character_data(defender["char_type"])

                damage = self._calculate_damage(
                    attacker["damage"],
                    attacker_data.element,
                    defender_data.element,
                    defender["armor"]
                )

                defender["hp"] -= damage
                battle_log.append(f"🛡️ Раунд {round_num}: {attacker['name']} наносит {damage} урона {defender['name']}")

                if defender["hp"] <= 0:
                    battle_log.append(f"💀 {defender['name']} повержен!")
                    a_chars.remove(defender)

            round_num += 1

        player_won = len(a_chars) > 0

        return {
            "player_won": player_won,
            "log": battle_log[-5:],  # Последние 5 действий
            "rounds": round_num - 1,
            "survivors": len(a_chars)
        }

    @staticmethod
    def _calculate_damage(base_damage: int, attacker_element: str, defender_element: str, armor: int) -> int:
        """Рассчитать урон с учетом элементов и брони"""
        element_advantage = {
            "fire": "air",
            "air": "earth",
            "earth": "water",
            "water": "fire"
        }

        multiplier = 1.0

        if element_advantage.get(attacker_element) == defender_element:
            multiplier = ELEMENT_ADVANTAGE_MULTIPLIER  # 1.3
        elif element_advantage.get(defender_element) == attacker_element:
            multiplier = ELEMENT_DISADVANTAGE_MULTIPLIER  # 0.7

        damage = int(base_damage * multiplier * random.uniform(0.9, 1.1))

        damage = max(1, damage - armor // 2)

        return damage