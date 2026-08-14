"""Add professional group chat metadata without replacing existing discussions."""
from alembic import op
import sqlalchemy as sa
revision="20260813_0006"; down_revision="20260811_0005"; branch_labels=None; depends_on=None

def upgrade():
    bind=op.get_bind(); inspector=sa.inspect(bind)
    columns={c["name"] for c in inspector.get_columns("group_discussions")}
    additions={"reply_to_message_id":sa.Column("reply_to_message_id",sa.Integer(),sa.ForeignKey("group_discussions.id",ondelete="SET NULL")),"message_type":sa.Column("message_type",sa.String(20),nullable=False,server_default="text"),"attachment_url":sa.Column("attachment_url",sa.String(500)),"attachment_name":sa.Column("attachment_name",sa.String(255)),"attachment_size":sa.Column("attachment_size",sa.Integer()),"learning_resource_type":sa.Column("learning_resource_type",sa.String(20)),"learning_resource_id":sa.Column("learning_resource_id",sa.Integer()),"edited_at":sa.Column("edited_at",sa.DateTime(timezone=True)),"deleted_at":sa.Column("deleted_at",sa.DateTime(timezone=True))}
    for name,column in additions.items():
        if name not in columns: op.add_column("group_discussions",column)
    if "muted_until" not in {c["name"] for c in inspector.get_columns("group_members")}: op.add_column("group_members",sa.Column("muted_until",sa.DateTime(timezone=True)))
    tables=set(inspector.get_table_names())
    if "group_message_reactions" not in tables: op.create_table("group_message_reactions",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("message_id",sa.Integer(),sa.ForeignKey("group_discussions.id",ondelete="CASCADE"),nullable=False),sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("emoji",sa.String(16),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.UniqueConstraint("message_id","user_id","emoji",name="uniq_group_message_reaction"))
    if "group_message_reads" not in tables: op.create_table("group_message_reads",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("group_id",sa.Integer(),sa.ForeignKey("study_groups.id",ondelete="CASCADE"),nullable=False),sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("last_read_message_id",sa.Integer(),sa.ForeignKey("group_discussions.id",ondelete="SET NULL")),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.UniqueConstraint("group_id","user_id",name="uniq_group_message_read"))
    if "group_message_reports" not in tables: op.create_table("group_message_reports",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("message_id",sa.Integer(),sa.ForeignKey("group_discussions.id",ondelete="CASCADE"),nullable=False),sa.Column("reporter_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("reason",sa.String(500),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="pending"),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.UniqueConstraint("message_id","reporter_id",name="uniq_group_message_report"))

def downgrade(): raise RuntimeError("Group chat downgrade is disabled to protect message history")
