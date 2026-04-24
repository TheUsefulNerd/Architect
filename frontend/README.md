# Architect — Frontend

Next.js 15 frontend for the Architect AI orchestration platform.

**Live:** `https://architect-ochre.vercel.app`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript 5 |
| Styling | Tailwind CSS — Deep Midnight theme |
| Auth | Supabase Auth (`@supabase/ssr`) |
| Visualization | React Flow |
| State | Zustand 5 |
| API | Axios (REST) + native EventSource (SSE) |
| Markdown | react-markdown + remark-gfm |
| Syntax | react-syntax-highlighter (Prism) |

---

## Local Setup

### 1. Install dependencies
```bash
cd frontend
npm install
```

### 2. Configure environment
```bash
cp .env.local.example .env.local
```

Fill in `frontend/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 3. Run dev server
```bash
npm run dev
```

Visit `http://localhost:3000`

---

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx                  # Root layout (fonts, metadata)
│   ├── page.tsx                    # Landing page (/)
│   ├── globals.css                 # Tailwind + Deep Midnight theme
│   ├── auth/
│   │   ├── login/page.tsx          # /auth/login
│   │   ├── register/page.tsx       # /auth/register
│   │   ├── callback/route.ts       # OAuth code exchange handler
│   │   └── signout/route.ts        # POST sign-out
│   ├── dashboard/
│   │   └── page.tsx                # /dashboard — project list
│   └── workspace/
│       └── [projectId]/page.tsx    # /workspace/:id — dual-pane IDE
│
├── components/
│   ├── dashboard/
│   │   └── CreateProjectDialog.tsx
│   └── workspace/
│       ├── WorkspaceShell.tsx      # Resizable panel host
│       ├── PhaseIndicator.tsx      # Phase stepper in header
│       ├── flow/FlowPanel.tsx      # React Flow roadmap
│       └── chat/
│           ├── ChatPanel.tsx       # Chat UI + SSE streaming
│           └── SyntaxHighlighter.tsx
│
├── hooks/
│   ├── useAuth.ts                  # Supabase auth state
│   ├── useProjects.ts              # Project CRUD
│   └── useChat.ts                  # Message send + stream
│
├── lib/
│   ├── api.ts                      # Axios client + all API calls
│   ├── utils.ts                    # Helpers
│   └── supabase/
│       ├── client.ts               # Browser Supabase client
│       ├── server.ts               # Server component client
│       └── middleware.ts           # Auth middleware helper
│
├── middleware.ts                   # Route protection + session refresh
├── stores/useProjectStore.ts       # Zustand global state
└── types/index.ts                  # TypeScript types
```

---

## Routes

| Route | Description | Auth |
|---|---|---|
| `/` | Landing page | No |
| `/auth/login` | Email + OAuth sign in | No |
| `/auth/register` | Email registration | No |
| `/auth/callback` | Supabase OAuth exchange | — |
| `/dashboard` | Project list + create | Yes |
| `/workspace/[projectId]` | Dual-pane workspace | Yes |

---

## Auth Setup (Supabase)

OAuth is configured for Google and GitHub. Required settings in Supabase dashboard:

**Authentication → URL Configuration:**
- Site URL: `https://architect-ochre.vercel.app`
- Redirect URLs:
  - `https://architect-ochre.vercel.app/auth/callback`
  - `http://localhost:3000/auth/callback`

**Authentication → Providers:**
- Google: enabled (credentials from Google Cloud Console)
- GitHub: enabled (credentials from GitHub OAuth Apps)

The `/auth/callback/route.ts` handler exchanges the OAuth code for a Supabase session and redirects the user to `/dashboard`.

---

## Deployment (Vercel)

Push to `main` on GitHub — Vercel auto-deploys.

**Required environment variables on Vercel:**
```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXT_PUBLIC_BACKEND_URL=https://architect-c10k.onrender.com
```

---

## Design System — Deep Midnight

| Token | Value | Usage |
|---|---|---|
| `midnight-950` | `#080c14` | Page background |
| `navy-800` | `#0d1220` | Surface cards / panels |
| `accent-indigo` | `#6366f1` | Primary CTA, active states |
| `accent-cyan` | `#06b6d4` | Librarian phase accent |
| `accent-violet` | `#8b5cf6` | Mentor phase accent |

**Custom CSS utilities** (in `globals.css`):
- `.glass` — dark frosted glass card
- `.glass-raised` — elevated glass surface
- `.gradient-text` — blue → indigo → violet gradient text
- `.glow-text` — indigo text shadow
- `.shimmer` — loading skeleton animation

**Fonts:**
- Display: `DM Serif Display`
- Body: `DM Sans`
- Mono: `JetBrains Mono`

---

## Development Commands

```bash
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run start        # Start production server
npm run type-check   # TypeScript check
npm run lint         # ESLint
npm run format       # Prettier
```