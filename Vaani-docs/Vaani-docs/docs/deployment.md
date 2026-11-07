# Munimji — Setup and Deployment

## 1. Environments

| Env | Where | Purpose |
|---|---|---|
| **dev** | Your laptop | Daily work. Gnani APIs live; Evon remote or hosted |
| **demo** | Your laptop (recording device) + Evon endpoint | The take you record; clean seeded DB |
| **public (optional)** | A small VM or PaaS | Judges can click a link. Needs auth and a working Evon endpoint (or the clearly labelled fallback) |

## 2. Prerequisites

- Python 3.11, `pip`, `venv`
- `ffmpeg` on PATH (`ffmpeg -version`)
  - Windows: `winget install Gyan.FFmpeg` (or download from ffmpeg.org)
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
- A Gnani API key (dashboard: `app.gnani.ai/voice`)
- A way to run Evon (§4)
- Chrome or Edge for development (MediaRecorder and microphone support; microphone needs **HTTPS or `localhost`**)

## 3. Local setup

```bash
git clone <your-repo-url> munimji && cd munimji
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env               # Windows: copy .env.example .env  → edit values
python scripts/seed_demo.py        # creates data/munimji.db with demo customers
uvicorn app.main:app --reload --port 8000 --app-dir backend
```

Open `http://localhost:8000`. Health check: `http://localhost:8000/api/v1/health`.

### Environment variables (`.env`)

| Variable | Example | Notes |
|---|---|---|
| `GNANI_API_KEY` | `…` | Sent as `X-API-Key-ID` |
| `GNANI_BASE_URL` | `https://api.vachana.ai` | |
| `STT_MODEL` | `prisma-v3.0` | Set empty to use default v2.5 and send `language_code` |
| `STT_DEFAULT_LANGUAGE` | `hi-IN` | Used when `STT_MODEL` is v2.5 or `lang_hint` forces a language |
| `TTS_MODEL` | `<Timbre v2.5 model string>` | From the TTS REST page |
| `TTS_VOICE_HI` / `TTS_VOICE_MR` / `TTS_VOICE_EN` | `sia` / `…` / `…` | From Available Voices |
| `EVON_BASE_URL` | `http://localhost:8001` | OpenAI-compatible root |
| `EVON_MODEL` | `gnani/gnani-evon-v3.3-30B-A3B` | |
| `EVON_API_KEY` | `…` | Optional, if you protect the endpoint |
| `EVON_ENABLED` | `true` | `false` forces the rules parser |
| `MARKET_SOURCE` | `yfinance` | or `sample` |
| `DB_PATH` | `data/munimji.db` | |
| `AUDIO_TTL_MIN` | `30` | Generated audio retention |
| `DEBUG` | `true` | Enables `/utterances` and dev panel |
| `CORS_ORIGINS` | `http://localhost:8000` | Lock down in public deploys |

## 4. Running Evon

**Decide within the first hour.** Order of preference:

### A. Hosted access
Check the challenge dashboard, Discord or email for provided inference access. If it exists, set `EVON_BASE_URL` and you are done.

### B. vLLM on a rented GPU
Hugging Face shows no inference provider for the model, so you host it yourself.

Memory guide: the model has ~30B parameters in total (mixture-of-experts, ~3B active per token), but **all weights must be loaded**. In BF16 that is roughly 60 GB for weights alone, so plan for an 80 GB-class GPU. A 4-bit quantised build needs roughly a quarter of that and can fit a 24 GB-class GPU — check the model's "Quantizations" link on Hugging Face and confirm the architecture (`nemotron_h`) is supported by your serving stack.

```bash
# On the GPU machine
python -m venv evon && source evon/bin/activate
pip install -U vllm huggingface_hub
huggingface-cli download gnani/gnani-evon-v3.3-30B-A3B     # start this EARLY: large download
vllm serve gnani/gnani-evon-v3.3-30B-A3B \
  --trust-remote-code \
  --max-model-len 8192 \
  --port 8001 \
  --api-key "$EVON_API_KEY"
```

> **VERIFY** flags and the minimum vLLM version on the model card; hybrid Mamba/Transformer ("nemotron_h") models often need a recent release.

Connect safely:

```bash
# From your laptop: SSH tunnel instead of exposing the port publicly
ssh -N -L 8001:localhost:8001 user@gpu-host
```

Then `EVON_BASE_URL=http://localhost:8001`.

Smoke test:

```bash
curl http://localhost:8001/v1/models -H "Authorization: Bearer $EVON_API_KEY"
```

### C. Quantised / smaller-GPU path
Use the quantised model linked from the Hugging Face model tree, serving with the stack that quantisation targets. Re-run the 40-utterance eval — accuracy must not drop below the bar.

### D. Rules-parser fallback
Set `EVON_ENABLED=false`. The app still works for Khata basics. Say so honestly if you demo this way.

### Cost control
- Provision GPU only for test sessions and the final recording. Stop the instance when idle.
- Record **all demo takes in one GPU session**.
- Keep the final submission independent of a running GPU: include the video, repo and README; a live link is a bonus.

## 5. Production-style run (optional public demo)

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 --chdir backend
```

Put it behind HTTPS (Caddy, Nginx, or the host's TLS). Microphone access **requires HTTPS** off localhost.

Minimal Dockerfile:

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY frontend ./frontend
COPY scripts ./scripts
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]
```

Public-deploy hardening: set a bearer token (`API_TOKEN`), restrict CORS, disable `/utterances`, rate-limit `/voice/turn` (e.g. 30/min per IP), and show a "demo data" banner.

## 6. Operations

| Task | How |
|---|---|
| Health | `GET /api/v1/health` (cheap checks, cached 30 s) |
| Logs | Structured JSON to stdout; one line per turn with `turn_id`, stage timings, status |
| Reset demo data | `python scripts/seed_demo.py --reset` |
| Backup | Copy `data/munimji.db` before every recording |
| Audio cleanup | Background task deletes files older than `AUDIO_TTL_MIN` |
| Key rotation | Replace `GNANI_API_KEY` in `.env`, restart |

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Mic button does nothing | Not on HTTPS/localhost, or permission blocked | Use `localhost`; reset site permissions |
| STT returns 401 | Wrong key or header name | Header must be `X-API-Key-ID` |
| STT returns empty transcript | Silence, wrong sample rate, too short | Check converted WAV (16 kHz mono); play it back |
| TTS audio won't play | Raw PCM returned without a WAV header | Wrap in WAV (`wave` module) |
| Digits or ₹ read oddly | TTS normalisation | Convert numbers to words in templates; test SSML pauses |
| Evon outputs prose / `<think>` | Reasoning mode on | Disable via the chat template or strip blocks; lower temperature |
| Evon too slow | Cold start or CPU offload | Warm-up call at startup; check GPU memory; shorten prompt |
| Market data fails | Unofficial source rate-limited | Cache for 5 min; switch to `sample` with the badge |
| SQLite "database is locked" | Concurrent writers | WAL on; keep writes short; one worker for the demo |
