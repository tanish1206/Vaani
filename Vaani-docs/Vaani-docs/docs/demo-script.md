# Munimji — Demo Script and Video Plan

Target: **≤ 60 seconds**, one continuous story, all three Gnani models visible, one language switch, real noise in the background.

## 1. Setup before recording

- Fresh DB: `python scripts/seed_demo.py --reset` (Ramesh ₹650, Sunita ₹150, Patil ₹1,200, Ganesh ₹400, Shinde ₹300).
- Evon endpoint warm: send one dummy turn.
- Browser at 100 % zoom, window sized to a phone-like column **or** a clean two-pane desktop layout. Dev panel off, except a thin latency line if it reads well.
- Noise source (YouTube "shop ambience" or a table fan) at moderate volume, audible but not drowning.
- Microphone: phone held ~25 cm from the mouth, as a shopkeeper would.
- Screen recording at 1080p, 30 fps; record voice **and** system audio (Munimji's replies). Test the audio mix first.
- Close notifications. Set Do Not Disturb.

## 2. Timeline

| Time | On screen | You say / Munimji says | Purpose |
|---|---|---|---|
| 0:00–0:05 | Title card: **Munimji** with tagline; logo; palette | Caption: *"A voice ledger, medicine reminder and market brief for small shops."* | Hook |
| 0:05–0:20 | Khata tab. Mic orb glows marigold; noise audible | **You:** "Ramesh ko 200 udhaar likh de, aur Sunita ne 150 diye." → **Munimji:** "Ramesh ke khaate mein ₹200 jod diye. Ab baaki ₹850 hai. Sunita ke ₹150 jama ho gaye." Card: ₹850 chip | Mixed language + noise + multi-action |
| 0:20–0:28 | Same tab | **You:** "Sabse zyada udhaar kiska hai?" → **Munimji:** "Patil ka, ₹1,200." Bars appear | Query + tool routing |
| 0:28–0:42 | Parchi tab | **You:** "Maa ko BP ki goli subah-shaam, 5 din, khaane ke baad." → **Munimji:** reads back the plan; time chips appear | Medicine flow |
| 0:42–0:50 | Bazaar tab | **You:** "Aaj market kaisa raha?" → **Munimji:** 2–3 sentence briefing. Badge shows **Live** + time | Third module |
| 0:50–0:57 | Switch to **मरा** | **You:** "रमेश चा बाकी किती आहे?" → **Munimji** answers in Marathi voice | Language switch |
| 0:57–1:00 | End card: logo + *"Built on Gnani Prisma · Evon · Timbre"* + name | — | Close |

If a segment is shaky, cut it, don't rush. Better a clean 50-second video than a stressed 60.

## 3. Voice-over / caption script (if you add one)

> Small shops run on voice, not forms.
> Munimji listens in Hindi, Marathi and English — mixed, even in a noisy shop.
> It writes the khata, sets medicine reminders, and reads the market in plain words.
> Built on Gnani's Prisma, Evon and Timbre.

Add burned-in captions in both Roman and Devanagari for the spoken lines — judges often watch muted first.

## 4. Rehearsal checklist

- [ ] Three consecutive clean runs
- [ ] Each Munimji reply spoken text matches on-screen text
- [ ] Total latency per turn < 4 s (cut or speed up dead air in the edit, never fake the result)
- [ ] The balance shown equals the balance spoken (₹850)
- [ ] No API key, `.env` or terminal secrets visible
- [ ] Prescription disclaimer visible on the card
- [ ] Market card shows data time; if sample data is used, the badge and voice say so
- [ ] Marathi segment sounds natural; voice name noted in README

## 5. Backup plan

| Failure | Backup |
|---|---|
| Evon down at recording time | Record with the rules-parser badge visible **only** for the Khata segment, and say so in the post. Prefer re-recording with Evon |
| Market source down | Use the sample snapshot **with** the visible "Sample data" badge |
| Marathi voice unavailable | Show the Marathi transcript and reply text; speak with the Hindi voice; mention honestly in the caption |
| Audio sync issues | Record voice-over separately and align in the editor |

Record a **backup video on Monday evening** even if imperfect.

## 6. Public post (template)

> **Munimji — boliye, Munimji sambhal lenge** 🎙️
> A voice assistant for small shops: ledger (udhaar/jama), medicine reminders and a plain-language market brief — in Hindi, Marathi and English, even code-mixed and in noise.
> Built on @Gnani.ai's **Prisma** (STT), **Evon** (reasoning) and **Timbre** (TTS).
> Solo build for the Great Indian AI Internship Challenge.
> GitHub: `<link>`
> `<REQUIRED HASHTAGS AND TAGS — copy exactly from the rules page>`

Post publicly (LinkedIn or the platform the rules specify), attach the video, and keep the link for the submission form.

## 7. Written submission summary (150 words)

> Munimji is a voice-first assistant for small-town shopkeepers. In one pipeline it records credit and payments (Bol-Khata), saves and reminds family medicines (Parchi), and gives a spoken market brief (Sensex Awaaz). Prisma transcribes code-mixed Hindi/Marathi/English speech; Evon converts it into validated structured actions; Timbre speaks every result. Python, not the model, does all arithmetic and writes the database, with undo for every change. Safety guardrails block medical dosing advice and investment advice. Built solo in three days.

## 8. Likely judge questions

| Question | Short answer |
|---|---|
| Why three modules? | One shopkeeper, one voice — the pipeline is shared, so adding modules is adding tools |
| How do you stop the LLM making up amounts? | It only extracts; Python validates, calculates and writes; every number in a reply is from SQL |
| What if the model is wrong? | Undo, confirmations for large or ambiguous entries, on-screen transcript |
| Why Evon rather than an API LLM? | Sovereign, open-weights, Indian-language focus, tool-calling, runs under your own control |
| What about noisy shops? | Show the noise results table from `testing.md` §4 |
| What's next? | Realtime streaming, offline queue, multi-device sync, shop-owner voice for customer reminders (with consent) |
