# Supabase Setup Guide

Supabase provides the PostgreSQL database and authentication for Architect.

---

## 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. New Project → name it `architect`
3. Choose a region close to you
4. Wait ~2 minutes for provisioning

---

## 2. Get API Keys

Project Settings → API:

| Key | Where it goes |
|---|---|
| Project URL | `SUPABASE_URL` in `.env` |
| anon/public key | `SUPABASE_KEY` in `.env` |
| service_role key (click Reveal) | `SUPABASE_SERVICE_KEY` in `.env` |

⚠️ Keep `service_role` secret — it bypasses all RLS policies.

---

## 3. Apply the Database Schema

1. Supabase dashboard → SQL Editor → New Query
2. Paste the full contents of `docs/database_setup.sql`
3. Click Run

Verify in Table Editor — you should see:
- `projects`
- `sessions`
- `messages`
- `technical_specs`
- `documentation_links`
- `code_scaffolds`

---

## 4. Configure Auth

### URL Configuration
Authentication → URL Configuration:

| Setting | Local | Production |
|---|---|---|
| Site URL | `http://localhost:3000` | `https://architect-ochre.vercel.app` |
| Redirect URLs | `http://localhost:3000/auth/callback` | `https://architect-ochre.vercel.app/auth/callback` |

### Google OAuth
1. Authentication → Providers → Google → Enable
2. Go to [console.cloud.google.com](https://console.cloud.google.com) → APIs & Services → Credentials
3. Create OAuth 2.0 Client ID
4. Authorized redirect URI: `https://<your-project-ref>.supabase.co/auth/v1/callback`
5. Copy Client ID and Secret back into Supabase

### GitHub OAuth
1. Authentication → Providers → GitHub → Enable
2. Go to GitHub → Settings → Developer settings → OAuth Apps → New OAuth App
3. Callback URL: `https://<your-project-ref>.supabase.co/auth/v1/callback`
4. Copy Client ID and Secret back into Supabase

---

## 5. Row Level Security (RLS) — TODO

RLS is **not yet configured**. All tables currently return all rows to all authenticated users. This needs to be fixed before the app is used by multiple real users.

Run this SQL for each table (adjust column name if not `user_id`):

```sql
-- Example for the projects table
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "select_own" ON projects
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "insert_own" ON projects
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "update_own" ON projects
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "delete_own" ON projects
  FOR DELETE USING (auth.uid() = user_id);
```

Apply to all 6 tables: `projects`, `sessions`, `messages`, `technical_specs`, `documentation_links`, `code_scaffolds`.

---

## Database Schema Overview

```
User
└── Project
    └── Session
        ├── Messages          (chat history)
        ├── Technical Spec    (Planner output)
        ├── Documentation Links (Librarian output)
        └── Code Scaffolds    (Mentor output)
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Can't connect from backend | Check `SUPABASE_URL` and keys in `.env` — no trailing slashes |
| OAuth redirect fails | Verify redirect URL in Supabase matches exactly including `/auth/callback` |
| Data visible across accounts | RLS not configured — see section 5 above |
| SQL errors on schema run | Run the SQL all at once, not line by line |