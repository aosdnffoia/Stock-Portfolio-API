import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.auth.models import User
from app.core.security import get_password_hash


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client_and_session():
    """Spin up a fresh in-memory DB and test client for each test."""
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


async def seed_user(session_factory, email: str, password: str) -> None:
    """Create a user in the test database."""
    async with session_factory() as session:
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()


@pytest.mark.asyncio
async def test_login_success_returns_token(client_and_session):
    client, session_factory = client_and_session
    await seed_user(session_factory, "demo@example.com", "demo123")

    response = await client.post(
        "/auth/login",
        json={"email": "demo@example.com", "password": "demo123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_401(client_and_session):
    client, session_factory = client_and_session
    await seed_user(session_factory, "demo@example.com", "demo123")

    response = await client.post(
        "/auth/login",
        json={"email": "demo@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_token(client_and_session):
    client, _ = client_and_session

    response = await client.get("/auth/me")

    # HTTPBearer returns 403 when credentials are missing
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(client_and_session):
    client, session_factory = client_and_session
    await seed_user(session_factory, "demo@example.com", "demo123")

    login_resp = await client.post(
        "/auth/login",
        json={"email": "demo@example.com", "password": "demo123"},
    )
    token = login_resp.json()["access_token"]

    me_resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == "demo@example.com"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_protected_route_rejects_invalid_token(client_and_session):
    client, _ = client_and_session

    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid.token.value"}
    )

    assert response.status_code == 401
