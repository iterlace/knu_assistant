"""added lessons_subgroups_members

Revision ID: 2606ce1554df
Revises: 2a96b6b05aec
Create Date: 2021-01-27 02:41:53.862560

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2606ce1554df'
down_revision = '2a96b6b05aec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lessons_subgroups_members',
    sa.Column('lesson_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.tg_id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('lessons_subgroups_members')
    # ### end Alembic commands ###