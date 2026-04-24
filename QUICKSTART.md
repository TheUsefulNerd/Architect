# Architect — Quick Start Guide

Get Architect running locally in 5 steps.

---

## Prerequisites

- Python 3.11 (not 3.12+ — grpcio-tools incompatibility)
- Node.js 18+
- Poetry
- API keys for: Groq, Gemini, Qdrant Cloud, Supabase

---

## Step 1 — Backend Setup

```bash
cd backend
poetry install
cp .env.example .env
```

Fill in `backend/.env`:
```env
GEMINI_API_KEY=          # aistudio.google.com
GROQ_API_KEY=            # console.groq.com/keys
QDRANT_URL=              # cloud.qdrant.io
QDRANT_API_KEY=
SUPABASE_URL=            # supabase.com → Settings → API
SUPABASE_KEY=            # anon key
SUPABASE_SERVICE_KEY=    # service role key
CORS_ORIGINS=http://localhost:3000
```

Run the backend:
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify: `http://localhost:8000/health`

---

## Step 2 — Database Setup

1. Go to your Supabase project → SQL Editor
2. Run the full contents of `docs/database_setup.sql`
3. Verify tables exist in Table Editor: `projects`, `sessions`, `messages`, `technical_specs`, `documentation_links`, `code_scaffolds`

See [`docs/supabase_setup.md`](supabase_setup.md) for full guide.

---

## Step 3 — Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
```

Fill in `frontend/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Run the frontend:
```bash
npm run dev
```

Visit: `http://localhost:3000`

---

## Step 4 — Configure Supabase Auth

In Supabase → Authentication → URL Configuration:
- **Site URL**: `http://localhost:3000`
- **Redirect URLs**: `http://localhost:3000/auth/callback`

For OAuth providers (Google/GitHub), see [`docs/supabase_setup.md`](supabase_setup.md).

---

## Step 5 — Verify Everything Works

1. Visit `http://localhost:3000` — landing page loads
2. Sign up with email or OAuth
3. Create a project from the dashboard
4. Describe your project idea in the workspace chat
5. Watch Planner → Librarian → Mentor pipeline run

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `poetry: command not found` | See `docs/poetry_setup.md` — add Poetry to PATH |
| `No module named 'google.generativeai'` | Run `poetry install` again — venv out of sync |
| Backend won't start on Python 3.12+ | Use Python 3.11 exactly |
| CORS errors in browser console | Check `CORS_ORIGINS` in `backend/.env` includes `http://localhost:3000` |
| OAuth redirect fails | Check Supabase redirect URL config matches exactly |
| Code tab empty on first Mentor message | Send one more message — known issue, being fixed |

---

## Production URLs

| Service | URL |
|---|---|
| Frontend | `https://architect-ochre.vercel.app` |
| Backend | `https://architect-c10k.onrender.com` |