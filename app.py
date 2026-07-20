from fastapi import FastAPI

from routes import router
from utils import init_db

app = FastAPI(
    title="Python + FastApi + JWT Auth + RAG Pipeline + HF embeddings",
    description="20-07-2026 - FastAPI with JWT Auth serving an RAG Application powered by Groq + HuggingFace embeddings",
    version="0.0.2",
    contact={
        "name": "Per Olsen",
        "url": "https://persteenolsen.netlify.app",
    },
)


app.include_router(router)


@app.on_event("startup")
def startup():
    init_db()
