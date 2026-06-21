"""update risk_scores table

Revision ID: b32de890f86a
Revises: e7badb528414
Create Date: 2026-01-23 23:43:12.780090

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b32de890f86a'
down_revision: Union[str, Sequence[str], None] = 'e7badb528414'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
