from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Numeric, BigInteger, UniqueConstraint, Index
from sqlalchemy.sql import func

from app.database import Base


class Ticker(Base):
    """Tracked market ticker."""

    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    exchange = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<Ticker(symbol={self.symbol})>"


class Price(Base):
    """Daily price for a ticker."""

    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("ticker_id", "price_date", name="uq_prices_ticker_date"),
        Index("ix_prices_ticker_date", "ticker_id", "price_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False)
    price_date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(14, 4), nullable=True)
    high = Column(Numeric(14, 4), nullable=True)
    low = Column(Numeric(14, 4), nullable=True)
    close = Column(Numeric(14, 4), nullable=False)
    volume = Column(BigInteger, nullable=True)
    change_pct = Column(Numeric(8, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<Price(ticker_id={self.ticker_id}, date={self.price_date})>"
