"""
VAANI — Vercel & Production ASGI Entrypoint.
Exports the FastAPI 'app' instance for Vercel Serverless Functions,
uvicorn, gunicorn, and local development.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so 'app.*' imports resolve cleanly
ROOT_DIR = Path(__file__).resolve().parent
backend_dir = ROOT_DIR / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import the FastAPI application instance
from app.main import app

# For local direct running: python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
