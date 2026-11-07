# Munimji — API Reference

Two parts:

1. **Gnani APIs** as Munimji consumes them (grounded in the docs and examples you shared; items marked **VERIFY** must be checked against the live docs page before relying on them).
2. **Munimji's own HTTP API** that the web UI calls.

---

## Part 1 — Gnani APIs

### 1.1 Basics

| Item | Value |
|---|---|
| Base URL | `https://api.vachana.ai` |
| Auth header | `X-API-Key-ID: <your_api_key>` on every request |
| Key source | Gnani API dashboard (`app.gnani.ai/voice`) |
| Failure on bad key | `401 Unauthorized` |
| Python SDK (optional) | `pip install gnani-vachana` (Python ≥ 3.9). Clients: `GnaniSTTClient`, `GnaniSTTStreamClient`, `GnaniTTSClient`, `GnaniTTSStreamClient`, `GnaniTTSRealtimeClient`. Reads `GNANI_API_KEY` if no key is passed |

Keep the key **server-side only**. The browser never sees it.

### 1.2 Speech-to-Text — Prisma

| Item | Value |
|---|---|
| Endpoint | `POST https://api.vachana.ai/stt/v3` |
| Content type | `multipart/form-data` |
| Audio field | `audio_file` (WAV, MP3, OGG, FLAC, AAC, M4A) |
| Language field | `language_code`, BCP-47 (e.g. `hi-IN`, `en-IN`). Marathi is expected to be `mr-IN` — **VERIFY** in the language table |
| Model | Default is Prisma v2.5. Prisma v3.0 is selected with `model=prisma-v3.0` and adds automatic language detection — **VERIFY** whether it is a form field or query parameter |
| Optional | `itn_native_numerals` (boolean, default `false`) — controls native-script numerals in the normalised text |
| Limits | The intro page says audio up to **30 s**. The REST page lists "≤ 60 s (ideal ≤ 30 s)". Design for ≤ 15 s and **cap recordings at 20 s** |
| Latency | P95 ≈ 200 ms for STT (vendor figure; expect higher end to end) |

**curl**

```bash
curl --request POST \
  --url https://api.vachana.ai/stt/v3 \
  --header 'X-API-Key-ID: '"$GNANI_API_KEY" \
  --form audio_file='@turn.wav' \
  --form language_code=hi-IN
```

For Munimji's default (code-mixed) mode, add the Prisma v3.0 model selector and leave language detection to the model:

```bash
curl --request POST \
  --url https://api.vachana.ai/stt/v3 \
  --header 'X-API-Key-ID: '"$GNANI_API_KEY" \
  --form audio_file='@turn.wav' \
  --form model=prisma-v3.0
```

**Response:** a JSON object containing a `transcript` field (the SDK exposes it as `result["transcript"]`). Log the full body once in your first run and pin the exact shape in `gnani/stt.py` — **VERIFY** fields such as detected language and confidence.

**Python (httpx) wrapper sketch**

```python
import httpx, os

STT_URL = "https://api.vachana.ai/stt/v3"

async def transcribe(wav_path: str, language_code: str | None = None,
                     model: str = "prisma-v3.0") -> dict:
    headers = {"X-API-Key-ID": os.environ["GNANI_API_KEY"]}
    data = {"model": model}
    if language_code:
        data["language_code"] = language_code
    async with httpx.AsyncClient(timeout=10) as client:
        with open(wav_path, "rb") as f:
            r = await client.post(STT_URL, headers=headers, data=data,
                                  files={"audio_file": ("turn.wav", f, "audio/wav")})
    r.raise_for_status()
    return r.json()
```

**SDK alternative**

```python
from gnani.stt import GnaniSTTClient
client = GnaniSTTClient()                       # uses GNANI_API_KEY
result = client.transcribe("turn.wav", language_code="hi-IN")
print(result["transcript"])
```

**Other STT modes (not used in MVP):** Realtime WebSocket `wss://api.vachana.ai/stt/v3` (live audio; sample rates 8000/16000/44100/48000 per the LiveKit plugin docs), and Batch STT for long files.

### 1.3 Text-to-Speech — Timbre

| Item | Value |
|---|---|
| Recommended model | **Timbre v2.5** (v2.0 deprecated) |
| REST | `POST https://api.vachana.ai/api/v1/tts/inference` — full audio in one binary response |
| Streaming (SSE) | `POST https://api.vachana.ai/api/v1/tts/sse` |
| Realtime | WebSocket `wss://api.vachana.ai/api/v1/tts` |
| Content type | `application/json` |
| Voice catalogue | "Available Voices" page. The quick-start example uses voice `sia` |
| SSML | Supported — useful for pauses between numbers |

**Request body (from the quick-start example)**

```json
{
  "text": "नमस्ते, आप कैसे हैं?",
  "voice": "sia",
  "model": "vachana-voice-v2",
  "audio_config": {
    "sample_rate": 44100,
    "num_channels": 1,
    "sample_width": 2,
    "encoding": "linear_pcm"
  }
}
```

> **VERIFY:** the quick-start shows `model: "vachana-voice-v2"`. The docs recommend Timbre v2.5, so look up the exact model string on the TTS REST page and use it. Also confirm the full `audio_config` options (container format, e.g. WAV vs raw PCM) and the Marathi voice name.

**curl**

```bash
curl -X POST https://api.vachana.ai/api/v1/tts/inference \
  -H 'Content-Type: application/json' \
  -H "X-API-Key-ID: $GNANI_API_KEY" \
  -d '{"text":"रमेश के खाते में दो सौ रुपये जोड़ दिए।","voice":"sia","model":"<timbre-v2.5-model-string>",
       "audio_config":{"sample_rate":44100,"num_channels":1,"sample_width":2,"encoding":"linear_pcm"}}' \
  --output reply.wav
```

**Python wrapper sketch**

```python
async def synthesize(text: str, voice: str, model: str) -> bytes:
    body = {"text": text, "voice": voice, "model": model,
            "audio_config": {"sample_rate": 44100, "num_channels": 1,
                             "sample_width": 2, "encoding": "linear_pcm"}}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post("https://api.vachana.ai/api/v1/tts/inference",
                              headers={"X-API-Key-ID": os.environ["GNANI_API_KEY"]},
                              json=body)
    r.raise_for_status()
    return r.content   # if raw PCM, wrap in a WAV header before sending to the browser
```

If the response is raw PCM, wrap it in a WAV header (Python `wave` module) so browsers can play it. The SDK's `synthesize()` returns valid WAV for streaming, which is a useful reference.

### 1.4 Voice cloning (stretch only)

| Step | Endpoint |
|---|---|
| Create embedding | `POST /api/v1/tts/voice-clone/embeddings` (multipart `audio_file`; WAV/MP3, ideally 5–30 s clear speech) |
| Synthesize | `POST /api/v1/tts/inference` with `model: "vachana-vc-v1"` and `speaker_embedding` |

Not part of the MVP. Requires explicit consent from the voice owner.

### 1.5 Evon (reasoning model)

Evon is **not** a Gnani REST API; it is an open-weights model (Apache-2.0) on Hugging Face: `gnani/gnani-evon-v3.3-30B-A3B` (mixture-of-experts, 32B parameters total, tool-calling and 11-language support per the model card tags). Serve it yourself (see `deployment.md`) and call it through an OpenAI-compatible endpoint.

```http
POST {EVON_BASE_URL}/v1/chat/completions
Content-Type: application/json

{
  "model": "gnani/gnani-evon-v3.3-30B-A3B",
  "messages": [
    {"role": "system", "content": "<system prompt from evon-prompts.md>"},
    {"role": "user", "content": "Ramesh ko 200 udhaar likh de"}
  ],
  "temperature": 0.1,
  "max_tokens": 400
}
```

Check the model card for the chat template, any reasoning toggle, and recommended sampling settings (**VERIFY**).

### 1.6 Error handling for Gnani calls

| Status | Meaning | Munimji behaviour |
|---|---|---|
| 401 | Missing or invalid key | Log `CONFIG_ERROR`; show setup hint in dev panel |
| 4xx other | Bad request (format, params) | Log body; no retry; show "Could not process audio" |
| 429 | Rate limit (if applicable — **VERIFY** in the Error Reference) | Back off 1 s, retry once |
| 5xx / timeout | Service issue | Retry once; then fallback (text input or text-only reply) |

Read the Gnani **Error Reference** page and copy its exact codes into `gnani/errors.py`.

---

## Part 2 — Munimji HTTP API

Base path: `/api/v1`. JSON unless stated. No auth in the hackathon build (single-user, local); add a bearer token before any public deployment.

### 2.1 Voice and text turns

#### `POST /api/v1/voice/turn`
Multipart form.

| Field | Type | Notes |
|---|---|---|
| `audio` | file | webm/opus, wav, or m4a from the browser |
| `session_id` | string | Client-generated UUID |
| `turn_id` | string | UUID for idempotency |
| `lang_hint` | string, optional | `auto` (default), `hi`, `mr`, `en` |

**200 response**

```json
{
  "turn_id": "5b1c…",
  "transcript": "Ramesh ko 200 udhaar likh de aur Sunita ne 150 diye",
  "language": "hinglish",
  "actions": [
    {"tool": "add_credit", "status": "done", "entry_id": 41,
     "customer": {"id": 3, "name": "Ramesh"}, "amount_paise": 20000, "balance_paise": 85000},
    {"tool": "record_payment", "status": "done", "entry_id": 42,
     "customer": {"id": 7, "name": "Sunita"}, "amount_paise": 15000, "balance_paise": 0}
  ],
  "cards": [{"type": "khata_summary", "data": {"…": "…"}}],
  "clarification": null,
  "reply_text": "Ramesh ke khaate mein ₹200 jod diye. Ab unka baaki ₹850 hai. Sunita ke ₹150 jama ho gaye.",
  "audio_url": "/audio/5b1c.wav",
  "fallbacks": {"parser": "evon", "tts": "timbre", "market_source": null},
  "timings_ms": {"upload": 40, "stt": 820, "llm": 1450, "logic": 12, "tts": 710, "total": 3100}
}
```

**Errors:** `400 AUDIO_TOO_SHORT`, `415 UNSUPPORTED_AUDIO`, `422 VALIDATION_ERROR`, `502 UPSTREAM_STT`, `502 UPSTREAM_LLM`, `504 TIMEOUT`.
Error body: `{"error": {"code": "AUDIO_TOO_SHORT", "message": "…", "retryable": true}}`.

#### `POST /api/v1/text/turn`
Same pipeline, skipping STT. Body: `{"session_id": "...", "turn_id": "...", "text": "...", "lang_hint": "auto", "dry_run": false}`. Used for typed fallback, tests and the eval script. With `"dry_run": true` the actions are parsed and validated but **nothing is written** to the database or audio store.

#### `POST /api/v1/confirm`
Resolves a pending clarification or confirmation.
Body: `{"session_id": "...", "pending_id": "...", "answer": "yes" | "no" | {"customer_id": 3}}`.

### 2.2 Ledger (Khata)

| Method & path | Purpose |
|---|---|
| `GET /ledger/customers?query=ram` | List or fuzzy-search customers with balances |
| `GET /ledger/customers/{id}` | One customer with entry history |
| `GET /ledger/summary?date=YYYY-MM-DD` | Day totals: credit given, payments received, net, top debtors |
| `GET /ledger/top-debtors?limit=5` | Highest outstanding balances |
| `POST /ledger/entries` | Manual entry (UI form): `{customer_id, type, amount_paise, note}` |
| `POST /ledger/entries/{id}/void` | Void an entry |
| `POST /ledger/undo` | Void the most recent non-voided entry of the session |
| `GET /ledger/reminder-draft/{customer_id}?lang=hi` | Text draft for the customer; the UI offers copy |

### 2.3 Prescriptions (Parchi)

| Method & path | Purpose |
|---|---|
| `GET /prescriptions` | Active prescriptions |
| `GET /prescriptions/{id}` | Detail with medicines and schedule |
| `POST /prescriptions/{id}/cancel` | Mark as cancelled |
| `GET /reminders?due=today` | Today's doses |
| `GET /reminders/due-now` | Doses due in the last 15 minutes and not done (polled by the UI) |
| `POST /reminders/{id}/done` | Mark dose taken |
| `POST /reminders/{id}/snooze` | Body `{minutes: 10}` |

### 2.4 Market (Sensex Awaaz)

| Method & path | Purpose |
|---|---|
| `GET /market/snapshot` | Indices and watchlist with `as_of`, `source`, `is_sample` |
| `GET /market/watchlist` | Watchlist symbols |
| `PUT /market/watchlist` | Replace watchlist (max 8) |

### 2.5 System

| Method & path | Purpose |
|---|---|
| `GET /health` | `{ "status": "ok", "stt": "ok", "llm": "ok|degraded", "tts": "ok", "db": "ok" }` — checks are cheap and cached for 30 s |
| `GET /settings`, `PUT /settings` | Language, voice, large-type, demo mode |
| `POST /tts` | Body `{text, lang}`; returns audio URL (used for reminders) |
| `GET /utterances?limit=50` | Debug log (disabled when `DEBUG=false`) |
| `GET /audio/{file}` | Serves generated audio; files auto-deleted after 30 min |

### 2.6 Card types returned to the UI

| `type` | Payload keys |
|---|---|
| `khata_summary` | `customers[]` (name, balance_paise, last_entry), `undo_token` |
| `khata_top_debtors` | `items[]` |
| `parchi_saved` | `prescription` (patient_label, medicines[], times[], duration_days), `disclaimer` |
| `parchi_due` | `reminder` |
| `bazaar_snapshot` | `indices[]`, `watchlist[]`, `as_of`, `is_sample`, `disclaimer` |
| `clarify` | `question`, `options[]` |
| `info` | `text` |

### 2.7 Conventions

- Money: integer `amount_paise`.
- Timestamps: ISO 8601 with offset (`+05:30`).
- IDs: integers for DB rows, UUIDs for sessions and turns.
- All text fields are UTF-8; keep Devanagari as-is.
- Versioned path (`/api/v1`). Breaking changes require `/v2`.
