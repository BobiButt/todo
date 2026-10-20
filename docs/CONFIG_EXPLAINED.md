# ============================================================================
# FILE:       docs/CONFIG_EXPLAINED.md
# PURPOSE:    Explain every key of every configuration file line by line.
#             JSON files (package.json, tsconfig.json, ...) CANNOT contain
#             comments — putting `//` inside them breaks parsing — so this
#             document is their official commenting layer (see spec 7.5).
# HOW IT WORKS: For each config file: a copy of the file with annotations on
#             every meaningful line, plus a "why it matters" summary.
# USED BY / DEPENDS ON: The real files live in backend/ and frontend/.
#             Keep this doc in sync when a config changes.
# KEY CONCEPTS: semver ranges, dev dependencies, compiler strictness, module
#             resolution, bundler dev server, PostCSS plugins, Tailwind JIT.
# ============================================================================

# Configuration Files, Explained

---

## 1. `backend/requirements.txt`

```text
# --- Web framework -------------------------------------------------------
# fastapi gives us async HTTP routes + automatic OpenAPI docs from type hints
fastapi==0.115.6
# uvicorn is the ASGI server that actually runs the FastAPI app (dev: --reload)
uvicorn[standard]==0.32.1
# python-multipart lets FastAPI parse multipart/form-data (file upload for CSV/JSON import)
python-multipart==0.0.19

# --- Database layer ------------------------------------------------------
# sqlalchemy 2.0 is the ORM (object-relational mapper): Python classes = tables
SQLAlchemy==2.0.36
# asyncpg is the non-blocking PostgreSQL driver used by SQLAlchemy's async engine
asyncpg==0.30.0
# alembic is the migration tool: versioned SQL scripts for schema changes
alembic==1.14.0

# --- Configuration & validation -----------------------------------------
# pydantic v2 validates request/response data and generates the OpenAPI schema
pydantic==2.10.3
# pydantic-settings loads .env files into typed Python settings objects
pydantic-settings==2.6.1
# email-validator makes Pydantic's EmailStr type actually work (unique emails)
email-validator==2.2.0

# --- Runtime helpers -----------------------------------------------------
# python-dotenv is used by pydantic-settings to read the .env file
python-dotenv==1.0.1

# --- Testing -------------------------------------------------------------
# pytest is the test runner (discovers files named test_*.py)
pytest==8.3.4
# pytest-asyncio lets pytest run `async def` test functions (our routes are async)
pytest-asyncio==0.24.0
# httpx provides AsyncClient: an in-process HTTP client that calls FastAPI
# directly without needing a live server or a real network socket
httpx==0.28.1
# aiosqlite lets the test suite run against an in-memory SQLite database,
# so tests never touch (or corrupt) your real PostgreSQL data
aiosqlite==0.20.0
# anyio is required by FastAPI/httpx for their async compatibility layers
anyio==4.7.0
```

**Why pin exact versions (`==`)?** Reproducibility: the code you run today and
the code your teammate runs must depend on identical library behaviour.
NOTE: pins may be upgraded later for security patches — a deliberate
maintenance decision, not an accident.

---

## 2. `backend/.env.example`

```ini
# ENVIRONMENT switches app behaviour: "development" enables Swagger UI at /docs
# and verbose error details; "production" hides them.
ENVIRONMENT=development

# DATABASE_URL is the single connection string SQLAlchemy parses to reach
# PostgreSQL. Format: <driver>+<dialect>://user:password@host:port/dbname
# NOTE: copy this file to `.env` and change the password before running.
DATABASE_URL=postgresql+asyncpg://taskflow_user:CHANGE_ME_strong_password@localhost:5432/taskflow

# CORS_ORIGINS is a JSON list of browser origins allowed to call the API.
# Vite's dev server runs on 5173 — without this entry the browser would
# block every fetch with a CORS error.
CORS_ORIGINS=["http://localhost:5173"]

# APP_PREFIX puts every API route under /api/v1 so a future v2 can coexist.
APP_PREFIX=/api/v1

# MAX_IMPORT_BYTES caps uploaded import files at 2 MB (413 above it).
MAX_IMPORT_BYTES=2097152

# Optional AI credentials stay on the backend. Provider fallback order is
# OpenRouter, then Gemini, then Groq. Model names can be overridden separately.
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
```

`.env` (git-ignored) holds the **real** values; `.env.example` (committed) is
the safe template. **SECURITY:** never commit real passwords.

---

## 3. `backend/alembic.ini`

```ini
# Where Alembic writes its script files (one .py per schema change)
script_location = alembic

# Absolute path to the same folder — prevents errors when running alembic
# from a different working directory
prepend_sys_path = .

# The SQLAlchemy URL is supplied by alembic/env.py (which reads .env) rather
# than here, so no password ever appears in a committed file
# sqlalchemy.url =

# Section name expected by alembic when it logs — plain logging config
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

# --- standard logging wiring (verbosity for migration output) ------------
[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**Why is `sqlalchemy.url` empty?** Because `alembic/env.py` (Phase 2) loads it
from `config.py` at runtime — one source of truth (`DATABASE_URL`), zero
duplicated secrets.

---

## 4. `frontend/package.json`

```jsonc
{
  // Unique project name — must be lowercase, no spaces (npm registry rules)
  "name": "taskflow-frontend",
  // Semantic version: MAJOR.MINOR.PATCH. 0.x = API may still change.
  "version": "0.1.0",
  // type:module => Node treats .js files as ES modules (import/export syntax)
  "type": "module",

  "scripts": {
    // `npm run dev` starts the Vite dev server with hot reload (port 5173)
    "dev": "vite",
    // `npm run build` type-checks (tsc -b) then bundles production assets to dist/
    "build": "tsc -b && vite build",
    // `npm run preview` serves the built dist/ folder locally for a smoke test
    "preview": "vite preview",
    // `npm run lint` checks for common JS/TS mistakes without compiling
    "lint": "eslint ."
  },

  "dependencies": {
    // React core + the DOM renderer (React 18 removed ReactDOM.render)
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    // React Router: declarative client-side routes (/admin/*, /*)
    "react-router-dom": "^6.28.0",
    // TanStack Query: server-state cache, retries, optimistic updates
    "@tanstack/react-query": "^5.62.7",
    // Framer Motion: layout animations, springs, AnimatePresence enter/exit
    "framer-motion": "^11.15.0",
    // Lucide React: the icon set (icons are tree-shaken per import)
    "lucide-react": "^0.468.0",
    // @dnd-kit: accessible drag-and-drop (keyboard support included)
    "@dnd-kit/core": "^6.3.1",
    "@dnd-kit/sortable": "^9.0.0",
    "@dnd-kit/utilities": "^3.2.2",
    // sonner: tiny toast library (showing "Undo" on delete, error messages)
    "sonner": "^1.7.1",
    // papaparse: fast CSV parsing for the import preview step (browser-side)
    "papaparse": "^5.4.1"
  },

  "devDependencies": {
    // Typescript compiler — dev-only, the browser never receives it
    "typescript": "~5.6.2",
    // Vite: dev server + bundler; the React plugin adds Fast Refresh
    "vite": "^6.0.1",
    "@vitejs/plugin-react": "^4.3.4",
    // Tailwind v3 pipeline: postcss runs tailwindcss + autoprefixer
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20",
    // Types for papaparse calls (papaparse ships no built-in types)
    "@types/papaparse": "^5.3.15"
  }
}
```

**Reading a caret range (`^5.62.7`):** any version `>=5.62.7 <6.0.0` is
accepted — bug-fix and feature updates apply, breaking major versions do not.

---

## 5. `frontend/tsconfig.json` & `tsconfig.node.json`

```jsonc
// tsconfig.json — rules for the application source code (src/)
{
  "compilerOptions": {
    "target": "ES2020",                  // emit modern JS (optional chaining, etc.)
    "useDefineForClassFields": true,     // class fields use ES semantics (React fast-refresh needs this)
    "lib": ["ES2020", "DOM", "DOM.Iterable"], // allowed built-ins: language + browser APIs
    "module": "ESNext",                  // use import/export syntax
    "moduleResolution": "bundler",       // resolve imports the way Vite/bundlers do
    "skipLibCheck": true,                // don't type-check node_modules' .d.ts (faster builds)
    "resolveJsonModule": true,           // allow `import data from './x.json'`
    "isolatedModules": true,             // each file compiles alone (required for esbuild)
    "noEmit": true,                      // type-check only — Vite does the actual transpiling

    "strict": true,                      // ALL strict checks: the core safety guarantee
    "noUnusedLocals": true,              // error on unused variables (catches dead code)
    "noUnusedParameters": true,          // error on unused function parameters
    "noFallthroughCasesInSwitch": true   // error on missing `break` in switch

    // NOTE: "jsx": "react-jsx" and "baseUrl" paths are added when the
    // frontend files are created in Phase 5 — kept out of this excerpt only
    // to keep the explanation focused; the real file includes them.
  },
  "include": ["src"]                    // apply these rules to src/ only
}

// tsconfig.node.json — rules for vite.config.ts only (it runs in Node, not the browser)
{
  "compilerOptions": {
    "composite": true,        // allow this config to be referenced by `tsc -b`
    "module": "ESNext",       // Vite config files use ESM
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true  // allow importing ".ts" extensions
  },
  "include": ["vite.config.ts"]          // scope: the Vite config file only
}
```

**Why two tsconfigs?** `vite.config.ts` runs in Node with Node APIs, while
`src/*` runs in the browser — mixing the two `lib` sets would allow browser
code to use Node-only modules (or vice versa) without noticing.

**NOTE:** sections 4 and 5 show comments (`//`) for teaching purposes. The
real `package.json` / `tsconfig.json` files are **strict JSON and contain no
comments** — this document is their commenting layer, exactly as the spec
requires.

---

## 6. `frontend/vite.config.ts`

```ts
// Import the React plugin: enables JSX transform + Fast Refresh (state kept
// across edits without a full page reload)
import react from '@vitejs/plugin-react';

// Import Node's path helpers so aliases work on every operating system
import path from 'path';

// Import Vite's defineConfig helper: gives autocompletion and type-safety
import { defineConfig } from 'vite';

// The exported object configures the dev server and the production build
export default defineConfig({
  // Plugins are build-time transformers; only React is needed here
  plugins: [react()],

  resolve: {
    alias: {
      // `@/...` in import statements now means `src/...` — short, unambiguous
      // paths instead of fragile '../../..' chains
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173, // Vite's conventional dev port; matches CORS_ORIGINS
    proxy: {
      // Anything requested from /api is forwarded to FastAPI during development.
      // Benefit: the browser sees same-origin requests, so CORS issues
      // disappear locally while the code stays identical to production.
      '/api': {
        target: 'http://localhost:8000', // FastAPI + uvicorn listen here
        changeOrigin: true,              // rewrite the Host header to the target
      },
    },
  },
});
```

---

## 7. `frontend/tailwind.config.js` and `postcss.config.js`

```js
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  // Scan these files for class names; only found classes are generated
  // (that's the "JIT" — just-in-time — engine, which enables arbitrary values)
  content: ['./index.html', './src/**/*.{ts,tsx}'],

  darkMode: 'class', // dark mode is toggled by adding `class="dark"` on <html>

  theme: {
    extend: {
      // Custom glass/aurora colours not present in Tailwind's default palette
      colors: {
        aurora: {
          500: '#6366f1', // indigo glow used in gradient meshes
          700: '#4338ca',
        },
      },
      // Reusable animation keyframes: card entrance, subtle float, shimmer
      keyframes: {
        shimmer: {                       // skeleton loading sweep
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        float: {                         // background blob drift
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.6s infinite', // pair each keyframe with a duration
        float: 'float 12s ease-in-out infinite',
      },
    },
  },

  // No third-party plugins: everything the UI needs is done with core
  // Tailwind classes + Framer Motion, keeping the bundle small
  plugins: [],
};

// postcss.config.js — wires Tailwind into the CSS build pipeline.
// Vite processes .css files with PostCSS; without this file,
// `@tailwind` directives would stay unresolved and styles would vanish.
export default {
  plugins: {
    tailwindcss: {},   // expands @tailwind directives into real CSS rules
    autoprefixer: {},  // adds -webkit/-moz prefixes for older browsers
  },
};
```

---

## 8. `frontend/.env.example` and `index.html`

```ini
# frontend/.env.example — copy to .env if you need to change the API location.
# VITE_ prefix is MANDATORY: Vite only exposes env vars starting with VITE_
# to browser code (anything else stays server-side secret).
VITE_API_BASE_URL=http://localhost:8000
# NOTE: in dev the api/client uses the '/api' proxy, so this value is only
# required for builds that talk to a remote API.
```

```html
<!-- index.html — the ONLY HTML file; Vite injects the bundled JS here -->
<div id="root"></div>  <!-- React mounts the whole app into this empty node -->
<script type="module" src="/src/main.tsx"></script>  <!-- entry point -->
```

---



