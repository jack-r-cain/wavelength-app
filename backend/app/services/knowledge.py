import json
import logging
from collections.abc import AsyncGenerator

from openai.types.responses.response_text_delta_event import ResponseTextDeltaEvent
from sqlmodel import Session

from app.agents.query_router import route_question
from app.core.clients import get_openai_client
from app.core.config import settings
from app.models import Item
from app.retrieval.pipeline import build_grounding_context, retrieve_sources
from app.schemas.items import ItemResponse
from app.schemas.knowledge import (
    Citation,
    ConnectionOutput,
    ConnectionResponse,
    GroundedAnswerOutput,
    QueryRoute,
    QuestionResponse,
    RetrievedSource,
    TimelineOutput,
    TimelineRequest,
    TimelineResponse,
    TopicSummaryOutput,
    TopicSummaryResponse,
)
from app.services.conversation import get_conversation
from app.utils.retries import with_retries


logger = logging.getLogger(__name__)


def _ensure_openai_is_configured() -> None:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")


def _normalize_citations(
    raw_citations: list[dict],
    sources: list[RetrievedSource],
) -> list[Citation]:
    source_by_id = {source.item.id: source for source in sources}
    citations: list[Citation] = []
    for citation in raw_citations:
        item_id = citation.get("item_id")
        if item_id not in source_by_id:
            continue
        source = source_by_id[item_id]
        citations.append(
            Citation(
                item_id=item_id,
                title=source.item.title,
                rationale=citation.get("rationale"),
            )
        )
    return citations


def _fallback_citations(sources: list[RetrievedSource]) -> list[Citation]:
    return [
        Citation(item_id=source.item.id, title=source.item.title)
        for source in sources[:2]
    ]


def _serialize_structured_payload(model) -> dict | None:
    if model is None:
        return None
    return json.loads(model.model_dump_json())


async def _parse_structured_response(
    *,
    prompt: str,
    instructions: str,
    text_format,
    session_id: str | None = None,
    use_conversation: bool = False,
):
    _ensure_openai_is_configured()
    client = get_openai_client()
    conversation = get_conversation(session_id or "default") if use_conversation else None

    async def _call_model():
        response = await client.responses.parse(
            model=settings.OPENAI_MODEL,
            instructions=instructions,
            input=prompt,
            text_format=text_format,
            previous_response_id=conversation.previous_response_id if conversation else None,
            store=True if use_conversation else False,
            temperature=0.2,
            user=session_id or "wavelength",
        )
        return response

    response = await with_retries(_call_model)
    if conversation:
        conversation.previous_response_id = response.id
    return response.output_parsed, response.id


def _base_instructions(context: str) -> str:
    return (
        "You are Wavelength, a grounded personal knowledge agent.\n"
        "Answer only from the provided sources.\n"
        "If the sources do not support a claim, say so plainly.\n"
        "Every citation must use an item_id that appears in the source list.\n\n"
        f"Sources:\n{context}"
    )


async def answer_question(
    question: str,
    session: Session,
    *,
    session_id: str = "default",
) -> QuestionResponse:
    route = route_question(question)
    sources = await retrieve_sources(question, session, top_k=5, fetch_k=12)
    if not sources:
        return QuestionResponse(
            route=route,
            answer="I couldn't find enough grounded material in your knowledge base to answer that yet.",
            citations=[],
            sources=[],
            response_id=None,
        )

    context = build_grounding_context(sources)

    if route == QueryRoute.SUMMARY:
        parsed, response_id = await _parse_structured_response(
            prompt=f"Summarize this topic using the provided sources only.\nTopic: {question}",
            instructions=_base_instructions(context),
            text_format=TopicSummaryOutput,
            session_id=session_id,
            use_conversation=True,
        )
        citations = _normalize_citations(parsed.citations, sources) or _fallback_citations(sources)
        return QuestionResponse(
            route=route,
            answer=parsed.summary,
            citations=citations,
            sources=sources,
            structured_payload=_serialize_structured_payload(parsed),
            response_id=response_id,
        )

    if route == QueryRoute.TIMELINE:
        parsed, response_id = await _parse_structured_response(
            prompt=f"Build a timeline grounded only in the provided sources.\nSubject: {question}",
            instructions=_base_instructions(context),
            text_format=TimelineOutput,
            session_id=session_id,
            use_conversation=True,
        )
        citations = _normalize_citations(parsed.citations, sources) or _fallback_citations(sources)
        timeline_lines = [parsed.summary]
        for event in parsed.events:
            prefix = str(event.year) if event.year else "Undated"
            timeline_lines.append(f"{prefix}: {event.label} — {event.description}")
        return QuestionResponse(
            route=route,
            answer="\n".join(timeline_lines),
            citations=citations,
            sources=sources,
            structured_payload=_serialize_structured_payload(parsed),
            response_id=response_id,
        )

    parsed, response_id = await _parse_structured_response(
        prompt=f"Answer the user's question with grounded citations only.\nQuestion: {question}",
        instructions=_base_instructions(context),
        text_format=GroundedAnswerOutput,
        session_id=session_id,
        use_conversation=True,
    )
    citations = _normalize_citations(parsed.citations, sources) or _fallback_citations(sources)
    return QuestionResponse(
        route=route,
        answer=parsed.answer,
        citations=citations,
        sources=sources,
        structured_payload=_serialize_structured_payload(parsed),
        response_id=response_id,
    )


async def stream_answer_question(
    question: str,
    session: Session,
    *,
    session_id: str = "default",
) -> AsyncGenerator[str, None]:
    _ensure_openai_is_configured()
    sources = await retrieve_sources(question, session, top_k=5, fetch_k=12)
    if not sources:
        yield "I couldn't find enough grounded material in your knowledge base to answer that yet."
        return

    context = build_grounding_context(sources)
    instructions = _base_instructions(context)
    prompt = (
        "Answer the user's question with a concise grounded explanation. "
        "Reference source labels inline like [S1] when relevant.\n"
        f"Question: {question}"
    )

    client = get_openai_client()
    conversation = get_conversation(session_id)
    async with client.responses.stream(
        model=settings.OPENAI_MODEL,
        instructions=instructions,
        input=prompt,
        previous_response_id=conversation.previous_response_id,
        store=True,
        temperature=0.2,
        user=session_id,
    ) as stream:
        async for event in stream:
            if isinstance(event, ResponseTextDeltaEvent):
                yield event.delta
        final_response = await stream.get_final_response()
        conversation.previous_response_id = final_response.id


async def analyze_connections(
    item_ids: list[int],
    session: Session,
) -> ConnectionResponse:
    items = [session.get(Item, item_id) for item_id in item_ids]
    valid_items = [item for item in items if item is not None]
    if len(valid_items) < 2:
        return ConnectionResponse(
            explanation="Pick at least two saved items to analyze their connections.",
            shared_themes=[],
            citations=[],
            sources=[],
        )

    sources = [
        RetrievedSource(
            item=ItemResponse.model_validate(item),
            citation_label=f"S{index}",
            snippet=item.notes or item.title,
            retrieval_score=1.0,
            semantic_score=1.0,
            lexical_score=1.0,
        )
        for index, item in enumerate(valid_items, start=1)
    ]
    context = build_grounding_context(sources)
    parsed, _ = await _parse_structured_response(
        prompt="Explain the meaningful connections across these saved items.",
        instructions=_base_instructions(context),
        text_format=ConnectionOutput,
    )
    citations = _normalize_citations(parsed.citations, sources) or _fallback_citations(sources)
    return ConnectionResponse(
        explanation=parsed.explanation,
        shared_themes=parsed.shared_themes,
        citations=citations,
        sources=sources,
    )


async def summarize_topic(topic: str, session: Session) -> TopicSummaryResponse:
    sources = await retrieve_sources(topic, session, top_k=6, fetch_k=12)
    if not sources:
        return TopicSummaryResponse(
            topic=topic,
            summary="I couldn't find enough grounded material in your knowledge base to summarize that topic yet.",
            key_people=[],
            key_projects=[],
            citations=[],
            sources=[],
        )

    parsed, _ = await _parse_structured_response(
        prompt=f"Summarize this topic from the provided sources only.\nTopic: {topic}",
        instructions=_base_instructions(build_grounding_context(sources)),
        text_format=TopicSummaryOutput,
    )
    citations = _normalize_citations(parsed.citations, sources) or _fallback_citations(sources)
    return TopicSummaryResponse(
        topic=parsed.topic,
        summary=parsed.summary,
        key_people=parsed.key_people,
        key_projects=parsed.key_projects,
        citations=citations,
        sources=sources,
    )


async def build_timeline(request: TimelineRequest, session: Session) -> TimelineResponse:
    sources = await retrieve_sources(request.subject, session, top_k=8, fetch_k=16)
    if not sources:
        return TimelineResponse(
            subject=request.subject,
            summary="I couldn't find enough grounded material in your knowledge base to build a timeline yet.",
            events=[],
            citations=[],
            sources=[],
        )

    parsed, _ = await _parse_structured_response(
        prompt=f"Build a grounded timeline for this subject.\nSubject: {request.subject}",
        instructions=_base_instructions(build_grounding_context(sources)),
        text_format=TimelineOutput,
    )
    citations = _normalize_citations(parsed.citations, sources) or _fallback_citations(sources)
    return TimelineResponse(
        subject=parsed.subject,
        summary=parsed.summary,
        events=parsed.events,
        citations=citations,
        sources=sources,
    )
