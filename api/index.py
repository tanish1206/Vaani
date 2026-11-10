"""
VAANI — Standard Vercel Serverless Function Entrypoint (api/index.py).
Exports the FastAPI 'app' instance for seamless Vercel runtime discovery.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure backend directory is in sys.path
backend_dir = BASE_DIR / "backend"
if backend_dir.exists() and str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import the configured FastAPI app instance
from main import app

