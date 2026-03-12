from dataclasses import dataclass


@dataclass
class ConversationState:
    previous_response_id: str | None = None


_conversations: dict[str, ConversationState] = {}


def get_conversation(session_id: str) -> ConversationState:
    if session_id not in _conversations:
        _conversations[session_id] = ConversationState()
    return _conversations[session_id]
