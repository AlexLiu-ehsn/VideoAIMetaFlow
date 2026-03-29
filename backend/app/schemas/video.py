from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class VideoBase(BaseModel):
    filename: str
    filesize: int
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    mime_type: str = "video/mp4"


class VideoCreate(VideoBase):
    filepath: str


class TagOut(BaseModel):
    id: int
    name: str
    label: str
    category_name: str
    category_label: str
    color: str | None = None

    model_config = {"from_attributes": True}


class SegmentOut(BaseModel):
    id: UUID
    start_time: float
    end_time: float
    title: str | None = None
    description: str
    visual_description: str | None = None
    audio_description: str | None = None
    segment_index: int

    model_config = {"from_attributes": True}


class CritiqueAnnotationOut(BaseModel):
    id: UUID
    timestamp: float
    end_time: float | None = None
    type: str
    comment: str
    severity: str = "info"

    model_config = {"from_attributes": True}


class VideoSummary(BaseModel):
    """影片列表用的簡要資訊"""
    id: UUID
    filename: str
    filesize: int
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    thumbnail: str | None = None
    status: str
    created_at: datetime
    tags: list[TagOut] = []

    model_config = {"from_attributes": True}


class VideoDetail(VideoSummary):
    """影片詳情（含完整分析結果）"""
    fps: float | None = None
    mime_type: str = "video/mp4"
    summary: str | None = None
    critique: str | None = None
    error_message: str | None = None
    analyzed_at: datetime | None = None
    analysis_duration: float | None = None
    segments: list[SegmentOut] = []
    critique_annotations: list[CritiqueAnnotationOut] = []

    model_config = {"from_attributes": True}


class VideoListResponse(BaseModel):
    items: list[VideoSummary]
    total: int
    page: int
    page_size: int


class UploadResponse(BaseModel):
    video_id: UUID
    filename: str
    status: str
