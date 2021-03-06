"""empty message

Revision ID: 590fa222f000
Revises: 95190fc568fe
Create Date: 2022-07-23 17:03:24.382870

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '590fa222f000'
down_revision = '95190fc568fe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('followers')
    # ### end Alembic commands ###
