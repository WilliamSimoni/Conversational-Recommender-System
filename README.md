# Conversational Recommender System

![Architecture Diagram](images/logo.png)

A conversational fragrance recommender powered by LangGraph, Qdrant, and LLMs. Users describe what they're looking for in natural language and the system retrieves relevant products from a vector database.

## Prerequisites

- Python 3.13+
- Docker and Docker Compose
- An OpenAI-compatible API key (or any LLM provider supported by LiteLLM)

## Setup

### 1. Backend Configuration

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your values.

**How model configuration works:**

The system uses a two-layer model setup:

**Layer 1 — Define providers** (connection details):

```
MODELS__<KEY>__BASE_URL=https://api.openai.com/v1
MODELS__<KEY>__API_KEY=sk-...
MODELS__<KEY>__MODEL_NAME=gpt-4o
MODELS__<KEY>__REASONING_MODEL=false
```

Define as many providers as you need (e.g. `OPENAI`, `MISTRAL`, `GEMINI`).

**Layer 2 — Assign roles** (which provider each agent uses):

```
ORCHESTRATOR_MODEL__MODEL=openai
ASK_MODEL__MODEL=openai
RECOMMEND_MODEL__MODEL=openai
```

Each role references a key defined in Layer 1. The `config.yaml` also supports `fallback` and `reasoning_effort` per role.

### 2. Start Infrastructure

Start Qdrant (and optionally Postgres) — these must be running before ingestion:

```bash
docker compose up --build
```

This starts:
- **Qdrant** (vector database) on port 6333
- **Postgres** (session persistence) on port 5432
- **Backend** (FastAPI) on port 8000
- **Frontend** (Vite) on port 5173

The backend will be unavailable until ingestion completes — that's expected.

### 3. Data Ingestion

With Qdrant running, prepare product data and load it into the vector store:

```bash
cd ingestion
cp .env.example .env
```

Edit `ingestion/.env` with your embedding API key and Qdrant URL.

Place your raw product catalog as `data/catalog.json`, then run:

```bash
# Extract & transform: parses raw products into a staging file
python extract_and_transform.py

# Load: generates embeddings and uploads to Qdrant
python load.py
```
