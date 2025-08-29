"""Add task_index field to analysis_tasks table

Revision ID: e2d201fb732d
Revises: 71f90b35b308
Create Date: 2025-08-29 11:11:18.160638

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e2d201fb732d"
down_revision: Union[str, None] = "71f90b35b308"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 task_index 字段到 analysis_tasks 表
    op.add_column("analysis_tasks", sa.Column("task_index", sa.String(255), nullable=True, comment="任务索引"))
    op.create_index(op.f("ix_analysis_tasks_task_index"), "analysis_tasks", ["task_index"], unique=False)


def downgrade() -> None:
    # 撤销 task_index 字段和相关索引
    op.drop_index(op.f("ix_analysis_tasks_task_index"), table_name="analysis_tasks")
    op.drop_column("analysis_tasks", "task_index")
