"""test alembic async setup

Revision ID: 823f89282182
Revises: 5d994ae765e8
Create Date: 2026-08-24 18:59:54.754889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '823f89282182'
down_revision: Union[str, Sequence[str], None] = '5d994ae765e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
