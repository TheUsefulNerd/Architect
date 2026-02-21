# Supabase Setup Guide for Architect

This guide will walk you through setting up Supabase for the Architect project.

## What is Supabase?

Supabase is an open-source Firebase alternative that provides:
- PostgreSQL database (with full SQL support)
- Authentication
- Auto-generated REST API
- Realtime subscriptions
- Storage

For Architect, we're primarily using it for the PostgreSQL database and its excellent API.

## Step 1: Create a Supabase Account

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign up with GitHub, Google, or email

## Step 2: Create a New Project

1. Click "New Project"
2. Fill in the details:
   - **Name**: architect-backend (or your preferred name)
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose the closest region to you
   - **Pricing Plan**: Free tier is fine for development
3. Click "Create new project"
4. Wait 2-3 minutes for the project to be provisioned

## Step 3: Get Your API Keys

Once your project is ready:

1. Go to **Project Settings** (gear icon in sidebar)
2. Click **API** in the sidebar
3. You'll see several important values:

### Copy These Values:

**Project URL:**
```
https://xxxxxxxxxxxxx.supabase.co
```
This goes in your `.env` as `SUPABASE_URL`

**anon/public key:**
```
eyJhbGc...long_string...
```
This goes in your `.env` as `SUPABASE_KEY`

**service_role key:** (click "Reveal" button)
```
eyJhbGc...different_long_string...
```
This goes in your `.env` as `SUPABASE_SERVICE_KEY`

⚠️ **IMPORTANT**: Keep the `service_role` key secret! It bypasses all security rules.

## Step 4: Run the Database Schema

1. In Supabase dashboard, click **SQL Editor** in the sidebar
2. Click **New Query**
3. Copy the entire contents of `docs/database_setup.sql`
4. Paste it into the SQL editor
5. Click **Run** (or press Ctrl+Enter)

You should see success messages like:
```
Success. No rows returned
```

## Step 5: Verify the Tables

1. Click **Table Editor** in the sidebar
2. You should see all the tables:
   - users
   - projects
   - sessions
   - messages
   - technical_specs
   - documentation_links
   - code_scaffolds

## Step 6: Update Your .env File

Update your `backend/.env` file with the values:

```env
# Supabase Configuration
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...your_anon_key...
SUPABASE_SERVICE_KEY=eyJhbGc...your_service_key...
```

## Step 7: Optional - Create a Test User

In the SQL Editor, run:

```sql
INSERT INTO users (email) VALUES ('test@architect.dev');
SELECT * FROM users;
```

You should see your test user!

## Understanding the Database Structure

### Core Tables:

1. **users**: User accounts
2. **projects**: Each user's projects
3. **sessions**: Individual conversation sessions within a project
4. **messages**: Chat messages (user and AI responses)

### Agent Output Tables:

5. **technical_specs**: Output from Planner agent (Phase I)
6. **documentation_links**: Output from Librarian agent (Phase II)
7. **code_scaffolds**: Output from Mentor agent (Phase III)

## Supabase Features We're Using

### 1. Auto-generated REST API
Every table automatically gets REST endpoints:
- `GET /rest/v1/users` - List users
- `POST /rest/v1/messages` - Create a message
- etc.

### 2. Row Level Security (RLS)
We've enabled RLS to ensure data security. Currently configured for service role access.

### 3. Real-time Subscriptions (Future)
You can subscribe to database changes for live updates in the frontend.

## Troubleshooting

### Can't connect to Supabase?
- Check your `SUPABASE_URL` and keys in `.env`
- Make sure there are no extra spaces or quotes
- Verify your project is active in Supabase dashboard

### SQL errors when running schema?
- Make sure you're running all the SQL at once
- Check if the UUID extension is enabled
- Try running the CREATE EXTENSION line first

### Permission errors?
- Make sure you're using the `service_role` key in your backend
- Check that RLS policies are set correctly

## Next Steps

Now that Supabase is set up:
1. ✅ Test the connection from your backend
2. ✅ Set up Qdrant for vector storage
3. ✅ Build the LangGraph agents

## Useful Supabase Dashboard Links

- **Table Editor**: View and edit data
- **SQL Editor**: Run custom queries
- **API Docs**: Auto-generated API documentation
- **Database**: See schema and relationships
- **Logs**: View API and database logs

---

**Pro Tips:**
- The Supabase dashboard has excellent built-in documentation
- You can use the API docs to test endpoints directly
- The Table Editor lets you manually add/edit data for testing
- Enable database backups in production (Settings → Database)