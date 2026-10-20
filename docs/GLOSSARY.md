# ============================================================================
# FILE:       docs/GLOSSARY.md
# PURPOSE:    Plain-English definition of every technical term used anywhere in
#             the TaskFlow project, so a beginner is never stuck on jargon.
# HOW IT WORKS: Grouped-by-topic list. Each entry explains the term, why
#             TaskFlow uses it, and points to the file where you can see it.
# USED BY / DEPENDS ON: Humans, at any time while reading the code.
# KEY CONCEPTS: vocabulary for full-stack web development.
# ============================================================================

# Glossary

*Terms are grouped by topic. "Where to see it" points at real project files.*

---

## A

**Async / Await (asynchronous programming)**
Normal code waits line-by-line: line 2 cannot start until line 1 finishes.
`async def` + `await` lets a program *start* a slow operation (like a database
query), do other work meanwhile, and resume when the result arrives — one
server thread can serve thousands of users without idling.
*Where:* every route in `backend/app/routers/*.py`.

**API (Application Programming Interface)**
A defined way for two programs to talk. TaskFlow's REST API exposes URLs like
`POST /api/v1/tasks` that accept and return JSON.
*Where:* `backend/app/main.py`, browsable at `/docs`.

**ASGI (Asynchronous Server Gateway Interface)**
The Python standard for async web servers. FastAPI is an ASGI application;
uvicorn is an ASGI server. (The older synchronous standard is WSGI.)
*Where:* `uvicorn app.main:app --reload`.

**Audit log / Activity log**
A permanent record of who did what and when. TaskFlow writes one row per
create/update/delete/import/export action.
*Where:* `backend/app/models/activity.py`, admin Activity page.

---

## C

**Cascade (ON DELETE CASCADE)**
A foreign-key rule: deleting the parent row automatically deletes its children.
Deleting a user removes their tasks; deleting a task removes its subtasks and
comments. Prevents orphan rows that point at nothing.
*Where:* `backend/app/models/task.py` and `docs/DATABASE_SCHEMA.md`.

**CORS (Cross-Origin Resource Sharing)**
Browsers block requests to a server unless that server explicitly allows the
calling page's origin. FastAPI must allow `http://localhost:5173` (Vite) or
every fetch from the React app fails.
*Where:* CORS middleware in `backend/app/main.py`.

**CRUD**
Create, Read, Update, Delete — the four basic operations of any persistent app.
*Where:* `/api/v1/tasks` endpoints.

**CSV (Comma-Separated Values)**
A plain-text table format Excel and Google Sheets can open: one row per line,
values separated by commas, quoted when they contain commas or newlines.
*Where:* export/import in `backend/app/services/transfer.py`.

**CSV injection**
A security risk where a cell like `=cmd|' /C calc'!A0` executes when the file is
opened in a spreadsheet app. Defence: prefix dangerous leading characters
(`=`, `+`, `-`, `@`) with a single quote so they are treated as text.
*Where:* `sanitize_csv_cell()` in `backend/app/services/transfer.py`.

---

## D

**Dependency injection (DI)**
A pattern where a function *asks* the framework for what it needs instead of
creating it itself. FastAPI runs `get_db()` to get a database session and
`get_current_user()` to identify the caller, then passes the results into your
route. Benefits: one place to change auth, easy test doubles.
*Where:* `backend/app/dependencies.py`.

**Dry run**
A rehearsal: the import endpoint validates all rows and reports what *would*
happen without writing anything, so the user can review errors first.
*Where:* `POST /tasks/import?dry_run=true`.

---

## E

**Endpoint / Route**
A specific URL + HTTP method that the server answers, e.g. `GET /api/v1/tasks`.
*Where:* `backend/app/routers/*.py`.

**ER diagram (Entity-Relationship diagram)**
A picture of tables (entities), their columns, and how they relate (1-to-many
lines). Mermaid is a text format that renders these diagrams inside Markdown.
*Where:* `docs/DATABASE_SCHEMA.md`.

---

## F

**Foreign key (FK)**
A column that stores the primary key of another table, creating a link:
`tasks.user_id` points at `users.id`. Usually paired with a cascade rule.

**Framework**
A library that provides the skeleton of an application (routing, validation,
servers) and calls *your* code — "inversion of control". FastAPI and React are
both frameworks.

---

## H

**Header (HTTP request header)**
Extra key/value metadata sent alongside every HTTP request. TaskFlow sends
`X-User-Id` and `X-Role` on each call; the `X-` prefix marks a custom,
non-standard header.
*Where:* `frontend/src/api/client.ts`.

---

## I

**Immutable / Mutability**
*Immutable* = cannot change after creation. React state and TanStack Query
cache entries are treated as immutable; instead of editing them you create a
new object — this is what makes React re-render reliably.

**Index (database)**
An ordered side-structure (like a book's index) that lets PostgreSQL find rows
without scanning the whole table. Cost: extra disk space and slightly slower
writes. TaskFlow indexes `user_id`, `status`, `due_date`, `task_id`.
*Where:* `docs/DATABASE_SCHEMA.md` section 4.

---

## J

**JSON (JavaScript Object Notation)**
The standard text format for structured data: `{"title": "Buy milk"}`. Every
API request and response in TaskFlow is JSON.

**JSONB**
PostgreSQL's binary JSON type: same data as JSON but stored so the database can
index and query inside it fast.
*Where:* `activity_log.detail`.

---

## L

**Light / Dark mode**
A UI colour-theme choice. TaskFlow is dark-first (`bg-slate-950`) with a class
toggle that switches Tailwind's `dark:` variants.

---

## M

**Migration (Alembic)**
A versioned Python file that describes one schema change (`create_table`,
`add_column`, ...). `alembic upgrade head` applies all pending migrations in
order; `alembic downgrade -1` reverses the last one. Migrations are how the
database schema evolves without losing data.
*Where:* `backend/alembic/versions/`.

**Middleware**
Code that runs on every request/response *before* your routes (or after them).
CORS handling is middleware: it inspects headers and adds CORS response
headers uniformly.
*Where:* `backend/app/main.py`.

**Model (ORM model)**
A Python class mapped to a database table; its attributes are the columns.
*Where:* `backend/app/models/*.py`.

**Mutation (TanStack Query)**
The Query terminology for any operation that *changes* server data (POST/PATCH/
DELETE), as opposed to a *query* which only reads it.
*Where:* `frontend/src/hooks/useTasks.ts`.

---

## N

**Node.js / npm**
Node.js runs JavaScript outside the browser (it powers the Vite dev server and
build tools). npm is its package manager: `npm install` downloads everything in
`package.json` into `node_modules/`.

---

## O

**Optimistic update**
Show the change in the UI *immediately*, before the server confirms — then
replace it with the server's version on success, or roll it back + show an
error on failure. The app *feels* instant while staying truthful.
*Where:* `useCreateTask` / `useAddComment` in `frontend/src/hooks/`.

**ORM (Object-Relational Mapper)**
A library that maps Python classes to SQL tables so you write `task.title = "x"`
instead of `UPDATE tasks SET title='x'`. SQLAlchemy is TaskFlow's ORM.
*Where:* `backend/app/models/`.

---

## P

**Pagination**
Splitting a long list into pages (`page=1&page_size=20`) so each response is
small and fast. Alternatives: infinite scroll (frontend keeps loading pages).

**POST / GET / PATCH / DELETE (HTTP methods)**
The verb of an HTTP request: GET reads, POST creates, PATCH partially updates,
DELETE removes. REST conventions map them onto resources like `/tasks`.

**Primary key (PK)**
The unique identifier column of a table (`id`). No two rows share it, and it is
never NULL.

**Pydantic**
A Python library that defines data shapes ("schemas") and validates data
against them at speed. FastAPI uses Pydantic to validate request bodies and to
generate the OpenAPI documentation automatically.
*Where:* `backend/app/schemas/`.

---

## R

**React component**
A function that returns JSX (HTML-like markup) and re-renders automatically
when its props or state change. Components are TaskFlow's building blocks.
*Where:* `frontend/src/components/**`.

**React Context**
A way to share data (here: current user + role) with every component without
passing props through dozens of layers.
*Where:* `frontend/src/context/RoleContext.tsx`.

**React Router**
Client-side routing: the URL changes (`/admin/users`) and React swaps which
page component is rendered — no full page reload, no server routes needed.

**REST (Representational State Transfer)**
An API style: nouns in URLs (`/tasks/42`), verbs in HTTP methods, JSON bodies,
status codes that mean what they say (201 created, 404 not found, 403 forbidden).

**Rollback**
Undoing an unfinished transaction so the database stays exactly as it was.
Used when any import row fails (all-or-nothing) and in optimistic UI updates.

---

## S

**Schema (database vs. Pydantic)**
*Database schema* = the layout of tables/columns. *Pydantic schema* = a Python
class describing allowed JSON fields. Same word, two layers — TaskFlow keeps
them in separate folders (`models/` vs `schemas/`) on purpose.

**SCRAM-SHA-256**
Modern password-authentication protocol PostgreSQL uses when a client connects
over TCP: the password never travels in clear text, and stolen hashes are hard
to crack. Configured in `pg_hba.conf`.
*Where:* `docs/POSTGRES_SETUP.md` section 4.

**Server-side rendering (SSR)**
Rendering HTML on the server per request. TaskFlow does *not* use SSR — Vite
serves one HTML shell and React renders in the browser (a SPA: single-page
application), which keeps the backend a pure JSON API.

**Soft delete**
Marking a row as deleted (`deleted_at = now()`) instead of removing it, so the
UI can offer *Undo* and history survives. Normal queries filter
`WHERE deleted_at IS NULL`.
*Where:* `DELETE /tasks/{id}` in `backend/app/routers/tasks.py`.

**StreamingResponse**
An HTTP response sent in chunks as they are produced, instead of building the
whole body in memory first — ideal for big CSV exports.
*Where:* export endpoint in `backend/app/routers/transfer.py`.

**Strict mode (TypeScript)**
Enables the compiler's full set of checks (e.g. `string | undefined` must be
narrowed before use). Catches whole bug classes before code ever runs.

---

## T

**Tailwind CSS**
A utility-first CSS framework: instead of custom `.card {}` classes you compose
small classes in markup — `backdrop-blur-md bg-white/5 border border-white/10`
is TaskFlow's "glass" look. Only classes actually used get compiled.

**TanStack Query (React Query)**
A library that manages *server* state: caching, background refetching, loading/
error flags, retries, and optimistic updates — so components don't hand-roll
`useEffect` + `useState` fetch logic.

**Timestamp with time zone (`TIMESTAMPTZ`)**
A PostgreSQL type storing an absolute point in time in UTC. The same instant
renders correctly in any user's local timezone.

---

## U

**Undo (soft-delete restore)**
After `DELETE`, the row still exists; a follow-up request clears `deleted_at`.
TaskFlow shows a 5-second toast with an Undo button after every deletion.

**URL query parameter**
The `?key=value&key2=value2` part of a URL: `GET /tasks?status=pending&sort=due`.
Used for filtering, sorting, pagination and export options.

---

## V

**Validation**
Checking that input matches the rules (length, type, enum) *before* it touches
the database. Rule #1: never trust the frontend — the same rules are enforced
by Pydantic, and again by database CHECK constraints.

**Vite**
A fast dev server and bundler: it serves modules on demand (instant startup)
and bundles an optimized `dist/` for production.

---

## X

**`X-User-Id` / `X-Role` headers**
TaskFlow's stand-in for authentication: the frontend says *who* is calling and
*in what role*; the backend verifies both against the database.
*Where:* `backend/app/dependencies.py`.

---

## 4 / 5 / 6

**Status codes** — the API's success/failure vocabulary:
`200` OK · `201` Created · `204` No Content · `400` Bad Request ·
`403` Forbidden (role denied) · `404` Not Found · `409` Conflict (duplicate) ·
`413` Payload Too Large (>2 MB import) · `415` Unsupported Media Type (bad file
type) · `422` Validation Error (Pydantic) · `500` Internal Server Error.

**WCAG / accessibility (a11y)**
Making UI usable by keyboard and screen-reader users: focus rings, ARIA labels,
navigable modals, and respecting `prefers-reduced-motion` to disable heavy
animations for sensitive users.



