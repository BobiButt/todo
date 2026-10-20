# ============================================================================
# FILE:       DECISIONS.md
# PURPOSE:    Architectural Decision Records (ADRs) and design rationale for
#             the TaskFlow application.
# HOW IT WORKS: Documents the 'why' behind key architectural choices so any
#             developer or reviewer understands the context and trade-offs.
# USED BY / DEPENDS ON: Team members, students, reviewers.
# KEY CONCEPTS: Architecture Decision Records, role-based architecture,
#             data safety, relational integrity, UX performance.
# ============================================================================

# TaskFlow Architectural Decision Records (ADRs)

## ADR-001: Demo Header Identity Until Real Authentication
- **Context:** The application needs role-based permissions (User vs Admin) for managing tasks, comments, and system metrics without requiring registration and login flows.
- **Decision:** Use `X-User-Id` as a local demo identity selector. The backend loads the user from PostgreSQL and derives the role from that record; `X-Role` is ignored.
- **Rationale:** Keeps the local demo immediately usable while keeping all permission decisions in backend dependencies and route checks.
- **Consequences:** Anyone who can call the API can choose a known user ID. This is not authentication and is not safe for public deployment; replace it with JWT/OAuth before exposing the app.

## ADR-002: PostgreSQL `text[]` Array for Tags
- **Context:** Tasks need multiple tags for categorization and filtering.
- **Decision:** Use PostgreSQL native `text[]` array (`sqlalchemy.dialects.postgresql.ARRAY(String)`) rather than an association table or JSON string.
- **Rationale:** Native arrays allow indexing via GIN, clean querying with `tag = ANY(tags)`, and avoid multi-table JOIN overhead for a simple string list. `category` is maintained as a separate single-value column.
- **Consequences:** Requires PostgreSQL (tests must run against a PostgreSQL test database rather than SQLite).

## ADR-003: Soft Delete for Tasks, Hard Delete for Comments & Subtasks
- **Context:** Accidental task deletion causes high user anxiety and data loss.
- **Decision:** Tasks have a nullable `deleted_at` timestamp. Queries filter `deleted_at IS NULL`. The frontend provides a 5-second "Undo" toast. Subtasks and comments use `CASCADE` hard delete when their parent task or user is deleted.
- **Rationale:** Tasks represent significant user investment and need restoration support. Comments and subtasks have no standalone identity without their parent task.

## ADR-004: Double Precision Position for Manual Task Ordering
- **Context:** Users can reorder tasks manually via drag-and-drop.
- **Decision:** Store `position` as `DOUBLE PRECISION`; the current UI moves tasks up/down and submits the visible order to the reorder API, which normalizes positions into integer intervals.
- **Rationale:** Keeps ordering explicit and persistent. Reordering the current list updates the rows in that list ($O(N)$), rather than pretending the current UI performs fractional drag-and-drop.

## ADR-005: Atomic Import and CSV Injection Protection
- **Context:** Users and Admins can import tasks from CSV/JSON and export task reports.
- **Decision:** 
  1. All imports run inside a single database transaction (`await db.begin()`) — either all valid rows commit or the entire batch rolls back.
  2. Dry-run mode (`dry_run=true`) validates rows and duplicate titles without committing.
  3. CSV export sanitizes formulas: any cell beginning with `=`, `+`, `-`, or `@` is prefixed with a single quote `'`.
- **Rationale:** Protects spreadsheets (Excel, LibreOffice) from Formula Injection / Remote Code Execution, and prevents partial corrupted imports.

## ADR-006: Audit Trail with Actor Snapshot
- **Context:** Activity log must persist when users are removed by administrators.
- **Decision:** `activity_log.user_id` is a nullable foreign key with `ON DELETE SET NULL`, and `actor_name` stores a snapshot string of the user's name at the moment the action was recorded.
- **Rationale:** Deleting a user must never delete audit history or break referential integrity.

## ADR-007: Dark Green Operations Workspace
- **Context:** Modern, high-craft visual presentation with high readability.
- **Decision:** Use a charcoal/green workspace with muted mint user actions, coral admin actions, compact task rows, and responsive layouts.
- **Rationale:** Keep a dense task-management UI readable and easy to scan while making user and administrator surfaces visually distinct.
