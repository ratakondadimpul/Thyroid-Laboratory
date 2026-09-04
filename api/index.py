"""
Vercel serverless entry for Thyroid Lab API (monorepo root).
Import the FastAPI app from backend/app/main.py
"""
import sys
from pathlib import Path

# Add backend to path when deployed as monorepo (root = AI-Powered Thyroid)
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app  # noqa: E402

# Vercel expects `app` variable
__all__ = ["app"]
