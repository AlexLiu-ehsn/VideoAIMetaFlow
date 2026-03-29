from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from app.services.search_service import hybrid_search

router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search_videos(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """混合搜尋（向量 + 關鍵字 + RRF 合併）"""
    results, total = await hybrid_search(
        db=db,
        query=request.query,
        mode=request.mode,
        tag_filters=[f.model_dump() for f in request.tag_filters],
        search_scope=request.search_scope,
        limit=request.limit,
        offset=request.offset,
    )

    return SearchResponse(
        results=[
            SearchResultItem(
                type=r["type"],
                video_id=r["video_id"],
                video_title=r["video_title"],
                thumbnail=r["thumbnail"],
                score=r["score"],
                segment=r["segment"],
                highlight=r["highlight"],
            )
            for r in results
        ],
        total=total,
    )
