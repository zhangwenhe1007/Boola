# Boola - Yale AI Assistant

A conversational AI assistant for Yale students that provides accurate, cited answers about courses, clubs, campus activities, events, and research labs.

## Architecture

- **Frontend**: Next.js 15 + shadcn/ui + Tailwind CSS
- **Backend**: FastAPI + PostgreSQL/pgvector
- **LLM**: Qwen2.5-14B via vLLM (local inference)
- **RAG**: Hybrid BM25 + vector search with reranking

## Project Structure

```
Boola/
├── frontend/          # Next.js chat interface
├── backend/           # FastAPI server
│   ├── api/          # API endpoints
│   ├── db/           # Database models & repositories
│   ├── rag/          # Retrieval logic
│   ├── tools/        # Yale data tools
│   ├── llm/          # LLM integration
│   └── scripts/      # Setup & utility scripts
├── crawler/          # Data collection
│   ├── spiders/      # Web crawlers
│   └── processors/   # Text processing
├── training/         # Fine-tuning (future)
├── evaluation/       # Test datasets
└── docs/            # Documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- (Optional) NVIDIA GPU with CUDA for local LLM inference

### 1. Start PostgreSQL with pgvector

```bash
# Start the database
docker-compose up -d postgres

# Verify it's running
docker-compose ps
```

### 2. Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Initialize database tables
python scripts/init_db.py

# Index sample documents (for testing)
python scripts/index_sample.py

# Start the API server
uvicorn api.main:app --reload --port 8000
```

The API will be available at http://localhost:8000 with docs at http://localhost:8000/docs

### 3. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

### 4. (Optional) Set Up vLLM for Local Inference

For the best experience, run a local LLM:

```bash
# Install vLLM (requires CUDA)
pip install vllm

# Start vLLM server with Qwen2.5-14B (requires ~10GB VRAM with 4-bit)
vllm serve Qwen/Qwen2.5-14B-Instruct-AWQ \
    --dtype auto \
    --max-model-len 4096 \
    --port 8001
```

Update `.env` to point to the vLLM server:
```
VLLM_BASE_URL=http://localhost:8001/v1
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Main chat endpoint with RAG |
| `/index` | POST | Index a document |
| `/documents` | GET | List indexed documents |
| `/stats` | GET | Get indexing statistics |
| `/health` | GET | Health check with service status |

## Configuration

Environment variables (`.env`):

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/boola

# LLM
VLLM_BASE_URL=http://localhost:8001/v1
VLLM_MODEL=Qwen/Qwen2.5-14B-Instruct

# Embedding
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
```

## Data Sources

- Yale Courses Web Service (official API)
- Yalies.io API (public directory)
- YaleIMs API (schedules)
- Official Yale pages (registrar, calendar, policies)

## Development

### Running Tests
```bash
cd backend
pytest
```

### Crawling Yale Pages
```bash
cd crawler
python -m spiders.yale_crawler
```

## License

MIT
