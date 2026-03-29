import asyncio
import logging
import time
from pathlib import Path

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

# 全域 Gemini 客戶端（延遲初始化）
_client: genai.Client | None = None


def get_client() -> genai.Client:
    """取得或建立 Gemini API 客戶端"""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def upload_video_to_gemini(filepath: Path) -> types.File:
    """
    上傳影片至 Gemini File API，等待處理完成後回傳 File 物件。
    Gemini File API 支援最大 20GB 檔案。
    """
    client = get_client()

    filesize_mb = filepath.stat().st_size / (1024 * 1024)
    logger.info("開始上傳影片至 Gemini: %s (%.1f MB)", filepath.name, filesize_mb)
    upload_start = time.monotonic()

    # 在 executor 中執行同步上傳（避免阻塞事件迴圈）
    loop = asyncio.get_event_loop()
    uploaded_file = await loop.run_in_executor(
        None,
        lambda: client.files.upload(file=filepath),
    )

    upload_elapsed = time.monotonic() - upload_start
    logger.info("檔案已上傳: %s (%.1fs)，等待 Gemini 處理...", uploaded_file.name, upload_elapsed)

    # 輪詢等待檔案處理完成（狀態從 PROCESSING 變為 ACTIVE）
    while uploaded_file.state == "PROCESSING":
        await asyncio.sleep(3)
        uploaded_file = await loop.run_in_executor(
            None,
            lambda: client.files.get(name=uploaded_file.name),
        )
        elapsed = time.monotonic() - upload_start
        logger.info("等待 Gemini 處理中... (%.0fs)", elapsed)

    if uploaded_file.state == "FAILED":
        raise RuntimeError(f"Gemini 檔案處理失敗: {uploaded_file.name}")

    total_elapsed = time.monotonic() - upload_start
    logger.info("Gemini 檔案已就緒: %s (總耗時 %.1fs)", uploaded_file.name, total_elapsed)
    return uploaded_file


async def generate_content(
    gemini_file: types.File,
    prompt: str,
    *,
    response_mime_type: str | None = None,
    model: str = "gemini-3.1-flash-lite-preview",
) -> str:
    """
    使用 Gemini 對影片進行分析，回傳生成的文字結果。

    Args:
        gemini_file: 已上傳的 Gemini File 物件
        prompt: 分析提示詞
        response_mime_type: 回應格式（如 "application/json"）
        model: 使用的模型名稱
    """
    client = get_client()
    loop = asyncio.get_event_loop()

    config = {}
    if response_mime_type:
        config["response_mime_type"] = response_mime_type

    generate_config = types.GenerateContentConfig(**config) if config else None

    t_start = time.monotonic()
    logger.info("傳送請求至 Gemini (%s)...", model)
    response = await loop.run_in_executor(
        None,
        lambda: client.models.generate_content(
            model=model,
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_uri(
                            file_uri=gemini_file.uri,
                            mime_type=gemini_file.mime_type,
                        ),
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ],
            config=generate_config,
        ),
    )

    logger.info("Gemini 回應完成 (%.1fs，%d chars)", time.monotonic() - t_start, len(response.text))
    return response.text


async def generate_embeddings(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    使用 Gemini Embedding 模型產生文字向量。

    Args:
        texts: 要產生 embedding 的文字列表
        task_type: 任務類型（RETRIEVAL_DOCUMENT 或 RETRIEVAL_QUERY）

    Returns:
        embedding 向量列表
    """
    client = get_client()
    loop = asyncio.get_event_loop()

    embeddings = []
    # 批次處理，每次最多 100 筆
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = await loop.run_in_executor(
            None,
            lambda b=batch: client.models.embed_content(
                model="gemini-embedding-001",
                contents=b,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=768,
                ),
            ),
        )
        embeddings.extend([e.values for e in result.embeddings])

    return embeddings


async def delete_gemini_file(file_name: str) -> None:
    """刪除 Gemini File API 上的檔案（清理用）"""
    try:
        client = get_client()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: client.files.delete(name=file_name),
        )
        logger.info("已刪除 Gemini 檔案: %s", file_name)
    except Exception as e:
        logger.warning("刪除 Gemini 檔案失敗: %s - %s", file_name, e)
