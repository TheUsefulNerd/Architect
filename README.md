# Architect

> An AI-powered orchestration platform that transforms naive ideas into professional engineering implementations.

## 🎯 Vision

Architect uses a **Socratic Loop** methodology to guide users through system design and documentation research, empowering them to build rather than building for them.

## 🏗️ Architecture

### Three-Phase Workflow

1. **Phase I - Planner**: Deconstructs user intent into a Technical Specification
   - Requirements gathering
   - Architecture design
   - Technology stack selection

2. **Phase II - Librarian/Crawler**: Identifies knowledge gaps and provides documentation
   - Analyzes tech stack from Planner
   - Searches and scrapes relevant documentation
   - Provides deep-links and citations (like AI web search)

3. **Phase III - Mentor**: Provides code scaffolding and implementation guidance
   - Generates code scaffolds with intentional gaps
   - Provides "hints" to force user implementation
   - Guides through the learning process

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Visualization**: React Flow (for roadmaps/workflows)

### Backend
- **Framework**: FastAPI (Python)
- **Agent Orchestration**: LangGraph (multi-agent system)
- **LLM Providers**: Google Gemini, Groq

### Databases
- **Vector Database**: Qdrant Cloud (semantic search, embeddings)
- **Relational Database**: Supabase (PostgreSQL)

### Infrastructure
- **Cloud Platform**: Google Cloud Platform (GCP)
  - Cloud Run (serverless containers)
  - Artifact Registry (container images)
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

## 🎨 Design Aesthetic

- **Entry**: Prompt-first interface
- **Dashboard**: "Deep Midnight" dual-pane layout
  - Left: React Flow roadmap visualization
  - Right: Interactive chat interface

## 📁 Project Structure

```
architect/
├── backend/              # FastAPI + LangGraph backend
│   ├── app/
│   │   ├── agents/      # Planner, Librarian, Mentor agents
│   │   ├── services/    # LLM, Vector DB, Database services
│   │   ├── models/      # Pydantic models and state definitions
│   │   └── api/         # FastAPI routes and WebSocket
│   └── tests/
├── frontend/             # Next.js 15 frontend
│   └── (to be built)
├── infrastructure/       # Terraform and Docker configs
│   ├── terraform/
│   └── docker/
├── .github/workflows/    # CI/CD pipelines
└── docs/                # Documentation
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend, later)
- Poetry (Python package manager)
- API Keys:
  - Google Gemini API
  - Groq API
  - Qdrant Cloud
  - Supabase

### Backend Setup

1. **Install Poetry** (see `docs/poetry_setup.md`)

2. **Install dependencies:**
   ```bash
   cd backend
   poetry install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Set up Supabase** (see `docs/supabase_setup.md`)
   - Create a Supabase project
   - Run the SQL schema from `docs/database_setup.sql`
   - Add Supabase credentials to `.env`

5. **Configure Qdrant:**
   - Create collections in Qdrant Cloud
   - Add credentials to `.env`

6. **Run the development server:**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

Visit: http://localhost:8000/docs for API documentation

### Frontend Setup

(Coming soon - Next.js 15 with App Router)

## 📚 Documentation

- [Poetry Setup Guide](docs/poetry_setup.md) - Install and use Poetry on Windows
- [Supabase Setup Guide](docs/supabase_setup.md) - Configure Supabase database
- [Database Schema](docs/database_setup.sql) - SQL schema for Supabase
- [Backend README](backend/README.md) - Backend-specific documentation

## 🧪 Development

### Running Tests
```bash
cd backend
poetry run pytest
```

### Code Formatting
```bash
poetry run black app/
poetry run isort app/
```

### Type Checking
```bash
poetry run mypy app/
```

## 🏛️ Design Principles

1. **Socratic Teaching**: Guide, don't build for the user
2. **Documentation First**: Always link to official docs
3. **Intentional Gaps**: Code scaffolds with learning opportunities
4. **Clean Code**: Proper formatting and documentation
5. **Stable Structure**: Single file structure, maintained consistently

## 🔮 Roadmap

- [x] Project structure and setup
- [x] Database schema design (Supabase + Qdrant)
- [ ] LangGraph multi-agent implementation
  - [ ] Planner agent
  - [ ] Librarian agent (web crawler)
  - [ ] Mentor agent
- [ ] FastAPI endpoints and WebSocket
- [ ] Frontend with Next.js 15
- [ ] React Flow integration
- [ ] GCP deployment with Terraform
- [ ] CI/CD with GitHub Actions

## 🤝 Contributing

This is a collaborative project. Contributions welcome!

## 📝 License

(To be determined)

---

Built with ❤️ using AI-powered orchestration
