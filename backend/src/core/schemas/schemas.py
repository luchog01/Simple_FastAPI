import pydantic as _pydantic
from pydantic import BaseModel
from enum import Enum
from dateutil.relativedelta import relativedelta

# -------------------------------------------------------------------
# DATABASE SCHEMAS
# -------------------------------------------------------------------

class Ticker(_pydantic.BaseModel):
    id: int = None # It will be set by the database
    name: str
    funds: dict
    price: int
    type: str

class Fondo(_pydantic.BaseModel):
    id: int
    name: str
    tickers: dict
    patrimony: int
    type: str

# -------------------------------------------------------------------
# BASIC SCHEMAS
# -------------------------------------------------------------------

class ticker_in_FCI_SCH(BaseModel):
    ticker: str
    fci: str

class PeriodBase(Enum):
    MONTH = "month"
    THREE_MONTHS = "three_months"
    SIX_MONTHS = "six_months"
    YEAR = "year"
    ALL = "all"

PERIOD_MAP = {
    PeriodBase.MONTH: relativedelta(months=1),
    PeriodBase.THREE_MONTHS: relativedelta(months=3),
    PeriodBase.SIX_MONTHS: relativedelta(months=6),
    PeriodBase.YEAR: relativedelta(years=1),
    PeriodBase.ALL: relativedelta(years=1000),
}

class Period(_pydantic.BaseModel):
    period: PeriodBase = PeriodBase.YEAR

    def delta(self) -> relativedelta:
        return PERIOD_MAP[self.period]
    
class HotColdItem(_pydantic.BaseModel):
    id: int
    name: str
    delta: float
   