# ============================================================================
# FILE:       docs/ARCHITECTURE.md
# PURPOSE:    Explain how the three parts of TaskFlow (frontend, backend,
#             database) cooperate, and walk through one full request from a
#             button click in React all the way to a PostgreSQL row and back.
# HOW IT WORKS: Section 1 gives the big picture, section 2 defines each
#             layer's responsibility, section 3 walks through task creation,
#             and later sections cover identity, assistant, comments and transfer.
# USED BY / DEPENDS ON: Humans reading the code; references files created in
#             Phases 2, 3 and 5-7.
# KEY CONCEPTS: layered architecture, dependency injection, ORM session,
#             Pydantic validation, TanStack Query cache, soft delete.
# ============================================================================

# TaskFlow Architecture

---

## 1. The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  BROWSER (React 18 + Vite + TypeScript)                                │
│                                                                         │
│  React workspace  →  api/ functions  →  fetch client                    │
│  (TaskWorkspace,     (typed endpoint     (adds demo identity headers,   │
│   AdminWorkspace)     wrappers)           parses responses/errors)     │
└───────────────┬─────────────────────────────────────────────────────────┘
                │  JSON over http://localhost:8000/api/v1/...
                │  CORS: Vite origin (5173) is allow-listed
┌───────────────▼─────────────────────────────────────────────────────────┐
│  FASTAPI (async Python)                                                │
│                                                                         │
│  router  →  dependency (get_current_user / require_admin)  →  service   │
│    │                          │                            │            │
│    │   reads X-User-Id,       │   Pydantic schema          │  business  │
│    │   X-Role headers         │   validates body/query     │  rules     │
│    └──────────┬───────────────┴──────────────┬─────────────┘            │
│               ▼                              ▼                          │
│        SQLAlchemy 2.0 async Session (ORM)  →  activity log writes       │
└───────────────┬─────────────────────────────────────────────────────────┘
                │  asyncpg driver (PostgreSQL wire protocol, port 5432)
┌───────────────▼─────────────────────────────────────────────────────────┐
│  POSTGRESQL                                                             │
│  users ─┬─< tasks ─┬─< subtasks                                        │
│         │          └─< comments ─> users (author)                      │
│         └─< activity_log                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

**Why layers?** Each layer only talks to its neighbours. You can swap the
frontend without touching the database, or replace the header-based roles with
JWT by editing only `dependencies.py`, because *authorization lives in exactly
one place*.

---

## 2. Layer Responsibilities

| Layer | Files | Does | Does NOT |
|---|---|---|---|
| UI workspaces | `frontend/src/components/*.tsx` | render task/admin/chat views and capture actions | construct raw HTTP requests |
| API service layer | `frontend/src/api/*.ts` | typed endpoint functions, attach demo identity headers, parse errors | render HTML or decide permissions |
| Routers | `backend/app/routers/*.py` | HTTP verbs/paths, status codes, call dependencies | write SQL by hand |
| Dependencies | `backend/app/dependencies.py` | resolve who the caller is from headers, enforce roles | know about tasks vs comments |
| Schemas | `backend/app/schemas/*.py` | validate & shape request/response JSON | touch the database |
| Models | `backend/app/models/*.py` | map Python classes to tables | know about HTTP |
| Services | `backend/app/services/*.py` | reusable business logic (CSV parsing, activity writes) | parse HTTP requests |

---

## 3. Request Lifecycle — "User creates a task"

| # | Where | What happens |
|---|---|---|
| 1 | `TaskWorkspace.tsx` | User fills the task form and presses **Add task**. The handler calls `createTask()` from `api/tasks.ts`. |
| 2 | `api/tasks.ts` | Serializes the task payload and calls `apiRequest('/tasks', ...)`. |
| 3 | `api/client.ts` | Builds the `/api/v1/tasks` URL and attaches `X-User-Id` and `X-Role` demo headers from local storage. |
| — | browser → server | FastAPI's CORS middleware checks `Origin: http://localhost:5173` against `CORS_ORIGINS` and adds `Access-Control-Allow-Origin`. |
| 5 | `routers/tasks.py` | `POST /api/v1/tasks` handler starts executing. Its signature declares dependencies: `db: AsyncSession = Depends(get_db)` opens a database session; `user = Depends(get_current_user)` resolves the caller. |
| 6 | `dependencies.py` | `get_current_user` loads the account by `X-User-Id`; role authorization uses the database row, not `X-Role`. |
| 7 | `schemas/task.py` | FastAPI validates the request against `TaskCreate`; invalid data receives **422**. |
| 8 | `routers/tasks.py` | Creates a task for the current owner at the next manual position and adds an audit entry. |
| 9 | `database.py` | The route commits the new task and returns its database-generated ID with **201 Created**. |
| 10 | `TaskWorkspace.tsx` | The client refreshes the visible task page and displays a success/error toast. |

---

## 4. Role Enforcement Flow (demo identity, database role authorization)

```
RoleSwitcher (UI) ──sets──> RoleContext { userId, role }
                               │ persisted in localStorage
                               ▼
api/client.ts ──attaches──> X-User-Id, X-Role on EVERY request
                               ▼
dependencies.get_current_user ──loads user by ID──>
   ├─ header missing / malformed / unknown user id → 401
   └─ known user → current User with role from database
                               ▼
dependencies.require_admin ──if user.role != "admin" → 403 else pass──>
                               ▼
            admin routers (stats, activity, user CRUD, moderation)
```

**SECURITY LIMIT:** `X-User-Id` selects a demo identity and is not
authentication. The role switcher is a development/grading convenience. The
backend ignores `X-Role` and grants admin routes only when the selected database
row has role `admin`, but anyone who can call this app can select another known
identity. Replace header identity with JWT/OAuth before public deployment.

## 5. Assistant Provider and Action Flow

`POST /api/v1/assistant/chat` resolves the same database-backed user dependency
as other routes. Provider credentials remain in backend settings and are tried
in this order: OpenRouter, Gemini, Groq. Model tool calls are restricted to an
allowlist in `services/assistant.py`; model-generated SQL is never accepted.
Every operation rechecks the stored role and task ownership, validates task
fields with existing Pydantic schemas, and writes task mutations to the activity
log. User tools expose only owned tasks. Admin-only tools provide system
summary, user management, comment moderation, task reassignment, and activity
inspection.

Chat messages are sent to the configured external model provider. Check the
selected provider's data handling terms before sending sensitive personal data.
The demo identity scheme is not suitable for public production use.

---

## 6. Comments Flow

1. Opening a task modal mounts `CommentThread`, which runs `useComments(taskId)`
   → `GET /tasks/{id}/comments` (the router already filtered by task ownership).
2. Adding a comment performs an optimistic insert (author = current user,
   `created_at = now`, temporary id), then `POST /tasks/{id}/comments`.
3. The server validates 1–1000 trimmed chars → 422 on failure → the frontend
   rolls back the optimistic row and shows an error toast.
4. Editing sets `updated_at` and `is_edited=true`; the UI shows an *edited* label.
5. Deleting: owner or admin only — enforced in the router with
   `comment.user_id != user.id and user.role != "admin"` → **403** otherwise.
6. Every mutation writes an activity-log row; the admin Activity page reads them.

---

## 7. Import / Export Flow

**Export** — `GET /tasks/export?format=csv|json[&filtered=true]`
1. The router resolves scope (own tasks; admin may export all or one user's).
2. If `filtered=true`, the exact same filter expression used by the list
   endpoint is applied, so "what I see" == "what I get".
3. `services/transfer.py` is a **generator function**: it fetches rows in
   batches and yields CSV/JSON chunks. FastAPI wraps it in a
   `StreamingResponse`, so memory usage stays flat even for 100k rows.
4. Before writing each cell, `sanitize_csv_cell()` prefixes `'` to values
   starting with `= + - @` → spreadsheet apps then treat them as text
   (**CSV injection** is blocked).
5. An activity row records the export (format + row count).
6. Filename looks like `tasks_2026-10-14.csv` (today's date).

**Import** — `POST /tasks/import?dry_run=true|false`
1. The frontend parses the file locally with papaparse for the **Preview**
   step (first rows + per-row errors) — preview costs no network traffic.
2. `dry_run=true`: the backend validates every row (schema, enums, dates, 2 MB
   limit, extension + MIME checks), detects duplicates (same `title` for the
   target user), and returns `{valid, invalid, duplicates, errors:[{row, reason}]}` —
   nothing is written to the database.
3. `dry_run=false` with `on_duplicate=skip|overwrite|create_anyway`: opens a
   **single transaction**. Any invalid row → `rollback()` → *zero* rows are
   imported, and a report lists exactly which rows failed and why. All valid →
   `commit()` + an activity row ("imported N tasks").
4. Admins may target another user via `?user_id=`; regular users always import
   into their own account.

---


