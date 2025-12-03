"""add tickers and prices tables

Revision ID: c3d5c4e9f4b1
Revises: 78ef11ffdf59
Create Date: 2025-12-01 15:05:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c3d5c4e9f4b1"
down_revision: Union[str, None] = "78ef11ffdf59"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tickers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("sector", sa.String(), nullable=True),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("exchange", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tickers_id", "tickers", ["id"], unique=False)
    op.create_index("ix_tickers_symbol", "tickers", ["symbol"], unique=True)

    op.create_table(
        "prices",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(14, 4), nullable=True),
        sa.Column("high", sa.Numeric(14, 4), nullable=True),
        sa.Column("low", sa.Numeric(14, 4), nullable=True),
        sa.Column("close", sa.Numeric(14, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("change_pct", sa.Numeric(8, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("ticker_id", "price_date", name="uq_prices_ticker_date"),
    )
    op.create_index("ix_prices_id", "prices", ["id"], unique=False)
    op.create_index("ix_prices_price_date", "prices", ["price_date"], unique=False)
    op.create_index("ix_prices_ticker_date", "prices", ["ticker_id", "price_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_prices_ticker_date", table_name="prices")
    op.drop_index("ix_prices_price_date", table_name="prices")
    op.drop_index("ix_prices_id", table_name="prices")
    op.drop_table("prices")

    op.drop_index("ix_tickers_symbol", table_name="tickers")
    op.drop_index("ix_tickers_id", table_name="tickers")
    op.drop_table("tickers")
