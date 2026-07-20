# app.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from sqlalchemy import create_engine, text

from groq import Groq
import numpy as np
import requests

import httpx
import asyncio

from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from auth import create_access_token, verify_token
from models import LoginRequest, TokenResponse, PromptRequest, URLRequest

from config import GROQ_API_KEY, DATABASE_URL, HF_TOKEN
from config import FAKE_USERNAME, FAKE_PASSWORD, ACCESS_TOKEN_EXPIRE_MINUTES

# -----------------------------
# APP
# -----------------------------
app = FastAPI(
    title="Python + FastApi + JWT Auth + RAG Pipeline + HF embeddings",
    description="20-07-2026 - FastAPI with JWT Auth serving an RAG Application powered by Groq + HuggingFace embeddings",
    version="0.0.2",
    contact={
        "name": "Per Olsen",
        "url": "https://persteenolsen.netlify.app",
    },
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
client = Groq(api_key=GROQ_API_KEY)


# ------------------------------
# LOGIN FOR VUE SPA
# ------------------------------
@app.post("/login-spa", response_model=TokenResponse)
def login_spa(request: LoginRequest):

    if request.username != FAKE_USERNAME or request.password != FAKE_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(
        {"sub": request.username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(access_token=access_token)


# ------------------------------
# OAUTH2 TOKEN FOR SWAGGER
# ------------------------------
@app.post("/token", response_model=TokenResponse)
def get_token(form: OAuth2PasswordRequestForm = Depends()):

    if form.username != FAKE_USERNAME or form.password != FAKE_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(
        {"sub": form.username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(access_token=access_token)


# -----------------------------
# EMBEDDING CONFIG
# -----------------------------
HF_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_VERSION = 2


# -----------------------------
# UTILS
# -----------------------------
def normalize(vec):
    v = np.array(vec)
    return (v / np.linalg.norm(v)).tolist()


async def hf_embed(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            HF_URL,
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"inputs": texts},
        )
        response.raise_for_status()
        return response.json()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Sync wrapper around async HF call
    """
    for attempt in range(3):
        try:
            vectors = asyncio.run(hf_embed(texts))
            return [normalize(v) for v in vectors]
        except Exception as e:
            if attempt == 2:
                raise e


# -----------------------------
# DB INIT
# -----------------------------
def init_db():
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
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))


# -----------------------------
# CHUNKING
# -----------------------------
# 13-04-2026 - Simple chunking based on "Topic:" lines. Adjust as needed.
def chunk_txt(text: str):
    chunks = []
    current_chunk = []

    for line in text.splitlines():
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


# -----------------------------
# FETCH TEXT
# -----------------------------
def fetch_txt_clean(url: str) -> str:
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    except Exception:
        raise HTTPException(status_code=400, detail="Request failed")

    if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch URL")

    content_type = res.headers.get("Content-Type", "")

    if not ("text/plain" in content_type or url.endswith(".txt")):
        raise HTTPException(status_code=400, detail="URL must be .txt")

    lines = [line.strip() for line in res.text.splitlines() if line.strip()]
    return "\n".join(lines)


# -----------------------------
# BACKGROUND WORKER
# -----------------------------
def process_chunks(chunks: list[str], source: str):
    # Batch processing (important for speed)
    batch_size = 32

    with engine.begin() as conn:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            vectors = embed_batch(batch)

            for chunk, vec in zip(batch, vectors):
                conn.execute(
                    text("""
                        INSERT INTO documents 
                        (content, embedding, source, embedding_model, embedding_version)
                        VALUES (:content, CAST(:embedding AS vector), :source, :model, :version)
                    """),
                    {
                        "content": chunk,
                        "embedding": vec,
                        "source": source,
                        "model": EMBED_MODEL,
                        "version": EMBED_VERSION,
                    },
                )


# -----------------------------
# RETRIEVAL
# -----------------------------
def retrieve(query: str, k: int = 5):
    qvec = embed_batch([query])[0]

    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT content, source
                FROM documents
                ORDER BY embedding <-> CAST(:embedding AS vector)
                LIMIT :k
            """),
            {"embedding": qvec, "k": k},
        ).fetchall()

    return [{"content": r[0], "source": r[1]} for r in rows]


# -----------------------------
# LLM
# -----------------------------
def llm(prompt: str):
    res = client.chat.completions.create(
        # 29-06-2026 - Will soon be out of service at Groq
        # model="llama-3.1-8b-instant",
        # 29-06-2026 - This is the solution for now :-)
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=800,
    )
    return res.choices[0].message.content


# -----------------------------
# ROUTES
# -----------------------------
@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/debug/retrieve")
def debug(req: PromptRequest):
    return retrieve(req.prompt)


@app.post("/ask")
def ask(req: PromptRequest, user=Depends(verify_token)):
    docs = retrieve(req.prompt)

    # 13-04-2026 - Debug output to verify retrieval quality before passing to LLM
    print("\n=== RETRIEVAL DEBUG ===")
    print(f"Query: {req.prompt}\n")

    for i, d in enumerate(docs):
        print(f"[{i}] SOURCE: {d['source']}")
        print(f"CONTENT: {d['content'][:200]}")
        print("------------------------")

    context = "\n\n".join(f"{d['content']} (source: {d['source']})" for d in docs)

    prompt = f"""
Context:
{context}

Question:
{req.prompt}
"""

    answer = llm(prompt)

    return {"answer": answer, "sources": list(set(d["source"] for d in docs))}


# 13-04-2026 - Endpoint to ingest .txt files from URLs. Protected by JWT auth and processes in background.
@app.post("/ingest")
def ingest(
    req: URLRequest, background_tasks: BackgroundTasks, user=Depends(verify_token)
):
    clean_text = fetch_txt_clean(req.url)
    chunks = chunk_txt(clean_text)

    background_tasks.add_task(process_chunks, chunks, req.url)

    return {"message": "Processing started", "chunks": len(chunks)}


# -----------------------------
# STARTUP
# -----------------------------
@app.on_event("startup")
def startup():
    init_db()
