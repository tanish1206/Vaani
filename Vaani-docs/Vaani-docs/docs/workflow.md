# Munimji — Build Workflow

Solo build. Deadline: **Tue 10 Nov 2026, 11:59 PM IST**. Today: **Sat 7 Nov, ~9 PM**.
Plan to **freeze code by Mon 9 Nov 11 PM** and use Tue only for the video, post and submission.

---

## 1. Schedule

### Sat 7 Nov (night, ~4 h) — "The loop breathes"
| Time | Task | Done when |
|---|---|---|
| 21:15 | Create repo, folders, `.env`, `.gitignore`, venv, `requirements.txt` | `uvicorn` serves a hello page |
| 21:45 | **Start Evon provisioning now** (see `deployment.md`) — weights download runs in the background | Instance up or hosted access confirmed |
| 22:00 | Prisma call from a script with a recorded Hindi clip | Transcript printed |
| 22:30 | Timbre call from a script | `.wav` plays |
| 23:00 | FastAPI `/api/v1/voice/turn` — **echo mode**: audio → STT → TTS of the transcript | Browser mic → hear echo |
| 00:00 | Frontend skeleton with mic button and transcript bubble | Full round trip works |
| 00:30 | Commit, write down open questions (voices, model strings, Marathi code) | Notes in `docs/open-questions.md` |

### Sun 8 Nov (~14 h) — "Khata is real"
| Time | Task |
|---|---|
| 09:00 | Evon adapter + JSON contract + Pydantic models (`evon-prompts.md`) |
| 10:30 | Khata tools: add_credit, record_payment, get_balance, top_debtors, undo, correct_last |
| 12:30 | Fuzzy customer matching (Latin romanisation key + rapidfuzz) |
| 13:30 | Lunch + first 20-utterance eval run |
| 14:30 | Reply templates (hi, mr, en) with number phrasing; test how Timbre reads `₹` and digits |
| 16:00 | UI: ledger card, balance chip, undo snackbar |
| 17:30 | Rules parser safety net for Khata (regex + lexicon) |
| 19:00 | Dinner |
| 20:00 | **Parchi:** prescription model, frequency mapping, reminders table |
| 22:30 | Parchi UI cards + spoken read-back; guardrail for medical advice |
| 00:00 | Commit, tag `v0.5-khata-parchi` |

### Mon 9 Nov (~14 h) — "Three modules, one product"
| Time | Task |
|---|---|
| 09:00 | **Sensex Awaaz:** data source, cache, sample snapshot fallback, summary prompt |
| 11:30 | **Cut-line check:** if Parchi or Khata is flaky, drop Sensex to a read-only card and spend time on quality |
| 12:00 | Language switch (hi / mr / en), Marathi voice and templates |
| 14:00 | Visual polish to `design.md`: mic orb states, motion, empty states |
| 16:00 | Noise test with fan / street / mixer audio; tune trimming and thresholds |
| 18:00 | Full 40-utterance eval; fix top failures |
| 20:00 | Record demo clips (see `demo-script.md`) — several takes |
| 22:00 | README, screenshots, architecture diagram export |
| 23:00 | **Code freeze** and tag `v1.0-demo` |

### Tue 10 Nov — "Ship"
| Time | Task |
|---|---|
| 09:00 | Edit the final video, caption it, export |
| 11:00 | Public post with the required hashtags and tags (copy exact ones from the rules page) |
| 12:00 | Submit the form; confirm receipt |
| 12:00–18:00 | Buffer for anything that went wrong. **No new features** |
| 18:00 | Final check from `submission-checklist.md`; **hard stop submitting by 20:00** |

## 2. Priority and cut order

Build in this order. If time runs out, cut from the bottom.

1. Voice loop (STT → TTS) · **P0**
2. Khata add/payment/balance · **P0**
3. Evon extraction + validation · **P0**
4. Undo / correct · **P0**
5. Parchi save + read-back · **P1**
6. Language switch hi/mr/en · **P1**
7. Sensex Awaaz snapshot · **P1**
8. Top debtors, daily summary, reminder draft · **P2**
9. Parchi reminders list + mark done · **P2**
10. SSE streaming TTS, night theme, notifications · **P3**

**Definition of "demo-ready":** items 1–7 work in one uninterrupted pass, three times in a row, on the recording device.

## 3. Daily rhythm

- **Start:** read yesterday's notes, run the eval script, pick top 3 tasks.
- **Every 90 min:** commit; run the happy-path demo once.
- **End:** update `docs/open-questions.md`; push to GitHub; write tomorrow's top 3.
- **Never** debug a flaky external service for more than 30 min without switching to the fallback.

## 4. Git workflow

- Single `main` branch plus short-lived feature branches (`feat/khata`, `feat/parchi`, `feat/bazaar`, `feat/ui-polish`).
- Commit format: `feat(khata): add_credit with undo` · `fix(stt): trim silence` · `docs: update api.md`.
- Tags at each milestone: `v0.1-loop`, `v0.5-khata-parchi`, `v1.0-demo`.
- Push at least every 2 hours. The remote is the backup.
- `.env`, `data/*.db` and `recordings/` are in `.gitignore`.

## 5. Quality gates

| Gate | When | Command / action |
|---|---|---|
| Lint + format | pre-commit | `ruff check . && ruff format .` |
| Unit tests | each commit | `pytest -q` |
| Utterance eval | each milestone | `python scripts/eval_utterances.py` (accuracy report) |
| Happy-path demo | every 90 min | Follow `demo-script.md` |
| Secret scan | before first push | `git grep -n "X-API-Key-ID"`, check `.env` ignored |

## 6. Definition of done (per feature)

- Works by voice **and** by typed text (`/api/v1/text/turn`).
- Has at least 3 test utterances in `testing.md` and they pass.
- Has a spoken reply and an on-screen card.
- Has an undo path or is read-only.
- Failure mode tested (empty audio, API failure).
- Colours and spacing follow `design.md` tokens.

## 7. Environment and tools

| Item | Choice |
|---|---|
| OS | Your laptop; Linux GPU box for Evon |
| Python | 3.11 (SDK needs ≥ 3.9) |
| Packages | `fastapi`, `uvicorn[standard]`, `httpx`, `pydantic`, `pydantic-settings`, `python-multipart`, `rapidfuzz`, `pytest`, `ruff`, optional `gnani-vachana`, `yfinance` |
| System | `ffmpeg` |
| Editor | VS Code + REST Client or Bruno |
| Notes | `docs/open-questions.md`, kept short |

## 8. Time-boxing rules for a solo builder

- 30-minute rule on any single blocker; then fallback or ask on the hackathon Discord.
- No refactors after Sunday night.
- Sleep at least 5 hours on each of the next two nights. A sharp demo beats a fourth feature.
- Record a backup demo video on Monday evening **even if imperfect**. Better a good-enough video than none.
