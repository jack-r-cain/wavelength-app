from anthropic import Anthropic
import os
from dotenv import load_dotenv
from .embeddings import search_items
from sqlmodel import Session
from app.models import Item

load_dotenv()

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def build_context_from_items(items: list[Item]) -> str:
    """
    Convert list of items into formatted context for LLM.
    
    Example output:
    "1. Blood on the Tracks by Bob Dylan (album, 1975)
        Notes: raw heartbreak album
     
     2. No Country for Old Men by Cormac McCarthy (book, 2005)
        Notes: nihilistic, sparse prose"
    """
    context = ''
    for index, item in enumerate(items):
        context += f"{index + 1}. {item.title}"
        if item.creator:
            context += f" by {item.creator}"
        context += f" ({item.type}"
        if item.year:
            context += f", {item.year}"
        context += ")\n"
        if item.notes:
            context += f"        Notes: {item.notes}\n\n"
        else: context += "\n\n"
    return context


def find_connections(item_ids: list[int], session: Session) -> str:
    """
    Find and explain connections between specific items.
    
    Args:
        item_ids: List of item IDs to analyze
        session: Database session
    
    Returns:
        AI-generated explanation of connections
    """
    
    items = [session.get(Item, id) for id in item_ids]
    valid_items: list[Item] = [item for item in items if item is not None]
    
    if not valid_items:
        return "No items found with those IDs"
    
    context = build_context_from_items(valid_items)
    prompt = f"""You are analyzing items from a user's personal influence archive. 
    Find meaningful connections and patterns between these items:

    {context}

    Explain:
    1. What themes or qualities connect these items?
    2. What patterns do you notice?
    3. Why might someone who loves one also appreciate the others?

    Be specific and insightful."""

    response = anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": prompt}
    ]
)

    return response.content[0].text # type: ignore


def ask_about_taste(question: str, session: Session) -> dict:
    """
    Answer questions about user's taste using RAG.
    
    Args:
        question: User's question (e.g., "What patterns do you see in my collection?")
        session: Database session
    
    Returns:
        {
            "answer": "AI response",
            "sources": [list of items that informed the answer]
        }
    """
    # TODO:
    # 1. Use search_items(question) to find relevant items
    # 2. Fetch full items from database
    # 3. Build context
    # 4. Create prompt with question + context
    # 5. Call Claude API
    # 6. Return answer + sources
    matches = search_items(question, top_k=5)
    item_ids = [match["id"] for match in matches]
   
    items: list[Item] = []
    for item_id in item_ids:
        item = session.get(Item, item_id)
        if item:
            items.append(item)
    
    if not items:
        return {
            "answer": "I don't have enough information in your collection to answer that.",
            "sources": []
        }
    context = build_context_from_items(items)
    prompt = f"""You are analyzing a user's personal influence archive to answer their question.

    Here are the most relevant items from their collection:

    {context}

    User's question: {question}

    Provide a thoughtful, personalized answer based on their specific collection. 
    Be insightful and reference specific items when relevant."""

    response = anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": prompt}
    ]
)
    answer = response.content[0].text # type: ignore

    return {'answer': answer, 'sources': [item.model_dump() for item in items]}

    


