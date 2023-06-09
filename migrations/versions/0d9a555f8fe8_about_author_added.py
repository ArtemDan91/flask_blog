"""about author added

Revision ID: 0d9a555f8fe8
Revises: 20ac645728ec
Create Date: 2023-03-24 23:20:31.598891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d9a555f8fe8'
down_revision = '20ac645728ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('about_author', sa.Text(length=500), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('about_author')

    # ### end Alembic commands ###
