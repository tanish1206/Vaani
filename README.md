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

## Repository Structure

```
backend/
  app/
    main.py              # FastAPI application & endpoints
    config.py            # Environment settings (Pydantic Settings)
frontend/
  index.html             # Editorial landing page matching design reference
  styles/
    tokens.css           # Design tokens (Ice Silver, Deep Aubergine, Marigold)
    landing.css          # Editorial layout, typography, grid, responsive styles
    components.css       # Bahi-Khata ledger, Parchi slip, Sensex chart, mic visualizer
  js/
    landing.js           # Navigation, multilingual translation, night mode, FAQ
    voice-simulator.js   # Voice lifecycle state machine & 40-utterance benchmark runner
    audio-visualizer.js  # Reactive golden waveform canvas
  assets/
    botanical-artwork.svg # High-fidelity botanical orchid with integrated audio waveforms
    mandala.svg          # Ornate golden Indian mandala medallion
data/
  vaani.db               # Local SQLite database (git-ignored)
scripts/
  run_dev.py             # Development server launcher
  test_landing_server.py # Test script for API & static asset delivery
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

