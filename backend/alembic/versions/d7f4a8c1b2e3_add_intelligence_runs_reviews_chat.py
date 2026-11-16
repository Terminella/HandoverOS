"""add intelligence runs, reviews, contradictions and chat persistence"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7f4a8c1b2e3"
down_revision: Union[str, Sequence[str], None] = "a716f8874ee1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reconstruction_runs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("initiated_by", sa.String(36), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="completed"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_fingerprint", sa.String(128), nullable=True),
        sa.Column("provider", sa.String(80), nullable=True),
        sa.Column("model", sa.String(255), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("result_counts", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["initiated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "idempotency_key", name="uq_reconstruction_run_idempotency"),
    )
    op.create_index("ix_reconstruction_runs_project_created", "reconstruction_runs", ["project_id", "created_at"])

    op.create_table(
        "run_sources",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("source_identifier", sa.String(255), nullable=False),
        sa.Column("content_fingerprint", sa.String(128), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["reconstruction_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "source_id", name="uq_run_source"),
    )
    op.create_index("ix_run_sources_source", "run_sources", ["source_id"])

    with op.batch_alter_table("knowledge_items") as batch:
        batch.add_column(sa.Column("run_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("claim_id", sa.String(255), nullable=True))
        batch.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("review_status", sa.String(30), nullable=False, server_default="unreviewed"))
        batch.add_column(sa.Column("reviewed_by", sa.String(36), nullable=True))
        batch.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("review_note", sa.Text(), nullable=True))
        batch.create_foreign_key("fk_knowledge_run", "reconstruction_runs", ["run_id"], ["id"])
        batch.create_foreign_key("fk_knowledge_reviewed_by", "users", ["reviewed_by"], ["id"])
    op.create_index("ix_knowledge_items_claim_id", "knowledge_items", ["claim_id"])

    op.create_table(
        "finding_reviews",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("finding_id", sa.String(36), nullable=False),
        sa.Column("reviewer_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("previous_status", sa.String(30), nullable=False),
        sa.Column("new_status", sa.String(30), nullable=False),
        sa.Column("previous_version", sa.Integer(), nullable=False),
        sa.Column("new_version", sa.Integer(), nullable=False),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("corrected_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["finding_id"], ["knowledge_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_finding_reviews_finding_created", "finding_reviews", ["finding_id", "created_at"])

    op.create_table(
        "finding_contradictions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("claim_ids", sa.JSON(), nullable=False),
        sa.Column("source_ids", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["reconstruction_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_finding_contradictions_run", "finding_contradictions", ["run_id"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("context_version", sa.String(128), nullable=True),
        sa.Column("source_fingerprint", sa.String(128), nullable=True),
        sa.Column("approved_knowledge_fingerprint", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_project_updated", "conversations", ["project_id", "updated_at"])

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("conversation_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context_version", sa.String(128), nullable=True),
        sa.Column("citation_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversation_messages_conversation_created", "conversation_messages", ["conversation_id", "created_at"])

    op.create_table(
        "project_context_snapshots",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("context_version", sa.String(128), nullable=False),
        sa.Column("source_fingerprint", sa.String(128), nullable=True),
        sa.Column("approved_knowledge_fingerprint", sa.String(128), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "context_version", name="uq_project_context_version"),
    )
    op.create_index("ix_context_snapshots_project_created", "project_context_snapshots", ["project_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_context_snapshots_project_created", table_name="project_context_snapshots")
    op.drop_table("project_context_snapshots")
    op.drop_index("ix_conversation_messages_conversation_created", table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_index("ix_conversations_project_updated", table_name="conversations")
    op.drop_table("conversations")
    op.drop_index("ix_finding_contradictions_run", table_name="finding_contradictions")
    op.drop_table("finding_contradictions")
    op.drop_index("ix_finding_reviews_finding_created", table_name="finding_reviews")
    op.drop_table("finding_reviews")
    op.drop_index("ix_knowledge_items_claim_id", table_name="knowledge_items")
    with op.batch_alter_table("knowledge_items") as batch:
        batch.drop_constraint("fk_knowledge_reviewed_by", type_="foreignkey")
        batch.drop_constraint("fk_knowledge_run", type_="foreignkey")
        for name in ("review_note", "reviewed_at", "reviewed_by", "review_status", "version", "claim_id", "run_id"):
            batch.drop_column(name)
    op.drop_index("ix_run_sources_source", table_name="run_sources")
    op.drop_table("run_sources")
    op.drop_index("ix_reconstruction_runs_project_created", table_name="reconstruction_runs")
    op.drop_table("reconstruction_runs")
