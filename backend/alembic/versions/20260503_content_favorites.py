"""content_favorites for user-saved analyze records

Revision ID: d1e2f3a4b5c6
Revises: c3d4e5f6a1b2
Create Date: 2026-05-03

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_favorites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["content_id"], ["contents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "content_id", name="uq_content_favorites_user_content"),
    )
    op.create_index(op.f("ix_content_favorites_content_id"), "content_favorites", ["content_id"], unique=False)
    op.create_index(op.f("ix_content_favorites_user_id"), "content_favorites", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_content_favorites_user_id"), table_name="content_favorites")
    op.drop_index(op.f("ix_content_favorites_content_id"), table_name="content_favorites")
    op.drop_table("content_favorites")
