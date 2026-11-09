# VAANI · वाणी

> *Boliye. Vaani Sambhal Legi.*  
> A multilingual, voice-first AI assistant for Indian shopkeepers, small businesses, and families: **digital business ledger (Bol-Khata)**, **medicine reminders (Parchi)**, and a **plain-language market briefing (Sensex Awaaz)** — in Hindi, Marathi, English, and code-mixed speech (Hinglish).

Built for the Gnani **Great Indian AI Internship Challenge** on Gnani's sovereign Indian foundation models:

| Stage | Model | Role |
|---|---|---|
| **Speech-to-Text** | **Prisma v3.0** | Multilingual automatic language detection & speech transcription |
| **Reasoning & Tool Extraction** | **Evon v3.3 (30B-A3B)** | Strict structured JSON action extraction |
| **Text-to-Speech** | **Timbre v2.5** | High-fidelity Indian voice synthesis in Hindi, Marathi, and English |

---

## Architecture & Data Flow

```
Shopkeeper Voice (WAV 16kHz)
  ↓
Prisma v3.0 (STT) → Transcript + Language Detection
  ↓
Evon v3.3 (Reasoning) → Strict JSON Intent Contract
  ↓
Python Guardrails → Amount Limits, Strict Verbatim Check, Medical/Financial Refusal
  ↓
Local SQLite WAL (vaani.db) → Integer Paise Precision, Append-Only Audit Trail
  ↓
Template Phrasing & Timbre v2.5 (TTS) → Spoken Natural Voice + Live UI Result Cards
```

> **Key Architectural Invariant:** Python validates, calculates, and writes the database. The language model only understands. The LLM never touches financial records directly and never computes balances.

---

## Quick Start

### 1. Requirements
- Python 3.10+
- Modern Web Browser (Chrome, Edge) supporting Web Audio & MediaRecorder

### 2. Run Development Server
```bash
python scripts/run_dev.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

### 3. Run Test Suite
```bash
$env:PYTHONPATH="backend"; python scripts/test_landing_server.py
```

---

## Three Core Modules

1. **Bol-Khata (बोल-खाता):** Digital business ledger. Handles credit (*udhaar*) and payment (*jama*) transactions with fuzzy customer matching (e.g., "रमेश" / "Ramesh"), integer paise math (never float drift), and an 8-second voice undo snackbar.
2. **Parchi (पर्ची):** Medicine reminders. Verbatim dosage recording without alteration, smart meal-slot scheduling (*subah, shaam, dopahar, khaane ke baad*), and automatic refusal of medical advice.
3. **Sensex Awaaz (सेंसेक्स आवाज़):** Spoken market overview. Plain-language summaries of BSE Sensex, Nifty 50, and watchlists with honest data freshness badges, and automatic refusal of investment recommendations.

---

## Multi-Page Product Architecture

VAANI features a dedicated multi-page workspace architecture:

| URL Route | Workspace | Description |
|---|---|---|
| `/` | **Landing Page** | Editorial landing page matching the visual direction with botanical orchid, golden audio waveforms, layered cards, and interactive voice demo |
| `/app` | **Overview Hub** | Central entry point showing quick balance statistics, meal slot timeline, live Sensex ticker, and global conversational agent |
| `/app/bol-khata` | **Bol-Khata** | Dedicated digital business ledger with customer search, customer drawer, add credit / record payment forms, WhatsApp reminder copy, and contextual voice agent |
| `/app/parchi` | **Parchi** | Dedicated medicine reminder workspace with meal-slot schedule (*subah, dopahar, shaam, raat*), "Mark Done", "Snooze 10m", add prescription dialog, and contextual voice agent |
| `/app/sensex-awaaz` | **Sensex Awaaz** | Dedicated market workspace with live Sensex & Nifty tiles, candlestick movement spectrum, personal watchlist, spoken market briefings, honest freshness tags, and contextual voice agent |
| `/app/settings` | **Settings & Diagnostics** | Shopkeeper preferences & evaluator AI readiness diagnostics (Prisma STT, Evon LLM, Timbre TTS, Market Provider, database health, masked credentials, demo reset) |

---

## Verification & Testing Suite

Run the automated verification test suites:

```bash
# 1. 40-Utterance Conversational Benchmark (100% Pass)
python scripts/eval_utterances.py

# 2. Phase 1 Server & Asset Integration Tests (100% Pass)
python scripts/test_landing_server.py

# 3. Phase 2 Multi-Page & API Readiness Test Suite (100% Pass)
python scripts/test_phase2_multi_page.py
```

---

## Configuration & Secret Safety

Copy `.env.example` to `.env` to configure live credentials:

```bash
# Production vs Demo Mode
DEMO_MODE=true                # Set to false for clean database with zero sample fixtures

# Gnani Sovereign AI Credentials (Server-Side Only)
GNANI_API_KEY=gnan_live_...   # Unified API key for Prisma, Evon, and Timbre
EVON_ENABLED=true             # Set to true when Evon LLM endpoint is active
EVON_API_KEY=gnan_live_...

# Market Provider
MARKET_PROVIDER=yahoo_finance # Real-time quotes via yfinance with 5-minute cache
```

> **Security Guarantee:** Credentials are strictly server-side. Diagnostics endpoints return masked strings (`gnan_****` or `Not Configured`). Secret keys are never leaked to client browsers.

---

## Repository Structure

```
backend/
  app/
    main.py              # FastAPI application, explicit HTML multi-page routes & static mount
    config.py            # Pydantic Settings with masked credentials and readiness checks
    api/
      khata.py           # /api/v1/khata endpoints (customers, transactions, undo)
      parchi.py          # /api/v1/parchi endpoints (prescriptions, doses, mark done, snooze)
      bazaar.py          # /api/v1/bazaar endpoints (overview, snapshot, spoken briefing)
      settings.py        # /api/v1/settings endpoints (preferences, diagnostics, latency ping, reset)
    modules/
      khata/             # Ledger logic with integer paise arithmetic and 8s undo
      parchi/            # Meal-slot scheduling, verbatim recording, and refusal guards
      bazaar/            # Safe yfinance market feeds with socket timeout guards & 5m cache
    core/
      pipeline.py        # Voice pipeline orchestrator (Prisma STT -> Evon -> Guardrails -> SQLite -> Timbre TTS)
      session.py         # Multi-turn conversational session state and undo stack
    db/
      session.py         # SQLite connection manager with WAL mode & foreign keys
      seed.py            # Sample demo fixtures & reset_demo_data()
frontend/
  index.html             # Editorial landing page matching design reference
  app/
    overview.html        # /app central gateway & module overview
    bol-khata.html       # /app/bol-khata dedicated ledger workspace
    parchi.html          # /app/parchi dedicated medicine reminder workspace
    sensex-awaaz.html    # /app/sensex-awaaz dedicated market intelligence workspace
    settings.html        # /app/settings shopkeeper preferences & diagnostics
  styles/
    tokens.css           # Design tokens (Ice Silver, Deep Aubergine, Marigold)
    landing.css          # Editorial layout, typography, grid, responsive styles
    app-shell.css        # Multi-page shell, topbar navigation, cards, drawers, forms
    agent-component.css  # Voice mic, speech wave, action confirmation bubbles
  js/
    agent-component.js   # Reusable conversational agent with Web Audio MediaRecorder
    bol-khata-page.js    # Ledger client-side controller & modal handlers
    parchi-page.js       # Medicine reminders controller & timeline handlers
    sensex-page.js       # Market overview controller & audio player
    settings-page.js     # Settings controller & live latency diagnostics runner
  assets/
    botanical-artwork.svg # High-fidelity botanical orchid with integrated audio waveforms
    mandala.svg          # Ornate golden Indian mandala medallion
data/
  vaani.db               # Local SQLite database in WAL mode (git-ignored)
scripts/
  run_dev.py             # Development server launcher
  eval_utterances.py     # 40-utterance benchmark test suite
  test_landing_server.py # Phase 1 integration tests
  test_phase2_multi_page.py # Phase 2 multi-page verification suite
```

---

## Design System

- **Palette:**
  - Warm Ivory (`#F8F6F0`) & Ice Silver (`#DDE3E8`)
  - Deep Aubergine ink (`#3A0F34`)
  - Marigold accent (`#EAAA00`) & Flame Amber (`#F58220`)
- **Typography:**
  - Display: *Fraunces* (Latin) & *Noto Serif Devanagari*
  - Body: *Noto Sans* & *Noto Sans Devanagari*
- **Visual Language:**
  - Architectural grid lines with meter coordinates (`TIME MET&DATE`, `SUBTLE METADATS`, `I FINE`)
  - Asymmetric editorial composition with botanical flower and horizontal audio frequency spectrum
  - Layered product mockups (central phone, Bahi-Khata ledger, Parchi slip, Sensex graph)

---

## Privacy & Safety

Audio and spoken responses are processed through Gnani's sovereign Indian speech infrastructure. All business records, customer balances, and prescriptions are stored locally in SQLite (`vaani.db`). Data is never monetized or sold to third parties.

