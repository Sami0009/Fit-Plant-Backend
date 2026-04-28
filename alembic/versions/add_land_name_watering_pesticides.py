"""add land_name, watering, and pesticides to tasks

Revision ID: add_land_name_watering_pesticides
Revises: ea55724616d2
Create Date: 2026-04-27
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_ln_wat_pest'
down_revision: Union[str, Sequence[str], None] = 'ea55724616d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('tasks', sa.Column('land_name', sa.String(), nullable=True))
    op.add_column('tasks', sa.Column('watering', sa.Boolean(), nullable=True))
    op.add_column('tasks', sa.Column('pesticides', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('tasks', 'pesticides')
    op.drop_column('tasks', 'watering')
    op.drop_column('tasks', 'land_name')
