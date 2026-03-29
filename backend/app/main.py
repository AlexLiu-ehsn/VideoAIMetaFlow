import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update

from app.api.router import api_router
from app.config import settings
from app.db.database import async_session_factory
from app.db.models import Video

# 設定日誌格式 — 在所有模組初始化前生效
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)-38s | %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)

_logger = logging.getLogger(__name__)

# 後端重啟後需要重新排入佇列的狀態
_INCOMPLETE_STATUSES = ("pending", "uploading_to_gemini", "analyzing")


async def _recover_incomplete_videos() -> None:
    """啟動時將上次未完成的分析任務重新排入佇列"""
    from app.workers.pipeline import enqueue_analysis

    async with async_session_factory() as db:
        result = await db.execute(
            select(Video.id, Video.filename, Video.status).where(
                Video.status.in_(_INCOMPLETE_STATUSES)
            )
        )
        rows = result.all()

        if not rows:
            return

        _logger.info("發現 %d 部未完成的影片，重新排入分析佇列...", len(rows))

        # 將中途狀態重置為 pending，避免殘留 uploading_to_gemini / analyzing
        interrupted_ids = [r.id for r in rows if r.status != "pending"]
        if interrupted_ids:
            await db.execute(
                update(Video)
                .where(Video.id.in_(interrupted_ids))
                .values(status="pending", error_message=None)
            )
            await db.commit()

        for row in rows:
            _logger.info("  重新排入: %s (%s)", row.filename, row.status)
            enqueue_analysis(row.id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時確保 storage 目錄存在
    settings.videos_path.mkdir(parents=True, exist_ok=True)
    settings.thumbnails_path.mkdir(parents=True, exist_ok=True)
    # 恢復上次未完成的分析任務
    await _recover_incomplete_videos()
    _logger.info("ViedoAIMetaFlow 後端服務已啟動，監聽 port %s", settings.app_port)
    yield
    _logger.info("後端服務已關閉")


app = FastAPI(
    title="ViedoAIMetaFlow",
    description="影片自動化標籤與摘要系統",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
