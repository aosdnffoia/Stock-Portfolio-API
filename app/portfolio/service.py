import random
from typing import List
from decimal import Decimal
import hashlib

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.etl.models import Ticker, Price
from app.portfolio.models import PortfolioHolding
from app.portfolio.schemas import PortfolioHoldingOut, PortfolioResponse


DEFAULT_HOLDINGS_COUNT = 5
MIN_QTY = 5
MAX_QTY = 50


def _deterministic_rng(user_id: int) -> random.Random:
    """Create a deterministic RNG based on user_id (stable across runs)."""
    seed_bytes = hashlib.sha256(f"portfolio-{user_id}".encode()).digest()
    seed_int = int.from_bytes(seed_bytes[:8], "big")
    return random.Random(seed_int)


async def _get_priced_tickers(db: AsyncSession) -> List[Ticker]:
    """Return tickers that have at least one price."""
    subq = select(Price.ticker_id).group_by(Price.ticker_id)
    result = await db.execute(select(Ticker).where(Ticker.id.in_(subq)).order_by(Ticker.symbol))
    return result.scalars().all()


async def generate_portfolio(db: AsyncSession, user: User, holdings_count: int = DEFAULT_HOLDINGS_COUNT) -> None:
    """Deterministically generate portfolio holdings for a user."""
    rng = _deterministic_rng(user.id)
    tickers = await _get_priced_tickers(db)
    if not tickers:
        return

    picks = []
    available = tickers.copy()
    for _ in range(min(holdings_count, len(available))):
        idx = rng.randrange(len(available))
        picks.append(available.pop(idx))

    for ticker in picks:
        qty = rng.uniform(MIN_QTY, MAX_QTY)
        holding = PortfolioHolding(
            user_id=user.id,
            ticker_id=ticker.id,
            quantity=Decimal(str(round(qty, 2))),
        )
        db.add(holding)
    await db.commit()


async def get_portfolio(db: AsyncSession, user: User) -> PortfolioResponse:
    """Return portfolio for user, generating deterministically if absent."""
    existing = await db.execute(
        select(PortfolioHolding).where(PortfolioHolding.user_id == user.id)
    )
    holdings = existing.scalars().all()
    if not holdings:
        await generate_portfolio(db, user)
        existing = await db.execute(
            select(PortfolioHolding).where(PortfolioHolding.user_id == user.id)
        )
        holdings = existing.scalars().all()

    if not holdings:
        return PortfolioResponse(holdings=[], totalValue=0.0)

    ticker_ids = [h.ticker_id for h in holdings]

    # Latest prices per ticker
    latest_date_subq = (
        select(Price.ticker_id, func.max(Price.price_date).label("max_date"))
        .where(Price.ticker_id.in_(ticker_ids))
        .group_by(Price.ticker_id)
        .subquery()
    )

    latest_prices_stmt = (
        select(Price, Ticker)
        .join(latest_date_subq, (Price.ticker_id == latest_date_subq.c.ticker_id) & (Price.price_date == latest_date_subq.c.max_date))
        .join(Ticker, Ticker.id == Price.ticker_id)
    )
    price_rows = await db.execute(latest_prices_stmt)
    price_map = {row.Price.ticker_id: row for row in price_rows}

    holdings_out: List[PortfolioHoldingOut] = []
    total_value = 0.0
    for h in holdings:
        row = price_map.get(h.ticker_id)
        if not row:
            continue
        price_obj: Price = row.Price
        ticker_obj: Ticker = row.Ticker
        qty = float(h.quantity)
        price_val = float(price_obj.close)
        value = qty * price_val
        total_value += value
        holdings_out.append(
            PortfolioHoldingOut(
                ticker=ticker_obj.symbol,
                name=ticker_obj.name,
                qty=qty,
                price=price_val,
                dailyChangePct=float(price_obj.change_pct) if price_obj.change_pct is not None else None,
                value=round(value, 2),
            )
        )

    return PortfolioResponse(
        holdings=holdings_out,
        totalValue=round(total_value, 2),
    )
