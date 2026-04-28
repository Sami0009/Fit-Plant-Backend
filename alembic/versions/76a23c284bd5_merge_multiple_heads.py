"""Merge multiple heads

Revision ID: 76a23c284bd5
Revises: add_land_name_watering_pesticides, bbdac4a870ff
Create Date: 2026-04-27 20:58:16.486983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76a23c284bd5'
down_revision: Union[str, Sequence[str], None] = ('add_ln_wat_pest', 'bbdac4a870ff')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
