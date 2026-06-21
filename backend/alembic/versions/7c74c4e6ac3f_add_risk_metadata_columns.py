"""add risk metadata columns

Revision ID: 7c74c4e6ac3f
Revises: 194fec348120
Create Date: 2026-01-30 14:06:23.413912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c74c4e6ac3f'
down_revision: Union[str, Sequence[str], None] = '194fec348120'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
