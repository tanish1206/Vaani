# Munimji · मुनीमजी

> *Boliye, Munimji sambhal lenge.*
> A voice assistant for small-town shopkeepers: **ledger (Bol-Khata)**, **medicine reminders (Parchi)** and a **plain-language market brief (Sensex Awaaz)** — in Hindi, Marathi and English, including code-mixed speech.

Built solo for the Gnani **Great Indian AI Internship Challenge** on Gnani's Indian models:

| Stage | Model |
|---|---|
| Speech-to-text | **Prisma** (v3.0, automatic language detection) |
| Understanding and tool-calling | **Evon** v3.3 30B-A3B (open weights, Apache-2.0) |
| Text-to-speech | **Timbre** v2.5 |

## How it works

```
mic → Prisma (STT) → Evon (JSON actions) → validate + guardrails → module logic (SQLite)
    → reply template / short LLM summary → Timbre (TTS) → audio + on-screen card
```

Python validates, calculates and writes the database. The model only understands.
Every change can be undone. Medical dosing advice and investment advice are refused by design.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env                                      # add your Gnani key; set EVON_BASE_URL
python scripts/seed_demo.py
uvicorn app.main:app --reload --port 8000 --app-dir backend
```

Open `http://localhost:8000`. Needs `ffmpeg` installed. Running Evon is covered in `deployment.md`.

## Documentation

| Doc | What's inside |
|---|---|
| [project.md](docs/project.md) | Vision, scope, success criteria, award mapping |
| [architecture.md](docs/architecture.md) | Components, data flow, ADRs, latency budget |
| [workflow.md](docs/workflow.md) | Hour-by-hour build plan, git and quality workflow |
| [design.md](docs/design.md) | Colour system (Ice Silver / Deep Aubergine / Marigold), type, components |
| [api.md](docs/api.md) | Gnani API usage and Munimji's own API |
| [userworkflow.md](docs/userworkflow.md) | User journeys, voice commands, error flows |
| [data-model.md](docs/data-model.md) | SQLite schema, name matching, seed data |
| [evon-prompts.md](docs/evon-prompts.md) | System prompt, tool schemas, validation, fallback parser |
| [testing.md](docs/testing.md) | 40-utterance set, noise and latency tests |
| [deployment.md](docs/deployment.md) | Setup, running Evon, hardening, troubleshooting |
| [security-privacy.md](docs/security-privacy.md) | Data handling, safety, disclaimers |
| [demo-script.md](docs/demo-script.md) | 60-second demo, video and post plan |
| [submission-checklist.md](docs/submission-checklist.md) | Final steps before the deadline |
| [risks.md](docs/risks.md) | Risk register and fallbacks |

## Repository layout (target)

```
backend/app/        api/ core/ gnani/ modules/{khata,parchi,bazaar}/ db/ tests/
frontend/           index.html app.js styles/tokens.css styles/app.css
scripts/            seed_demo.py eval_utterances.py smoke_live.py run_dev.sh
data/               munimji.db (git-ignored), demo_snapshot.json
docs/               the documents above
```

## Status

- [ ] Voice loop (STT → TTS)
- [ ] Evon adapter + contract
- [ ] Bol-Khata
- [ ] Parchi
- [ ] Sensex Awaaz
- [ ] Language switch (hi / mr / en)
- [ ] UI polish to `design.md`
- [ ] Eval ≥ 90 %
- [ ] Demo video and public post
- [ ] Submission

## Privacy and safety in one paragraph

Audio and spoken replies are processed by Gnani's speech services; everything else stays on your device in a local SQLite file. Munimji is a record-keeping and reminder tool: it does **not** give medical advice, dosing guidance or investment advice.

## Licence

Choose before publishing (MIT is a safe default). Evon is Apache-2.0; follow Gnani's terms for API use.
