from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base
from app.etl.service import run_etl
from app.etl.models import Ticker, Price

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session_factory():
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield SessionLocal

    await engine.dispose()


async def fetch_prices(session_factory):
    async with session_factory() as session:
        tickers = (await session.execute(Ticker.__table__.select())).all()
        prices = (await session.execute(Price.__table__.select())).all()
    return tickers, prices


@pytest.mark.asyncio
async def test_run_etl_inserts_tickers_and_prices(session_factory):
    stub_data = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "currency": "USD",
            "exchange": "NASDAQ",
            "price_date": date(2024, 1, 1),
            "open": 100.0,
            "high": 110.0,
            "low": 99.0,
            "close": 105.0,
            "volume": 1_000_000,
            "change_pct": 5.0,
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft Corp.",
            "sector": "Technology",
            "currency": "USD",
            "exchange": "NASDAQ",
            "price_date": date(2024, 1, 1),
            "open": 200.0,
            "high": 210.0,
            "low": 195.0,
            "close": 205.0,
            "volume": 2_000_000,
            "change_pct": 2.5,
        },
    ]

    async with session_factory() as session:
        processed = await run_etl(session, market_data=stub_data)
        await session.commit()

    assert processed == 2

    async with session_factory() as session:
        tickers = (await session.execute(Ticker.__table__.select())).all()
        prices = (await session.execute(Price.__table__.select())).all()

    assert len(tickers) == 2
    assert len(prices) == 2


@pytest.mark.asyncio
async def test_run_etl_updates_existing_price(session_factory):
    stub_data = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "currency": "USD",
            "exchange": "NASDAQ",
            "price_date": date(2024, 1, 1),
            "open": 100.0,
            "high": 110.0,
            "low": 99.0,
            "close": 105.0,
            "volume": 1_000_000,
            "change_pct": 5.0,
        }
    ]
    updated_data = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "currency": "USD",
            "exchange": "NASDAQ",
            "price_date": date(2024, 1, 1),
            "open": 101.0,
            "high": 111.0,
            "low": 98.0,
            "close": 104.0,
            "volume": 1_500_000,
            "change_pct": 4.0,
        }
    ]

    async with session_factory() as session:
        await run_etl(session, market_data=stub_data)
        await run_etl(session, market_data=updated_data)
        await session.commit()

    async with session_factory() as session:
        result = await session.execute(
            select(Price).where(Price.price_date == date(2024, 1, 1))
        )
        price = result.scalars().first()

    assert price is not None
    assert float(price.close) == 104.0
    assert price.volume == 1_500_000


@pytest.mark.asyncio
async def test_run_etl_no_data_returns_zero_and_writes_nothing(session_factory):
    async with session_factory() as session:
        processed = await run_etl(session, market_data=[])
        await session.commit()

    assert processed == 0

    async with session_factory() as session:
        tickers = (await session.execute(Ticker.__table__.select())).all()
        prices = (await session.execute(Price.__table__.select())).all()

    assert tickers == []
    assert prices == []
