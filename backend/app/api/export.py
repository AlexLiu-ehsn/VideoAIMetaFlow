import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.analysis import ExportRequest
from app.services.export_service import export_csv, export_json, export_xlsx

router = APIRouter()

MIME_TYPES = {
    "json": "application/json",
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

EXTENSIONS = {
    "json": "json",
    "csv": "csv",
    "xlsx": "xlsx",
}


def _validate_format(fmt: str) -> str:
    fmt = fmt.lower()
    if fmt not in MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"不支援的匯出格式: {fmt}，可用: json, csv, xlsx")
    return fmt


@router.get("/videos/{video_id}/export")
async def export_single_video(
    video_id: uuid.UUID,
    format: str = Query("json", description="匯出格式: json, csv, xlsx"),
    db: AsyncSession = Depends(get_db),
):
    """匯出單一影片 metadata"""
    fmt = _validate_format(format)
    video_ids = [video_id]

    if fmt == "json":
        data = await export_json(db, video_ids)
    elif fmt == "csv":
        data = await export_csv(db, video_ids)
    else:
        data = await export_xlsx(db, video_ids)

    return Response(
        content=data,
        media_type=MIME_TYPES[fmt],
        headers={
            "Content-Disposition": f'attachment; filename="video_metadata.{EXTENSIONS[fmt]}"'
        },
    )


@router.post("/export/batch")
async def export_batch(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
):
    """批次匯出多個影片 metadata"""
    fmt = _validate_format(request.format)
    video_ids = [uuid.UUID(vid) for vid in request.video_ids]

    if not video_ids:
        raise HTTPException(status_code=400, detail="未指定影片")

    if fmt == "json":
        data = await export_json(db, video_ids)
    elif fmt == "csv":
        data = await export_csv(db, video_ids)
    else:
        data = await export_xlsx(db, video_ids)

    return Response(
        content=data,
        media_type=MIME_TYPES[fmt],
        headers={
            "Content-Disposition": f'attachment; filename="videos_metadata.{EXTENSIONS[fmt]}"'
        },
    )
