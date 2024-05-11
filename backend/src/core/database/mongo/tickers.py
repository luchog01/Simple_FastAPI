from . import NotFoundException, AlreadyExistsException, Database
from ...schemas.schemas import Ticker

TICKERS_COLLECTION = "tickers"

class TickersDatabase:
    def __init__(self):
        self.collection = Database.database[TICKERS_COLLECTION]
    
    async def get_next_id(self) -> int:
        last_ticker = await self.collection.find_one(sort=[("id", -1)])
        if not last_ticker:
            return 1
        return last_ticker["id"] + 1

    async def create(self, ticker: Ticker):
        ticker.id = await self.get_next_id()
        if await self.collection.find_one({"name": ticker.name}):
            raise AlreadyExistsException(f"Ticker with name {ticker.name}")

        await self.collection.insert_one(ticker.model_dump())

    async def get(self, id: int) -> Ticker:
        ticker = await self.collection.find_one({"id": id})
        if not ticker:
            raise NotFoundException(f"Ticker with id {id}")
        return Ticker(**ticker)

    async def get_by_name(self, name: str) -> Ticker:
        ticker = await self.collection.find_one({"name": name})
        if not ticker:
            raise NotFoundException(f"Ticker with name {name}")
        return Ticker(**ticker)

    async def get_all(self) -> list[Ticker]:
        return [Ticker(**ticker) async for ticker in self.collection.find()]

    async def update(self, ticker: Ticker):
        if not await self.collection.find_one({"id": ticker.id}):
            raise NotFoundException(f"Ticker with id {ticker.id}")
        await self.collection.update_one({"name": ticker.name}, {"$set": ticker.model_dump()})

    async def delete(self, id: int):
        if not await self.collection.find_one({"id": id}):
            raise NotFoundException(f"Ticker with id {id}")
        await self.collection.delete_one({"id": id})

    async def delete_by_name(self, name: str):
        if not await self.collection.find_one({"name": name}):
            raise NotFoundException(f"Ticker with name {name}")
        await self.collection.delete_one({"name": name})
