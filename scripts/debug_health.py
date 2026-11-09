import sys
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

print("[1] Importing app.config...")
t0 = time.time()
from app.config import settings
print(f"    Done in {time.time()-t0:.2f}s")

print("[2] Importing app.db.session...")
t0 = time.time()
from app.db.session import init_db, get_db
print(f"    Done in {time.time()-t0:.2f}s")

print("[3] Calling init_db()...")
t0 = time.time()
init_db()
print(f"    Done in {time.time()-t0:.2f}s")

print("[4] Importing routers...")
t0 = time.time()
from app.api import text, voice, khata, parchi, bazaar, settings as settings_api
print(f"    Done in {time.time()-t0:.2f}s")

print("[5] Importing FastAPI and creating app...")
t0 = time.time()
from app.main import app
print(f"    Done in {time.time()-t0:.2f}s")

print("[6] Running health_check function directly...")
import asyncio
from app.main import health_check
t0 = time.time()
res = asyncio.run(health_check())
print(f"    Done in {time.time()-t0:.2f}s")
print("    Result:", res)
