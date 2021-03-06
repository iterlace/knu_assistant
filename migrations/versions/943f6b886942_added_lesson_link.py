"""added Lesson.link

Revision ID: 943f6b886942
Revises: 59695dbfeafe
Create Date: 2021-02-05 18:44:52.052643

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '943f6b886942'
down_revision = '59695dbfeafe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lessons', sa.Column('link', sa.String(), nullable=True))
    op.drop_column('users', 'state_data')
    op.drop_column('users', 'current_state')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('current_state', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('state_data', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), autoincrement=False, nullable=False))
    op.drop_column('lessons', 'link')
    # ### end Alembic commands ###
