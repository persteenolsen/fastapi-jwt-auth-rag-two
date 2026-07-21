# Python + FastAPI + OAuth2 Password Bearer + JWT Auth + RAG + Hugging Face Embeddings

A production-style **Retrieval-Augmented Generation (RAG)** API built with **FastAPI**.  
This project combines **OAuth2 Password Bearer authentication**, **JWT access tokens**, **vector search with pgvector**, **Hugging Face embeddings**, and **Groq LLMs** to deliver context-aware answers from your own data.

---

## 📌 Project Info

- **Last Updated:** 21-07-2026
- **Python Version:** 3.12

---

## 🖥️ Frontend Client

This repository contains the FastAPI backend for the RAG system.

A separate Vue 3 SPA frontend is available as a client application and provides:

- JWT authenticated user login
- RAG question interface
- AI-generated answer display
- Retrieved source document display
- Pinia state management
- Production-ready Vite build

The Vue frontend communicates with this API through the protected `/login-spa` and `/ask` endpoints.

Frontend repository:

- `vue-fastapi-jwt-auth-rag-two` - Vue 3 SPA client for interacting with this FastAPI RAG API

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

## 📁 Project Structure

The application is organized into separate modules to improve maintainability while keeping the core RAG pipeline logic centralized.

Current structure:

- `app.py`
  - Creates the FastAPI application
  - Registers API routes
  - Handles application startup events

- `routes.py`
  - Contains all API endpoints
  - Handles authentication flows, RAG queries, and document ingestion requests

- `utils.py`
  - Contains the core RAG and service functionality:
    - Hugging Face embedding generation
    - PostgreSQL + pgvector database operations
    - Document chunking and text processing
    - Document ingestion pipeline
    - Vector similarity retrieval
    - Groq LLM communication

- `auth.py`
  - Handles JWT authentication functionality
  - Creates and validates access tokens
  - Provides authentication utilities for protected endpoints

- `models.py`
  - Contains Pydantic models used for API request validation and response serialization
  - Defines the data schemas exchanged between clients and the API

- `config.py`
  - Contains application configuration settings
  - Loads environment-based values such as API keys, database configuration, and authentication parameters

This structure separates the API layer, authentication, configuration, data schemas, and RAG services while keeping the project simple, readable, and easy to extend.

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

# 💡 Use Cases and Applications

This FastAPI RAG backend can be used as the foundation for AI-powered knowledge systems. By combining document retrieval, vector search, and LLM-generated responses, applications can provide accurate answers based on trusted information sources.

## 💬 Chat Assistants

- Build AI-powered assistants connected to private knowledge sources
- Answer user questions using retrieved documents as context
- Provide conversational access to internal or external information

Examples:

- Customer support assistants
- Employee knowledge assistants
- Product support chatbots
- FAQ assistants

## 📚 Document Question Answering

- Query large document collections using natural language
- Retrieve relevant information from documents
- Generate answers with source references for transparency

Examples:

- Technical documentation assistants
- Policy and procedure assistants
- Research assistants
- Document analysis systems

## 🏢 Enterprise Knowledge Systems

- Connect employees with company knowledge bases
- Provide secure access to internal information
- Reduce time spent searching across multiple systems

Examples:

- Internal company assistants
- HR knowledge systems
- IT support assistants
- Training platforms

## 🎓 Education and Learning Assistants

- Create AI tutors based on educational content
- Help users explore course material through questions
- Provide explanations grounded in learning resources

Examples:

- Course assistants
- Learning platforms
- Training systems
- Educational chatbots

## 🛠️ Developer and Technical Assistants

- Provide answers from technical documentation and repositories
- Help developers understand frameworks, APIs, and systems
- Improve access to technical knowledge

Examples:

- API documentation assistants
- Programming assistants
- DevOps assistants
- Software architecture assistants

## 🔎 Semantic Search and Knowledge Discovery

- Replace traditional keyword search with AI-powered semantic search
- Find relevant information based on meaning rather than exact wording
- Combine retrieval with natural language explanations

Examples:

- Enterprise search engines
- Research tools
- Digital libraries
- Knowledge management systems

## 🔐 Secure AI Applications

With FastAPI authentication, protected endpoints, and controlled access to knowledge sources, the backend can support secure AI applications.

Examples:

- Private company assistants
- Customer portals
- Role-based AI systems
- Member-only knowledge platforms

---

## 📄 License

MIT License

---

## 🙌 Final Notes

This project is designed as a **clean, production-style RAG backend** that can serve multiple clients.

The FastAPI API can be extended into:

- Chatbots
- Internal knowledge systems
- AI assistants
- Document search platforms
- Enterprise knowledge applications

A Vue 3 SPA frontend is included as a separate client application, demonstrating how to securely integrate authentication, API communication, and RAG-based question answering into a modern web application.

Happy coding :-)

