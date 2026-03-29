import asyncio
import logging
from collections import defaultdict
from uuid import UUID

from app.config import settings
from app.db.database import async_session_factory
from app.services.analysis_service import run_analysis_pipeline

logger = logging.getLogger(__name__)

# 並行控制信號量
_semaphore: asyncio.Semaphore | None = None

# SSE 狀態發布：video_id → list[asyncio.Queue]
_status_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

# 追蹤正在執行的分析任務
_active_tasks: dict[str, asyncio.Task] = {}


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(settings.max_concurrent_analysis)
    return _semaphore


def publish_status(video_id: str, data: dict) -> None:
    """推送分析狀態至所有訂閱者"""
    for queue in _status_subscribers.get(video_id, []):
        try:
            queue.put_nowait(data)
        except asyncio.QueueFull:
            pass  # 丟棄溢出的事件


def subscribe_status(video_id: str) -> asyncio.Queue:
    """訂閱影片分析狀態，回傳一個 Queue"""
    queue = asyncio.Queue(maxsize=50)
    _status_subscribers[video_id].append(queue)
    return queue


def unsubscribe_status(video_id: str, queue: asyncio.Queue) -> None:
    """取消訂閱"""
    subscribers = _status_subscribers.get(video_id, [])
    if queue in subscribers:
        subscribers.remove(queue)
    if not subscribers and video_id in _status_subscribers:
        del _status_subscribers[video_id]


async def _run_with_semaphore(video_id: UUID) -> None:
    """在信號量限制下執行分析管線"""
    sem = _get_semaphore()
    async with sem:
        async with async_session_factory() as db:
            try:
                await run_analysis_pipeline(db, video_id)
            except Exception:
                logger.exception("分析任務異常: %s", video_id)
            finally:
                # 清理 active task
                _active_tasks.pop(str(video_id), None)


def enqueue_analysis(video_id: UUID) -> bool:
    """
    將影片加入分析佇列（建立背景任務）。
    如果該影片已在分析中則跳過。
    回傳 True 表示成功排入佇列。
    """
    vid_str = str(video_id)
    if vid_str in _active_tasks and not _active_tasks[vid_str].done():
        logger.info("影片 %s 已在分析佇列中", video_id)
        return False

    task = asyncio.create_task(_run_with_semaphore(video_id))
    _active_tasks[vid_str] = task
    logger.info("影片 %s 已加入分析佇列", video_id)
    return True


def get_queue_status() -> dict:
    """取得分析佇列狀態"""
    active = sum(1 for t in _active_tasks.values() if not t.done())
    return {
        "active": active,
        "max_concurrent": settings.max_concurrent_analysis,
    }
