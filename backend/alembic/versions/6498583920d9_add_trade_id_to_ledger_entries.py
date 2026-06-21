"""add trade_id to ledger_entries

Revision ID: 6498583920d9
Revises: b32de890f86a
Create Date: 2026-01-30 00:42:14.994276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6498583920d9'
down_revision: Union[str, Sequence[str], None] = 'b32de890f86a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
