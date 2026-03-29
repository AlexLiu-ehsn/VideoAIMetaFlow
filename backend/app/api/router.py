from fastapi import APIRouter

from app.api import analysis, export, search, tags, videos

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(videos.router, prefix="/videos", tags=["影片管理"])
api_router.include_router(search.router, prefix="/search", tags=["搜尋"])
api_router.include_router(tags.router, prefix="/tags", tags=["標籤"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["分析"])
api_router.include_router(export.router, tags=["匯出"])
