"""empty message

Revision ID: a0b003abaac8
Revises: e827c1336bb4
Create Date: 2021-11-22 02:36:04.138227

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a0b003abaac8"
down_revision = "e827c1336bb4"
branch_labels = None
depends_on = None

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "fields", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_fields_stream_id_streams", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_fields_stream_id_streams"),
            "streams",
            ["stream_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table(
        "infos", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_infos_file_id_files", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_infos_file_id_files"),
            "files",
            ["file_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table(
        "streams", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_streams_parent_id_streams", type_="foreignkey")
        batch_op.drop_constraint("fk_streams_info_id_infos", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_streams_parent_id_streams"),
            "streams",
            ["parent_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_streams_info_id_infos"),
            "infos",
            ["info_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "streams", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_streams_info_id_infos"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_streams_parent_id_streams"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_streams_parent_id_streams", "streams", ["parent_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_streams_info_id_infos", "infos", ["info_id"], ["id"]
        )

    with op.batch_alter_table(
        "infos", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_infos_file_id_files"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_infos_file_id_files", "files", ["file_id"], ["id"]
        )

    with op.batch_alter_table(
        "fields", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_fields_stream_id_streams"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_fields_stream_id_streams", "streams", ["stream_id"], ["id"]
        )

    # ### end Alembic commands ###