from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.core import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)

    coins = Column(Integer, default=5000)
    crystals = Column(Integer, default=0)
    diamonds = Column(Integer, default=0)

    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)

    battle_wins = Column(Integer, default=0)
    battle_losses = Column(Integer, default=0)
    last_battle_time = Column(DateTime, nullable=True)

    reputation = Column(Integer, default=0)

    is_banned = Column(Boolean, default=False)
    ban_reason = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_visit = Column(DateTime, default=datetime.utcnow)
    last_passive_collect = Column(DateTime, nullable=True)

    characters = relationship("Character", back_populates="owner", cascade="all, delete-orphan")
    farm_slots = relationship("FarmSlot", back_populates="owner", cascade="all, delete-orphan")
    battle_history = relationship("BattleLog", back_populates="player", foreign_keys="BattleLog.player_id",
                                  cascade="all, delete-orphan")
    market_listings = relationship("MarketListing", back_populates="seller", cascade="all, delete-orphan")
    economy_logs = relationship("EconomyLog", back_populates="user", cascade="all, delete-orphan")

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    character_type = Column(String(50), nullable=False)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)

    current_hp = Column(Integer)
    max_hp = Column(Integer)
    base_damage = Column(Integer)
    base_armor = Column(Integer)
    base_agility = Column(Integer)
    base_intelligence = Column(Integer)

    is_in_team = Column(Boolean, default=False)
    is_on_farm = Column(Boolean, default=False)
    battle_wins = Column(Integer, default=0)
    battle_losses = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="characters")
    farm_slot = relationship("FarmSlot", back_populates="character", uselist=False)
    market_listing = relationship("MarketListing", back_populates="character", uselist=False)


class FarmSlot(Base):
    __tablename__ = "farm_slots"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    slot_number = Column(Integer, nullable=False)

    growth_stage = Column(String(50), default="seed")
    stage_progress = Column(Float, default=0.0)

    planted_at = Column(DateTime, default=datetime.utcnow)
    last_watered = Column(DateTime, default=datetime.utcnow)
    ready_at = Column(DateTime)

    owner = relationship("User", back_populates="farm_slots")
    character = relationship("Character", back_populates="farm_slot")


class BattleLog(Base):
    __tablename__ = "battle_logs"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    opponent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_pve = Column(Boolean, default=False)
    pve_type = Column(String(50), nullable=True)

    player_won = Column(Boolean, nullable=False)
    player_team = Column(Text)
    opponent_team = Column(Text)

    coins_earned = Column(Integer, default=0)
    crystals_earned = Column(Integer, default=0)

    battle_date = Column(DateTime, default=datetime.utcnow)

    player = relationship("User", back_populates="battle_history", foreign_keys=[player_id])


class MarketListing(Base):
    __tablename__ = "market_listings"

    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)

    price = Column(Integer, nullable=False)
    is_sold = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))

    seller = relationship("User", back_populates="market_listings")
    character = relationship("Character", back_populates="market_listing")


class EconomyLog(Base):
    __tablename__ = "economy_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    transaction_type = Column(String(50), nullable=False)
    give_resource = Column(String(50))
    give_amount = Column(Integer)
    receive_resource = Column(String(50))
    receive_amount = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="economy_logs")


class WeeklyRating(Base):
    __tablename__ = "weekly_ratings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    rating_position = Column(Integer)
    wins_count = Column(Integer, default=0)
    week_start = Column(DateTime, default=datetime.utcnow)
    week_end = Column(DateTime)