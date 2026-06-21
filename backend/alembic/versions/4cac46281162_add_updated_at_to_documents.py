"""add updated_at to documents

Revision ID: 4cac46281162
Revises: b462c1efe1cc
Create Date: 2026-01-21 10:36:14.716376

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cac46281162'
down_revision: Union[str, Sequence[str], None] = 'b462c1efe1cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
