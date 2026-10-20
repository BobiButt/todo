# ============================================================================
# FILE:       README.md
# PURPOSE:    Single entry point for the TaskFlow project: what it is, what it
#             can do, how the code is organized (full folder trees), and how to
#             run it end to end.
# HOW IT WORKS: Read top to bottom. The folder trees mirror the real
#             filesystem exactly, so you can use them as a map while reading
#             code. Setup commands are repeated here for convenience, but the
#             PostgreSQL part lives in docs/POSTGRES_SETUP.md with full notes.
# USED BY / DEPENDS ON: Humans. Points to every other document in docs/.
# KEY CONCEPTS: monorepo layout (backend/ + frontend/ in one repository),
#             layered architecture, role-based (not authenticated) access.
# ============================================================================

# TaskFlow — Modern Full-Stack Todo App

TaskFlow is a local-development todo application with task and subtask CRUD,
comments, CSV/JSON import & export, manual ordering, an administrator console,
and separate role-scoped AI assistants.

There is **no real authentication** (no JWT, no login forms). Instead, a header
identity selector lets you choose a demo user. The backend resolves that user
from `X-User-Id` and uses the database-stored role; it ignores `X-Role`. This is
not authentication and must not be exposed publicly without replacing the demo
identity mechanism with JWT/OAuth.

---

## 1. Tech Stack

| Layer     | Technology |
|-----------|------------|
| Backend   | Python 3.12+, FastAPI (async), SQLAlchemy 2.0 async + asyncpg, Pydantic v2, pydantic-settings, Alembic, pytest + httpx |
| Database  | PostgreSQL (local instance on Fedora) |
| Frontend  | React 18 + Vite + TypeScript, Tailwind CSS, Lucide React, sonner, papaparse |

---

## 2. Feature Highlights

**User panel**
- Create / read / update / delete / complete tasks (soft delete with a 5-second **Undo** toast)
- Fields: title, description, priority, due date, tags, category, status, timestamps
- Subtasks with completion counts
- Search, filters (status, priority, tag, overdue, due today), sorting, pagination
- Manual up/down ordering (persisted `position`)
- Personal status and overdue totals

**Comments**
- Thread per task, add and edit own comments, delete own comments
- Edit (marked "edited") and delete — own comments only; admins can delete any
- Admin comment moderation can delete comments across tasks
- Validation 1–1000 chars, comment-count badge on each card, included in activity log

**Import / Export**
- Export CSV or JSON (streamed), respecting active filters, with CSV-injection protection
- Import flow validates with a dry run and asks for confirmation; duplicate
  handling supports skip / overwrite / create; imports use a database transaction
- Downloadable CSV/JSON sample templates; admins can import for any user

**Admin panel**
- Dashboard stats (users, tasks, completion rate, per-user chart, overdue, comments)
- Users CRUD with cascade-delete confirmation and task counts
- Global task table with reassignment, filtering, bulk delete / mark complete
- Comment moderation and an activity log of who did what and when

**Role-scoped assistant**
- Separate personal and administrator assistant experiences. Users can search and manage only their own tasks; admins can inspect system tasks, list users, review aggregate metrics, and reassign tasks.
- The assistant uses allowlisted TaskFlow operations only. It cannot execute arbitrary SQL or act outside the selected database identity's stored role.
- Provider priority is OpenRouter, then Gemini, then Groq. Configure keys only in `backend/.env`; chat messages are sent to the configured external provider.

---

## 3. Project Layout

The current frontend combines task actions in `TaskWorkspace.tsx`, admin tools
in `AdminWorkspace.tsx`, and assistant chat in `AssistantPanel.tsx`. The detailed
component/page tree below was the original target structure; files still
unchecked in `PROGRESS.md` have not been created as separate components.

```
todo/
│
├── README.md                     ← you are here
├── .gitignore                    ← files git must never commit (.env, node_modules, ...)
│
├── docs/
│   ├── POSTGRES_SETUP.md         ← Fedora PostgreSQL install guide (do this FIRST)
│   ├── ARCHITECTURE.md           ← how the layers talk + request-lifecycle walkthrough
│   ├── DATABASE_SCHEMA.md        ← Mermaid ER diagram + every column explained
│   ├── CONFIG_EXPLAINED.md       ← line-by-line explanation of all JSON/config files
│   └── GLOSSARY.md               ← plain-English definitions of every jargon term
│
├── backend/
│   ├── .env                      ← real secrets (NEVER committed)
│   ├── .env.example              ← safe template copied to .env
│   ├── requirements.txt          ← pip dependencies with version pins
│   ├── alembic.ini               ← Alembic migration tool configuration
│   ├── seed.py                   ← creates 1 admin + 5 sample users with data
│   │
│   ├── app/
│   │   ├── __init__.py           ← marks app/ as a Python package
│   │   ├── main.py               ← FastAPI app factory: CORS, routers, /health
│   │   ├── config.py             ← pydantic-settings: reads .env into typed settings
│   │   ├── database.py           ← async engine, session factory, get_db dependency
│   │   ├── dependencies.py       ← get_current_user / require_admin (role enforcement)
│   │   │
│   │   ├── models/               ← SQLAlchemy ORM classes (= database tables)
│   │   │   ├── __init__.py       ← re-exports all models so Alembic sees them
│   │   │   ├── user.py           ← users table
│   │   │   ├── task.py           ← tasks table (soft delete, position, tags)
│   │   │   ├── subtask.py        ← subtasks table (checklist items)
│   │   │   ├── comment.py        ← comments table (1–1000 chars)
│   │   │   └── activity.py       ← activity_log table (admin audit trail)
│   │   │
│   │   ├── schemas/              ← Pydantic v2 request/response contracts
│   │   │   ├── __init__.py
│   │   │   ├── common.py         ← pagination envelope, error shape, Role enum
│   │   │   ├── user.py           ← UserCreate / UserUpdate / UserRead
│   │   │   ├── task.py           ← TaskCreate / TaskUpdate / TaskRead / filters
│   │   │   ├── comment.py        ← CommentCreate / CommentUpdate / CommentRead
│   │   │   └── transfer.py       ← import row schema, export row shape, report
│   │   │
│   │   ├── routers/              ← FastAPI route handlers (the HTTP layer)
│   │   │   ├── __init__.py
│   │   │   ├── users.py          ← /api/v1/users CRUD
│   │   │   ├── tasks.py          ← /api/v1/tasks CRUD + toggle + reorder
│   │   │   ├── comments.py       ← /api/v1/tasks/{id}/comments CRUD
│   │   │   ├── transfer.py       ← /api/v1/tasks/export, /tasks/import, templates
│   │   │   └── admin.py          ← /api/v1/admin/stats, /activity, moderation
│   │   │
│   │   └── services/             ← business logic reused by several routers
│   │       ├── __init__.py
│   │       ├── activity.py       ← write_activity() audit helper
│   │       └── transfer.py       ← CSV/JSON parse, validate, stream, injection guard
│   │
│   ├── alembic/
│   │   ├── env.py                ← tells Alembic which metadata to diff
│   │   ├── script.py.mako        ← template for new migration files
│   │   └── versions/
│   │       └── 0001_initial_schema.py  ← first migration: creates all tables
│   │
│   └── tests/
│       ├── conftest.py           ← fixtures: in-memory app, AsyncClient, test DB
│       ├── test_users.py         ← user CRUD + role enforcement
│       ├── test_tasks.py         ← task CRUD, filters, toggle, reorder, soft delete
│       ├── test_comments.py      ← comment permissions + validation
│       ├── test_transfer.py      ← import dry-run/rollback, CSV-injection export
│       └── test_admin.py         ← admin stats/activity 403s for non-admins
│
└── frontend/
    ├── index.html                ← the single HTML page Vite serves
    ├── package.json              ← npm dependencies and scripts
    ├── tsconfig.json             ← TypeScript strictness rules
    ├── tsconfig.node.json        ← TypeScript rules for vite.config.ts only
    ├── vite.config.ts            ← Vite dev server + proxy + React plugin
    ├── tailwind.config.js        ← Tailwind: dark-first palette, animations
    ├── postcss.config.js         ← plugs Tailwind into the CSS pipeline
    ├── .env.example              ← VITE_API_BASE_URL template
    │
    └── src/
        ├── main.tsx              ← React entry point: providers + router
        ├── App.tsx               ← route table (user + admin pages)
        ├── index.css             ← Tailwind directives + aurora/glass utilities
        ├── vite-env.d.ts         ← Vite client types
        │
        ├── types/index.ts        ← shared TypeScript interfaces (Task, Comment, ...)
        │
        ├── api/                  ← raw HTTP layer (fetch wrappers)
        │   ├── client.ts         ← fetch + X-User-Id/X-Role headers + error parse
        │   ├── users.ts          ← user endpoints
        │   ├── tasks.ts          ← task endpoints incl. export/import
        │   ├── comments.ts       ← comment endpoints
        │   └── admin.ts          ← stats, activity, moderation endpoints
        │
        ├── context/RoleContext.tsx   ← current user + role, persisted to localStorage
        │
        ├── hooks/                ← TanStack Query hooks (cache, optimistic updates)
        │   ├── useUsers.ts
        │   ├── useTasks.ts
        │   ├── useComments.ts
        │   └── useAdmin.ts
        │
        ├── utils/
        │   ├── dates.ts          ← relative time, overdue/due-soon helpers
        │   └── csv.ts            ← client-side CSV parse (papaparse) + preview
        │
        ├── components/
        │   ├── shared/           ← reusable UI primitives
        │   │   ├── Modal.tsx         ← spring modal, focus trap, Esc to close
        │   │   ├── Skeleton.tsx      ← loading shimmer blocks
        │   │   ├── EmptyState.tsx    ← friendly "nothing here" view
        │   │   ├── GlassCard.tsx     ← glassmorphic card wrapper
        │   │   ├── ConfirmDialog.tsx ← destructive-action confirmation
        │   │   └── ErrorBanner.tsx   ← inline error message
        │   │
        │   ├── layout/
        │   │   ├── AppShell.tsx      ← aurora background + header + outlet
        │   │   ├── Header.tsx        ← title, search hint, shortcuts, theme toggle
        │   │   └── RoleSwitcher.tsx  ← User⇄Admin toggle + user picker dropdown
        │   │
        │   ├── tasks/
        │   │   ├── TaskCard.tsx      ← draggable card, tilt hover, badges, comment count
        │   │   ├── TaskModal.tsx     ← create/edit dialog hosting comments
        │   │   ├── TaskForm.tsx      ← validated form fields
        │   │   ├── TaskList.tsx      ← dnd-kit sortable list + pagination
        │   │   ├── SubtaskList.tsx   ← checklist + progress bar
        │   │   ├── CommentThread.tsx ← comment list, editor, autoscroll
        │   │   ├── FiltersBar.tsx    ← search/filter/sort controls
        │   │   ├── StatsWidget.tsx   ← personal stats (completed/pending/overdue)
        │   │   └── TaskCardBadge.tsx ← overdue / due-soon pill
        │   │
        │   ├── transfer/
        │   │   ├── ExportMenu.tsx    ← CSV/JSON dropdown + "filtered only" option
        │   │   └── ImportWizard.tsx  ← stepper: Upload→Preview→Options→Result
        │   │
        │   └── admin/
        │       ├── StatsCards.tsx        ← KPI tiles
        │       ├── TasksPerUserChart.tsx ← bar chart (pure SVG, no extra lib)
        │       ├── UsersTable.tsx        ← users CRUD table
        │       ├── GlobalTasksTable.tsx  ← all tasks + bulk actions + reassign
        │       ├── CommentsModeration.tsx← delete-any-comment view
        │       └── ActivityLog.tsx       ← audit trail list
        │
        └── pages/
            ├── UserView.tsx        ← main user workspace
            ├── AdminDashboard.tsx  ← stats + charts
            ├── AdminUsers.tsx      ← users management
            ├── AdminTasks.tsx      ← global task management
            ├── AdminComments.tsx   ← comment moderation
            ├── AdminActivity.tsx   ← activity log
            └── NotFound.tsx        ← 404 fallback
```

---

## 4. Setup & Run (summary — full details in Phase 7)

```bash
# 0. PostgreSQL (Fedora) — follow docs/POSTGRES_SETUP.md completely first.

# 1. Backend
cd backend                                        # enter backend folder
python3 -m venv .venv                             # create an isolated Python environment
source .venv/bin/activate                         # activate it (fish: source .venv/bin/activate.fish)
pip install -r requirements.txt                   # install pinned dependencies
cp -n .env.example .env                           # first setup only; does not overwrite an existing .env
# Open backend/.env in a text editor and paste provider key(s) on the matching lines (below).
alembic upgrade head                              # create all tables via migration
python seed.py                                    # insert demo users/tasks/comments
uvicorn app.main:app --reload                     # start API on http://localhost:8000

# 2. Frontend (in a NEW terminal)
cd frontend                                       # enter frontend folder
npm install                                       # install JS dependencies
npm run dev                                        # start Vite on http://localhost:5173
```

- App: <http://localhost:5173>
- API: <http://localhost:8000>
- Interactive docs (Swagger UI): <http://localhost:8000/docs>

---

## 5. Documentation Map

| Document | Read it when… |
|---|---|
| `docs/POSTGRES_SETUP.md` | You need to install/configure PostgreSQL on Fedora |
| `docs/ARCHITECTURE.md` | You want to understand how a click becomes a database row |
| `docs/DATABASE_SCHEMA.md` | You need the tables, columns, and relationships |
| `docs/CONFIG_EXPLAINED.md` | A JSON/config file looks like an unreadable wall |
| `docs/GLOSSARY.md` | You hit a term you don't know (ORM, CORS, soft delete, ...) |

---

## 6. Delivery Phases

This project is delivered in 7 phases. Each phase ends with a file list and
open decisions; the next phase begins only after you reply **continue**.

1. **Phase 1** — PostgreSQL Fedora guide, folder trees, `docs/` files ← *current*
2. **Phase 2** — Backend core: config, database, models, schemas, Alembic, requirements
3. **Phase 3** — Backend logic: dependencies, routers, main, seed
4. **Phase 4** — Backend tests
5. **Phase 5** — Frontend foundation: Tailwind/Vite, API layer, context, hooks, shared components
6. **Phase 6** — Frontend features: tasks, comments, filters, import/export
7. **Phase 7** — Admin view, routing, final setup & manual test checklist

### Assistant provider configuration

Set one or more provider keys in `backend/.env`. The backend tries configured
providers in this order: `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, then
`GROQ_API_KEY`. Optional model overrides are `OPENROUTER_MODEL`, `GEMINI_MODEL`,
and `GROQ_MODEL`. Provider keys must never use a `VITE_` prefix or be placed in
frontend configuration. If no key is configured, the assistant responds with a
setup error while the rest of TaskFlow remains usable.

The assistant is restricted to TaskFlow task/user operations. User operations
are constrained by the database-resolved user identity; admin operations are
available only for a database user whose stored role is `admin`. This project
still uses selectable demo identities (`X-User-Id`) rather than real login, so
do not expose it publicly without replacing that development identity scheme
with real authentication. Chat content is sent to the selected model provider.

To enter a key, open **`backend/.env`** (not `frontend/.env`) in VS Code and
replace the blank value after the provider name. For example, paste your actual
OpenRouter key after `OPENROUTER_API_KEY=`. Leave fallback providers blank if
you do not use them. You may set multiple providers; if an earlier configured
provider is unavailable, TaskFlow tries the next configured provider.

```ini
OPENROUTER_API_KEY=paste-your-openrouter-key-here
GEMINI_API_KEY=
GROQ_API_KEY=
```

Use your actual key only in the local, git-ignored backend file. Do not paste it
into this chat, source code, `frontend/.env`, or any `VITE_` variable. Restart
the backend after changing `.env` so it reloads the configuration.



---

