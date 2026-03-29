import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.analysis import AnalysisStatus
from app.services.video_service import get_video_detail
from app.workers.pipeline import (
    enqueue_analysis,
    get_queue_status,
    subscribe_status,
    unsubscribe_status,
)

router = APIRouter()


@router.post("/videos/{video_id}/analyze", response_model=AnalysisStatus)
async def trigger_analysis(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """觸發或重新觸發影片分析"""
    video = await get_video_detail(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="影片不存在")

    if video.status in ("uploading_to_gemini", "analyzing"):
        return AnalysisStatus(
            video_id=str(video_id),
            status=video.status,
            message="影片正在分析中",
        )

    enqueued = enqueue_analysis(video_id)
    return AnalysisStatus(
        video_id=str(video_id),
        status="pending" if enqueued else video.status,
        message="已加入分析佇列" if enqueued else "影片已在佇列中",
    )


@router.get("/videos/{video_id}/status")
async def stream_analysis_status(video_id: uuid.UUID):
    """SSE 端點：即時推播影片分析狀態"""
    queue = subscribe_status(str(video_id))

    async def event_generator():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": "status",
                        "data": json.dumps(data, ensure_ascii=False),
                    }
                    # 分析完成或失敗時結束串流
                    if data.get("status") in ("completed", "failed"):
                        break
                except asyncio.TimeoutError:
                    # 定期傳送心跳保持連線
                    yield {"event": "ping", "data": ""}
        finally:
            unsubscribe_status(str(video_id), queue)

    return EventSourceResponse(event_generator())


@router.get("/queue")
async def analysis_queue():
    """查看分析佇列狀態"""
    return get_queue_status()
