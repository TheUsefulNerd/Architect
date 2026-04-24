# Architect — Backend

FastAPI + LangGraph backend for the Architect AI orchestration platform.

**Live API:** `https://architect-c10k.onrender.com`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Agent Orchestration | LangGraph |
| Primary LLM | Groq — `llama-3.3-70b-versatile` |
| Fallback LLM | Gemini — `gemini-2.5-flash` |
| Vector DB | Qdrant Cloud |
| Database | Supabase (PostgreSQL) |
| Package Manager | Poetry |

---

## Local Setup

### Prerequisites
- Python 3.11 (pinned — 3.12+ breaks grpcio-tools)
- Poetry

### 1. Install dependencies
```bash
cd backend
poetry install
```

### 2. Configure environment
```bash
cp .env.example .env
```

Fill in `backend/.env`:
```env
GEMINI_API_KEY=            # Google AI Studio
GROQ_API_KEY=              # console.groq.com
QDRANT_URL=                # cloud.qdrant.io
QDRANT_API_KEY=
SUPABASE_URL=              # supabase.com dashboard
SUPABASE_KEY=              # anon key
SUPABASE_SERVICE_KEY=      # service role key
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
DEBUG=true
```

### 3. Run the server
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: `http://localhost:8000/docs`
Health check: `http://localhost:8000/health`

---

## LLM Architecture

Groq is the primary LLM. Gemini is the fallback. Both have independent exponential backoff retry loops (5 attempts: 2→4→8→16s) before the fallback triggers. The public method names (`gemini_chat`, `gemini_generate`, `gemini_stream`) are unchanged so no agent code needs to know which provider is running.

```
Request → Groq (retry x5) → [fail] → Gemini (retry x5) → [fail] → raise
```

---

## Agent Workflow

```
User message → Router → Planner → Librarian → Mentor → Response
                  ↑_____________________________|
                  (continuing conversation skips to Mentor)
```

### Planner (`agents/planner.py`)
Gathers requirements via Socratic conversation. Outputs a Technical Spec: requirements, architecture, tech stack, and a roadmap. Transitions to Librarian when spec is ready.

### Librarian (`agents/librarian.py`)
Crawls official documentation for each technology in the tech stack. Stores embeddings in Qdrant. Synthesises a cited, Perplexity-style response. Transitions to Mentor when docs are ready.

### Mentor (`agents/mentor.py`)
Generates code scaffolds with intentional TODOs and Socratic hints. Guides implementation conversationally. Never rewrites the user's code completely.

---

## State Restoration (Cold Start)

Render's free tier spins down after 15 minutes. On restart, all in-memory state is lost. State is restored in `routes.py` via `_build_existing_state()`:

1. Reads `graph_state` from session metadata in Supabase
2. Falls back to `technical_specs` table if `requirements` is null (handles older sessions)
3. Converts phase string back to `Phase` enum before passing to the graph

---

## API Endpoints

```
POST   /api/projects                         Create project
GET    /api/projects                         List projects
GET    /api/projects/{id}                    Get project
DELETE /api/projects/{id}                    Delete project

POST   /api/sessions                         Create session
GET    /api/sessions?project_id={id}         Get session by project
GET    /api/sessions/{id}                    Get session
GET    /api/sessions/{id}/messages           Get message history
GET    /api/sessions/{id}/spec               Get technical spec
GET    /api/sessions/{id}/docs               Get documentation links
GET    /api/sessions/{id}/scaffolds          Get code scaffolds

POST   /api/chat                             Chat (blocking)
POST   /api/chat/stream                      Chat (SSE streaming)
```

---

## Deployment (Render)

**Build command:**
```
poetry install --no-root
```

**Start command:**
```
poetry run uvicorn app.main:app --host 0.0.0.0 --port 10000
```

**Required environment variables on Render:**
```
GEMINI_API_KEY
GROQ_API_KEY
QDRANT_URL
QDRANT_API_KEY
SUPABASE_URL
SUPABASE_KEY
SUPABASE_SERVICE_KEY
CORS_ORIGINS=https://architect-ochre.vercel.app,http://localhost:3000
ENVIRONMENT=production
DEBUG=false
PYTHON_VERSION=3.11.0
```

### Known Render gotchas
- Python must be pinned to 3.11 via `PYTHON_VERSION=3.11.0` env var — grpcio-tools is incompatible with 3.12+
- Poetry 2.x removed the `pip` subcommand — never use `poetry pip ...` in build commands
- Port must be hardcoded to `10000` — `$PORT` variable expansion is unreliable in the start command
- Free tier cold starts (~30s) — set up a cron ping at [cron-job.org](https://cron-job.org) hitting `/health` every 10 minutes to keep it warm

---

## Development Commands

```bash
poetry run pytest                  # Run tests
poetry run black app/              # Format code
poetry run isort app/              # Sort imports
poetry run mypy app/               # Type check
poetry run flake8 app/             # Lint
```