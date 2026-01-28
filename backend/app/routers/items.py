from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from app.database import get_session
from app.schemas import ItemCreate, ItemResponse
from app.models import Item, ItemType
from app.services.embeddings import store_item_embedding, search_items
from app.services.rag import find_connections, ask_about_taste, ask_about_taste_stream
from pydantic import BaseModel
import asyncio


class ConnectionRequest(BaseModel):
    item_ids: list[int]
class QuestionRequest(BaseModel):
    question: str
    session_id: str = 'default'

router = APIRouter(prefix="/items", tags=["items"])

@router.post("/", response_model=ItemResponse)
def create_item(item: ItemCreate, session: Session = Depends(get_session)):
    # 1. Convert Pydantic schema to SQLModel
    # 2. Add to session
    # 3. Commit
    # 4. Refresh to get generated ID
    # 5. Return
    db_item = Item.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    # Store embedding in Pinecone
    store_item_embedding(db_item)
    return db_item

@router.post("/connections")
def find_connections_endpoint(request: ConnectionRequest, session: Session = Depends(get_session)):
    result = find_connections(request.item_ids, session)
    return {"explanation": result}

@router.post("/ask")
def ask_endpoint(request: QuestionRequest, session: Session = Depends(get_session)):
    return ask_about_taste(request.question, session, request.session_id)

@router.post("/ask/stream")
async def ask_stream_endpoint(
    request: QuestionRequest,
    session: Session = Depends(get_session)
):
    """Streaming version of ask endpoint."""
    
    async def generate():
        for chunk in ask_about_taste_stream(
            request.question, 
            session, 
            request.session_id
        ):
            # Send each chunk immediately
            yield f"data: {chunk}\n\n"
            # Force flush
            await asyncio.sleep(0)  # Yield control to allow sending
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

@router.get("/", response_model=list[ItemResponse])
def get_items(
    session: Session = Depends(get_session),
    type: ItemType | None = None,
    limit: int = 100
):
    query = select(Item)

    if type:
        query = query.where(Item.type == type)
    
    query = query.limit(limit)

    results = session.exec(query).all()
    return results

@router.get("/search")
def search_items_endpoint( query: str, limit: int = 10, session: Session = Depends(get_session)):
    matches = search_items(query, top_k=limit)
    results = []
    for match in matches:
        item = session.get(Item, match["id"])
        if item:
            results.append({
                **item.model_dump(),  # All item fields
                "score": match["score"]  # Add similarity score
            })
    
    return results

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/{item_id}")
def delete_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
    return {"message": "Item deleted"}



