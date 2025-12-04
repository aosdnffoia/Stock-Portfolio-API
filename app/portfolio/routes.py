from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_active_user
from app.auth.models import User
from app.portfolio.service import get_portfolio
from app.portfolio.schemas import PortfolioResponse

router = APIRouter()


@router.get("/portfolio", response_model=PortfolioResponse)
async def read_portfolio(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    portfolio = await get_portfolio(db, current_user)
    if portfolio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not available")
    return portfolio
