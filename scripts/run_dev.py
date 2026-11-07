"""
Development server runner for VAANI.
Usage:
    python scripts/run_dev.py
"""

import sys
import os
from pathlib import Path

# Add backend directory to PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  VAANI — Boliye. Vaani Sambhal Legi.")
    print("  Starting development server on http://localhost:8000")
    print("=" * 60)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, app_dir=str(backend_dir))

