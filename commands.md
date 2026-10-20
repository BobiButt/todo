# TaskFlow — Run Commands

All commands are run from the project root: `/home/bobi/Desktop/Python projects hccda/todo`

## 0. Prerequisites

- PostgreSQL installed and running (Fedora: `sudo systemctl enable --now postgresql`)
- Database `taskflow` and role `taskflow_user` created (see `docs/POSTGRES_SETUP.md`)
- Python 3.12+ with `venv`
- Node.js + npm

---

## 1. Backend (one terminal)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env
# Edit backend/.env and add your AI provider keys (OpenRouter / Gemini / Groq)
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

Backend API: `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

---

## 2. Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend app: `http://localhost:5173`

---

## 3. One-click scripts

| Platform | File | How to run |
|----------|------|------------|
| Linux / macOS | `run-linux.sh` | `chmod +x run-linux.sh && ./run-linux.sh` |
| Windows | `run-windows.bat` | Double-click or run `run-windows.bat` |

Both scripts start PostgreSQL, the backend, the frontend, and open `http://localhost:5173` in your default browser.
- Linux/macOS: `chmod +x run-linux.sh && ./run-linux.sh`
- Windows: double-click `run-windows.bat`

> **Important:** Before running, edit `backend/.env` and paste your real AI provider keys (OpenRouter / Gemini / Groq). Replace `your-groq-api-key-here` with your actual Groq key.

---

## 4. Tests (backend)

```bash
cd backend
source .venv/bin/activate
pytest
```

---

## 5. Useful shortcuts

| Task | Command |
|------|---------|
| Apply database migrations | `cd backend && alembic upgrade head` |
| Re-seed demo data | `cd backend && python seed.py` |
| Backend health check | `curl http://localhost:8000/health` |
| Stop backend | `Ctrl+C` in the uvicorn terminal |
| Stop frontend | `Ctrl+C` in the Vite terminal |
