from datetime import datetime
from enum import Enum
from sqlmodel import Field, SQLModel


class ItemType(str, Enum):
    """Types of items that can be stored in the archive"""
    ALBUM = "album"
    FILM = "film"
    BOOK = "book"
    PERSON = "person"
    PLACE = "place"


class Item(SQLModel, table=True):
    """
    Represents an influence in the user's archive.
    
    Examples:
    - Album: "Blood on the Tracks" by Bob Dylan
    - Film: "No Country for Old Men" by Coen Brothers
    - Book: "Blood Meridian" by Cormac McCarthy
    - Person: "Elliott Smith"
    - Place: "Blue Ridge Mountains"
    """
    # Primary key
    id: int | None = Field(default=None, primary_key=True)
    
    # Core fields
    title: str = Field(index=True)  # Index for faster searches
    type: ItemType
    
    # Optional metadata
    creator: str | None = Field(default=None, index=True)  # Artist, author, director
    year: int | None = Field(default=None, ge=1700, le=2100)  # Validate reasonable year range
    notes: str | None = None  # User's personal notes about this item
    image_url: str | None = None  # Cover art, poster, photo
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)