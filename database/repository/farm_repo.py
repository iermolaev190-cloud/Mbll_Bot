from typing import Optional, List, Sequence
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import FarmSlot, Character
from database.repository.base import BaseRepository
from config.game_config import PLANT_GROWTH_STAGES, FARM_SLOTS, PLANT_WATER_INTERVAL

class FarmRepository(BaseRepository[FarmSlot]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FarmSlot)

    async def get_slots_by_owner(self, owner_id: int) -> Sequence[FarmSlot]:
        result = await self.session.execute(
            select(FarmSlot).where(FarmSlot.owner_id == owner_id).order_by(FarmSlot.slot_number)
        )
        return result.scalars().all()

    async def get_slot(self, owner_id: int, slot_number: int) -> Optional[FarmSlot]:
        result = await self.session.execute(
            select(FarmSlot).where(
                FarmSlot.owner_id == owner_id,
                FarmSlot.slot_number == slot_number
            )
        )
        return result.scalars().first()

    async def create_farm_for_user(self, owner_id: int):
        for slot_num in range(1, FARM_SLOTS + 1):
            slot = FarmSlot(owner_id=owner_id, slot_number=slot_num)
            await self.create(slot)

    async def plant_seed(self, owner_id: int, slot_number: int, character: Character) -> Optional[FarmSlot]:
        slot = await self.get_slot(owner_id, slot_number)
        if slot and not slot.character_id:
            slot.character_id = character.id
            slot.growth_stage = "seed"
            slot.stage_progress = 0.0
            slot.planted_at = datetime.utcnow()
            slot.last_watered = datetime.utcnow()

            total_hours = sum(
                PLANT_GROWTH_STAGES[stage]["duration"].total_seconds() / 3600
                for stage in ["seed", "sprout", "teenager"]
            )
            slot.ready_at = datetime.utcnow() + timedelta(hours=total_hours)

            character.is_on_farm = True
            await self.session.merge(character)

            return await self.update(slot)
        return None

    async def water_plant(self, owner_id: int, slot_number: int) -> Optional[FarmSlot]:
        slot = await self.get_slot(owner_id, slot_number)
        if slot:
            slot.last_watered = datetime.utcnow()
            return await self.update(slot)
        return None

    async def harvest(self, owner_id: int, slot_number: int) -> Optional[tuple]:
        """Собрать урожай - возвращает (slot, character)"""
        try:
            print(f"🌾 farm_repo.harvest: owner={owner_id}, slot={slot_number}")

            slot = await self.get_slot(owner_id, slot_number)
            if slot and slot.character_id:
                char_id = slot.character_id
                print(f"   Найден character_id={char_id}")

                char = await self.session.get(Character, char_id)
                if char:
                    print(f"   Персонаж: {char.character_type}, owner={char.owner_id}")

                    # Очищаем слот
                    slot.character_id = None
                    slot.growth_stage = "seed"
                    slot.stage_progress = 0.0
                    await self.update(slot)
                    print(f"   Слот очищен")


                    return slot, char
            print(f"   Ничего не найдено")
            return None
        except Exception as e:
            print(f"❌ Ошибка в harvest: {e}")
            return None

    async def get_slots_needing_water(self, owner_id: int) -> List[FarmSlot]:
        slots = await self.get_slots_by_owner(owner_id)
        now = datetime.utcnow()
        return [s for s in slots if s.character_id and (now - s.last_watered) > PLANT_WATER_INTERVAL]

    async def update_farm_growth(self, owner_id: int):
        slots = await self.get_slots_by_owner(owner_id)
        now = datetime.utcnow()

        for slot in slots:
            if not slot.character_id:
                continue

            time_passed = (now - slot.planted_at).total_seconds()
            current_stage = slot.growth_stage
            stage_data = PLANT_GROWTH_STAGES.get(current_stage)

            if not stage_data:
                continue

            stage_duration = stage_data["duration"].total_seconds()

            if time_passed >= stage_duration:
                stages = list(PLANT_GROWTH_STAGES.keys())
                current_idx = stages.index(current_stage)

                if current_idx < len(stages) - 1:
                    slot.growth_stage = stages[current_idx + 1]
                    slot.stage_progress = 0.0
                else:
                    slot.growth_stage = "adult"
                    slot.stage_progress = 100.0

                await self.update(slot)
            else:
                progress = (time_passed / stage_duration) * 100
                slot.stage_progress = min(progress, 100.0)
                await self.update(slot)