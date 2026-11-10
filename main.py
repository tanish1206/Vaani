"""
VAANI — Root Entrypoint forwarding to Vaani backend.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
vaani_dir = BASE_DIR / "Vaani"

if (vaani_dir / "backend").exists():
    if str(vaani_dir / "backend") not in sys.path:
        sys.path.insert(0, str(vaani_dir / "backend"))
    if str(vaani_dir) not in sys.path:
        sys.path.insert(0, str(vaani_dir))
elif (BASE_DIR / "backend").exists():
    if str(BASE_DIR / "backend") not in sys.path:
        sys.path.insert(0, str(BASE_DIR / "backend"))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
