from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.callbacks import *
from config.texts import *
from config.emoji import UI_EMOJI, RARITY_EMOJI, ACTION_EMOJI
from config.character_config import CHARACTERS


def get_character(character_type: str):
    """Получить данные персонажа"""
    return CHARACTERS.get(character_type, CHARACTERS.get("layla"))


def main_menu_kb() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{ACTION_EMOJI['profile']} {BUTTON_PROFILE}",
                callback_data=MainMenuCallback(action="profile").pack()
            ),
            InlineKeyboardButton(
                text=f"{ACTION_EMOJI['farm']} {BUTTON_FARM}",
                callback_data=MainMenuCallback(action="farm").pack()
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{ACTION_EMOJI['battle']} {BUTTON_BATTLE}",
                callback_data=MainMenuCallback(action="battle").pack()
            ),
            InlineKeyboardButton(
                text=f"{ACTION_EMOJI['market']} {BUTTON_MARKET}",
                callback_data=MainMenuCallback(action="market").pack()
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{ACTION_EMOJI['economy']} {BUTTON_ECONOMY}",
                callback_data=MainMenuCallback(action="economy").pack()
            ),
            InlineKeyboardButton(
                text="💰 Собрать доход",
                callback_data=MainMenuCallback(action="collect").pack()
            ),
        ],
        [
            InlineKeyboardButton(
                text="🏆 Рейтинги",
                callback_data=RatingCallback(action="show").pack()
            ),
            InlineKeyboardButton(
                text="🎰 Казино",
                callback_data=MainMenuCallback(action="casino").pack()
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{UI_EMOJI['info']} {BUTTON_HELP}",
                callback_data=MainMenuCallback(action="help").pack()
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def farm_menu_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text="🌱 Мои грядки",
            callback_data=FarmCallback(action="slots").pack()
        )],
        [InlineKeyboardButton(
            text="💧 Полить все",
            callback_data=FarmCallback(action="water_all").pack()
        )],
        [InlineKeyboardButton(
            text=BUTTON_BACK,
            callback_data=MainMenuCallback(action="profile").pack()
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def farm_slots_kb() -> InlineKeyboardMarkup:
    """Клавиатура для выбора грядки"""
    buttons = []
    row = []
    for i in range(1, 10):
        row.append(InlineKeyboardButton(
            text=f"#{i}",
            callback_data=FarmCallback(action="slot", slot_id=i).pack()
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(
        text=BUTTON_BACK,
        callback_data=FarmCallback(action="slots").pack()
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def slot_actions_kb(slot_id: int, has_plant: bool = False, is_adult: bool = False,
                    needs_water: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура действий с грядкой"""
    buttons = []

    if not has_plant:
        buttons.append([InlineKeyboardButton(
            text="🥚 Посадить яйцо (5000💰)",
            callback_data=FarmCallback(action="plant", slot_id=slot_id).pack()
        )])
    else:
        if needs_water:
            buttons.append([InlineKeyboardButton(
                text="💧 Полить (10💰)",
                callback_data=FarmCallback(action="water", slot_id=slot_id).pack()
            )])
        if is_adult:
            buttons.append([InlineKeyboardButton(
                text="🐣 Вылупить",
                callback_data=FarmCallback(action="harvest", slot_id=slot_id).pack()
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text="⏳ Еще растет...",
                callback_data="no_action"
            )])

    buttons.append([InlineKeyboardButton(
        text=BUTTON_BACK,
        callback_data=FarmCallback(action="slots").pack()
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def battle_menu_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=BUTTON_SELECT_TEAM,
            callback_data=BattleCallback(action="select_team").pack()
        )],
        [InlineKeyboardButton(
            text=BUTTON_VIEW_TEAM,
            callback_data=BattleCallback(action="view_team").pack()
        )],
        [
            InlineKeyboardButton(
                text=BUTTON_PVP,
                callback_data=BattleCallback(action="start_pvp").pack()
            ),
            InlineKeyboardButton(
                text=BUTTON_PVE,
                callback_data=BattleCallback(action="start_pve").pack()
            ),
        ],
        [InlineKeyboardButton(
            text=BUTTON_BACK,
            callback_data=MainMenuCallback(action="profile").pack()
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def character_selection_kb(characters: list, selected_ids: list = None) -> InlineKeyboardMarkup:
    """Клавиатура выбора персонажей в команду"""
    if selected_ids is None:
        selected_ids = []

    buttons = []
    for char in characters[:12]:
        char_data = get_character(char.character_type)
        status = "✅" if char.id in selected_ids else "⭕"
        text = f"{status} {RARITY_EMOJI.get(char_data.rarity, '⚪')} {char_data.name} L{char.level}"
        action = "remove" if char.id in selected_ids else "add"

        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=CharacterSelectCallback(action=action, character_id=char.id).pack()
        )])

    buttons.append([InlineKeyboardButton(
        text=BUTTON_BACK,
        callback_data=BattleCallback(action="menu").pack()
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def market_menu_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{UI_EMOJI['search']} {BUTTON_BROWSE}",
            callback_data=MarketCallback(action="list").pack()
        )],
        [InlineKeyboardButton(
            text=f"{UI_EMOJI['coin']} {BUTTON_SELL}",
            callback_data=MarketCallback(action="sell").pack()
        )],
        [InlineKeyboardButton(
            text=f"{UI_EMOJI['star']} {BUTTON_MY_LISTINGS}",
            callback_data=MarketCallback(action="my_listings").pack()
        )],
        [InlineKeyboardButton(
            text=BUTTON_BACK,
            callback_data=MainMenuCallback(action="profile").pack()
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def market_listings_kb(listings: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком объявлений"""
    buttons = []
    for listing in listings[:10]:
        char_data = get_character(listing["character"].character_type)
        text = f"{RARITY_EMOJI.get(char_data.rarity, '⚪')} {char_data.name} L{listing['character'].level} - {listing['price']}💰"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=MarketCallback(action="buy", listing_id=listing["id"]).pack()
        )])
    buttons.append([InlineKeyboardButton(
        text=BUTTON_BACK,
        callback_data=MarketCallback(action="menu").pack()
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def listing_detail_kb(listing_id: int) -> InlineKeyboardMarkup:
    """Клавиатура деталей объявления"""
    buttons = [
        [InlineKeyboardButton(
            text=BUTTON_BUY,
            callback_data=MarketCallback(action="confirm_buy", listing_id=listing_id).pack()
        )],
        [InlineKeyboardButton(
            text=BUTTON_BACK,
            callback_data=MarketCallback(action="list").pack()
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def sell_character_kb(characters: list) -> InlineKeyboardMarkup:
    """Клавиатура выбора персонажа для продажи"""
    buttons = []
    for char in characters[:10]:
        char_data = get_character(char.character_type)
        text = f"{RARITY_EMOJI.get(char_data.rarity, '⚪')} {char_data.name} L{char.level}"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=MarketCallback(action="set_price", character_id=char.id).pack()
        )])
    buttons.append([InlineKeyboardButton(
        text=BUTTON_BACK,
        callback_data=MarketCallback(action="menu").pack()
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def sell_confirm_kb(character_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения продажи"""
    buttons = [
        [
            InlineKeyboardButton(
                text=BUTTON_CONFIRM,
                callback_data=MarketCallback(action="create_listing", character_id=character_id).pack()
            ),
            InlineKeyboardButton(
                text=BUTTON_CANCEL,
                callback_data=MarketCallback(action="menu").pack()
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def my_listings_kb(listings: list) -> InlineKeyboardMarkup:
    """Клавиатура моих объявлений"""
    buttons = []
    for listing in listings[:10]:
        char_data = get_character(listing["character"].character_type)
        text = f"📋 {char_data.name} - {listing['price']}💰"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=MarketCallback(action="cancel_listing", listing_id=listing["id"]).pack()
        )])
    buttons.append([InlineKeyboardButton(
        text=BUTTON_BACK,
        callback_data=MarketCallback(action="menu").pack()
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def economy_menu_kb() -> InlineKeyboardMarkup:
    """Клавиатура меню экономики"""
    buttons = [
        [InlineKeyboardButton(
            text="1️⃣ 💰→💎",
            callback_data=EconomyCallback(action="exchange_coins").pack()
        )],
        [InlineKeyboardButton(
            text="2️⃣ 💰+💎→💠",
            callback_data=EconomyCallback(action="exchange_complex").pack()
        )],
        [InlineKeyboardButton(
            text="3️⃣ 💎→💠",
            callback_data=EconomyCallback(action="exchange_crystals").pack()
        )],
        [InlineKeyboardButton(
            text=BUTTON_BACK,
            callback_data=MainMenuCallback(action="profile").pack()
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_kb(action: str, target_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения обмена"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ ДА, ОБМЕНЯТЬ",
                callback_data=ConfirmCallback(action=action, target_id=target_id).pack()
            ),
            InlineKeyboardButton(
                text="❌ ОТМЕНА",
                callback_data=MainMenuCallback(action="economy").pack()
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rating_menu_kb() -> InlineKeyboardMarkup:
    """Меню выбора категории рейтинга"""
    buttons = [
        [InlineKeyboardButton(text="🏆 По победам", callback_data=RatingCallback(action="wins").pack())],
        [InlineKeyboardButton(text="💰 По богатству", callback_data=RatingCallback(action="wealth").pack())],
        [InlineKeyboardButton(text="👥 По персонажам", callback_data=RatingCallback(action="characters").pack())],
        [InlineKeyboardButton(text="⚔️ По боям", callback_data=RatingCallback(action="battles").pack())],
        [InlineKeyboardButton(text="📈 За неделю", callback_data=RatingCallback(action="weekly").pack())],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data=MainMenuCallback(action="profile").pack())],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def casino_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню казино"""
    buttons = [
        [InlineKeyboardButton(text="🎳 Боулинг (x2)", callback_data="casino_bowling_bet")],
        [InlineKeyboardButton(text="🏀 Баскетбол (x3)", callback_data="casino_basketball_bet")],
        [InlineKeyboardButton(text="🎯 Дартс (x5)", callback_data="casino_darts_bet")],
        [InlineKeyboardButton(text="🎰 Слоты (x10)", callback_data="casino_slots_bet")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data=MainMenuCallback(action="profile").pack())],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def casino_bet_kb(game: str) -> InlineKeyboardMarkup:
    """Клавиатура для ставок в казино"""
    bets = [100, 500, 1000, 5000]
    buttons = []
    row = []
    for bet in bets:
        row.append(InlineKeyboardButton(
            text=f"{bet}💰",
            callback_data=f"{game}_{bet}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(
        text=BUTTON_BACK,
        callback_data="casino_back"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def casino_choice_kb(game: str, bet: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора исхода в казино"""
    if game == "bowling":
        buttons = [
            [
                InlineKeyboardButton(text="🎳 СТРАЙК", callback_data=f"bowling_choice_strike_{bet}"),
                InlineKeyboardButton(text="💔 ПРОМАХ", callback_data=f"bowling_choice_miss_{bet}"),
            ],
            [InlineKeyboardButton(text=BUTTON_BACK, callback_data=f"casino_{game}_bet")],
        ]
    elif game == "basketball":
        buttons = [
            [
                InlineKeyboardButton(text="🏀 ГОЛ", callback_data=f"basketball_choice_score_{bet}"),
                InlineKeyboardButton(text="💔 ПРОМАХ", callback_data=f"basketball_choice_miss_{bet}"),
            ],
            [InlineKeyboardButton(text=BUTTON_BACK, callback_data=f"casino_{game}_bet")],
        ]
    elif game == "darts":
        buttons = [
            [
                InlineKeyboardButton(text="🎯 ЯБЛОЧКО", callback_data=f"darts_choice_bull_{bet}"),
                InlineKeyboardButton(text="💔 ПРОМАХ", callback_data=f"darts_choice_miss_{bet}"),
            ],
            [InlineKeyboardButton(text=BUTTON_BACK, callback_data=f"casino_{game}_bet")],
        ]
    else:
        buttons = [[InlineKeyboardButton(text=BUTTON_BACK, callback_data="casino_back")]]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_menu_kb() -> InlineKeyboardMarkup:
    """Клавиатура админ панели"""
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data=AdminCallback(action="stats").pack())],
        [
            InlineKeyboardButton(text="💰 Выдать", callback_data=AdminCallback(action="give").pack()),
            InlineKeyboardButton(text="💸 Изъять", callback_data=AdminCallback(action="take").pack()),
        ],
        [
            InlineKeyboardButton(text="🔨 Бан", callback_data=AdminCallback(action="ban").pack()),
            InlineKeyboardButton(text="🔓 Разбан", callback_data=AdminCallback(action="unban").pack()),
        ],
        [InlineKeyboardButton(text="📋 Список банов", callback_data=AdminCallback(action="banned_list").pack())],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=MainMenuCallback(action="profile").pack())],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)