"""Initial migration — creates all core tables and enables pgvector."""

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable extensions first
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Learning sessions
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("thread_id", sa.String(36), unique=True, nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("learning_goal", sa.String(500), nullable=False),
        sa.Column("progress", sa.Float(), default=0.0),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Knowledge points
    op.create_table(
        "knowledge_points",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), default="unfamiliar"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "name", name="uq_session_knowledge"),
    )

    # Error notebook
    op.create_table(
        "error_notebook",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quiz_data", sa.Text(), nullable=False),
        sa.Column("user_answer", sa.String(10)),
        sa.Column("is_correct", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Document chunks for RAG (pgvector)
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.Text()),
        sa.Column(
            "embedding",
            sa.ARRAY(sa.Float()),
            nullable=False,
        ),
    )
    # Note: vector index must be created via raw SQL after table creation
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding "
        "ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade():
    op.drop_table("document_chunks")
    op.drop_table("error_notebook")
    op.drop_table("knowledge_points")
    op.drop_table("sessions")
    op.drop_table("users")
