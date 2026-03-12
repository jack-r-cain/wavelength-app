from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Item, ItemType
from app.schemas import ItemCreate, ItemResponse, ItemSearchResult, ItemUpdate
from app.retrieval.pipeline import retrieve_sources
from app.services.embeddings import delete_item_embedding, store_item_embedding


router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    db_item = Item.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    background_tasks.add_task(store_item_embedding, db_item.model_copy())
    return db_item


@router.get("/", response_model=list[ItemResponse])
def get_items(
    session: Session = Depends(get_session),
    type: ItemType | None = None,
    limit: int = 100,
):
    query = select(Item)
    if type:
        query = query.where(Item.type == type)
    return session.exec(query.limit(limit)).all()


@router.get("/search", response_model=list[ItemSearchResult])
async def search_items_endpoint(
    query: str,
    limit: int = 10,
    session: Session = Depends(get_session),
):
    sources = await retrieve_sources(query, session, top_k=limit, fetch_k=max(limit * 2, 10))
    return [
        ItemSearchResult(
            **source.item.model_dump(),
            score=source.retrieval_score,
            semantic_score=source.semantic_score,
            lexical_score=source.lexical_score,
        )
        for source in sources
    ]


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


_EMBEDDING_FIELDS = {"title", "creator", "year", "notes", "type"}


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db_item.updated_at = datetime.now()

    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    if update_data.keys() & _EMBEDDING_FIELDS:
        background_tasks.add_task(store_item_embedding, db_item.model_copy())

    return db_item


@router.delete("/{item_id}")
async def delete_item(item_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
    background_tasks.add_task(delete_item_embedding, item_id)
    return {"message": "Item deleted"}
