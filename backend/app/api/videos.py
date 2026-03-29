import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import update as sa_update

from app.config import settings
from app.db.database import get_db
from app.db.models import Video
from app.schemas.video import (
    CritiqueAnnotationOut,
    SegmentOut,
    TagOut,
    UploadResponse,
    VideoDetail,
    VideoListResponse,
    VideoSummary,
)
from app.services.video_service import (
    create_video_record,
    delete_video,
    generate_thumbnail,
    get_video_detail,
    get_video_list,
    save_upload_file,
)
from app.workers.pipeline import enqueue_analysis

router = APIRouter()


def _build_tags_out(video) -> list[TagOut]:
    """從 video.video_tags 組裝 TagOut 列表"""
    tags = []
    for vt in video.video_tags:
        tag = vt.tag
        cat = tag.category
        tags.append(TagOut(
            id=tag.id,
            name=tag.name,
            label=tag.label,
            category_name=cat.name,
            category_label=cat.label,
            color=cat.color,
        ))
    return tags


def _build_video_summary(video) -> VideoSummary:
    return VideoSummary(
        id=video.id,
        filename=video.filename,
        filesize=video.filesize,
        duration=video.duration,
        width=video.width,
        height=video.height,
        thumbnail=video.thumbnail,
        status=video.status,
        created_at=video.created_at,
        tags=_build_tags_out(video),
    )


def _build_video_detail(video) -> VideoDetail:
    return VideoDetail(
        id=video.id,
        filename=video.filename,
        filesize=video.filesize,
        duration=video.duration,
        width=video.width,
        height=video.height,
        fps=video.fps,
        mime_type=video.mime_type,
        thumbnail=video.thumbnail,
        status=video.status,
        created_at=video.created_at,
        summary=video.summary,
        critique=video.critique,
        error_message=video.error_message,
        analyzed_at=video.analyzed_at,
        analysis_duration=video.analysis_duration,
        tags=_build_tags_out(video),
        segments=[
            SegmentOut(
                id=s.id,
                start_time=s.start_time,
                end_time=s.end_time,
                title=s.title,
                description=s.description,
                visual_description=s.visual_description,
                audio_description=s.audio_description,
                segment_index=s.segment_index,
            )
            for s in video.segments
        ],
        critique_annotations=[
            CritiqueAnnotationOut(
                id=ca.id,
                timestamp=ca.timestamp,
                end_time=ca.end_time,
                type=ca.type,
                comment=ca.comment,
                severity=ca.severity,
            )
            for ca in video.critique_annotations
        ],
    )


@router.post("/upload", response_model=list[UploadResponse], status_code=202)
async def upload_videos(
    files: list[UploadFile],
    db: AsyncSession = Depends(get_db),
):
    """批次上傳影片"""
    results = []
    for file in files:
        if not file.content_type or not file.content_type.startswith("video/"):
            continue

        filepath, filesize = await save_upload_file(file)
        video = await create_video_record(db, filepath, file.filename or "unknown", filesize)
        results.append(UploadResponse(
            video_id=video.id,
            filename=video.filename,
            status=video.status,
        ))

    if not results:
        raise HTTPException(status_code=400, detail="未提供有效的影片檔案")

    # 自動觸發分析
    for r in results:
        enqueue_analysis(r.video_id)

    return results


@router.get("", response_model=VideoListResponse)
async def list_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """取得影片列表"""
    videos, total = await get_video_list(db, page, page_size, status)
    return VideoListResponse(
        items=[_build_video_summary(v) for v in videos],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{video_id}", response_model=VideoDetail)
async def get_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """取得影片詳情"""
    video = await get_video_detail(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="影片不存在")
    return _build_video_detail(video)


@router.delete("/{video_id}", status_code=204)
async def remove_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """刪除影片"""
    deleted = await delete_video(db, video_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="影片不存在")


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """串流播放影片"""
    video = await get_video_detail(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="影片不存在")

    video_path = settings.storage_path / video.filepath
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="影片檔案不存在")

    return FileResponse(
        path=str(video_path),
        media_type=video.mime_type,
        filename=video.filename,
    )


@router.post("/{video_id}/thumbnail/regenerate", status_code=200)
async def regenerate_thumbnail(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """重新產生影片縮圖（ffmpeg 安裝後補跑用）"""
    video = await get_video_detail(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="影片不存在")

    video_path = settings.storage_path / video.filepath
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="影片檔案不存在")

    thumb_name = f"{video_path.stem}.jpg"
    thumb_path = settings.thumbnails_path / thumb_name
    ok = await generate_thumbnail(video_path, thumb_path)
    if not ok:
        raise HTTPException(status_code=500, detail="縮圖產生失敗，請確認 ffmpeg 已安裝")

    thumbnail_rel = f"thumbnails/{thumb_name}"
    await db.execute(
        sa_update(Video).where(Video.id == video_id).values(thumbnail=thumbnail_rel)
    )
    return {"thumbnail": thumbnail_rel}


@router.get("/{video_id}/thumbnail")
async def get_thumbnail(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """取得影片縮圖"""
    video = await get_video_detail(db, video_id)
    if not video or not video.thumbnail:
        raise HTTPException(status_code=404, detail="縮圖不存在")

    thumb_path = settings.storage_path / video.thumbnail
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="縮圖檔案不存在")

    return FileResponse(path=str(thumb_path), media_type="image/jpeg")
