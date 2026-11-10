"""
VAANI — Root Entrypoint forwarding to Vaani backend.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Ensure backend directory is in sys.path
backend_dir = BASE_DIR / "backend"
if backend_dir.exists() and str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Also support nested Vaani directory if present
nested_backend = BASE_DIR / "Vaani" / "backend"
if nested_backend.exists() and str(nested_backend) not in sys.path:
    sys.path.insert(0, str(nested_backend))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
