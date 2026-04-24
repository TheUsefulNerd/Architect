# Architect

> An AI-powered orchestration platform that transforms naive ideas into professional engineering implementations.

**Live:** [architect-ochre.vercel.app](https://architect-ochre.vercel.app) · **API:** [architect-c10k.onrender.com](https://architect-c10k.onrender.com)

---

## Vision

Architect uses a **Socratic Loop** methodology — it guides users through system design and documentation research rather than building things for them. Every response is a nudge, not an answer.

---

## Three-Phase Workflow

```
User Idea → [Planner] → [Librarian] → [Mentor] → Implementation
```

| Phase | Agent | What it does |
|---|---|---|
| I | **Planner** | Deconstructs intent into Requirements, Architecture, Tech Stack, and a Roadmap |
| II | **Librarian** | Crawls official docs for the tech stack, stores embeddings in Qdrant, returns Perplexity-style cited responses |
| III | **Mentor** | Generates code scaffolds with intentional gaps, guides implementation conversationally via Socratic hints |

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI (Python) |
| Agent Orchestration | LangGraph |
| Primary LLM | Groq — `llama-3.3-70b-versatile` |
| Fallback LLM | Gemini — `gemini-2.5-flash` |
| Vector DB | Qdrant Cloud |
| Relational DB | Supabase (PostgreSQL) |
| Package Manager | Poetry |

### Frontend
| Layer | Technology |
|---|---|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript 5 |
| Styling | Tailwind CSS — Deep Midnight theme |
| Auth | Supabase Auth (`@supabase/ssr`) |
| Visualization | React Flow |
| State | Zustand 5 |

### Infrastructure
| Layer | Technology |
|---|---|
| Frontend Deploy | Vercel |
| Backend Deploy | Render |
| Auth + DB | Supabase |
| Vector DB | Qdrant Cloud |
| CI/CD | GitHub Actions *(pending)* |

---

## Project Structure

```
architect/
├── backend/
│   ├── app/
│   │   ├── agents/               # LangGraph agents
│   │   │   ├── planner.py        # Phase I
│   │   │   ├── librarian.py      # Phase II
│   │   │   ├── mentor.py         # Phase III
│   │   │   └── graph.py          # Orchestration + routing
│   │   ├── services/
│   │   │   ├── llm_service.py    # Groq primary, Gemini fallback
│   │   │   ├── vector_service.py # Qdrant operations
│   │   │   ├── db_service.py     # Supabase CRUD
│   │   │   └── crawler_service.py# Documentation web scraper
│   │   ├── models/
│   │   │   ├── schemas.py        # Pydantic models
│   │   │   └── state.py          # LangGraph state (TypedDict)
│   │   ├── api/
│   │   │   └── routes.py         # All FastAPI endpoints
│   │   ├── config.py             # Pydantic settings
│   │   └── main.py               # FastAPI entry point
│   ├── pyproject.toml
│   └── poetry.lock
│
├── frontend/
│   ├── app/
│   │   ├── auth/                 # Login, register, callback
│   │   ├── dashboard/            # Project list
│   │   └── workspace/[projectId] # Dual-pane workspace
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   └── stores/
│
└── docs/
    ├── database_setup.sql
    ├── supabase_setup.md
    └── poetry_setup.md
```

---

## Getting Started

### Backend

```bash
cd backend
poetry install
cp .env.example .env   # fill in your keys
poetry run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # fill in your keys
npm run dev
```

See [`docs/poetry_setup.md`](docs/poetry_setup.md) and [`docs/supabase_setup.md`](docs/supabase_setup.md) for detailed setup.

---

## Environment Variables

### Backend (`backend/.env`)
```env
GEMINI_API_KEY=
GROQ_API_KEY=
QDRANT_URL=
QDRANT_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

---

## Design Principles

1. **Socratic Teaching** — Guide, don't build for the user
2. **Documentation First** — Always link to official sources
3. **Intentional Gaps** — Scaffolds leave TODOs the user must fill
4. **Clean Code** — Proper formatting and inline documentation
5. **Stable Structure** — Single file structure, never reorganised between updates

---

## Deployment

| Service | URL |
|---|---|
| Frontend (Vercel) | `https://architect-ochre.vercel.app` |
| Backend (Render) | `https://architect-c10k.onrender.com` |

See [`backend/README.md`](backend/README.md) for Render-specific deployment notes.