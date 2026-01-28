from langchain_core.chat_history import InMemoryChatMessageHistory

# Store conversations by session_id
conversations: dict[str, InMemoryChatMessageHistory] = {}

def get_conversation(session_id: str) -> InMemoryChatMessageHistory:
    """Get or create a conversation history."""
    if session_id not in conversations:
        conversations[session_id] = InMemoryChatMessageHistory()
    return conversations[session_id]