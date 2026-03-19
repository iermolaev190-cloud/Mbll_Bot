import random
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository import CharacterRepository, FarmRepository, UserRepository
from config.game_config import HARVEST_RARITY_CHANCE, FARM_SLOTS, PLANT_WATER_INTERVAL
from config.character_config import get_character, CHARACTERS


class FarmService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.character_repo = CharacterRepository(session)
        self.farm_repo = FarmRepository(session)
        self.user_repo = UserRepository(session)

    async def initialize_farm(self, user_id: int):
        await self.farm_repo.create_farm_for_user(user_id)

    def _get_random_rarity(self) -> str:
        """Вернуть случайную редкость по шансам"""
        rand = random.random()
        cumulative = 0
        for rarity, chance in HARVEST_RARITY_CHANCE.items():
            cumulative += chance
            if rand <= cumulative:
                return rarity
        return "common"

    async def get_random_character_type(self) -> str:
        """Получить случайный тип персонажа с учетом редкости"""
        target_rarity = self._get_random_rarity()

        eligible_chars = []
        for char_type, char_data in CHARACTERS.items():
            if char_data.rarity == target_rarity:
                eligible_chars.append(char_type)

        if not eligible_chars:
            eligible_chars = list(CHARACTERS.keys())

        return random.choice(eligible_chars)

    async def plant_on_farm(self, user_id: int, slot_number: int) -> tuple:
        """Посадить семя на ферме"""
        slot = await self.farm_repo.get_slot(user_id, slot_number)
        if not slot:
            return None, "❌ Слот не найден"

        if slot.character_id:
            return None, "❌ Слот уже занят"

        character_type = await self.get_random_character_type()
        character = await self.character_repo.create_character(user_id, character_type, level=1)

        result = await self.farm_repo.plant_seed(user_id, slot_number, character)
        if not result:
            await self.session.delete(character)
            await self.session.commit()
            return None, "❌ Ошибка посадки"

        return result, character

    async def water_plant(self, user_id: int, slot_number: int) -> str:
        """Полить растение"""
        slot = await self.farm_repo.get_slot(user_id, slot_number)
        if not slot or not slot.character_id:
            return "❌ На этой грядке ничего не растет"

        time_since_water = datetime.utcnow() - slot.last_watered
        if time_since_water < PLANT_WATER_INTERVAL:
            return f"⏳ Полив нужен через {int((PLANT_WATER_INTERVAL - time_since_water).total_seconds() / 60)} минут"

        await self.farm_repo.water_plant(user_id, slot_number)
        return "✅ Полито! Следующий полив через 2 часа"

    async def harvest_plant(self, user_id: int, slot_number: int) -> tuple:
        """Собрать урожай"""
        try:
            slot = await self.farm_repo.get_slot(user_id, slot_number)
            if not slot or not slot.character_id:
                return None, "❌ На этой грядке ничего не растет"

            if slot.growth_stage != "adult":
                time_left = max(0, (
                            slot.ready_at - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds() / 3600)
                return None, f"⏳ Еще не готово. Осталось {int(time_left)} часов"

            result = await self.farm_repo.harvest(user_id, slot_number)
            if not result:
                return None, "❌ Ошибка сбора"

            slot, character = result

            character.is_in_team = False
            character.is_on_farm = False
            await self.session.merge(character)
            await self.session.commit()

            return character, "✅ Урожай собран!"
        except Exception as e:
            return None, f"❌ Ошибка: {str(e)}"

    async def get_farm_status(self, user_id: int) -> dict:
        """Получить статус всей фермы"""
        await self.farm_repo.update_farm_growth(user_id)
        slots = await self.farm_repo.get_slots_by_owner(user_id)

        slots_info = []
        for slot in slots:
            slot_info = {
                "slot_number": slot.slot_number,
                "is_occupied": bool(slot.character_id),
                "growth_stage": slot.growth_stage,
                "progress": slot.stage_progress,
                "needs_water": False,
            }

            if slot.character_id:
                character = await self.character_repo.get_by_id(slot.character_id)
                char_data = get_character(character.character_type)
                slot_info["character_name"] = char_data.name
                slot_info["rarity"] = char_data.rarity

                time_since_water = datetime.utcnow() - slot.last_watered
                slot_info["needs_water"] = time_since_water > PLANT_WATER_INTERVAL
                slot_info["last_watered_hours"] = int(time_since_water.total_seconds() / 3600)

                if slot.ready_at:
                    time_left = max(0, (slot.ready_at - datetime.utcnow()).total_seconds() / 3600)
                    slot_info["time_left_hours"] = int(time_left)

            slots_info.append(slot_info)

        return {
            "slots": slots_info,
            "total_slots": FARM_SLOTS,
            "occupied_slots": sum(1 for s in slots_info if s["is_occupied"]),
            "needs_water_slots": sum(1 for s in slots_info if s.get("needs_water", False)),
        }
async def plant_on_farm(self, user_id: int, slot_number: int) -> tuple:
    """Посадить семя на ферме"""
    try:
        slot = await self.farm_repo.get_slot(user_id, slot_number)
        if not slot:
            return "❌ Слот не найден", None

        if slot.character_id:
            return "❌ Слот уже занят", None

        character_type = await self.get_random_character_type()
        character = await self.character_repo.create_character(user_id, character_type, level=1)

        result = await self.farm_repo.plant_seed(user_id, slot_number, character)
        if not result:
            await self.session.delete(character)
            await self.session.commit()
            return "❌ Ошибка посадки", None

        return result, character
    except Exception as e:
        return f"❌ Ошибка: {str(e)}", None


async def water_plant(self, user_id: int, slot_number: int) -> str:
    """Полить растение"""
    try:
        slot = await self.farm_repo.get_slot(user_id, slot_number)
        if not slot or not slot.character_id:
            return "❌ На этой грядке ничего не растет"

        time_since_water = datetime.utcnow() - slot.last_watered
        if time_since_water < PLANT_WATER_INTERVAL:
            hours = (PLANT_WATER_INTERVAL - time_since_water).total_seconds() / 3600
            minutes = int(hours * 60)
            return f"⏳ Полив нужен через {minutes} минут"

        await self.farm_repo.water_plant(user_id, slot_number)
        return "✅ Полито! Следующий полив через 2 часа"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


async def harvest_plant(self, user_id: int, slot_number: int) -> tuple:
    """Собрать урожай"""
    try:
        print(f"🌾 Сбор урожая: пользователь {user_id}, слот {slot_number}")

        slot = await self.farm_repo.get_slot(user_id, slot_number)
        if not slot or not slot.character_id:
            return None, "❌ На этой грядке ничего не растет"

        character = await self.character_repo.get_by_id(slot.character_id)
        if not character:
            return None, "❌ Персонаж не найден"

        print(f"👤 Найден персонаж: ID={character.id}, тип={character.character_type}, владелец={character.owner_id}")

        result = await self.farm_repo.harvest(user_id, slot_number)
        if not result:
            return None, "❌ Ошибка сбора"

        character.is_on_farm = False
        character.is_in_team = False
        await self.character_repo.update(character)

        print(
            f"✅ Персонаж {character.id} собран. Статус: is_on_farm={character.is_on_farm}, is_in_team={character.is_in_team}")

        check_char = await self.character_repo.get_by_id(character.id)
        print(f"🔍 Проверка после сохранения: is_on_farm={check_char.is_on_farm}, owner={check_char.owner_id}")

        return character, "✅ Урожай собран!"
    except Exception as e:
        print(f"❌ Ошибка в harvest_plant: {e}")
        import traceback
        traceback.print_exc()
        return None, f"❌ Ошибка: {str(e)}"