"""added users.last_active

Revision ID: 7f37e6641a37
Revises: 3c9149132801
Create Date: 2021-02-15 22:04:06.026956

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7f37e6641a37'
down_revision = '3c9149132801'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('last_active', sa.DateTime(), nullable=True))
    op.execute("UPDATE users SET last_active = now()")
    op.alter_column('users', 'last_active', nullable=False)


def downgrade():
    op.drop_column('users', 'last_active')
