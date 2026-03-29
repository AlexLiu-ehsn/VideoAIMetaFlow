"""初始資料庫架構

Revision ID: 001
Revises:
Create Date: 2026-03-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 啟用 pgvector 擴充
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 影片主表
    op.create_table(
        "videos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("filepath", sa.String(1000), nullable=False),
        sa.Column("filesize", sa.Integer(), nullable=False),
        sa.Column("duration", sa.Float()),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("fps", sa.Float()),
        sa.Column("mime_type", sa.String(50), server_default="video/mp4"),
        sa.Column("thumbnail", sa.String(1000)),
        sa.Column("gemini_file_uri", sa.String(500)),
        sa.Column("gemini_file_name", sa.String(500)),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text()),
        sa.Column("summary", sa.Text()),
        sa.Column("critique", sa.Text()),
        sa.Column("summary_embedding", Vector(768)),
        sa.Column("search_vector", sa.dialects.postgresql.TSVECTOR()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("analyzed_at", sa.DateTime()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_videos_status", "videos", ["status"])
    op.create_index("ix_videos_search_vector", "videos", ["search_vector"], postgresql_using="gin")

    # 標籤分類
    op.create_table(
        "tag_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("color", sa.String(7)),
        sa.PrimaryKeyConstraint("id"),
    )

    # 標籤
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("tag_categories.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "name", name="uq_tag_category_name"),
    )

    # 影片-標籤關聯
    op.create_table(
        "video_tags",
        sa.Column("video_id", sa.UUID(), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0"),
        sa.PrimaryKeyConstraint("video_id", "tag_id"),
    )

    # 時間軸分段
    op.create_table(
        "segments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("video_id", sa.UUID(), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("visual_description", sa.Text()),
        sa.Column("audio_description", sa.Text()),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(768)),
        sa.Column("search_vector", sa.dialects.postgresql.TSVECTOR()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("video_id", "segment_index", name="uq_segment_video_index"),
    )
    op.create_index("ix_segments_search_vector", "segments", ["search_vector"], postgresql_using="gin")

    # 製作人評析標註
    op.create_table(
        "critique_annotations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("video_id", sa.UUID(), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float()),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), server_default="info"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 建立 HNSW 向量索引
    op.execute(
        "CREATE INDEX ix_videos_summary_embedding ON videos "
        "USING hnsw (summary_embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_segments_embedding ON segments "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # 預設標籤分類
    op.execute("""
        INSERT INTO tag_categories (name, label, color) VALUES
        ('video_theme', '影片主題', '#3B82F6'),
        ('target_audience', '目標受眾', '#8B5CF6'),
        ('product_feature', '商品特色', '#F59E0B'),
        ('content_format', '內容形式', '#10B981'),
        ('mood_tone', '情緒語調', '#EF4444'),
        ('product_mentioned', '提及產品', '#EC4899'),
        ('language', '語言', '#6B7280')
    """)


def downgrade() -> None:
    op.drop_table("critique_annotations")
    op.drop_table("segments")
    op.drop_table("video_tags")
    op.drop_table("tags")
    op.drop_table("tag_categories")
    op.drop_table("videos")
    op.execute("DROP EXTENSION IF EXISTS vector")
