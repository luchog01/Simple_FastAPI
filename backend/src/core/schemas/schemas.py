from pydantic import BaseModel, Field
from enum import Enum
from typing import List
from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import timezone

# -------------------------------------------------------------------
# DATABASE SCHEMAS
# -------------------------------------------------------------------

def utcnow():
    return datetime.now(timezone.utc)

class UserSession(BaseModel):
    started_at: datetime = Field(default_factory=utcnow)

class User(BaseModel):
    ip: str
    created_at: datetime = Field(default_factory=utcnow)
    last_access: datetime = Field(default_factory=utcnow)
    sessions: List[UserSession] = []

    def new_session(self):
        self.sessions.append(UserSession())
        self.last_access = utcnow()

class Ticker(BaseModel):
    id: int = None # It will be set by the database
    name: str
    funds: dict
    price: int
    type: str

class Fondo(BaseModel):
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

class Period(BaseModel):
    period: PeriodBase = PeriodBase.YEAR

    def delta(self) -> relativedelta:
        return PERIOD_MAP[self.period]
    
class HotColdItem(BaseModel):
    id: int
    name: str
    delta: float
   