from sqlalchemy import Column, Integer, Numeric, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.sql import func

from app.database import Base


class PortfolioHolding(Base):
    """A holding in a user's portfolio."""

    __tablename__ = "portfolio_holdings"
    __table_args__ = (
        UniqueConstraint("user_id", "ticker_id", name="uq_user_ticker_portfolio"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
