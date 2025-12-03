from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.auth.models import User
from app.core.security import get_password_hash, create_access_token
from app.etl.models import Ticker, Price


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client_and_session():
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client, SessionLocal

    app.dependency_overrides.clear()
    await engine.dispose()


async def seed_user(session_factory, email: str, password: str = "pass123"):
    async with session_factory() as session:
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def seed_market_data(session_factory):
    async with session_factory() as session:
        tickers = [
            Ticker(symbol="AAPL", name="Apple", sector="Tech"),
            Ticker(symbol="MSFT", name="Microsoft", sector="Tech"),
            Ticker(symbol="AMZN", name="Amazon", sector="Consumer"),
        ]
        session.add_all(tickers)
        await session.flush()

        prices = [
            Price(ticker_id=tickers[0].id, price_date=date(2024, 1, 1), close=Decimal("150"), change_pct=Decimal("1.0")),
            Price(ticker_id=tickers[1].id, price_date=date(2024, 1, 1), close=Decimal("300"), change_pct=Decimal("0.5")),
            Price(ticker_id=tickers[2].id, price_date=date(2024, 1, 1), close=Decimal("120"), change_pct=Decimal("2.0")),
        ]
        session.add_all(prices)
        await session.commit()


def auth_header(user: User):
    token = create_access_token({"sub": user.email, "user_id": user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_portfolio_generated_and_returns_totals(client_and_session):
    client, session_factory = client_and_session
    user = await seed_user(session_factory, "demo1@example.com")
    await seed_market_data(session_factory)

    resp = await client.get("/portfolio", headers=auth_header(user))
    assert resp.status_code == 200
    data = resp.json()
    assert "holdings" in data
    assert len(data["holdings"]) > 0
    assert data["totalValue"] > 0


@pytest.mark.asyncio
async def test_portfolio_is_deterministic_for_user(client_and_session):
    client, session_factory = client_and_session
    user = await seed_user(session_factory, "demo2@example.com")
    await seed_market_data(session_factory)

    resp1 = await client.get("/portfolio", headers=auth_header(user))
    resp2 = await client.get("/portfolio", headers=auth_header(user))

    assert resp1.status_code == 200
    assert resp1.json() == resp2.json()


@pytest.mark.asyncio
async def test_portfolio_differs_between_users(client_and_session):
    client, session_factory = client_and_session
    user1 = await seed_user(session_factory, "user1@example.com")
    user2 = await seed_user(session_factory, "user2@example.com")
    await seed_market_data(session_factory)

    resp1 = await client.get("/portfolio", headers=auth_header(user1))
    resp2 = await client.get("/portfolio", headers=auth_header(user2))

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json() != resp2.json()
