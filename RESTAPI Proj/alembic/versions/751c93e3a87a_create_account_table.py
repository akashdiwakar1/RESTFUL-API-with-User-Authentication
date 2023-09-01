"""create tasks table

Revision ID: 751c93e3a87a
Revises: 
Create Date: 2023-08-28 17:58:17.741756

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '751c93e3a87a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(50), index=True),  # Match with your model
        sa.Column('description', sa.String),  # Match with your model
        sa.Column('project_id', sa.Integer),  # Match with your model
        sa.Column('completed', sa.Boolean)  # Match with your model
    )

def downgrade():
    op.drop_table('tasks')  # Drop the correct table name

