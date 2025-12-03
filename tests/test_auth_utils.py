import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base
from app.auth import utils
from app.auth.models import User
from app.auth.schemas import UserCreate
from app.core.security import get_password_hash


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session_factory():
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield SessionLocal

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user_and_authenticate(session_factory):
    user_data = UserCreate(email="demo@example.com", password="secret123", full_name="Demo")
    async with session_factory() as session:
        created = await utils.create_user(session, user_data)
        assert created.email == "demo@example.com"
        assert created.hashed_password != "secret123"

    async with session_factory() as session:
        authed = await utils.authenticate_user(session, "demo@example.com", "secret123")
        assert authed is not None
        assert authed.email == "demo@example.com"


@pytest.mark.asyncio
async def test_authenticate_invalid_password(session_factory):
    async with session_factory() as session:
        user = User(
            email="demo@example.com",
            hashed_password=get_password_hash("secret123"),
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()

    async with session_factory() as session:
        authed = await utils.authenticate_user(session, "demo@example.com", "wrongpass")
        assert authed is None


@pytest.mark.asyncio
async def test_create_or_get_oauth_user_new(session_factory):
    async with session_factory() as session:
        user = await utils.create_or_get_oauth_user(
            db=session,
            email="oauth@example.com",
            provider="google",
            provider_id="google_oauth@example.com",
            full_name="OAuth User",
        )
        assert user.email == "oauth@example.com"
        assert user.oauth_provider == "google"
        assert user.oauth_provider_id == "google_oauth@example.com"


@pytest.mark.asyncio
async def test_create_or_get_oauth_user_existing_adds_provider(session_factory):
    async with session_factory() as session:
        user = User(
            email="existing@example.com",
            hashed_password=get_password_hash("secret123"),
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()

    async with session_factory() as session:
        updated = await utils.create_or_get_oauth_user(
            db=session,
            email="existing@example.com",
            provider="facebook",
            provider_id="facebook_existing@example.com",
            full_name="Existing User",
        )
        assert updated.oauth_provider == "facebook"
        assert updated.oauth_provider_id == "facebook_existing@example.com"
