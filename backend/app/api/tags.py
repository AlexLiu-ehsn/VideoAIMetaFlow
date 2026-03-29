from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Tag, TagCategory, VideoTag
from app.schemas.tag import TagCategoryOut, TagWithCount

router = APIRouter()


@router.get("/categories", response_model=list[TagCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """取得所有標籤分類及其標籤數量"""
    query = (
        select(
            TagCategory,
            func.count(Tag.id).label("tag_count"),
        )
        .outerjoin(Tag)
        .group_by(TagCategory.id)
        .order_by(TagCategory.id)
    )
    result = await db.execute(query)
    rows = result.all()
    return [
        TagCategoryOut(
            id=cat.id,
            name=cat.name,
            label=cat.label,
            color=cat.color,
            tag_count=count,
        )
        for cat, count in rows
    ]


@router.get("", response_model=list[TagWithCount])
async def list_tags(
    category: str | None = Query(None, description="依分類名稱篩選"),
    db: AsyncSession = Depends(get_db),
):
    """取得所有標籤及其影片數量"""
    query = (
        select(
            Tag,
            TagCategory,
            func.count(VideoTag.video_id).label("video_count"),
        )
        .join(TagCategory)
        .outerjoin(VideoTag)
        .group_by(Tag.id, TagCategory.id)
        .order_by(TagCategory.name, Tag.label)
    )

    if category:
        query = query.where(TagCategory.name == category)

    result = await db.execute(query)
    rows = result.all()
    return [
        TagWithCount(
            id=tag.id,
            name=tag.name,
            label=tag.label,
            category_name=cat.name,
            category_label=cat.label,
            color=cat.color,
            video_count=count,
        )
        for tag, cat, count in rows
    ]
