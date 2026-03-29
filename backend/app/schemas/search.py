from uuid import UUID

from pydantic import BaseModel


class TagFilter(BaseModel):
    category: str
    values: list[str]


class SearchRequest(BaseModel):
    query: str
    mode: str = "hybrid"  # hybrid | semantic | keyword
    tag_filters: list[TagFilter] = []
    search_scope: str = "both"  # videos | segments | both
    limit: int = 20
    offset: int = 0


class SearchResultItem(BaseModel):
    type: str  # video | segment
    video_id: UUID
    video_title: str
    thumbnail: str | None = None
    score: float
    segment: dict | None = None  # {id, start_time, end_time, description}
    highlight: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    total: int
