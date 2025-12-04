"""add portfolio holdings table

Revision ID: d4a8f6b2c7e9
Revises: c3d5c4e9f4b1
Create Date: 2025-12-02 16:28:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d4a8f6b2c7e9"
down_revision: Union[str, None] = "c3d5c4e9f4b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolio_holdings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "ticker_id", name="uq_user_ticker_portfolio"),
    )
    op.create_index("ix_portfolio_holdings_id", "portfolio_holdings", ["id"], unique=False)
    op.create_index("ix_portfolio_holdings_user_id", "portfolio_holdings", ["user_id"], unique=False)
    op.create_index("ix_portfolio_holdings_ticker_id", "portfolio_holdings", ["ticker_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_portfolio_holdings_ticker_id", table_name="portfolio_holdings")
    op.drop_index("ix_portfolio_holdings_user_id", table_name="portfolio_holdings")
    op.drop_index("ix_portfolio_holdings_id", table_name="portfolio_holdings")
    op.drop_table("portfolio_holdings")
