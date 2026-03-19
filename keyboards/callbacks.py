from aiogram.filters.callback_data import CallbackData
from typing import Optional

class MainMenuCallback(CallbackData, prefix="main"):
    action: str  # profile, farm, battle, market, economy, help, casino, collect

class FarmCallback(CallbackData, prefix="farm"):
    action: str  # slots, slot, plant, water, harvest, water_all
    slot_id: Optional[int] = None

class BattleCallback(CallbackData, prefix="battle"):
    action: str  # menu, select_team, view_team, start_pvp, start_pve, start_pve_difficulty
    character_id: Optional[int] = None
    battle_type: Optional[str] = None

class MarketCallback(CallbackData, prefix="market"):
    action: str  # menu, list, buy, sell, my_listings, cancel_listing, confirm_buy, set_price, create_listing
    listing_id: Optional[int] = None
    character_id: Optional[int] = None
    page: int = 1

class EconomyCallback(CallbackData, prefix="economy"):
    action: str  # menu, exchange
    exchange_type: Optional[str] = None

class CharacterSelectCallback(CallbackData, prefix="char"):
    action: str  # add, remove, view
    character_id: int

class ConfirmCallback(CallbackData, prefix="confirm"):
    action: str
    target_id: Optional[int] = None

class AdminCallback(CallbackData, prefix="admin"):
    action: str  # stats, give_item, reset

class RatingCallback(CallbackData, prefix="rating"):
    action: str  # show, wins, wealth, characters, battles, weekly

class CasinoCallback(CallbackData, prefix="casino"):
    action: str  # menu, play, bowling, basketball, darts, slots
    bet: Optional[int] = None