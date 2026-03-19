from typing import List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import MarketListing
from database.repository.base import BaseRepository

class MarketRepository(BaseRepository[MarketListing]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MarketListing)

    async def create_listing(self, seller_id: int, character_id: int, price: int) -> MarketListing:
        listing = MarketListing(
            seller_id=seller_id, character_id=character_id, price=price,
            created_at=datetime.utcnow()
        )
        return await self.create(listing)

    async def get_active_listings(self, limit: int = 50) -> List[MarketListing]:
        result = await self.session.execute(
            select(MarketListing).where(MarketListing.is_sold == False)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_seller_listings(self, seller_id: int) -> List[MarketListing]:
        result = await self.session.execute(
            select(MarketListing).where(
                MarketListing.seller_id == seller_id,
                MarketListing.is_sold == False
            )
        )
        return result.scalars().all()

    async def purchase_listing(self, listing_id: int) -> bool:
        listing = await self.get_by_id(listing_id)
        if listing:
            listing.is_sold = True
            await self.update(listing)
            return True
        return False

    async def remove_expired_listings(self):
        result = await self.session.execute(
            select(MarketListing).where(
                MarketListing.expires_at <= datetime.utcnow(),
                MarketListing.is_sold == False
            )
        )
        expired = result.scalars().all()
        for listing in expired:
            await self.session.delete(listing)
        await self.session.commit()