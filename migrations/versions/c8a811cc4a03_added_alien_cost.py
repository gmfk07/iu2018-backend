"""added alien cost

Revision ID: c8a811cc4a03
Revises: 7f7c416941f3
Create Date: 2018-08-22 11:15:52.760336

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8a811cc4a03'
down_revision = '7f7c416941f3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('alien_species', sa.Column('cost1', sa.Integer(), nullable=True))
    op.add_column('alien_species', sa.Column('cost2', sa.Integer(), nullable=True))
    op.add_column('alien_species', sa.Column('cost3', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('alien_species', 'cost3')
    op.drop_column('alien_species', 'cost2')
    op.drop_column('alien_species', 'cost1')
    # ### end Alembic commands ###
