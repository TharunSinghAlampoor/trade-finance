"""update risk_scores table

Revision ID: e7badb528414
Revises: ced5264e9a76
Create Date: 2026-01-23 23:42:40.941523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7badb528414'
down_revision: Union[str, Sequence[str], None] = 'ced5264e9a76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
