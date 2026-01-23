from datetime import datetime
from sqlmodel import SQLModel
from .models import ItemType


class ItemBase(SQLModel):
    """Base fields shared across create/update/response"""
    title: str
    type: ItemType
    creator: str | None = None
    year: int | None = None
    notes: str | None = None
    image_url: str | None = None


class ItemCreate(ItemBase):
    """Schema for creating a new item (no id or timestamps)"""
    pass


class ItemUpdate(SQLModel):
    """Schema for updating an item (all fields optional)"""
    title: str | None = None
    type: ItemType | None = None
    creator: str | None = None
    year: int | None = None
    notes: str | None = None
    image_url: str | None = None


class ItemResponse(ItemBase):
    """Schema for API responses (includes id and timestamps)"""
    id: int
    created_at: datetime
    updated_at: datetime