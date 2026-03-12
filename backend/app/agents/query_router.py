from app.schemas.knowledge import QueryRoute


TIMELINE_HINTS = ("timeline", "chronology", "when", "history", "evolution")
SUMMARY_HINTS = ("summary", "summarize", "overview", "brief", "recap")


def route_question(question: str) -> QueryRoute:
    lowered = question.lower()
    if any(hint in lowered for hint in TIMELINE_HINTS):
        return QueryRoute.TIMELINE
    if any(hint in lowered for hint in SUMMARY_HINTS):
        return QueryRoute.SUMMARY
    return QueryRoute.ANSWER
