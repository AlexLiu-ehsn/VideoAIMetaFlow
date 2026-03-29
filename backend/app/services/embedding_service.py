import logging
from uuid import UUID

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Segment, Video
from app.services.gemini_service import generate_embeddings

logger = logging.getLogger(__name__)


async def generate_video_embeddings(db: AsyncSession, video_id: UUID) -> None:
    """為影片產生 summary embedding 並寫入 DB"""
    from app.services.video_service import get_video_detail

    video = await get_video_detail(db, video_id)
    if not video or not video.summary:
        return

    # 組合 summary + 標籤文字作為影片級 embedding 來源
    tag_text = " ".join(
        f"{vt.tag.category.label}:{vt.tag.label}" for vt in video.video_tags
    )
    text = f"{video.summary}\n\n標籤: {tag_text}"

    logger.info("[%s] 產生影片 summary embedding", video.filename)
    embeddings = await generate_embeddings([text])

    if embeddings:
        await db.execute(
            update(Video)
            .where(Video.id == video_id)
            .values(summary_embedding=embeddings[0])
        )


async def generate_segment_embeddings(db: AsyncSession, video_id: UUID) -> None:
    """為影片的所有分段產生 embedding 並寫入 DB"""
    from app.services.video_service import get_video_detail

    video = await get_video_detail(db, video_id)
    if not video or not video.segments:
        return

    # 組合各分段的描述文字
    texts = []
    segment_ids = []
    for seg in video.segments:
        parts = [seg.description]
        if seg.title:
            parts.insert(0, seg.title)
        if seg.visual_description:
            parts.append(f"畫面: {seg.visual_description}")
        if seg.audio_description:
            parts.append(f"語音: {seg.audio_description}")
        texts.append("\n".join(parts))
        segment_ids.append(seg.id)

    logger.info("[%s] 產生 %d 個分段 embedding", video.filename, len(texts))
    embeddings = await generate_embeddings(texts)

    # 逐一更新分段 embedding
    for seg_id, embedding in zip(segment_ids, embeddings):
        await db.execute(
            update(Segment)
            .where(Segment.id == seg_id)
            .values(embedding=embedding)
        )


async def update_search_vectors(db: AsyncSession, video_id: UUID) -> None:
    """更新影片和分段的全文搜尋 tsvector 欄位"""
    from app.services.video_service import get_video_detail

    video = await get_video_detail(db, video_id)
    if not video:
        return

    logger.info("[%s] 更新全文搜尋 tsvector 索引", video.filename)
    # 更新影片級 search_vector
    tag_text = " ".join(vt.tag.label for vt in video.video_tags)
    summary_text = video.summary or ""
    video_text = f"{video.filename} {summary_text} {tag_text}"

    await db.execute(
        update(Video)
        .where(Video.id == video_id)
        .values(
            search_vector=func.to_tsvector("simple", video_text)
        )
    )

    # 更新分段級 search_vector
    for seg in video.segments:
        seg_text = f"{seg.title or ''} {seg.description} {seg.visual_description or ''} {seg.audio_description or ''}"
        await db.execute(
            update(Segment)
            .where(Segment.id == seg.id)
            .values(
                search_vector=func.to_tsvector("simple", seg_text)
            )
        )
