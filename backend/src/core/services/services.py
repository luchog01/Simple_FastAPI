from ..schemas import schemas as _schemas
from typing import List
from ..database.mongo.tickers import UserDatabase


def get_db():
    db = UserDatabase()
    try:
        yield db
    finally:
        del db


async def get_ticker(db: UserDatabase, id: int):
    return await db.get(id)


async def get_ticker_by_name(db: UserDatabase, name: str):
    return await db.get_by_name(name)


async def get_tickers(db: UserDatabase) -> List[_schemas.Ticker]:
    return await db.get_all()


async def create_ticker(db: UserDatabase, ticker: _schemas.Ticker):
    return await db.create(ticker)

async def update_ticker(db: UserDatabase, ticker: _schemas.Ticker):
    return await db.update(ticker)

async def delete_ticker_by_name(db: UserDatabase, name: str):
    return await db.delete_by_name(name)
