from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CharacterData:
    name: str
    rarity: str
    element: str
    base_hp: int
    base_damage: int
    base_armor: int
    base_agility: int
    base_intelligence: int
    special_skill: str


CHARACTERS: Dict[str, CharacterData] = {
    # МИФИЧЕСКИЕ
    "lunox": CharacterData(
        name="🌙 Люнокс", rarity="mythical", element="light",
        base_hp=180, base_damage=65, base_armor=12,
        base_agility=25, base_intelligence=45,
        special_skill="Порядок и Хаос",
    ),
    "julian": CharacterData(
        name="⚔️ Джулиан", rarity="mythical", element="dark",
        base_hp=200, base_damage=70, base_armor=15,
        base_agility=35, base_intelligence=30,
        special_skill="Комбо Клинков",
    ),
    "helcurt": CharacterData(
        name="🦂 Хелкарт", rarity="mythical", element="dark",
        base_hp=175, base_damage=75, base_armor=10,
        base_agility=50, base_intelligence=15,
        special_skill="Тишина",
    ),

    # ЛЕГЕНДАРНЫЕ
    "kadita": CharacterData(
        name="🌊 Кадита", rarity="legendary", element="water",
        base_hp=165, base_damage=60, base_armor=12,
        base_agility=30, base_intelligence=40,
        special_skill="Океанская Воронка",
    ),
    "fredrin": CharacterData(
        name="🦇 Фредрин", rarity="legendary", element="dark",
        base_hp=190, base_damage=58, base_armor=18,
        base_agility=28, base_intelligence=25,
        special_skill="Кровавая Охота",
    ),
    "wanwan": CharacterData(
        name="🏹 Ванван", rarity="legendary", element="air",
        base_hp=155, base_damage=62, base_armor=8,
        base_agility=55, base_intelligence=20,
        special_skill="Тигровый Прыжок",
    ),
    "ling": CharacterData(
        name="🐉 Линг", rarity="legendary", element="air",
        base_hp=170, base_damage=64, base_armor=10,
        base_agility=52, base_intelligence=18,
        special_skill="Горный Сокол",
    ),
    "gusion": CharacterData(
        name="⚔️ Гусион", rarity="legendary", element="light",
        base_hp=168, base_damage=66, base_armor=12,
        base_agility=45, base_intelligence=22,
        special_skill="Мечи Веры",
    ),

    # ЭПИЧЕСКИЕ
    "chou": CharacterData(
        name="🐯 Чоу", rarity="epic", element="fire",
        base_hp=185, base_damage=55, base_armor=16,
        base_agility=40, base_intelligence=15,
        special_skill="Путь Дракона",
    ),
    "lancelot": CharacterData(
        name="🗡️ Ланселот", rarity="epic", element="light",
        base_hp=170, base_damage=58, base_armor=14,
        base_agility=48, base_intelligence=18,
        special_skill="Рыцарский Выпад",
    ),
    "fanny": CharacterData(
        name="🦅 Фанни", rarity="epic", element="air",
        base_hp=150, base_damage=60, base_armor=8,
        base_agility=60, base_intelligence=12,
        special_skill="Стальные Тросы",
    ),
    "alucard": CharacterData(
        name="🧛 Алукард", rarity="epic", element="dark",
        base_hp=190, base_damage=54, base_armor=15,
        base_agility=35, base_intelligence=15,
        special_skill="Вампирский Клинок",
    ),
    "hayabusa": CharacterData(
        name="🥷 Хаябуса", rarity="epic", element="dark",
        base_hp=165, base_damage=56, base_armor=12,
        base_agility=52, base_intelligence=18,
        special_skill="Теневой Удар",
    ),
    "karrie": CharacterData(
        name="⚡ Кэрри", rarity="epic", element="light",
        base_hp=160, base_damage=57, base_armor=10,
        base_agility=48, base_intelligence=20,
        special_skill="Световая Молния",
    ),

    # РЕДКИЕ
    "tigreal": CharacterData(
        name="🛡️ Тигрил", rarity="rare", element="earth",
        base_hp=210, base_damage=45, base_armor=25,
        base_agility=15, base_intelligence=12,
        special_skill="Удар Силой",
    ),
    "akai": CharacterData(
        name="🐼 Акай", rarity="rare", element="earth",
        base_hp=200, base_damage=48, base_armor=22,
        base_agility=25, base_intelligence=14,
        special_skill="Панда-Ураган",
    ),
    "nana": CharacterData(
        name="🐱 Нана", rarity="rare", element="nature",
        base_hp=140, base_damage=52, base_armor=8,
        base_agility=32, base_intelligence=40,
        special_skill="Молли Волшебница",
    ),
    "eudora": CharacterData(
        name="⚡ Эйдора", rarity="rare", element="water",
        base_hp=145, base_damage=50, base_armor=7,
        base_agility=22, base_intelligence=45,
        special_skill="Громовой Удар",
    ),
    "saber": CharacterData(
        name="🗡️ Сабер", rarity="rare", element="dark",
        base_hp=160, base_damage=53, base_armor=14,
        base_agility=38, base_intelligence=16,
        special_skill="Клинок Возмездия",
    ),

    # НЕОБЫЧНЫЕ
    "layla": CharacterData(
        name="🎯 Лейла", rarity="uncommon", element="light",
        base_hp=130, base_damage=48, base_armor=8,
        base_agility=28, base_intelligence=18,
        special_skill="Малефика Снайпер",
    ),
    "miya": CharacterData(
        name="🏹 Мийя", rarity="uncommon", element="light",
        base_hp=135, base_damage=46, base_armor=9,
        base_agility=35, base_intelligence=15,
        special_skill="Стрела Луны",
    ),
    "balmond": CharacterData(
        name="🪓 Бальмонд", rarity="uncommon", element="dark",
        base_hp=180, base_damage=50, base_armor=18,
        base_agility=18, base_intelligence=10,
        special_skill="Кровавая Жатва",
    ),

    # ОБЫЧНЫЕ
    "zilong": CharacterData(
        name="🐉 Зилонг", rarity="common", element="fire",
        base_hp=160, base_damage=42, base_armor=12,
        base_agility=38, base_intelligence=8,
        special_skill="Драконий Удар",
    ),
    "bruno": CharacterData(
        name="⚽ Бруно", rarity="common", element="air",
        base_hp=145, base_damage=44, base_armor=10,
        base_agility=40, base_intelligence=12,
        special_skill="Волшебный Мяч",
    ),
    "rafaela": CharacterData(
        name="✨ Рафаэла", rarity="common", element="light",
        base_hp=125, base_damage=35, base_armor=6,
        base_agility=25, base_intelligence=35,
        special_skill="Святое Благословение",
    ),
}

RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythical"]

RARITY_STAT_MULTIPLIER = {
    "common": 1.0,
    "uncommon": 1.15,
    "rare": 1.35,
    "epic": 1.65,
    "legendary": 2.0,
    "mythical": 2.5,
}


def get_character(char_type: str) -> CharacterData:
    """Получить данные персонажа по ID"""
    return CHARACTERS.get(char_type, CHARACTERS.get("layla"))


def get_all_characters() -> List[str]:
    """Получить список всех ID персонажей"""
    return list(CHARACTERS.keys())


def get_characters_by_rarity(rarity: str) -> List[str]:
    """Получить персонажей по редкости"""
    return [k for k, v in CHARACTERS.items() if v.rarity == rarity]


def get_characters_by_element(element: str) -> List[str]:
    """Получить персонажей по элементу"""
    return [k for k, v in CHARACTERS.items() if v.element == element]