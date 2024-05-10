from typing import List
from ..database.mongo.tickers import UserDatabase
from ..schemas.schemas import HotColdItem
from ..services import services as db_services

async def get_hot_cold_items(db: UserDatabase, ignore: list = []) -> List[HotColdItem]:
    tickers = await db_services.get_tickers(db=db)
    tickers = [ticker for ticker in tickers if ticker.name not in ignore]
    items = []
    for ticker in tickers:
        if len(ticker.funds["total"]["qty"]) > 2:
            prev_week_qty = ticker.funds["total"]["qty"][-2]
            this_week_qty = ticker.funds["total"]["qty"][-1]
            delta = (this_week_qty - prev_week_qty) / (prev_week_qty) if prev_week_qty else 0
            items.append(
                HotColdItem(
                    id=ticker.id,
                    name=ticker.name,
                    delta=delta,
                )
            )
    return items

async def get_hots(db: UserDatabase, limit: int = 5, ignore: list = []) -> List[HotColdItem]:
    items = await get_hot_cold_items(db, ignore)
    sorted_items = sorted(items, key=lambda x: x.delta, reverse=True)
    return sorted_items[:limit]

async def get_colds(db: UserDatabase, limit: int = 5, ignore: list = []) -> List[HotColdItem]:
    items = await get_hot_cold_items(db, ignore)
    sorted_items = sorted(items, key=lambda x: x.delta)
    return sorted_items[:limit]
    
