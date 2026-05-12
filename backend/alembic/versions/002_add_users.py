"""add users table + quizzes.user_id FK

Revision ID: 002
Revises: 001
Create Date: 2026-05-10
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.add_column(
        "quizzes",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_quizzes_user", "quizzes", "users", ["user_id"], ["id"]
    )
    op.create_index("ix_quizzes_user_id", "quizzes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_quizzes_user_id", table_name="quizzes")
    op.drop_constraint("fk_quizzes_user", "quizzes", type_="foreignkey")
    op.drop_column("quizzes", "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
