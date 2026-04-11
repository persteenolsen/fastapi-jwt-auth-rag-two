# app.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from groq import Groq
import numpy as np
import jwt
import os
import requests
import datetime

# -----------------------------
# ENV
# -----------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
FAKE_USERNAME = os.getenv("FAKE_USERNAME")
FAKE_PASSWORD = os.getenv("FAKE_PASSWORD")

if not DATABASE_URL:
    raise Exception("Missing DATABASE_URL")

# -----------------------------
# APP
# -----------------------------
# app = FastAPI(title="FastAPI with JWT Auth and RAG")

# 11-04-2026 - Initialize the FastAPI app
app = FastAPI(

    title="Python + FastApi + JWT Auth + LLM + Groq + RAG pipeline",
    description="11-04-2026 - FastAPI with JWT Auth serving an RAG Application powered by one of Groq's LLaMA models",
    version="0.0.1",

    contact={
        "name": "Per Olsen",
        "url": "https://persteenolsen.netlify.app",
         },
)


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
client = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# AUTH
# -----------------------------
bearer = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        decoded = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return decoded["username"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# -----------------------------
# MODELS
# -----------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

class PromptRequest(BaseModel):
    prompt: str

class URLRequest(BaseModel):
    url: str

# -----------------------------
# EMBEDDING CONFIG
# -----------------------------
# NOTE: fake embeddings for demo purposes only
EMBED_MODEL = "mock-384"   # since you're still using fake embeddings
EMBED_VERSION = 1

# -----------------------------
# UTILS
# -----------------------------
def normalize(vec):
    v = np.array(vec)
    return (v / np.linalg.norm(v)).tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    # 🔥 Replace with actual Groq embedding model when available
    # TEMP fallback (deterministic fake but stable)
    vectors = []
    for text in texts:
        np.random.seed(abs(hash(text)) % (10**6))
        vec = np.random.rand(384)
        vectors.append(normalize(vec))
    return vectors

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
def chunk_txt(text: str, size=500, overlap=50):
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i+size]
        chunks.append(chunk.strip())
        i += size - overlap
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
    embeddings = embed_batch(chunks)

    with engine.begin() as conn:
        for chunk, vec in zip(chunks, embeddings):
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
                    "version": EMBED_VERSION
                }
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
            {"embedding": qvec, "k": k}
        ).fetchall()

    return [{"content": r[0], "source": r[1]} for r in rows]

# -----------------------------
# LLM
# -----------------------------
def llm(prompt: str):
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
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

# DEBUG route to test retrieval without auth or LLM
@app.post("/debug/retrieve")
def debug(req: PromptRequest):
    return retrieve(req.prompt)

@app.post("/login")
def login(req: LoginRequest):
    if req.username == FAKE_USERNAME and req.password == FAKE_PASSWORD:
        payload = {
            "username": req.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return {"token": token}

    raise HTTPException(status_code=401, detail="Bad credentials")

@app.post("/ask")
def ask(req: PromptRequest, user=Depends(verify_token)):
    docs = retrieve(req.prompt)

    # 11-04-2026 - DEBUG / LEARNING LOGGING
    print("\n=== RETRIEVAL DEBUG ===")
    print(f"Query: {req.prompt}\n")

    for i, d in enumerate(docs):
        print(f"[{i}] SOURCE: {d['source']}")
        print(f"CONTENT: {d['content'][:200]}")
        print("------------------------")

    context = "\n\n".join(
        f"{d['content']} (source: {d['source']})"
        for d in docs
    )

    prompt = f"""
Context:
{context}

Question:
{req.prompt}
"""

    answer = llm(prompt)

    return {
        "answer": answer,
        "sources": list(set(d["source"] for d in docs))
    }

@app.post("/ingest")
def ingest(req: URLRequest, background_tasks: BackgroundTasks, user=Depends(verify_token)):
    clean_text = fetch_txt_clean(req.url)
    chunks = chunk_txt(clean_text)

    background_tasks.add_task(process_chunks, chunks, req.url)

    return {
        "message": "Processing started",
        "chunks": len(chunks)
    }

# -----------------------------
# STARTUP
# -----------------------------
@app.on_event("startup")
def startup():
    init_db()