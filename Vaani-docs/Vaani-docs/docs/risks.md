# Munimji — Risk Register

Likelihood and impact: **L**ow / **M**edium / **H**igh. "Trigger" is the moment you switch to the fallback.

| # | Risk | L | I | Mitigation | Trigger → Fallback |
|---|---|---|---|---|---|
| 1 | **Evon cannot be run in time** (30B model, no inference provider) | H | H | Decide on day 1 hour 1; start download immediately; ask Gnani/Discord about hosted access; try a quantised build | No endpoint by Sun 12:00 → rules parser for Khata + clearly labelled badge; keep trying in the background |
| 2 | Evon gives non-JSON or verbose output | M | H | Strict prompt, low temperature, strip reasoning, one retry with the error, JSON mode if the server supports it | Two failures on a turn → rules parser → typed input |
| 3 | Prisma accuracy drops on code-mixed or noisy speech | M | H | Use v3.0 auto-detect; compare with v2.5 + `language_code`; trim silence; keep clips short; tune mic distance | Accuracy < 80 % on test set → per-language selector (user taps hi/mr) and v2.5 |
| 4 | Marathi TTS voice not available or sounds off | M | M | Check voice catalogue early; test a Marathi sentence on day 1 | No Marathi voice → show Marathi text, speak with Hindi voice, state it honestly |
| 5 | Timbre reads `₹` and digits badly | M | M | Test on day 1; use words ("do sau rupaye") or SSML | Templates emit number words |
| 6 | Latency > 4 s | M | M | Short replies, parallel work, GPU close to you, warm Evon, SSE TTS | Trim reply text; show a progress strip; accept 5 s but cut dead air in edit (without faking) |
| 7 | Browser audio format rejected by STT | M | M | ffmpeg → 16 kHz mono WAV always | Re-encode with different flags; test on target device |
| 8 | Name matching errors (Devanagari vs Latin) | H | M | Evon returns roman name; normalised key; fuzzy + ask on tie | Disambiguation chips; allow typing the name |
| 9 | Market data source unreliable (unofficial API, rate limits, symbol quirks) | M | M | 5-min cache; sample snapshot labelled clearly | Source fails → sample data with badge and spoken disclosure |
| 10 | Medical safety slip (model suggests a dose or advice) | L | H | Whitelisted tools, `dose_text` must appear in transcript, refusal templates, disclaimers | Any slip found in testing → block the path and add a regression test |
| 11 | Financial advice slip | L | H | `decline(investment_advice)`, summary prompt forbids predictions, facts-only check | Same |
| 12 | Scope creep — three modules in three days solo | H | H | Strict priority list in `workflow.md`; Sensex is read-only and thin | Cut order: Sensex → reminders list → Parchi extras. Keep Khata + Parchi save |
| 13 | Solo fatigue and late-night mistakes | H | M | Sleep ≥ 5 h; freeze on Mon 11 PM; no new features Tue | Reduce scope sooner rather than later |
| 14 | API quota or rate-limit during demo | L | H | Check quota; avoid loops; cache TTS for repeated phrases | Pre-generate common replies; text-only reply |
| 15 | API key leaked via git or screen recording | M | H | `.gitignore`, `.env.example`, pre-push check, no terminal on screen | Rotate key immediately |
| 16 | Public demo link breaks (GPU stopped, CORS, HTTPS) | M | M | Video is the primary artefact; link optional | README explains local run |
| 17 | SQLite locked under concurrent requests | L | M | WAL, short transactions, one worker | Retry with backoff |
| 18 | Mic permission or HTTPS issues on judges' devices | M | M | `localhost` for demo; typed input fallback | Provide the video as the main proof |
| 19 | Submission format misunderstood | M | H | Read rules/FAQ on Mon morning; use `submission-checklist.md` | Ask on Discord/email early |
| 20 | Hackathon rules require something not planned (specific model usage, repo licence) | L | M | Re-read the rules page once on Sunday | Adjust README |

## Early-warning dashboard (check every 90 minutes)

| Signal | Green | Amber | Red |
|---|---|---|---|
| Voice loop works end to end | Yes | Flaky | No |
| Evon reachable | Yes | Slow | No |
| Eval accuracy (text) | ≥ 90 % | 80–90 % | < 80 % |
| Median latency | < 3.5 s | 3.5–5 s | > 5 s |
| Hours left vs open P0/P1 tasks | Ahead | On track | Behind |

Red on two or more rows → invoke the cut order immediately.
