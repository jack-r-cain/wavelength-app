import re


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(value: str) -> set[str]:
    return set(TOKEN_RE.findall(value.lower()))


def lexical_score(query: str, text: str) -> float:
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    text_tokens = tokenize(text)
    if not text_tokens:
        return 0.0
    overlap = query_tokens & text_tokens
    return len(overlap) / len(query_tokens)


def hybrid_score(*, semantic_score: float, lexical: float) -> float:
    semantic = max(semantic_score, 0.0)
    return round((semantic * 0.75) + (lexical * 0.25), 4)
