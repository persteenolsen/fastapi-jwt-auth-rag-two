# Python + FastAPI + OAuth2 Password Bearer + JWT Auth + RAG + Hugging Face Embeddings

A production-style **Retrieval-Augmented Generation (RAG)** API built with **FastAPI**.  
This project combines **OAuth2 Password Bearer authentication**, **JWT access tokens**, **vector search with pgvector**, **Hugging Face embeddings**, and **Groq LLMs** to deliver context-aware answers from your own data.

---

## 📌 Project Info

- **Last Updated:** 20-07-2026
- **Python Version:** 3.12

---

## ✨ Features

### 🔐 Authentication
- OAuth2 Password Bearer authentication
- JWT access tokens (HS256)
- Swagger UI OAuth2 authorization support
- Protected endpoints using Bearer tokens
- Separate login endpoint for SPA clients (`/login-spa`)
- Environment-based credentials

---

### 🧠 RAG Pipeline
- Ingests `.txt` documents from URLs
- Splits content into **topic-based chunks**
- Generates embeddings using Hugging Face
- Stores vectors in PostgreSQL (`pgvector`)
- Retrieves relevant context for queries

---

### 🤖 LLM Integration (Groq)
- Model: `openai/gpt-oss-20b`
- Context-aware answer generation
- Structured prompting for grounded responses

---

### 🔎 Semantic Search
- Query → embedding
- Top-K similarity search via `pgvector`
- Cosine distance (`<->`)

---

### 🗄️ Vector Database (PostgreSQL + pgvector)

Stores:
- Document content
- Embeddings (384-dim vectors)
- Source URL
- Metadata
- Timestamp

Optimizations:
- `VECTOR(384)` column
- `ivfflat` index for fast retrieval

---

### ⚙️ Background Processing
- FastAPI `BackgroundTasks`
- Async ingestion pipeline
- Non-blocking embedding + DB insert

---

### 🧪 Debug Tools
- `/debug/retrieve` → test retrieval without LLM
- Console logging for inspection

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login-spa` | Login endpoint for SPA clients (JWT) |
| POST | `/token` | OAuth2 Password Bearer token endpoint (Swagger/UI clients) |
| POST | `/ask` | Ask questions (RAG-powered) 🔐 |
| POST | `/ingest` | Ingest `.txt` files from URLs 🔐 |
| POST | `/debug/retrieve` | Debug semantic search |

🔐 = Requires authentication

---

## ⚙️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

---

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows (PowerShell):**

```bash
venv\Scripts\activate
```

**Mac/Linux:**

```bash
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```bash
uvicorn app:app --reload
```

Once running:

- 🌐 API: http://127.0.0.1:8000
- 📄 Swagger Docs: http://127.0.0.1:8000/docs

### Using Swagger UI

1. Open `/docs`
2. Click **Authorize**
3. Sign in using your username and password (OAuth2 Password flow)
4. Swagger automatically stores and sends the Bearer token for protected endpoints

---

## 🔑 Authentication Flow

### Swagger / API Clients (OAuth2 Password Bearer)

1. Call `/token` using the OAuth2 Password flow
2. Receive a JWT access token
3. Use it automatically through Swagger or manually:

```http
Authorization: Bearer <your_token>
```

### SPA Clients

Frontend applications can authenticate via:

```text
POST /login-spa
```

which returns the same JWT access token for subsequent authenticated requests.

---

## 🧠 How RAG Works

```text
User Query
   ↓
Embedding (Hugging Face)
   ↓
pgvector Similarity Search
   ↓
Top-K Relevant Chunks
   ↓
Groq LLM (GPT-OSS-20B)
   ↓
Final Answer + Sources
```

---

## 📥 Document Ingestion

### `/ingest`

- Accepts `.txt` file URLs
- Downloads and cleans content
- Splits into topic-based chunks
- Generates embeddings
- Stores results in PostgreSQL

---

## 🧾 Embeddings

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- 384-dimensional normalized vectors
- Batch processing with retry support
- Powered via Hugging Face Inference API

---

## 🗄️ Database Initialization

On application startup:

- Creates `pgvector` extension
- Creates `documents` table
- Builds `ivfflat` similarity index

---

## 🛠️ Text Processing

- Fetches `.txt` files from URLs
- Validates content type
- Cleans and normalizes text

---

## 📌 Future Improvements

- 🔄 Refresh tokens
- 📊 Admin dashboard
- 🔍 Hybrid search (BM25 + vector)
- 📈 Monitoring & logging
- 🧩 Plugin/tool integrations
- Split `app.py` into separate modules for improved project structure

---

## 📄 License

MIT License

---

## 🙌 Final Notes

This project is designed as a **clean, production-style RAG backend** and can be extended into:

- Chatbots
- Internal knowledge systems
- AI assistants
- Document search platforms

Happy coding :-)
