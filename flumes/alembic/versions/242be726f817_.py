"""empty message

Revision ID: 242be726f817
Revises: 30374e2904cd
Create Date: 2022-04-22 16:17:21.217049

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "242be726f817"
down_revision = "30374e2904cd"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "errors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=True),
        sa.Column("error_log", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["files.id"],
            name=op.f("fk_errors_file_id_files"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_errors")),
    )
    with op.batch_alter_table("files", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_files_id"), ["id"])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("files", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_files_id"), type_="unique")

    op.drop_table("errors")
    # ### end Alembic commands ###