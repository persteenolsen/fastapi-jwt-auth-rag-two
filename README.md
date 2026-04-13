# Python + FastAPI + JWT Auth + RAG + Hugging Face embeddings

Last updated:

- 13-04-2026

Python Version:

- 3.12

# Get startet

- Clone the repository from my GitHub 

- Create a virtual environment by Powershell or VS Code:

"python -m venv <name_of_venv>"

- Go to the virtual environment's directory and activate it:

"Scripts/activate"

- Install the requirements:

"pip3 install -r requirements.txt"

# Swagger documentation / Testing the API

FastAPI provides the Swagger documentation of the API where you can perform CRUD operations

To access the documentation, we must run uvicorn:

"uvicorn main:app --reload"

If everything works fine, the FastAPI and Swagger documentation is now available at: 

`http://127.0.0.1:8000/docs`

- Use the Swagger for Login by the Credentials to get the JWT Access Token for Auth

# FastAPI RAG System (JWT + pgvector + Hugging Face + Groq)

A production-style **Retrieval-Augmented Generation (RAG)** system built with FastAPI.  
It combines **JWT authentication, PostgreSQL vector search (pgvector), Hugging Face embeddings, and Groq LLMs** to answer questions based on ingested documents.

---

# Features

## Authentication
- JWT-based authentication (HS256)
- Protected endpoints using HTTP Bearer tokens
- Environment-based login credentials

---

## RAG Pipeline
- Ingests `.txt` files from URLs
- Splits documents into **topic-based chunks**
- Generates embeddings using Hugging Face
- Stores vectors in PostgreSQL with `pgvector`
- Retrieves semantically relevant context for queries

---

## Embeddings (Hugging Face)
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Hosted via Hugging Face Inference Router API
- Produces 384-dimensional normalized vectors
- Batch processing with retry support

---

## Vector Database (PostgreSQL + pgvector)
- Stores:
  - Document content
  - Embeddings
  - Source URL
  - Embedding metadata
  - Timestamp

- Uses:
  - `VECTOR(384)` type
  - `ivfflat` index for fast similarity search
  - cosine distance operator (`<->`)

---

## Semantic Retrieval
- Converts queries into embeddings
- Finds top-k most similar document chunks
- Returns relevant context for LLM generation

---

## LLM (Groq)
- Model: `llama-3.1-8b-instant`
- Generates answers based on retrieved context
- Uses structured prompting for grounded responses

---

## Question Answering API
### `/ask`
- JWT protected endpoint
- Retrieves relevant context
- Sends prompt + context to LLM
- Returns final answer + source references

---

## Document Ingestion
### `/ingest`
- Accepts `.txt` file URLs
- Downloads and cleans content
- Splits into topic-based chunks
- Processes embeddings in background
- Stores results in PostgreSQL

---

## Debug Tools
- `/debug/retrieve` → test vector search without LLM
- Console logs retrieval results for inspection

---

## Background Processing
- Uses FastAPI `BackgroundTasks`
- Non-blocking ingestion pipeline
- Handles embedding + DB insertion asynchronously

---

## Text Processing
- Fetches `.txt` files from URLs
- Validates content type
- Cleans and normalizes text input

---

## Database Initialization
On startup:
- Creates `pgvector` extension
- Creates `documents` table
- Builds vector similarity index (`ivfflat`)

---

# Architecture Overview

```text
User
  ↓
/ask (JWT Protected)
  ↓
Query Embedding (Hugging Face)
  ↓
pgvector Similarity Search
  ↓
Top-K Context Chunks
  ↓
Groq LLM (LLaMA 3.1)
  ↓
Final Answer + Sources

Happy coding :-)