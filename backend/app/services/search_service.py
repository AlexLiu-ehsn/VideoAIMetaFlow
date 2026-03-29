import logging
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Segment, Tag, TagCategory, Video, VideoTag
from app.services.gemini_service import generate_embeddings

logger = logging.getLogger(__name__)


async def _vector_search_videos(
    db: AsyncSession,
    query_embedding: list[float],
    limit: int,
    tag_filter_ids: list[int] | None = None,
) -> list[dict]:
    """pgvector 向量搜尋影片"""
    query = (
        select(
            Video.id,
            Video.filename,
            Video.thumbnail,
            Video.summary_embedding.cosine_distance(query_embedding).label("distance"),
        )
        .where(Video.summary_embedding.is_not(None))
        .order_by("distance")
        .limit(limit)
    )

    if tag_filter_ids:
        query = query.where(
            Video.id.in_(
                select(VideoTag.video_id).where(VideoTag.tag_id.in_(tag_filter_ids))
            )
        )

    result = await db.execute(query)
    return [
        {
            "type": "video",
            "video_id": row.id,
            "video_title": row.filename,
            "thumbnail": row.thumbnail,
            "score": 1 - row.distance,  # cosine similarity
            "segment": None,
            "highlight": None,
        }
        for row in result.all()
    ]


async def _vector_search_segments(
    db: AsyncSession,
    query_embedding: list[float],
    limit: int,
) -> list[dict]:
    """pgvector 向量搜尋分段"""
    query = (
        select(
            Segment.id,
            Segment.video_id,
            Segment.start_time,
            Segment.end_time,
            Segment.description,
            Segment.title,
            Video.filename,
            Video.thumbnail,
            Segment.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .join(Video, Segment.video_id == Video.id)
        .where(Segment.embedding.is_not(None))
        .order_by("distance")
        .limit(limit)
    )

    result = await db.execute(query)
    return [
        {
            "type": "segment",
            "video_id": row.video_id,
            "video_title": row.filename,
            "thumbnail": row.thumbnail,
            "score": 1 - row.distance,
            "segment": {
                "id": str(row.id),
                "start_time": row.start_time,
                "end_time": row.end_time,
                "description": row.description,
            },
            "highlight": row.description[:200] if row.description else None,
        }
        for row in result.all()
    ]


async def _fts_search_videos(
    db: AsyncSession,
    query: str,
    limit: int,
    tag_filter_ids: list[int] | None = None,
) -> list[dict]:
    """PostgreSQL 全文搜尋影片"""
    tsquery = func.plainto_tsquery("simple", query)

    q = (
        select(
            Video.id,
            Video.filename,
            Video.thumbnail,
            Video.summary,
            func.ts_rank(Video.search_vector, tsquery).label("rank"),
        )
        .where(Video.search_vector.op("@@")(tsquery))
        .order_by(text("rank DESC"))
        .limit(limit)
    )

    if tag_filter_ids:
        q = q.where(
            Video.id.in_(
                select(VideoTag.video_id).where(VideoTag.tag_id.in_(tag_filter_ids))
            )
        )

    result = await db.execute(q)
    return [
        {
            "type": "video",
            "video_id": row.id,
            "video_title": row.filename,
            "thumbnail": row.thumbnail,
            "score": float(row.rank),
            "segment": None,
            "highlight": (row.summary or "")[:200],
        }
        for row in result.all()
    ]


async def _fts_search_segments(
    db: AsyncSession,
    query: str,
    limit: int,
) -> list[dict]:
    """PostgreSQL 全文搜尋分段"""
    tsquery = func.plainto_tsquery("simple", query)

    q = (
        select(
            Segment.id,
            Segment.video_id,
            Segment.start_time,
            Segment.end_time,
            Segment.description,
            Video.filename,
            Video.thumbnail,
            func.ts_rank(Segment.search_vector, tsquery).label("rank"),
        )
        .join(Video, Segment.video_id == Video.id)
        .where(Segment.search_vector.op("@@")(tsquery))
        .order_by(text("rank DESC"))
        .limit(limit)
    )

    result = await db.execute(q)
    return [
        {
            "type": "segment",
            "video_id": row.video_id,
            "video_title": row.filename,
            "thumbnail": row.thumbnail,
            "score": float(row.rank),
            "segment": {
                "id": str(row.id),
                "start_time": row.start_time,
                "end_time": row.end_time,
                "description": row.description,
            },
            "highlight": row.description[:200] if row.description else None,
        }
        for row in result.all()
    ]


def _reciprocal_rank_fusion(result_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """
    Reciprocal Rank Fusion (RRF) 合併多個排序結果列表。
    對每個結果，RRF score = Σ 1/(k + rank)
    """
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for result_list in result_lists:
        for rank, item in enumerate(result_list):
            # 用 video_id + segment_id 作為唯一 key
            seg_id = item.get("segment", {}).get("id", "") if item.get("segment") else ""
            key = f"{item['video_id']}:{item['type']}:{seg_id}"

            scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
            if key not in items:
                items[key] = item

    # 依 RRF score 排序
    sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
    results = []
    for key in sorted_keys:
        item = items[key]
        item["score"] = round(scores[key], 6)
        results.append(item)

    return results


async def _resolve_tag_filter_ids(
    db: AsyncSession,
    tag_filters: list[dict],
) -> list[int] | None:
    """將標籤篩選條件轉換為 tag ID 列表"""
    if not tag_filters:
        return None

    tag_ids = []
    for f in tag_filters:
        category_name = f.get("category", "")
        values = f.get("values", [])
        if not values:
            continue

        result = await db.execute(
            select(Tag.id)
            .join(TagCategory)
            .where(TagCategory.name == category_name, Tag.name.in_(values))
        )
        tag_ids.extend([row[0] for row in result.all()])

    return tag_ids if tag_ids else None


async def hybrid_search(
    db: AsyncSession,
    query: str,
    mode: str = "hybrid",
    tag_filters: list[dict] | None = None,
    search_scope: str = "both",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """
    執行混合搜尋。

    Args:
        query: 搜尋查詢
        mode: hybrid | semantic | keyword
        tag_filters: 標籤篩選
        search_scope: videos | segments | both
        limit: 結果數量上限
        offset: 偏移量

    Returns:
        (results, total)
    """
    tag_filter_ids = await _resolve_tag_filter_ids(db, tag_filters or [])
    result_lists: list[list[dict]] = []

    # 語意搜尋
    if mode in ("hybrid", "semantic"):
        embeddings = await generate_embeddings([query], task_type="RETRIEVAL_QUERY")
        if embeddings:
            query_embedding = embeddings[0]
            if search_scope in ("videos", "both"):
                result_lists.append(
                    await _vector_search_videos(db, query_embedding, limit, tag_filter_ids)
                )
            if search_scope in ("segments", "both"):
                result_lists.append(
                    await _vector_search_segments(db, query_embedding, limit)
                )

    # 關鍵字搜尋
    if mode in ("hybrid", "keyword"):
        if search_scope in ("videos", "both"):
            result_lists.append(
                await _fts_search_videos(db, query, limit, tag_filter_ids)
            )
        if search_scope in ("segments", "both"):
            result_lists.append(
                await _fts_search_segments(db, query, limit)
            )

    # 合併結果
    if len(result_lists) == 1:
        merged = result_lists[0]
    elif len(result_lists) > 1:
        merged = _reciprocal_rank_fusion(result_lists)
    else:
        merged = []

    total = len(merged)
    return merged[offset:offset + limit], total
