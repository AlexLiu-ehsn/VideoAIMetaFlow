import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    filepath = Column(String(1000), nullable=False)
    filesize = Column(Integer, nullable=False)
    duration = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    fps = Column(Float)
    mime_type = Column(String(50), default="video/mp4")
    thumbnail = Column(String(1000))

    # Gemini File API 參照
    gemini_file_uri = Column(String(500))
    gemini_file_name = Column(String(500))

    # 分析狀態: pending | uploading_to_gemini | analyzing | completed | failed
    status = Column(String(50), nullable=False, default="pending")
    error_message = Column(Text)

    # 分析結果
    summary = Column(Text)
    critique = Column(Text)  # 整體評價文字

    # 向量 embedding（摘要 + 標籤）
    summary_embedding = Column(Vector(768))

    # 全文搜尋
    search_vector = Column(TSVECTOR)

    analysis_duration = Column(Float)  # 分析總耗時（秒）

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    analyzed_at = Column(DateTime)

    # 關聯
    video_tags = relationship("VideoTag", back_populates="video", cascade="all, delete-orphan")
    segments = relationship("Segment", back_populates="video", cascade="all, delete-orphan", order_by="Segment.segment_index")
    critique_annotations = relationship("CritiqueAnnotation", back_populates="video", cascade="all, delete-orphan", order_by="CritiqueAnnotation.timestamp")

    __table_args__ = (
        Index("ix_videos_status", "status"),
        Index("ix_videos_search_vector", "search_vector", postgresql_using="gin"),
    )


class TagCategory(Base):
    __tablename__ = "tag_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    label = Column(String(200), nullable=False)
    color = Column(String(7))  # hex color

    tags = relationship("Tag", back_populates="category", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("tag_categories.id"), nullable=False)
    name = Column(String(200), nullable=False)
    label = Column(String(200), nullable=False)

    category = relationship("TagCategory", back_populates="tags")
    video_tags = relationship("VideoTag", back_populates="tag", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_tag_category_name"),
    )


class VideoTag(Base):
    __tablename__ = "video_tags"

    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    confidence = Column(Float, default=1.0)

    video = relationship("Video", back_populates="video_tags")
    tag = relationship("Tag", back_populates="video_tags")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    title = Column(String(500))
    description = Column(Text, nullable=False)
    visual_description = Column(Text)
    audio_description = Column(Text)
    segment_index = Column(Integer, nullable=False)

    # 向量 embedding
    embedding = Column(Vector(768))

    # 全文搜尋
    search_vector = Column(TSVECTOR)

    video = relationship("Video", back_populates="segments")

    __table_args__ = (
        UniqueConstraint("video_id", "segment_index", name="uq_segment_video_index"),
        Index("ix_segments_search_vector", "search_vector", postgresql_using="gin"),
    )


class CritiqueAnnotation(Base):
    __tablename__ = "critique_annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(Float, nullable=False)
    end_time = Column(Float)
    type = Column(String(50), nullable=False)  # strength | weakness | suggestion | highlight
    comment = Column(Text, nullable=False)
    severity = Column(String(20), default="info")  # info | minor | major

    video = relationship("Video", back_populates="critique_annotations")
