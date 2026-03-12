from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.items import ItemResponse


class QueryRoute(str, Enum):
    ANSWER = "answer"
    SUMMARY = "summary"
    TIMELINE = "timeline"


class Citation(BaseModel):
    item_id: int
    title: str
    rationale: str | None = None


class RetrievedSource(BaseModel):
    item: ItemResponse
    citation_label: str
    snippet: str
    retrieval_score: float
    semantic_score: float
    lexical_score: float


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=400)
    session_id: str = "default"


class QuestionResponse(BaseModel):
    route: QueryRoute
    answer: str
    citations: list[Citation]
    sources: list[RetrievedSource]
    structured_payload: dict[str, Any] | None = None
    response_id: str | None = None


class ConnectionRequest(BaseModel):
    item_ids: list[int] = Field(min_length=2, max_length=8)


class ConnectionResponse(BaseModel):
    explanation: str
    shared_themes: list[str]
    citations: list[Citation]
    sources: list[RetrievedSource]


class TopicSummaryRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=160)


class TopicSummaryResponse(BaseModel):
    topic: str
    summary: str
    key_people: list[str]
    key_projects: list[str]
    citations: list[Citation]
    sources: list[RetrievedSource]


class TimelineRequest(BaseModel):
    subject: str = Field(min_length=2, max_length=160)


class TimelineEvent(BaseModel):
    year: int | None = None
    label: str
    description: str
    item_id: int | None = None


class TimelineResponse(BaseModel):
    subject: str
    summary: str
    events: list[TimelineEvent]
    citations: list[Citation]
    sources: list[RetrievedSource]


class GroundedAnswerOutput(BaseModel):
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)


class ConnectionOutput(BaseModel):
    explanation: str
    shared_themes: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)


class TopicSummaryOutput(BaseModel):
    topic: str
    summary: str
    key_people: list[str] = Field(default_factory=list)
    key_projects: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)


class TimelineOutput(BaseModel):
    subject: str
    summary: str
    events: list[TimelineEvent] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
