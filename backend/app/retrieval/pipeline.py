from sqlmodel import Session

from app.models import Item
from app.retrieval.ranking import hybrid_score, lexical_score
from app.schemas.items import ItemResponse
from app.schemas.knowledge import RetrievedSource
from app.services.embeddings import create_text_for_embedding, search_items


def _item_snippet(item: Item) -> str:
    if item.notes:
        return item.notes[:220]

    parts = [item.title]
    if item.creator:
        parts.append(item.creator)
    if item.year:
        parts.append(str(item.year))
    return " • ".join(parts)


async def retrieve_sources(
    query: str,
    session: Session,
    *,
    top_k: int = 5,
    fetch_k: int = 12,
) -> list[RetrievedSource]:
    matches = await search_items(query, top_k=max(top_k, fetch_k))
    sources: list[RetrievedSource] = []

    for index, match in enumerate(matches, start=1):
        item = session.get(Item, match["id"])
        if not item:
            continue
        semantic = float(match["score"])
        lexical = lexical_score(query, create_text_for_embedding(item))
        score = hybrid_score(semantic_score=semantic, lexical=lexical)
        sources.append(
            RetrievedSource(
                item=ItemResponse.model_validate(item),
                citation_label=f"S{index}",
                snippet=_item_snippet(item),
                retrieval_score=score,
                semantic_score=semantic,
                lexical_score=lexical,
            )
        )

    sources.sort(key=lambda source: source.retrieval_score, reverse=True)
    return sources[:top_k]


def build_grounding_context(sources: list[RetrievedSource]) -> str:
    lines: list[str] = []
    for source in sources:
        item = source.item
        descriptor = f"{item.title} ({item.type}"
        if item.year:
            descriptor += f", {item.year}"
        descriptor += ")"
        if item.creator:
            descriptor += f" by {item.creator}"
        lines.append(
            f"[{source.citation_label}] item_id={item.id} :: {descriptor}\n"
            f"Snippet: {source.snippet}"
        )
    return "\n\n".join(lines)
