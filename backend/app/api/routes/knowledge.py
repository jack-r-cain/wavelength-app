import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.database import get_session
from app.schemas import (
    ConnectionRequest,
    ConnectionResponse,
    QuestionRequest,
    QuestionResponse,
    TimelineRequest,
    TimelineResponse,
    TopicSummaryRequest,
    TopicSummaryResponse,
)
from app.services.knowledge import (
    analyze_connections,
    answer_question,
    build_timeline,
    stream_answer_question,
    summarize_topic,
)


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    session: Session = Depends(get_session),
):
    return await answer_question(request.question, session, session_id=request.session_id)


@router.post("/ask/stream")
async def ask_question_stream(
    request: QuestionRequest,
    session: Session = Depends(get_session),
):
    async def generate():
        async for chunk in stream_answer_question(
            request.question,
            session,
            session_id=request.session_id,
        ):
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/connections", response_model=ConnectionResponse)
async def find_connections(
    request: ConnectionRequest,
    session: Session = Depends(get_session),
):
    return await analyze_connections(request.item_ids, session)


@router.post("/summaries", response_model=TopicSummaryResponse)
async def summarize(
    request: TopicSummaryRequest,
    session: Session = Depends(get_session),
):
    return await summarize_topic(request.topic, session)


@router.post("/timeline", response_model=TimelineResponse)
async def timeline(
    request: TimelineRequest,
    session: Session = Depends(get_session),
):
    return await build_timeline(request, session)
