from pydantic import BaseModel


class TagCategoryOut(BaseModel):
    id: int
    name: str
    label: str
    color: str | None = None
    tag_count: int = 0

    model_config = {"from_attributes": True}


class TagWithCount(BaseModel):
    id: int
    name: str
    label: str
    category_name: str
    category_label: str
    color: str | None = None
    video_count: int = 0

    model_config = {"from_attributes": True}
