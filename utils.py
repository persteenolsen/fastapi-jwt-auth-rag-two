"""
Utility functions for the RAG pipeline.

This module contains the core application services:

- PostgreSQL + pgvector database initialization
- HuggingFace embedding generation
- Text cleaning and chunking
- Document ingestion
- Vector similarity retrieval
- Groq LLM communication

The API routes should call these functions but should not contain
the implementation details of the RAG pipeline.
"""

# ============================================================
# IMPORTS
# ============================================================

import asyncio
import requests
import httpx
import numpy as np

from sqlalchemy import create_engine, text
from groq import Groq

from fastapi import HTTPException

from config import (
    DATABASE_URL,
    GROQ_API_KEY,
    HF_TOKEN,
)

# ============================================================
# CLIENTS AND CONFIGURATION
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

client = Groq(api_key=GROQ_API_KEY)


# HuggingFace inference endpoint used for generating embeddings.
HF_URL = (
    "https://router.huggingface.co/"
    "hf-inference/models/"
    "sentence-transformers/all-MiniLM-L6-v2/"
    "pipeline/feature-extraction"
)


EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Increment this if the embedding strategy changes.
# This allows future migrations/re-indexing decisions.
EMBED_VERSION = 2


# ============================================================
# EMBEDDINGS
# ============================================================


def normalize(vec):
    """
    Normalize an embedding vector.

    Vector normalization allows cosine similarity searches to work
    consistently regardless of the original vector magnitude.
    """

    vector = np.array(vec)

    return (vector / np.linalg.norm(vector)).tolist()


async def hf_embed(texts: list[str]):
    """
    Generate embeddings using HuggingFace.

    The function is asynchronous because the operation is an external
    HTTP request and may take several seconds.
    """

    async with httpx.AsyncClient(timeout=60.0) as http_client:

        response = await http_client.post(
            HF_URL,
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"inputs": texts},
        )

        response.raise_for_status()

        return response.json()


def embed_batch(texts: list[str]):
    """
    Synchronous wrapper around the async HuggingFace call.

    Batches are used because sending multiple texts in one request is
    significantly faster than embedding documents individually.

    A small retry mechanism is included because external APIs can
    occasionally fail temporarily.
    """

    for attempt in range(3):

        try:

            vectors = asyncio.run(hf_embed(texts))

            return [normalize(vector) for vector in vectors]

        except Exception as error:

            if attempt == 2:
                raise error


# ============================================================
# DATABASE
# ============================================================


def init_db():
    """
    Initialize PostgreSQL objects required by the RAG system.

    Creates:
    - pgvector extension
    - documents table
    - vector similarity index
    """

    with engine.begin() as conn:

        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT,
                embedding VECTOR(384),
                source TEXT,
                embedding_model TEXT,
                embedding_version INT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS documents_embedding_idx
            ON documents
            USING ivfflat
            (embedding vector_cosine_ops)
            WITH (lists = 100);
            """))


# ============================================================
# DOCUMENT PROCESSING
# ============================================================


def chunk_txt(text_value: str):
    """
    Split text documents into smaller searchable chunks.

    Current strategy:
    A new chunk starts whenever a line begins with "Topic:".

    This works well for structured text files. More advanced chunking
    strategies can be added later without changing the RAG pipeline.
    """

    chunks = []

    current_chunk = []

    for line in text_value.splitlines():

        line = line.strip()

        if line.startswith("Topic:"):

            if current_chunk:

                chunks.append(" ".join(current_chunk))

                current_chunk = []

        if line:

            current_chunk.append(line)

    if current_chunk:

        chunks.append(" ".join(current_chunk))

    return chunks


def fetch_txt_clean(url: str):
    """
    Download and clean a plain text document.

    Only .txt resources are accepted because the ingestion pipeline
    expects clean text rather than HTML pages.
    """

    try:

        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Request failed",
        )

    if response.status_code != 200:

        raise HTTPException(
            status_code=400,
            detail="Failed to fetch URL",
        )

    content_type = response.headers.get("Content-Type", "")

    if not ("text/plain" in content_type or url.endswith(".txt")):

        raise HTTPException(
            status_code=400,
            detail="URL must be .txt",
        )

    lines = [line.strip() for line in response.text.splitlines() if line.strip()]

    return "\n".join(lines)


# ============================================================
# INGESTION WORKER
# ============================================================


def process_chunks(chunks: list[str], source: str):
    """
    Store document chunks and their embeddings.

    This function is normally executed as a FastAPI BackgroundTask
    so large documents do not block the API response.
    """

    batch_size = 32

    with engine.begin() as conn:

        for index in range(0, len(chunks), batch_size):

            batch = chunks[index : index + batch_size]

            vectors = embed_batch(batch)

            for chunk, vector in zip(batch, vectors):

                conn.execute(
                    text("""
                    INSERT INTO documents
                    (
                        content,
                        embedding,
                        source,
                        embedding_model,
                        embedding_version
                    )
                    VALUES
                    (
                        :content,
                        CAST(:embedding AS vector),
                        :source,
                        :model,
                        :version
                    )
                    """),
                    {
                        "content": chunk,
                        "embedding": vector,
                        "source": source,
                        "model": EMBED_MODEL,
                        "version": EMBED_VERSION,
                    },
                )


# ============================================================
# RETRIEVAL
# ============================================================


def retrieve(query: str, k: int = 5):
    """
    Find the most similar document chunks for a query.

    Returns a list containing:
    - document content
    - original source URL
    """

    query_vector = embed_batch([query])[0]

    with engine.begin() as conn:

        rows = conn.execute(
            text("""
            SELECT content, source
            FROM documents
            ORDER BY embedding <-> CAST(:embedding AS vector)
            LIMIT :k
            """),
            {
                "embedding": query_vector,
                "k": k,
            },
        ).fetchall()

    return [
        {
            "content": row[0],
            "source": row[1],
        }
        for row in rows
    ]


# ============================================================
# LARGE LANGUAGE MODEL
# ============================================================


def llm(prompt: str):
    """
    Send the final RAG prompt to Groq and return the answer text.

    Keeping this wrapper separate makes it easier to later replace
    the model provider or add streaming responses.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
        max_tokens=800,
    )

    return response.choices[0].message.content
