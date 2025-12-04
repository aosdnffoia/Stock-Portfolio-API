from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import logging

from app.database import get_db
from app.auth.schemas import UserLogin, Token, SocialLoginRequest, UserInDB
from app.auth.utils import authenticate_user, create_or_get_oauth_user
from app.core.security import create_access_token, get_current_active_user
from app.auth.models import User
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    logger.info(f"Login attempt for email: {user_credentials.email}")
    user = await authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        logger.warning(f"Failed login attempt for email: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {user_credentials.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    logger.info(f"Successful login for user: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/social", response_model=Token)
async def social_login(
    provider: str = Query(..., pattern="^(google|facebook)$"),
    social_data: SocialLoginRequest = None,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Social login attempt with provider: {provider}")
    if not social_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Social login data required")
    if social_data.provider != provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider mismatch")
    provider_id = f"{provider}_{social_data.email}"
    user = await create_or_get_oauth_user(
        db=db, email=social_data.email, provider=provider,
        provider_id=provider_id, full_name=social_data.name
    )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    logger.info(f"Successful social login for user: {user.email} via {provider}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserInDB)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user
