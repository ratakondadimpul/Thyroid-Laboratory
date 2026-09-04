"""
Vercel serverless entry when backend is deployed as separate Vercel project
(rootDirectory = backend)
"""
from app.main import app

__all__ = ["app"]
