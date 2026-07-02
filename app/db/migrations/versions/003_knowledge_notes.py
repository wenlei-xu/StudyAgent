"""Add knowledge_notes table — distilled learning notes from AI interactions."""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "knowledge_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tags", sa.ARRAY(sa.String(50)), nullable=False, server_default="{}"),
        sa.Column("source_type", sa.String(20), nullable=False, server_default="auto"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_knowledge_notes_tags", "knowledge_notes", ["tags"], postgresql_using="gin")


def downgrade():
    op.drop_table("knowledge_notes")
