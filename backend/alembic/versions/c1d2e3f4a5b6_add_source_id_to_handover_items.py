"""add source_id to handover items

Revision ID: c1d2e3f4a5b6
Revises: b3c9f1a2d4e5
Create Date: 2026-11-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b3c9f1a2d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite does not support ALTER TABLE for adding constraints outside
    # batch mode. batch_alter_table recreates the table to apply changes.
    with op.batch_alter_table('handover_items') as batch_op:
        batch_op.add_column(
            sa.Column('source_id', sa.String(length=36), nullable=True)
        )
        batch_op.create_foreign_key(
            'fk_handover_item_source',
            'sources',
            ['source_id'],
            ['id'],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('handover_items') as batch_op:
        batch_op.drop_constraint('fk_handover_item_source', type_='foreignkey')
        batch_op.drop_column('source_id')
