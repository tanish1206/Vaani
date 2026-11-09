import sys
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

print("Step B: Importing VoicePipeline...", flush=True)
t0 = time.time()
from app.core.pipeline import VoicePipeline
print(f"Step B Done in {time.time()-t0:.2f}s", flush=True)

async def main():
    print("Step C: Inside main, calling run_turn...", flush=True)
    t0 = time.time()
    res = await VoicePipeline.run_turn(
        transcript="Ramesh ko 200 udhaar likh de",
        session_id="eval-session",
        lang_hint="auto",
        dry_run=True
    )
    print(f"Step C Done in {time.time()-t0:.2f}s", flush=True)
    print("Step D: Result:", res["actions"], res["reply_text"], flush=True)

if __name__ == "__main__":
    print("Step E: Starting asyncio.run...", flush=True)
    asyncio.run(main())
    print("Step F: All finished!", flush=True)
