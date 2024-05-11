import sqlalchemy as _sql
from ..database import database as _database


class Ticker(_database.Base):
    __tablename__ = "tickers"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, index=True, default="")
    funds = _sql.Column(_sql.JSON, default={})
    price = _sql.Column(_sql.Integer, default=-1)
    type = _sql.Column(_sql.String, default="")


class Funds(_database.Base):
    __tablename__ = "funds"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, index=True, default="")
    tickers = _sql.Column(_sql.JSON, default={})
    patrimony = _sql.Column(_sql.Integer, default=-1)
    type = _sql.Column(_sql.String, default="")
    