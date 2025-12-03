import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.security import create_access_token, decode_access_token, get_current_user
from app.auth.models import User
from app.database import Base
from app.core.security import get_password_hash
from sqlalchemy import select

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
async def test_decode_access_token_invalid():
    with pytest.raises(HTTPException):
        decode_access_token("invalid.token.here")


@pytest.mark.asyncio
async def test_get_current_user_returns_user(session_factory):
    async with session_factory() as session:
        user = User(
            email="demo@example.com",
            hashed_password=get_password_hash("secret123"),
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()

    token = create_access_token({"sub": "demo@example.com", "user_id": 1})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    async with session_factory() as session:
        result = await get_current_user(credentials=credentials, db=session)
        assert result.email == "demo@example.com"
