from anthropic import Anthropic
import os
from dotenv import load_dotenv
from .embeddings import search_items
from sqlmodel import Session
from app.models import Item
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from .conversation import get_conversation

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
    # 1. Get and validate items
    items = [session.get(Item, id) for id in item_ids]
    valid_items: list[Item] = [item for item in items if item is not None]
    
    if not valid_items:
        return "No items found with those IDs"
    
    context = build_context_from_items(valid_items)
    
    # 2. Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are analyzing items from a user's personal influence archive."),
        ("user", """Find meaningful connections and patterns between these items:
         
        {context}

        Explain:
        1. What themes or qualities connect these items?
        2. What patterns do you notice?
        3. Why might someone who loves one also appreciate the others?

        Be specific and insightful.""")
            ])
    # 3. Create LLM
    llm = ChatAnthropic(model_name="claude-sonnet-4-20250514", max_tokens_to_sample=1024) # type: ignore

    # 4. Create output parser
    output_parser = StrOutputParser()

    #  5. Build chain using LCEL
    chain = prompt | llm | output_parser

    # 6. Invoke chain
    response = chain.invoke({"context": context})
    return response


def ask_about_taste(question: str, session: Session, session_id: str = "default") -> dict:
    """Answer questions with conversation memory."""


    # 1. Search and get items
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
    
    # 2. Create prompt template with system + user messages
    prompt = ChatPromptTemplate.from_messages([
    ("system", "You are analyzing a user's personal influence archive to answer their question."),
    MessagesPlaceholder(variable_name="history"),
    ("user", """Here are the most relevant items from their collection:

{context}

User's question: {question}

Provide a thoughtful, personalized answer based on their specific collection. 
Be insightful and reference specific items when relevant.""")
])

    # 3. Create LLM 
    llm = ChatAnthropic(model_name="claude-sonnet-4-20250514", max_tokens_to_sample=1024) # type: ignore

    # 4. Create output parser
    output_parser = StrOutputParser()

    # 5. Build chain
    chain = prompt | llm | output_parser

    # 6. Wrap chain with message history
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_conversation,
        input_messages_key='question',
        history_messages_key='history'
    )

    # 7. Invoke chain with context and question and session_id
    response = chain_with_history.invoke({
        "context": context,
        "question": question
    }, config={'configurable': {'session_id': session_id}})
    # 8. Return response with sources
    return {
        'answer': response,  # From chain
        'sources': [item.model_dump() for item in items]
    }

def ask_about_taste_stream(question: str, session: Session, session_id: str = "default"):
    """Streaming version of ask_about_taste."""
    
    # Search and get items 
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
    
    # Create chain 
    prompt = ChatPromptTemplate.from_messages([
    ("system", "You are analyzing a user's personal influence archive to answer their question."),
    MessagesPlaceholder(variable_name="history"),
    ("user", """Here are the most relevant items from their collection:

{context}

User's question: {question}

Provide a thoughtful, personalized answer based on their specific collection. 
Be insightful and reference specific items when relevant.""")
])
    
    llm = ChatAnthropic(model_name="claude-sonnet-4-20250514", max_tokens_to_sample=1024) # type: ignore
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_conversation,
        input_messages_key="question",
        history_messages_key="history",
    )
    
    # Use .stream() instead of .invoke()
    for chunk in chain_with_history.stream(
        {"context": context, "question": question},
        config={"configurable": {"session_id": session_id}}
    ):
        yield chunk  # Yield each token as it comes
    


