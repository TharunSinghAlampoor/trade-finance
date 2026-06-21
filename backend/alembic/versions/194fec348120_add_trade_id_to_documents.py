"""add trade_id to documents

Revision ID: 194fec348120
Revises: 6498583920d9
Create Date: 2026-01-30 11:20:59.495597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '194fec348120'
down_revision: Union[str, Sequence[str], None] = '6498583920d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
