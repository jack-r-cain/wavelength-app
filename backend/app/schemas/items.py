from datetime import datetime

from sqlmodel import SQLModel

from app.models import ItemType


class ItemBase(SQLModel):
    title: str
    type: ItemType
    creator: str | None = None
    year: int | None = None
    notes: str | None = None
    image_url: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    title: str | None = None
    type: ItemType | None = None
    creator: str | None = None
    year: int | None = None
    notes: str | None = None
    image_url: str | None = None


class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ItemSearchResult(ItemResponse):
    score: float
    semantic_score: float
    lexical_score: float
