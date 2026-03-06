"""Add pattern_skills table

Revision ID: 003_add_pattern_skills
Revises: 002_add_audit_logs
Create Date: 2024-01-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "003_add_pattern_skills"
down_revision: Union[str, None] = "002_add_audit_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 pattern_skills 表"""
    op.create_table(
        "pattern_skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scene", sa.String(length=50), nullable=False),
        sa.Column("pattern_name", sa.String(length=100), nullable=False),
        sa.Column(
            "situation_template",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "advantages_template",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "blindspots_template",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "actions_library",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scene", "pattern_name", name="uq_pattern_skills_scene_pattern"),
    )
    op.create_index("ix_pattern_skills_id", "pattern_skills", ["id"], unique=False)
    op.create_index("ix_pattern_skills_scene", "pattern_skills", ["scene"], unique=False)
    op.create_index("ix_pattern_skills_pattern_name", "pattern_skills", ["pattern_name"], unique=False)
    op.create_index("ix_pattern_skills_is_active", "pattern_skills", ["is_active"], unique=False)
    op.create_index("ix_pattern_skills_deleted_at", "pattern_skills", ["deleted_at"], unique=False)


def downgrade() -> None:
    """删除 pattern_skills 表"""
    op.drop_index("ix_pattern_skills_deleted_at", table_name="pattern_skills")
    op.drop_index("ix_pattern_skills_is_active", table_name="pattern_skills")
    op.drop_index("ix_pattern_skills_pattern_name", table_name="pattern_skills")
    op.drop_index("ix_pattern_skills_scene", table_name="pattern_skills")
    op.drop_index("ix_pattern_skills_id", table_name="pattern_skills")
    op.drop_table("pattern_skills")
