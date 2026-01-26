from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
import os

load_dotenv()


    
# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pinecone_client.Index("wavelength-dev")


def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector for given text."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def create_text_for_embedding(item) -> str:
    """Create searchable text from item."""
    text = [item.title]
    if item.creator:
        text.append(f"by {item.creator}")
    
    # Add type and year
    text.append(f"{item.type}")
    if item.year:
        text.append(f"from {item.year}")
    
    # Add notes if exists
    if item.notes:
        text.append(f"Notes: {item.notes}")
    
    # Join with periods or commas
    return ". ".join(text)



def store_item_embedding(item):
    # Create searchable text
    text = create_text_for_embedding(item)
    
    # Generate embedding
    embedding = generate_embedding(text)
    
    # Store in Pinecone
    index.upsert([
        {
            "id": str(item.id),  # Convert to string
            "values": embedding,
            "metadata": {
                "title": item.title,
                "type": item.type,
                "creator": item.creator,
                "year": item.year
            }
        }
    ])


def search_items(query: str, top_k: int = 10) -> list[dict]:
    # Generate embedding for search query
    query_embedding = generate_embedding(query)
    
    # Search Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    # Return matches
    return [
        {
            "id": int(match.id),
            "score": match.score,
            "title": match.metadata.get("title"),
            "type": match.metadata.get("type"),
            "creator": match.metadata.get("creator"),
            "year": match.metadata.get("year"),
        }
        for match in results.matches # type: ignore
    ]  