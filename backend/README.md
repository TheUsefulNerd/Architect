# Architect Backend

AI-powered orchestration platform backend built with FastAPI and LangGraph.

## Tech Stack

- **Framework**: FastAPI
- **Agent Orchestration**: LangGraph
- **LLM Providers**: Google Gemini, Groq
- **Vector Database**: Qdrant Cloud
- **Database**: Supabase (PostgreSQL)
- **Package Manager**: Poetry

## Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Gemini API Key
- Groq API Key
- Qdrant Cloud account
- Supabase project

## Setup Instructions

### 1. Install Poetry (if not already installed)

**Windows (PowerShell):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Add Poetry to your PATH:
```powershell
$env:Path += ";$env:APPDATA\Python\Scripts"
```

### 2. Install Dependencies

```bash
cd backend
poetry install
```

This will:
- Create a virtual environment
- Install all dependencies from pyproject.toml
- Set up development tools (pytest, black, etc.)

### 3. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
GEMINI_API_KEY=your_actual_gemini_key
GROQ_API_KEY=your_actual_groq_key
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
```

### 4. Database Setup

Run the SQL scripts in `docs/database_setup.sql` in your Supabase SQL editor to create tables.

### 5. Run the Development Server

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or activate the virtual environment first:
```bash
poetry shell
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

## Project Structure

```
backend/
├── app/
│   ├── agents/          # LangGraph agents (Planner, Librarian, Mentor)
│   ├── services/        # Business logic services
│   ├── models/          # Pydantic models and state definitions
│   ├── api/             # FastAPI routes and WebSocket handlers
│   ├── utils/           # Helper utilities
│   ├── config.py        # Configuration management
│   └── main.py          # FastAPI application entry point
├── tests/               # Unit and integration tests
├── pyproject.toml       # Poetry dependencies and config
└── .env                 # Environment variables (not in git)
```

## Development Commands

### Running Tests
```bash
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

### Linting
```bash
poetry run flake8 app/
```

## API Endpoints

- `POST /api/projects` - Create a new project
- `POST /api/sessions` - Create a new session
- `POST /api/chat` - Send a message to the orchestration system
- `GET /api/sessions/{session_id}` - Get session details
- `WebSocket /ws/{session_id}` - Real-time streaming updates

## LangGraph Workflow

1. **Planner Agent**: Analyzes user input → Generates technical spec
2. **Librarian Agent**: Identifies tech stack → Finds documentation
3. **Mentor Agent**: Creates code scaffolds → Provides implementation hints

## Environment Variables Reference

See `.env.example` for complete list of configuration options.

## Troubleshooting

### Poetry not found
Make sure Poetry is in your PATH. Restart your terminal after installation.

### Import errors
Make sure you're in the Poetry virtual environment:
```bash
poetry shell
```

### Database connection issues
Verify your Supabase credentials in `.env` are correct.

## Next Steps

1. Set up Supabase database schema
2. Configure Qdrant collections
3. Implement agent logic
4. Test the LangGraph workflow
