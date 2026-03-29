import asyncio
import json
import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.models import Segment, Tag, TagCategory, Video, VideoTag

logger = logging.getLogger(__name__)


def _find_executable(name: str) -> str:
    """搜尋可執行檔路徑，優先使用 PATH，再搜尋 winget 常見安裝位置"""
    found = shutil.which(name)
    if found:
        return found

    # winget 安裝路徑（Windows）
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    winget_base = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
    if winget_base.exists():
        for pkg_dir in winget_base.iterdir():
            if "ffmpeg" in pkg_dir.name.lower():
                exe = next(pkg_dir.rglob(f"{name}.exe"), None)
                if exe:
                    return str(exe)

    return name  # 找不到就回傳原名，讓 subprocess 自己報錯


def _run_ffprobe(filepath: Path) -> dict:
    """同步呼叫 ffprobe（供 executor 使用，跨平台相容）"""
    cmd = [
        _find_executable("ffprobe"), "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(filepath),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        logger.warning("ffprobe 未安裝，略過元資料提取")
        return {}
    if result.returncode != 0:
        return {}
    return json.loads(result.stdout)


async def extract_video_metadata(filepath: Path) -> dict:
    """使用 ffprobe 提取影片元資料（透過 executor 避免 Windows event loop 限制）"""
    logger.info("提取影片元資料 (ffprobe): %s", filepath.name)
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, _run_ffprobe, filepath)

    if not data:
        return {}

    video_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
        None,
    )

    result = {}
    if video_stream:
        result["width"] = int(video_stream.get("width", 0))
        result["height"] = int(video_stream.get("height", 0))
        # 計算 fps
        r_frame_rate = video_stream.get("r_frame_rate", "0/1")
        if "/" in r_frame_rate:
            num, den = r_frame_rate.split("/")
            result["fps"] = round(int(num) / max(int(den), 1), 2)

    fmt = data.get("format", {})
    if fmt.get("duration"):
        result["duration"] = float(fmt["duration"])

    logger.info("元資料: 時長=%.1fs, 分辨率=%sx%s, fps=%s",
                result.get("duration", 0), result.get("width", "?"), result.get("height", "?"), result.get("fps", "?"))
    return result


async def generate_thumbnail(filepath: Path, output_path: Path, timestamp: float = 1.0) -> bool:
    """使用 ffmpeg 從影片截取縮圖（透過 executor 避免 Windows event loop 限制）"""
    logger.info("產生縮圖: %s", filepath.name)
    cmd = [
        _find_executable("ffmpeg"), "-y",
        "-ss", str(timestamp),
        "-i", str(filepath),
        "-vframes", "1",
        "-vf", "scale=480:-1",
        "-q:v", "3",
        str(output_path),
    ]
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace"),
        )
        ok = result.returncode == 0
    except FileNotFoundError:
        logger.warning("ffmpeg 未安裝，略過縮圖產生")
        return False
    if ok:
        logger.info("縮圖已產生: %s", output_path.name)
    else:
        logger.warning("縮圖產生失敗: %s", filepath.name)
    return ok


async def save_upload_file(upload_file: UploadFile) -> tuple[Path, int]:
    """儲存上傳檔案，回傳 (路徑, 檔案大小)"""
    file_id = uuid.uuid4().hex[:12]
    # 磁碟檔名只用 ASCII（避免 Windows subprocess 中文路徑編碼問題）
    original_name = upload_file.filename or "video"
    suffix = Path(original_name).suffix or ".mp4"
    safe_name = f"{file_id}{suffix}"
    filepath = settings.videos_path / safe_name
    logger.info("儲存上傳檔案: %s", upload_file.filename)

    filesize = 0
    async with aiofiles.open(filepath, "wb") as f:
        while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
            await f.write(chunk)
            filesize += len(chunk)

    logger.info("檔案已儲存: %s (%.1f MB)", safe_name, filesize / (1024 * 1024))
    return filepath, filesize


async def create_video_record(db: AsyncSession, filepath: Path, filename: str, filesize: int) -> Video:
    """建立影片資料庫記錄"""
    logger.info("建立影片記錄: %s", filename)
    # 提取元資料
    metadata = await extract_video_metadata(filepath)

    # 產生縮圖
    thumb_name = f"{filepath.stem}.jpg"
    thumb_path = settings.thumbnails_path / thumb_name
    thumb_ok = await generate_thumbnail(filepath, thumb_path)

    video = Video(
        filename=filename,
        filepath=str(filepath.relative_to(settings.storage_path)),
        filesize=filesize,
        duration=metadata.get("duration"),
        width=metadata.get("width"),
        height=metadata.get("height"),
        fps=metadata.get("fps"),
        thumbnail=f"thumbnails/{thumb_name}" if thumb_ok else None,
        status="pending",
    )
    db.add(video)
    await db.flush()
    logger.info("影片記錄建立完成 (ID: %s)，狀態: %s", video.id, video.status)
    return video


async def get_video_list(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[Video], int]:
    """取得影片列表（含標籤）"""
    query = (
        select(Video)
        .options(
            selectinload(Video.video_tags).selectinload(VideoTag.tag).selectinload(Tag.category)
        )
        .order_by(Video.created_at.desc())
    )

    if status:
        query = query.where(Video.status == status)

    # 計算總數
    count_query = select(func.count(Video.id))
    if status:
        count_query = count_query.where(Video.status == status)
    total = (await db.execute(count_query)).scalar() or 0

    # 分頁
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    videos = list(result.scalars().all())

    return videos, total


async def get_video_detail(db: AsyncSession, video_id: uuid.UUID) -> Video | None:
    """取得影片詳情（含所有關聯資料）"""
    query = (
        select(Video)
        .options(
            selectinload(Video.video_tags).selectinload(VideoTag.tag).selectinload(Tag.category),
            selectinload(Video.segments),
            selectinload(Video.critique_annotations),
        )
        .where(Video.id == video_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def delete_video(db: AsyncSession, video_id: uuid.UUID) -> bool:
    """刪除影片及其所有關聯資料"""
    video = await get_video_detail(db, video_id)
    if not video:
        return False

    # 刪除實體檔案
    video_path = settings.storage_path / video.filepath
    if video_path.exists():
        video_path.unlink()

    if video.thumbnail:
        thumb_path = settings.storage_path / video.thumbnail
        if thumb_path.exists():
            thumb_path.unlink()

    await db.delete(video)
    return True
