"""add project member role constraint

Revision ID: a716f8874ee1
Revises: c1d2e3f4a5b6
Create Date: 2026-11-15 12:17:45.135062
"""

from typing import Sequence, Union
from alembic import op


revision: str = "a716f8874ee1"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("project_members") as batch_op:
        batch_op.create_check_constraint(
            "ck_project_member_role",
            "role IN ('owner', 'editor', 'viewer')",
        )


def downgrade() -> None:
    with op.batch_alter_table("project_members") as batch_op:
        batch_op.drop_constraint(
            "ck_project_member_role",
            type_="check",
        )