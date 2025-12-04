import asyncio
import logging
from datetime import date
from typing import Iterable, List, Optional

import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.etl.models import Ticker, Price

logger = logging.getLogger(__name__)
FETCH_TIMEOUT_SECONDS = 8.0


def _fetch_symbol(symbol: str) -> Optional[dict]:
    """Fetch recent daily data for a single symbol using yfinance (sync)."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d", interval="1d")
        if hist.empty:
            logger.warning(f"No price history for {symbol}")
            return None

        latest = hist.iloc[-1]
        prev_close = hist.iloc[-2]["Close"] if len(hist) > 1 else None
        change_pct = None
        if prev_close and prev_close != 0:
            change_pct = float((latest["Close"] - prev_close) / prev_close * 100)

        info = ticker.info if hasattr(ticker, "info") else {}

        return {
            "symbol": symbol.upper(),
            "name": info.get("shortName") or info.get("longName"),
            "sector": info.get("sector"),
            "currency": info.get("currency"),
            "exchange": info.get("exchange"),
            "price_date": latest.name.date() if hasattr(latest, "name") else date.today(),
            "open": float(latest.get("Open")) if "Open" in latest else None,
            "high": float(latest.get("High")) if "High" in latest else None,
            "low": float(latest.get("Low")) if "Low" in latest else None,
            "close": float(latest.get("Close")) if "Close" in latest else None,
            "volume": int(latest.get("Volume")) if "Volume" in latest and not latest.isna().get("Volume", False) else None,
            "change_pct": change_pct,
        }
    except Exception as exc:  # pragma: no cover - network errors
        logger.error(f"Failed to fetch {symbol}: {exc}")
        return None


async def _fetch_with_timeout(symbol: str, timeout: float) -> Optional[dict]:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_fetch_symbol, symbol), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching {symbol} after {timeout}s")
        return None


async def fetch_market_data(symbols: Iterable[str], timeout: float = FETCH_TIMEOUT_SECONDS, retries: int = 0) -> List[dict]:
    """Fetch market data concurrently for a list of symbols with simple timeouts/retries."""

    async def fetch_one(sym: str) -> Optional[dict]:
        attempt = 0
        while attempt <= retries:
            result = await _fetch_with_timeout(sym, timeout)
            if result is not None or attempt == retries:
                return result
            attempt += 1
            await asyncio.sleep(0.5)

    tasks = [fetch_one(s) for s in symbols]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r]


async def upsert_ticker(db: AsyncSession, data: dict) -> int:
    """Create or update a ticker record and return its ID."""
    symbol = data["symbol"]
    result = await db.execute(select(Ticker).where(Ticker.symbol == symbol))
    ticker = result.scalar_one_or_none()

    if ticker:
        ticker.name = data.get("name") or ticker.name
        ticker.sector = data.get("sector") or ticker.sector
        ticker.currency = data.get("currency") or ticker.currency
        ticker.exchange = data.get("exchange") or ticker.exchange
        await db.flush()
        return ticker.id

    ticker = Ticker(
        symbol=symbol,
        name=data.get("name"),
        sector=data.get("sector"),
        currency=data.get("currency"),
        exchange=data.get("exchange"),
    )
    db.add(ticker)
    await db.flush()
    return ticker.id


async def upsert_price(db: AsyncSession, ticker_id: int, data: dict) -> None:
    """Insert or update a price row for the given ticker/date."""
    result = await db.execute(
        select(Price).where(
            Price.ticker_id == ticker_id,
            Price.price_date == data["price_date"],
        )
    )
    price = result.scalar_one_or_none()

    if price:
        price.open = data.get("open")
        price.high = data.get("high")
        price.low = data.get("low")
        price.close = data.get("close")
        price.volume = data.get("volume")
        price.change_pct = data.get("change_pct")
        await db.flush()
        return

    price = Price(
        ticker_id=ticker_id,
        price_date=data["price_date"],
        open=data.get("open"),
        high=data.get("high"),
        low=data.get("low"),
        close=data.get("close"),
        volume=data.get("volume"),
        change_pct=data.get("change_pct"),
    )
    db.add(price)
    await db.flush()


async def run_etl(
    db: AsyncSession,
    symbols: Optional[Iterable[str]] = None,
    market_data: Optional[List[dict]] = None,
) -> int:
    """
    Run the ETL job:
    - fetch market data (or use provided market_data)
    - upsert tickers and prices
    Returns count of prices processed.
    """
    tickers = list(symbols) if symbols else settings.ticker_list
    data = market_data or await fetch_market_data(tickers)
    if not data:
        logger.warning("No market data fetched; ETL skipped.")
        return 0

    processed = 0
    for item in data:
        ticker_id = await upsert_ticker(db, item)
        await upsert_price(db, ticker_id, item)
        processed += 1

    await db.commit()
    logger.info(f"ETL complete: processed {processed} price rows.")
    return processed
