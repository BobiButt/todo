"""Vercel serverless entry point for the TaskFlow FastAPI backend."""

from app.main import app

# Vercel's Python runtime looks for `app` (the ASGI application) in api/index.py.
handler = app
