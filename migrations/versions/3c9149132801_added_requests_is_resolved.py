"""added requests.is_resolved

Revision ID: 3c9149132801
Revises: 02c6d479417b
Create Date: 2021-02-07 22:24:36.652149

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c9149132801'
down_revision = '02c6d479417b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('requests', sa.Column('is_resolved', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('requests', 'is_resolved')
    # ### end Alembic commands ###
