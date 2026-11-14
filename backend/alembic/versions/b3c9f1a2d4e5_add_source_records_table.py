"""add source records table

Revision ID: b3c9f1a2d4e5
Revises: e85619cdeaea
Create Date: 2026-11-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b3c9f1a2d4e5'
down_revision: Union[str, Sequence[str], None] = 'e85619cdeaea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'source_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.String(length=100), nullable=False, index=True),
        sa.Column('source_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('source_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('content_hash', sa.String(length=128), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=False, default={}),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_source_project_type',
        'source_records',
        ['project_id', 'source_type'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_source_project_type', table_name='source_records')
    op.drop_table('source_records')
