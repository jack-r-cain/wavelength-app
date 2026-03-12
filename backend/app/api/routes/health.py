from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from app.core.config import settings
from app.database import get_session
from app.schemas import HealthResponse
from app.utils.request_context import get_request_id


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(session: Session = Depends(get_session)):
    session.exec(text("SELECT 1"))
    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        environment=settings.APP_ENV,
        request_id=get_request_id(),
        checks={
            "database": "ok",
            "openai": "configured" if bool(settings.OPENAI_API_KEY) else "missing",
            "pinecone": "configured" if bool(settings.PINECONE_API_KEY) else "missing",
        },
    )
