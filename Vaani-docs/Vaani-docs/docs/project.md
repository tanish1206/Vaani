# Munimji — Project Brief

> **Tagline:** *Boliye, Munimji sambhal lenge.* (Just speak — Munimji will handle it.)
> **Event:** Gnani "Great Indian AI Internship Challenge" · **Deadline:** 10 Nov 2026, 11:59 PM IST
> **Team:** Solo (Tanish Soni)

---

## 1. One-line pitch

A single voice assistant, in the user's own language, that runs a small-town shopkeeper's **credit ledger**, **family medicine reminders**, and **market briefing** — built end to end on Gnani's sovereign Indian models: **Prisma** (speech-to-text), **Evon** (reasoning and tool-calling), **Timbre** (text-to-speech).

## 2. Problem

A kirana or small-shop owner in a town like Panvel, Nashik or Kolhapur:

- Runs the shop on **voice and memory**. Udhaar (credit) lives in a paper notebook, in the head, or in a customer's promise.
- Speaks **code-mixed** Hindi/Marathi/English. Most apps force typing, English menus, or a single clean language.
- Handles **family health** (parents' BP and sugar tablets, a child's course of antibiotics) with scribbled notes and forgotten doses.
- Has **money in the market** (a few stocks, a mutual fund SIP) but no time or comfort to read English market sites.

No tool serves all of this by voice, in their language, on a cheap phone.

## 3. Solution

One voice loop: **hold the mic → speak naturally → Munimji acts → Munimji replies in voice (and on screen).**

| Module | Name | Example utterance | Result |
|---|---|---|---|
| Ledger | **Bol-Khata** | "Ramesh ko 200 udhaar likh de, aur Sunita ne 150 diye." | Two ledger entries written; spoken balance summary |
| Health | **Parchi** | "Maa ko BP ki goli subah-shaam, 5 din." | Prescription stored; reminder schedule created; spoken read-back |
| Markets | **Sensex Awaaz** | "Aaj market kaisa raha?" | Spoken, plain-language briefing of index and watchlist |

A router built on Evon picks the right tool(s) per utterance. The three modules share one pipeline, one design system, one language layer.

## 4. Users

**Primary persona — Shankar-kaka, 48, general store, semi-urban Maharashtra**
Speaks Marathi + Hindi + a little English. Android phone, patchy data. Wants speed: his hands are busy and the shop is noisy.

**Secondary persona — his daughter, 22**
Sets things up, reviews the ledger on a bigger screen, shares reminders to a customer.

## 5. Scope

### In scope (MVP — must ship)
1. Voice turn pipeline: mic → Prisma → Evon → action → Timbre → playback, with on-screen transcript and result cards.
2. **Bol-Khata:** add credit, record payment, balance query, top debtors, daily summary, undo/correct last entry, reminder-message draft (text only, copy to clipboard).
3. **Parchi:** save a spoken prescription, build reminder schedule, list today's doses, mark dose done, read back in plain words. No medical advice.
4. **Sensex Awaaz:** spoken snapshot for indices and a small watchlist, with clear "information, not advice" framing and honest data-freshness labelling.
5. Languages: Hindi, Marathi, English, and code-mixed speech (Hinglish / Marathi-Hindi).
6. Single-device, local SQLite storage.
7. Branded UI in the specified palette (see `design.md`).

### Stretch (only after MVP is demo-ready)
- Streaming TTS (SSE) for faster first audio.
- Night-shop dark theme.
- Browser notifications for reminders.
- Weekly "kaun kitna baaki" PDF/image to share.
- Shop-owner's cloned voice for customer reminders (needs explicit consent flow; post-hackathon).

### Out of scope
- Prescription photo/OCR, multi-user accounts, cloud sync, payments/UPI, buy-sell advice, tax/GST features.

## 6. Success criteria

| Criterion | Target |
|---|---|
| End-to-end latency (Khata turn, speech end → audio start) | ≤ 4 s typical |
| Intent + entity accuracy on the 40-utterance test set (`testing.md`) | ≥ 90 % |
| Works with background noise (shop-level, ~60 dB) in demo | Yes |
| Demo video length | ≤ 60 s, shows all three modules, one language switch |
| Arithmetic correctness | 100 % (Python computes; the model never does the maths) |
| Safety | Zero dose suggestions; zero buy/sell advice; zero silent data loss (undo always works) |

## 7. How this fits the Gnani challenge

| Requirement / award angle | How Munimji answers |
|---|---|
| Build on Gnani's Indian models | Uses all three: Prisma, Evon, Timbre |
| **Solo Ninja** | Solo build, one cohesive product |
| **Mixed Vibes** | Code-mixed speech is the default input, not an edge case |
| **Real Deal** | Solves a daily problem for a real user group |
| **Small Town Big Build** | Built for semi-urban shopkeepers, low-end phone, regional language |
| **Noise Canceller** | Demo recorded with ambient noise; STT robustness is the headline |
| **Jugaad Genius** | One router, three jobs; deterministic safety net around a probabilistic model |
| **Demo Day Drop / Crowd Favourite** | 60-second demo with a clear story and a switch to Marathi |

> Check the exact award wording and rules on the challenge page before final submission. Mapping above is based on the award titles and short descriptions only.

## 8. Principles

1. **One product, not three apps.** Shared pipeline, tools and UI.
2. **The model understands; code decides.** Evon extracts intent and entities. Python validates, does arithmetic, and writes the database.
3. **Never lose the user's data.** Every write is logged and undoable.
4. **Say what you did.** Every action is spoken back and shown on screen.
5. **Honesty in the demo.** If data is a sample or a fallback is active, the UI and voice say so.
6. **Ship the loop first.** A rough end-to-end loop on day 1 beats a polished fragment on day 3.

## 9. Key decisions (summary)

| Decision | Choice | Why |
|---|---|---|
| STT model | Prisma v3.0 (`model=prisma-v3.0`) | Multilingual, automatic language detection suits code-mixed speech |
| STT mode | REST (≤ 30 s clips) | A shop command is a few seconds; simplest to build |
| LLM | Evon v3.3 (30B-A3B) behind an adapter | Required Gnani model; Apache-2.0 open weights; supports tool-calling |
| LLM output | Strict JSON contract, validated by Pydantic | More portable than relying on a specific tool-call parser |
| TTS | Timbre v2.5, REST first, SSE later | v2.5 is the recommended model (v2.0 deprecated) |
| Backend | Python 3.11, FastAPI | Fast to build, async, easy testing |
| Frontend | Vanilla HTML/CSS/JS served by FastAPI | No build step; solo-friendly |
| Storage | SQLite | Zero-ops, local |
| Replies | Python templates in each language; LLM only for market and prescription explanations | Lower latency, fewer hallucinations |

See `architecture.md` for details and `risks.md` for what can go wrong.

## 10. Document map

| File | Purpose |
|---|---|
| `README.md` | Entry point and quick start |
| `project.md` | This brief |
| `architecture.md` | System design, components, ADRs |
| `workflow.md` | Build plan, hour-by-hour schedule, git and quality workflow |
| `design.md` | Visual and interaction design system |
| `api.md` | Gnani API usage and Munimji's own API |
| `userworkflow.md` | User journeys, voice commands, error flows |
| `data-model.md` | Database schema |
| `evon-prompts.md` | System prompt, tool schemas, few-shot examples |
| `testing.md` | Test plan and utterance set |
| `deployment.md` | Setup, running Evon, environments |
| `security-privacy.md` | Data handling, safety, disclaimers |
| `demo-script.md` | 60-second demo and video plan |
| `submission-checklist.md` | Final submission steps |
| `risks.md` | Risk register and fallbacks |
