# Quick Start Guide - Architect Setup

Follow these steps in order to get Architect up and running!

## ✅ Step 1: Install Poetry

**Windows PowerShell:**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

**Add to PATH:**
```powershell
$env:Path += ";$env:APPDATA\Python\Scripts"
```

**Verify installation:**
```bash
poetry --version
```

📖 Full guide: `docs/poetry_setup.md`

## ✅ Step 2: Install Backend Dependencies

```bash
cd backend
poetry install
```

This will take a few minutes the first time.

## ✅ Step 3: Set Up Supabase

1. Go to https://supabase.com and create an account
2. Create a new project (name it `architect-backend`)
3. Wait for project provisioning (~2 minutes)
4. Go to **Settings > API** and copy:
   - Project URL
   - anon/public key
   - service_role key (click Reveal)
5. Go to **SQL Editor** and run the contents of `docs/database_setup.sql`

📖 Full guide: `docs/supabase_setup.md`

## ✅ Step 4: Configure Environment Variables

```bash
cd backend
cp .env.example .env
```

Edit `.env` and fill in your API keys:

```env
# Get from Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Get from Google AI Studio (https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_key

# Get from Groq Console (https://console.groq.com/keys)
GROQ_API_KEY=your_groq_key

# Get from Qdrant Cloud (https://cloud.qdrant.io)
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key
```

## ✅ Step 5: Run the Backend

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## ✅ Step 6: Test the API

Open your browser and go to:
- http://localhost:8000/docs - Interactive API documentation
- http://localhost:8000/health - Health check endpoint

## 🎯 What's Next?

Now that the foundation is set up, we'll build:

1. **LangGraph Agents**:
   - Planner agent (Phase I)
   - Librarian agent (Phase II)
   - Mentor agent (Phase III)

2. **API Endpoints**:
   - Project and session management
   - Chat interface with streaming
   - WebSocket for real-time updates

3. **Frontend** (after backend is working):
   - Next.js 15 setup
   - Dual-pane interface
   - React Flow integration

## 📋 Checklist

- [ ] Poetry installed and working
- [ ] Backend dependencies installed
- [ ] Supabase project created
- [ ] Database schema applied
- [ ] `.env` file configured with all keys
- [ ] Backend server running on port 8000
- [ ] Can access API docs at localhost:8000/docs

## 🆘 Troubleshooting

**Poetry not found?**
- Restart your terminal after installation
- Make sure Poetry is in your PATH

**Can't connect to Supabase?**
- Double-check your URL and keys in `.env`
- Make sure there are no extra spaces or quotes

**Import errors?**
- Make sure you're in the Poetry virtual environment: `poetry shell`
- Try reinstalling: `poetry install`

**Port 8000 already in use?**
- Change the port: `uvicorn app.main:app --reload --port 8001`
- Or kill the process using port 8000

## 📚 Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

---

**You're all set! Ready to build the agents? Let me know when you're ready for Step 3! 🚀**
