# Architect — Frontend

> Next.js 15 frontend for the Architect AI orchestration platform.

## Tech Stack

| Layer         | Technology                                  |
|---------------|---------------------------------------------|
| Framework     | Next.js 15 (App Router)                     |
| Language      | TypeScript 5                                |
| Styling       | Tailwind CSS 3 + custom Deep Midnight theme |
| State         | Zustand 5                                   |
| Auth          | Supabase Auth (@supabase/ssr)               |
| API calls     | Axios (REST) + native WebSocket             |
| Visualization | React Flow (workflow diagram)               |
| Layout        | react-resizable-panels                      |
| Markdown      | react-markdown + remark-gfm                 |
| Syntax        | react-syntax-highlighter (Prism)            |

---

## Project Structure

```
src/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx                # Root layout (fonts, metadata)
│   ├── page.tsx                  # Landing page  (/)
│   ├── globals.css               # Global styles + Tailwind
│   │
│   ├── auth/
│   │   ├── login/page.tsx        # /auth/login
│   │   ├── register/page.tsx     # /auth/register
│   │   ├── callback/route.ts     # OAuth code exchange
│   │   └── signout/route.ts      # POST sign-out
│   │
│   ├── dashboard/
│   │   └── page.tsx              # /dashboard — project list
│   │
│   └── workspace/
│       └── [projectId]/
│           └── page.tsx          # /workspace/:id — dual-pane IDE
│
├── components/
│   ├── dashboard/
│   │   └── CreateProjectDialog.tsx   # Create project modal
│   └── workspace/
│       ├── WorkspaceShell.tsx        # Resizable panel host
│       ├── PhaseIndicator.tsx        # Phase stepper in header
│       ├── flow/
│       │   └── FlowPanel.tsx         # React Flow visualization
│       └── chat/
│           ├── ChatPanel.tsx         # Chat UI + streaming
│           └── SyntaxHighlighter.tsx # Code block renderer
│
├── hooks/
│   ├── useAuth.ts         # Supabase auth state
│   ├── useProjects.ts     # Project CRUD
│   └── useChat.ts         # Message send + WebSocket stream
│
├── lib/
│   ├── api.ts             # Axios client + all API calls
│   ├── utils.ts           # cn(), formatDate(), phase helpers
│   └── supabase/
│       ├── client.ts      # Browser client
│       ├── server.ts      # Server component client
│       └── middleware.ts  # Auth middleware helper
│
├── middleware.ts           # Route protection & session refresh
├── stores/
│   └── useProjectStore.ts # Zustand: project/session/chat state
└── types/
    └── index.ts           # TypeScript types mirroring backend schemas
```

---

## Quick Start

### 1. Prerequisites

- Node.js 18+
- pnpm (or npm / yarn)
- A running Architect backend at `http://localhost:8000`
- Supabase project with Auth enabled

### 2. Install dependencies

```bash
cd frontend
npm install          # or pnpm install
```

### 3. Set up environment variables

```bash
cp .env.local.example .env.local
```

Edit `.env.local` and fill in:

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 4. Configure Supabase Auth

In your Supabase dashboard:

1. **Authentication → Providers** — enable Google and/or GitHub
2. **Authentication → URL Configuration**:
   - Site URL: `http://localhost:3000`
   - Redirect URLs: `http://localhost:3000/auth/callback`
3. For Google OAuth: create credentials at [console.cloud.google.com](https://console.cloud.google.com)
4. For GitHub OAuth: create an OAuth App at [github.com/settings/developers](https://github.com/settings/developers)

### 5. Run the dev server

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

---

## Pages & Routes

| Route                    | Description                                        | Auth required |
|--------------------------|----------------------------------------------------|---------------|
| `/`                      | Landing page with hero + features                  | No            |
| `/auth/login`            | Email + OAuth sign in                              | No (redirects if authed) |
| `/auth/register`         | Email registration                                 | No (redirects if authed) |
| `/auth/callback`         | Supabase OAuth exchange (route handler)            | —             |
| `/dashboard`             | Project list + create project                      | Yes           |
| `/workspace/[projectId]` | Dual-pane workspace (React Flow + Chat)            | Yes           |

---

## Connecting to the Backend

The API client (`src/lib/api.ts`) automatically:
- Reads `NEXT_PUBLIC_BACKEND_URL` for REST calls
- Reads `NEXT_PUBLIC_WS_URL` for WebSocket connections
- Attaches the Supabase JWT to every request via an Axios interceptor

**Expected backend endpoints:**

```
GET  /api/projects                    → ProjectResponse[]
POST /api/projects                    → ProjectResponse
GET  /api/projects/:id                → ProjectResponse
DELETE /api/projects/:id

POST /api/sessions                    → SessionResponse
GET  /api/sessions?project_id=:id     → SessionResponse
GET  /api/sessions/:id/messages       → MessageResponse[]
GET  /api/sessions/:id/technical-spec → TechnicalSpecResponse
GET  /api/sessions/:id/documentation-links → DocumentationLinkResponse[]
GET  /api/sessions/:id/scaffolds      → CodeScaffoldResponse[]

POST /api/chat                        → ChatResponse
WS   /api/ws/chat/:sessionId          → streaming StreamChunk[]
```

---

## Design System — Deep Midnight

The theme uses a custom Tailwind palette defined in `tailwind.config.ts`:

| Token               | Value         | Usage                        |
|---------------------|---------------|------------------------------|
| `midnight-950`      | `#080c14`     | Page background              |
| `navy-800`          | `#0d1220`     | Surface cards / panels       |
| `accent-indigo`     | `#6366f1`     | Primary CTA, active states   |
| `accent-cyan`       | `#06b6d4`     | Librarian phase accent       |
| `accent-violet`     | `#8b5cf6`     | Mentor phase accent          |

**Custom CSS utilities** (in `globals.css`):
- `.glass` — dark frosted glass card
- `.glass-raised` — elevated glass surface
- `.gradient-text` — blue → indigo → violet gradient text
- `.glow-text` — indigo text shadow
- `.shimmer` — loading skeleton animation

**Fonts:**
- Display: `DM Serif Display` — headings
- Body: `DM Sans` — UI text
- Mono: `JetBrains Mono` — code blocks

---

## Development Scripts

```bash
npm run dev        # Start dev server (port 3000)
npm run build      # Production build
npm run start      # Start production server
npm run type-check # TypeScript check (no emit)
npm run lint       # ESLint
npm run format     # Prettier
```

---

## Environment Variables Reference

| Variable                         | Required | Description                               |
|----------------------------------|----------|-------------------------------------------|
| `NEXT_PUBLIC_SUPABASE_URL`       | ✅       | Your Supabase project URL                 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`  | ✅       | Supabase anon/public key                  |
| `NEXT_PUBLIC_BACKEND_URL`        | ✅       | FastAPI backend base URL                  |
| `NEXT_PUBLIC_WS_URL`             | ✅       | WebSocket base URL (ws:// or wss://)      |
| `NEXT_PUBLIC_SITE_URL`           | Optional | Full site URL (used in sign-out redirect) |
