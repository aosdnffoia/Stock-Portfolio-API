from typing import List
from pydantic import BaseModel


class PortfolioHoldingOut(BaseModel):
    ticker: str
    name: str | None = None
    qty: float
    price: float
    dailyChangePct: float | None = None
    value: float


class PortfolioResponse(BaseModel):
    holdings: List[PortfolioHoldingOut]
    totalValue: float
