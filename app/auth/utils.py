from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.auth.models import User
from app.auth.schemas import UserCreate
from app.core.security import get_password_hash, verify_password


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_or_get_oauth_user(
    db: AsyncSession,
    email: str,
    provider: str,
    provider_id: str,
    full_name: Optional[str] = None
) -> User:
    user = await get_user_by_email(db, email)
    if user:
        if not user.oauth_provider:
            user.oauth_provider = provider
            user.oauth_provider_id = provider_id
            await db.commit()
            await db.refresh(user)
        return user
    user = User(
        email=email,
        hashed_password=get_password_hash("oauth_user_no_password"),
        full_name=full_name,
        is_active=True,
        is_superuser=False,
        oauth_provider=provider,
        oauth_provider_id=provider_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
