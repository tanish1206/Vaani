# VAANI · वाणी

> ***Boliye. Vaani Sambhal Legi.***  
> A multilingual, voice-first AI assistant for Indian shopkeepers, small businesses, and families: **digital business ledger (Bol-Khata)**, **medicine reminders (Parchi)**, and a **plain-language market briefing (Sensex Awaaz)** — in Hindi, Marathi, English, and code-mixed speech (Hinglish).

Built for the **Gnani Great Indian AI Internship Challenge** around Gnani's sovereign Indian foundation models:

| Stage | Model / Engine | Role |
|---|---|---|
| **Speech-to-Text (STT)** | **Gnani Prisma v3.0** | Multilingual REST & real-time WebSocket transcription with automatic Indic language detection |
| **Intent Reasoning** | **Gnani Evon v3.3 (30B-A3B)** + Deterministic Rules Engine | Strict structured JSON action extraction with offline deterministic fallback |
| **Text-to-Speech (TTS)** | **Gnani Timbre v3.0** (13 Pan-India voices) & **Timbre v2.5** (42 vernacular voices) | Expressive Indian voice synthesis across 10 Indian languages |

---

## Key Architectural Invariant

> **Python validates, calculates, and writes the database. The language model only understands.**  
> The LLM never touches financial records directly and never computes customer balances. All monetary calculations execute deterministically in integer **paise** inside Python and SQLite.

```
Shopkeeper Voice (Browser WebM/OGG/MP4/WAV)
  ↓  In-memory transcoding (PyAV → 16 kHz Mono 16-bit PCM WAV)
Gnani Prisma v3.0 (STT) → Transcript + Detected Language
  ↓
Gnani Evon v3.3 (or Deterministic Multilingual Rules Fallback) → Structured JSON Intent
  ↓
Python Guardrails → Name-Span Verification, Direction Cross-Check, ₹1L Cap, Medical/SEBI Refusal
  ↓
Local SQLite WAL (vaani.db) → Integer Paise Arithmetic & Append-Only Audit Trail
  ↓
Localized Reply Templates + Gnani Timbre v3.0 / v2.5 (TTS) → Spoken Audio + Live Workspace Cards
```

---

## Core Product Modules

1. **Bol-Khata (बोल-खाता) — Digital Business Ledger**
   - Records customer credit (*udhaar*) and payments (*jama*) via voice or manual forms, including compound multi-action utterances (e.g., *"Ramesh ko 200 udhaar likh de aur Sunita ne 150 diye"*).
   - Fuzzy customer matching (`rapidfuzz`) normalizes honorifics and transliterated Devanagari/Latin names (e.g., `"रमेश"`, `"Ramesh"`, `"Ramesh ji"`).
   - Integer paise arithmetic (`to_paise` / `format_rupees`) prevents floating-point drift.
   - Append-only ledger with **8-second Voice Undo** (*"Galat ho gaya, hata do"*), entry correction (*"Nahi, 300 likh"*), top debtors, daily cashflow summaries, and WhatsApp reminder drafts.

2. **Parchi (पर्ची) — Family Medicine Reminders**
   - Stores patient labels, medicine names, and `dose_text` strictly verbatim from the user's transcript (strips any unverified or hallucinated dosages).
   - Maps Indian meal slots (*subah, dopahar, shaam, raat, khaane ke baad/pehle*) and explicit clock times to scheduled reminders.
   - Supports marking doses done (*"De di"*), snoozing (*"10 minute baad yaad dilana"*), and strictly refuses medical advice or dosage modifications while routing emergencies (`chest pain`, `saans`, etc.) to `108` / emergency care.

3. **Sensex Awaaz (सेंसेक्स आवाज़) — Plain-Language Market Briefing**
   - Summarizes BSE Sensex, Nifty 50, and personal stock watchlists in jargon-free Hindi/Hinglish.
   - Integrates Yahoo Finance (`yfinance`) with a 5-minute SQLite cache (`market_cache`), 2-second socket timeout protection, and honest freshness badges (`Live`, `Cached`, `Sample data`, or `Unavailable`).
   - Strictly refuses buy/sell recommendations or price targets.

---

## Multi-Page Application Routes

| Route | Workspace | Capabilities |
|---|---|---|
| `/` | **Landing Page** | Editorial design with scroll-driven botanical blossom hero, interactive Bol-Khata/Parchi/Sensex showcases, live Voice Lab inspector, multilingual switcher, and FAQ |
| `/app` | **Overview Hub** | Central summary metrics, workspace launcher cards, AI readiness status badges, and global conversational agent |
| `/app/bol-khata` | **Bol-Khata** | Customer ledger table, live search, customer entry history drawer, manual Credit/Payment modals, WhatsApp reminder copy, and contextual Khata agent |
| `/app/parchi` | **Parchi** | Today's dose timeline, active prescriptions summary, quick Mark Done / 10m Snooze controls, prescription modal, and contextual Parchi agent |
| `/app/sensex-awaaz` | **Sensex Awaaz** | BSE Sensex & Nifty 50 tiles, candlestick movement spectrum, spoken audio briefing player, personal watchlist table, and contextual Bazaar agent |
| `/app/settings` | **Settings & Diagnostics** | Two-model Gnani voice browser (55 voices across Timbre v3.0 & v2.5) with live ephemeral previews, shopkeeper thresholds, subsystem latency pings, and clean-slate DB reset |

---

## Quick Start

### 1. Prerequisites
- **Python 3.10+**
- Modern browser (Chrome, Edge, Firefox) with microphone / `MediaRecorder` support for live voice turns

### 2. Installation
```bash
git clone <your-repo-url>
cd Vaani
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment
Copy `.env.example` to `.env` inside `Vaani/` (or project root) and set your credentials:

```bash
cp .env.example .env
```

Key environment variables:
```ini
# Gnani Sovereign Speech APIs (Server-Side Only)
GNANI_API_KEY=your_gnani_api_key
GNANI_BASE_URL=https://api.vachana.ai
GNANI_STT_MODEL=prisma-v3.0
GNANI_TTS_MODEL=timbre-v3.0
GNANI_DEFAULT_VOICE=Shivani

# Optional Self-Hosted Evon v3.3 OpenAI-Compatible Endpoint
# When EVON_API_KEY is unset, VAANI automatically uses its deterministic rules parser
EVON_ENABLED=true
EVON_BASE_URL=http://localhost:8001
EVON_MODEL=gnani/gnani-evon-v3.3-30B-A3B
EVON_API_KEY=

# Market Data ("yfinance" | "dhan" | "sample")
MARKET_SOURCE=yfinance

# Application & Local Database
DB_PATH=data/vaani.db
DEMO_MODE=false
DEBUG=false
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

> **Security Guarantee:** API keys remain strictly server-side. Diagnostics endpoints (`/api/v1/health`, `/api/v1/settings/diagnostics`) only expose masked credentials (e.g., `vach****1760` or `Not Configured`) and never leak secrets or stack traces in production (`DEBUG=false`).

### 4. Run the Development Server
```bash
python scripts/run_dev.py
```
Open **[http://localhost:8000](http://localhost:8000)** for the landing page or **[http://localhost:8000/app](http://localhost:8000/app)** for the multi-page workspace.

---

## API Overview

Base path: `/api/v1`

| Group | Endpoints |
|---|---|
| **Turns** | `POST /api/v1/text/turn`, `POST /api/v1/voice/turn`, `WS /api/v1/voice/stream` |
| **Voice Engine** | `GET /api/v1/voice/health`, `GET /api/v1/voice/catalog`, `GET /api/v1/voice/options`, `POST /api/v1/voice/preview`, `POST /api/v1/voice/transcribe`, `POST /api/v1/voice/speak` |
| **Bol-Khata** | `GET /api/v1/khata/customers`, `GET /api/v1/khata/customer/{id}/entries`, `GET /api/v1/khata/summary`, `GET /api/v1/khata/debtors`, `POST /api/v1/khata/transaction`, `POST /api/v1/khata/undo` |
| **Parchi** | `GET /api/v1/parchi/doses`, `POST /api/v1/parchi/dose/{id}/done`, `POST /api/v1/parchi/done`, `POST /api/v1/parchi/snooze` |
| **Sensex Awaaz** | `GET /api/v1/bazaar/snapshot`, `GET /api/v1/bazaar/overview`, `GET /api/v1/bazaar/briefing`, `POST /api/v1/bazaar/watchlist` |
| **Settings & Health** | `GET /api/v1/health`, `GET/POST /api/v1/settings`, `GET/PUT /api/v1/settings/voice`, `GET /api/v1/settings/diagnostics`, `POST /api/v1/settings/test-connectivity`, `POST /api/v1/settings/reset-demo` |

---

## Verification & Test Suites

Run the automated test suites and benchmarks:

```bash
# 1. Unit, Guardrail, and Isolated API Regression Tests (pytest)
python -m pytest tests -v

# 2. 40-Utterance Multilingual Conversational Benchmark
python scripts/eval_utterances.py

# 3. Phase 2 Multi-Page & API Readiness Verification
python scripts/test_phase2_multi_page.py

# 4. Landing Page & Gnani Branding Verification
python scripts/test_phase2_frontend.py

# 5. Gnani Speech Integration, Catalogue & Zero-Demo-Data Verification
python scripts/test_gnani_speech_integration.py
```

---

## Deployment (Vercel Serverless)

`vercel.json` and ASGI entrypoints (`main.py`, `index.py`, `api/index.py`) are pre-configured for Vercel Python serverless deployment. When running on Vercel/AWS Lambda (`is_serverless()`), VAANI automatically copies any bundled `data/vaani.db` into the writable `/tmp/vaani.db` directory and adjusts SQLite journaling accordingly.

---

## Repository Structure

```text
Vaani/
├── api/index.py                 # Vercel serverless ASGI entrypoint
├── main.py / index.py           # Local & serverless FastAPI app re-exports
├── vercel.json                  # Vercel function bundling config
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata & Vercel entrypoint
├── .env.example                 # Environment configuration template
├── backend/app/
│   ├── main.py                  # FastAPI app, routes, health check, static serving
│   ├── config.py                # Pydantic v2 Settings & service readiness checks
│   ├── api/                     # REST & WebSocket routers (text, voice, khata, parchi, bazaar, settings)
│   ├── core/                    # Pipeline orchestrator, guardrails, i18n templates, session state
│   ├── db/                      # SQLite schema.sql, WAL session manager, seed/reset utilities
│   ├── gnani/                   # Evon v3.3 client + deterministic parser, Prisma/Timbre adapters
│   ├── modules/                 # Domain services (khata, parchi, bazaar)
│   └── services/
│       ├── gnani/               # Unified GnaniClient, ASR, TTS (REST+SSE), WebSocket relay, 55-voice catalog
│       └── voice/               # In-memory PyAV 16 kHz WAV transcoder & SQLite voice settings
├── frontend/
│   ├── index.html               # Editorial landing page
│   ├── app/                     # Dedicated pages (overview, bol-khata, parchi, sensex-awaaz, settings)
│   ├── js/                      # Controllers, reusable VaaniAgent, audio visualizer, blossom hero
│   ├── styles/                  # Design tokens, landing, app-shell, components, agent styles
│   └── assets/                  # Botanical & mandala SVGs, Gnani logos
├── scripts/                     # Dev launcher, DB inspection/cleanup, eval benchmark, integration tests
└── tests/                       # Pytest regression & isolated API unit tests
```

---

## Privacy & Safety

- **Zero Disk Audio Retention:** Microphone audio is validated and transcoded purely in memory (`io.BytesIO`) and discarded immediately after transcription.
- **Local-First Ledger:** Business records, balances, and prescriptions reside locally in SQLite (`vaani.db`) with foreign keys and WAL mode enabled.
- **Strict Domain Boundaries:** No LLM arithmetic, no medical advice or unverified dosages, and no stock buy/sell recommendations.
