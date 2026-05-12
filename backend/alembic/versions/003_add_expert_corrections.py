"""add expert_corrections table + questions.expert_verified

Revision ID: 003
Revises: 002
Create Date: 2026-05-10
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column(
            "expert_verified",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.create_table(
        "expert_corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("original_question", sa.JSON, nullable=True),
        sa.Column("corrected_question", sa.JSON, nullable=False),
        sa.Column("topic_tags", sa.JSON, nullable=False),
        sa.Column(
            "expert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "approved",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "ix_expert_corrections_expert_id", "expert_corrections", ["expert_id"]
    )
    op.create_index(
        "ix_expert_corrections_approved", "expert_corrections", ["approved"]
    )


def downgrade() -> None:
    op.drop_index("ix_expert_corrections_approved", table_name="expert_corrections")
    op.drop_index("ix_expert_corrections_expert_id", table_name="expert_corrections")
    op.drop_table("expert_corrections")
    op.drop_column("questions", "expert_verified")
