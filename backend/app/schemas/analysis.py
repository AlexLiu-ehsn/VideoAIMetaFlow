from pydantic import BaseModel


class AnalysisStatus(BaseModel):
    video_id: str
    status: str
    step: str | None = None  # current analysis step
    progress: float | None = None  # 0.0 - 1.0
    message: str | None = None


class ExportRequest(BaseModel):
    video_ids: list[str]
    format: str = "json"  # json | csv | xlsx
