from sqlalchemy.ext.asyncio import AsyncSession
from database.repository.market_repo import MarketRepository
from database.repository.character_repo import CharacterRepository
from database.repository.user_repo import UserRepository
from config.game_config import MARKET_COMMISSION_PERCENT, MIN_MARKET_PRICE, MAX_MARKET_PRICE
from config.character_config import get_character, RARITY_STAT_MULTIPLIER


class MarketService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.market_repo = MarketRepository(session)
        self.character_repo = CharacterRepository(session)
        self.user_repo = UserRepository(session)

    async def create_listing(self, seller_id: int, character_id: int, price: int) -> dict:
        if price < MIN_MARKET_PRICE or price > MAX_MARKET_PRICE:
            return {"error": "invalid_price"}

        character = await self.character_repo.get_by_id(character_id)
        if not character or character.owner_id != seller_id:
            return {"error": "not_found"}

        if character.is_in_team or character.is_on_farm:
            return {"error": "in_use"}

        listing = await self.market_repo.create_listing(seller_id, character_id, price)
        return {"success": True, "listing_id": listing.id}

    async def purchase_listing(self, buyer_id: int, listing_id: int) -> dict:
        listing = await self.market_repo.get_by_id(listing_id)
        if not listing or listing.is_sold:
            return {"error": "not_found"}

        buyer = await self.user_repo.get_by_id(buyer_id)
        seller = await self.user_repo.get_by_id(listing.seller_id)

        if buyer.coins < listing.price:
            return {"error": "insufficient_funds", "need": listing.price, "have": buyer.coins}

        commission = int(listing.price * MARKET_COMMISSION_PERCENT)
        seller_gets = listing.price - commission

        buyer.coins -= listing.price
        seller.coins += seller_gets

        await self.user_repo.update(buyer)
        await self.user_repo.update(seller)

        character = await self.character_repo.get_by_id(listing.character_id)
        character.owner_id = buyer_id
        await self.character_repo.update(character)

        await self.market_repo.purchase_listing(listing_id)

        return {
            "success": True,
            "character_id": character.id,
            "price": listing.price,
            "commission": commission,
        }

    async def get_active_listings(self, limit: int = 50) -> list:
        listings = await self.market_repo.get_active_listings(limit)
        result = []

        for listing in listings:
            character = await self.character_repo.get_by_id(listing.character_id)
            seller = await self.user_repo.get_by_id(listing.seller_id)
            char_data = get_character(character.character_type)

            result.append({
                "id": listing.id,
                "character": character,
                "character_name": char_data.name,
                "rarity": char_data.rarity,
                "element": char_data.element,
                "level": character.level,
                "price": listing.price,
                "seller_name": seller.first_name or f"Player {seller.telegram_id}",
            })

        return result

    async def get_seller_listings(self, seller_id: int) -> list:
        """Получить активные объявления продавца"""
        listings = await self.market_repo.get_seller_listings(seller_id)
        result = []

        for listing in listings:
            character = await self.character_repo.get_by_id(listing.character_id)
            if not character:
                continue

            char_data = get_character(character.character_type)
            result.append({
                "id": listing.id,
                "character": character,
                "character_name": char_data.name,
                "rarity": char_data.rarity,
                "level": character.level,
                "price": listing.price,
                "created_at": listing.created_at,
            })

        return result

    async def get_recommended_price(self, character_type: str, level: int) -> int:
        char_data = get_character(character_type)

        base_price = 1000
        rarity_mult = RARITY_STAT_MULTIPLIER.get(char_data.rarity, 1.0)
        level_mult = 1.0 + (level - 1) * 0.1

        price = int(base_price * rarity_mult * level_mult)
        return max(MIN_MARKET_PRICE, min(MAX_MARKET_PRICE, price))

    async def cancel_listing(self, seller_id: int, listing_id: int) -> dict:
        listing = await self.market_repo.get_by_id(listing_id)
        if not listing or listing.seller_id != seller_id or listing.is_sold:
            return {"error": "cannot_cancel"}

        await self.session.delete(listing)
        await self.session.commit()

        return {"success": True}
