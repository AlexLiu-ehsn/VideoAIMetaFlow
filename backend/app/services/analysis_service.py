import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import (
    CritiqueAnnotation,
    Segment,
    Tag,
    TagCategory,
    Video,
    VideoTag,
)
from app.prompts.combined import COMBINED_ANALYSIS_PROMPT
from app.services.embedding_service import (
    generate_segment_embeddings,
    generate_video_embeddings,
    update_search_vectors,
)
from app.services.gemini_service import (
    delete_gemini_file,
    generate_content,
    upload_video_to_gemini,
)

logger = logging.getLogger(__name__)


def _parse_time(time_str: str) -> float:
    """將 MM:SS 或 HH:MM:SS 格式轉換為秒數"""
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return 0.0


def _clean_json(text: str) -> str:
    """清理 LLM 回傳的 JSON 文字（移除 markdown 包裹等）"""
    text = text.strip()
    # 移除 ```json ... ``` 包裹
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


async def _update_status(
    db: AsyncSession,
    video_id: UUID,
    status: str,
    *,
    step: str | None = None,
    error: str | None = None,
    elapsed_seconds: float | None = None,
) -> None:
    """更新影片分析狀態並推送 SSE 事件"""
    values = {"status": status, "updated_at": datetime.utcnow()}
    if error:
        values["error_message"] = error
    await db.execute(update(Video).where(Video.id == video_id).values(**values))
    await db.commit()

    from app.workers.pipeline import publish_status
    publish_status(str(video_id), {
        "status": status,
        "step": step,
        "elapsed_seconds": elapsed_seconds,
        "message": error or (f"正在執行: {step}" if step else None),
    })


async def _save_tags(db: AsyncSession, video_id: UUID, tags_data: dict, video_name: str) -> None:
    """將標籤資料寫入資料庫（供 step_combined_analysis 呼叫）"""
    # 標籤分類名稱 → DB 分類的對應
    category_map = {}
    result = await db.execute(select(TagCategory))
    for cat in result.scalars().all():
        category_map[cat.name] = cat

    # 清除舊標籤（bulk DELETE 避免 autoflush 競態）
    await db.execute(delete(VideoTag).where(VideoTag.video_id == video_id))
    await db.flush()

    # 寫入新標籤
    for category_name, tag_labels in tags_data.items():
        category = category_map.get(category_name)
        if not category or not isinstance(tag_labels, list):
            continue

        for label in tag_labels:
            if not isinstance(label, str) or not label.strip():
                continue
            label = label.strip()
            name = label.lower()

            tag_result = await db.execute(
                select(Tag).where(
                    Tag.category_id == category.id,
                    Tag.name == name,
                )
            )
            tag = tag_result.scalar_one_or_none()
            if not tag:
                tag = Tag(category_id=category.id, name=name, label=label)
                db.add(tag)
                await db.flush()

            db.add(VideoTag(video_id=video_id, tag_id=tag.id))

    tag_count = sum(len(v) for v in tags_data.values() if isinstance(v, list))
    logger.info("[%s] 共提取 %d 個標籤", video_name, tag_count)


async def _save_timeline(db: AsyncSession, video_id: UUID, segments_data: list, video_name: str) -> None:
    """將時間軸分段資料寫入資料庫（供 step_combined_analysis 呼叫）"""
    if not isinstance(segments_data, list):
        raise ValueError(f"時間軸回傳格式不正確: {type(segments_data)}")

    # 清除舊分段（bulk DELETE 避免 autoflush 競態）
    await db.execute(delete(Segment).where(Segment.video_id == video_id))
    await db.flush()

    # 寫入新分段
    for idx, seg_data in enumerate(segments_data):
        segment = Segment(
            video_id=video_id,
            start_time=_parse_time(str(seg_data.get("start_time", "0:00"))),
            end_time=_parse_time(str(seg_data.get("end_time", "0:00"))),
            title=seg_data.get("title"),
            description=seg_data.get("description", ""),
            visual_description=seg_data.get("visual_description"),
            audio_description=seg_data.get("audio_description"),
            segment_index=idx,
        )
        db.add(segment)

    logger.info("[%s] 共建立 %d 個時間軸分段", video_name, len(segments_data))


async def _save_critique(db: AsyncSession, video_id: UUID, critique_data: dict, video_name: str) -> None:
    """將評析資料寫入資料庫（供 step_combined_analysis 呼叫）"""
    overall = critique_data.get("overall_assessment", "")
    await db.execute(
        update(Video).where(Video.id == video_id).values(critique=overall)
    )

    # 清除舊標註（bulk DELETE 避免 autoflush 競態）
    await db.execute(delete(CritiqueAnnotation).where(CritiqueAnnotation.video_id == video_id))
    await db.flush()

    # 寫入新標註
    annotations = critique_data.get("annotations", [])
    for ann_data in annotations:
        annotation = CritiqueAnnotation(
            video_id=video_id,
            timestamp=_parse_time(str(ann_data.get("timestamp", "0:00"))),
            end_time=_parse_time(str(ann_data["end_time"])) if ann_data.get("end_time") else None,
            type=ann_data.get("type", "suggestion"),
            comment=ann_data.get("comment", ""),
            severity=ann_data.get("severity", "info"),
        )
        db.add(annotation)

    logger.info("[%s] 共建立 %d 個評析標註", video_name, len(annotations))


async def step_combined_analysis(db: AsyncSession, video_id: UUID, gemini_file, video_name: str = "") -> None:
    """
    單一 Gemini API 呼叫完成所有分析：摘要、標籤、時間軸、評析。
    回傳統一 JSON 後分別解析並寫入資料庫。
    注意：status 更新由 run_analysis_pipeline 統一管理。
    """
    raw = await generate_content(
        gemini_file,
        COMBINED_ANALYSIS_PROMPT,
        response_mime_type="application/json",
    )
    data = json.loads(_clean_json(raw))

    # 解析摘要
    summary = data.get("summary", "").strip()
    await db.execute(
        update(Video).where(Video.id == video_id).values(summary=summary)
    )
    logger.info("[%s] 摘要字數: %d 字", video_name, len(summary))

    # 解析並儲存標籤
    await _save_tags(db, video_id, data.get("tags", {}), video_name)

    # 解析並儲存時間軸
    await _save_timeline(db, video_id, data.get("timeline", []), video_name)

    # 解析並儲存評析
    await _save_critique(db, video_id, data.get("critique", {}), video_name)

    await db.commit()


async def run_analysis_pipeline(db: AsyncSession, video_id: UUID) -> None:
    """
    執行完整的影片分析管線。

    流程：上傳至 Gemini → 摘要 → 標籤 → 時間軸 → 評析 → Embedding → 搜尋索引
    """
    pipeline_start = time.monotonic()
    try:
        # 取得影片記錄
        result = await db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        if not video:
            logger.error("影片不存在: %s", video_id)
            return

        video_path = settings.storage_path / video.filepath
        if not video_path.exists():
            await _update_status(db, video_id, "failed", error="影片檔案不存在")
            return

        vname = video.filename
        sep = "=" * 56
        logger.info(sep)
        logger.info("[%s] 開始影片分析管線", vname)
        logger.info(sep)

        # 步驟 0: 上傳至 Gemini
        logger.info("[%s] 步驟 0/3 ▶ 上傳至 Gemini File API", vname)
        t0 = time.monotonic()
        await _update_status(
            db, video_id, "uploading_to_gemini", step="upload",
            elapsed_seconds=round(time.monotonic() - pipeline_start, 1),
        )
        gemini_file = await upload_video_to_gemini(video_path)
        logger.info("[%s] ✓ Gemini 上傳完成 (%.1fs)", vname, time.monotonic() - t0)

        await db.execute(
            update(Video)
            .where(Video.id == video_id)
            .values(
                gemini_file_uri=gemini_file.uri,
                gemini_file_name=gemini_file.name,
            )
        )
        await db.commit()

        # 步驟 1: 單次 Gemini 呼叫完成所有分析（摘要、標籤、時間軸、評析）
        logger.info("[%s] 步驟 1/3 ▶ Gemini 綜合分析（摘要 + 標籤 + 時間軸 + 評析）", vname)
        t0 = time.monotonic()
        await _update_status(
            db, video_id, "analyzing", step="analyzing",
            elapsed_seconds=round(time.monotonic() - pipeline_start, 1),
        )
        await step_combined_analysis(db, video_id, gemini_file, vname)
        logger.info("[%s] ✓ Gemini 分析完成 (%.1fs)", vname, time.monotonic() - t0)

        # 步驟 2: 產生 Embedding
        logger.info("[%s] 步驟 2/3 ▶ 產生語意向量 (Embedding)", vname)
        t0 = time.monotonic()
        await _update_status(
            db, video_id, "analyzing", step="embedding",
            elapsed_seconds=round(time.monotonic() - pipeline_start, 1),
        )
        await generate_video_embeddings(db, video_id)
        await generate_segment_embeddings(db, video_id)
        await db.commit()
        logger.info("[%s] ✓ Embedding 完成 (%.1fs)", vname, time.monotonic() - t0)

        # 步驟 3: 更新全文搜尋索引
        logger.info("[%s] 步驟 3/3 ▶ 更新全文搜尋索引", vname)
        t0 = time.monotonic()
        await _update_status(
            db, video_id, "analyzing", step="indexing",
            elapsed_seconds=round(time.monotonic() - pipeline_start, 1),
        )
        await update_search_vectors(db, video_id)
        await db.commit()
        logger.info("[%s] ✓ 搜尋索引完成 (%.1fs)", vname, time.monotonic() - t0)

        # 完成
        total = round(time.monotonic() - pipeline_start, 1)
        await db.execute(
            update(Video)
            .where(Video.id == video_id)
            .values(
                status="completed",
                analyzed_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                analysis_duration=total,
            )
        )
        await db.commit()

        from app.workers.pipeline import publish_status
        publish_status(str(video_id), {
            "status": "completed",
            "step": None,
            "elapsed_seconds": total,
            "message": "分析完成",
        })
        logger.info(sep)
        logger.info("[%s] 分析管線全部完成！總耗時: %.1fs", vname, total)
        logger.info(sep)

        # 清理 Gemini 上的暫存檔案
        if gemini_file.name:
            await delete_gemini_file(gemini_file.name)

    except Exception as e:
        logger.exception("分析管線錯誤: %s", e)
        try:
            await db.rollback()
            elapsed = round(time.monotonic() - pipeline_start, 1)
            await _update_status(
                db, video_id, "failed", error=str(e),
                elapsed_seconds=elapsed,
            )
        except Exception:
            logger.exception("無法更新失敗狀態: %s", video_id)
