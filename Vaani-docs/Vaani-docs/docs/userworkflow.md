# Munimji — User Workflows

How a real user moves through the product. Each flow lists the spoken input, system behaviour, and reply.

---

## 1. First-run onboarding (≤ 30 seconds)

1. Screen: big mic orb, language switch (हिं · मरा · EN), one line: *"Bolkar dekhiye."*
2. Permission prompt for the microphone, preceded by a one-line explanation: "Munimji aapki awaaz sunne ke liye mic use karta hai. Recording turant delete ho jaati hai."
3. Munimji greets by voice: *"Namaste! Main Munimji hoon. Aap bolkar khaata, dawa aur bazaar sambhal sakte hain."*
4. Three tappable example chips: **"Ramesh ko 200 udhaar"**, **"Maa ki dawa"**, **"Market kaisa hai?"**. Tapping one runs it as a typed turn (also teaches the voice pattern).
5. Optional: add watchlist symbols (default: Sensex, Nifty, plus 2–3 large companies).

## 2. The core voice turn

```
Hold or tap mic  →  speak  →  release / tap to stop
→ "Samajh raha hoon…"  →  result card appears  →  Munimji speaks
→ (optional) Undo / Replay / follow-up
```

**Rules**
- Recording auto-stops after 1.2 s of silence, or at 20 s.
- Visual and audio feedback within 300 ms of pressing the mic.
- While Munimji speaks, the user can tap the orb to interrupt and speak again.

## 3. Bol-Khata (ledger)

### 3.1 Add credit

| User says | System does | Munimji replies |
|---|---|---|
| "Ramesh ko 200 udhaar likh de" | `add_credit(Ramesh, 200)` | "Ramesh ke khaate mein ₹200 jod diye. Ab unka baaki ₹850 hai." |
| "Sharma ji ne aaj 500 ka saaman liya, udhaar" | `add_credit(Sharma, 500)` | Same pattern |

### 3.2 Record payment

| User says | Reply |
|---|---|
| "Sunita ne 150 diye" | "Sunita ke ₹150 jama ho gaye. Ab unka koi baaki nahi." |
| "Ramesh ne 300 de diye" | "Ramesh ke ₹300 jama ho gaye. Ab unka baaki ₹550 hai." |

### 3.3 Multi-action in one breath
"Ramesh ko 200 udhaar likh de, aur Sunita ne 150 diye." → two actions, one combined reply, two entries on the card, one Undo button that reverts both.

### 3.4 Query

| User says | Result |
|---|---|
| "Ramesh ka kitna baaki hai?" | Spoken balance + card with last 5 entries |
| "Sabse zyada udhaar kiska hai?" | Top-5 list, top name spoken with amount |
| "Aaj ka hisaab batao" | Today's credit given, payments received, net, count of entries |
| "Is hafte kitna wasool hua?" (stretch) | Weekly payments received |

### 3.5 Correction and undo

| User says | System |
|---|---|
| "Nahi, 300 likh" (right after an entry) | `correct_last_entry(300)` → voids the last entry, adds a corrected one |
| "Galat ho gaya, hata do" / "Undo" | `undo_last()` voids the last entry |
| Tap Undo on the snackbar | Same as above, for 8 s |

### 3.6 Reminder message draft
"Ramesh ko yaad dilane ka message bana do." → card with a polite draft in the customer's likely language, **Copy** button. Munimji never sends messages.

> *"Namaste Ramesh ji, aapka ₹850 baaki hai. Jab suvidha ho, kripya bhej dein. Dhanyavaad."*

### 3.7 Ambiguity and confirmation rules

| Situation | Behaviour |
|---|---|
| Name matches 2+ customers closely | "Ramesh Patil ya Ramesh Shinde?" with two chips; user taps or says the surname |
| New customer name | Creates the customer **and says so**: "Naya khaata banaya: Ramesh." Undo covers this too |
| Amount ≥ ₹5,000 | Confirm: "₹5,000 Ramesh ke naam likhun?" Answer "haan" or "nahi" |
| Amount missing | "Kitne rupaye?" |
| Confidence < 0.6 | "Maine suna: …. Sahi hai?" |
| Negative or zero amount | Refuse, ask again |

## 4. Parchi (prescription helper)

### 4.1 Save a prescription by voice
User: *"Maa ko BP ki goli subah-shaam, 5 din, khaane ke baad."*

System:
1. Evon extracts `patient_label: "Maa"`, medicine "BP ki goli", times `["morning","evening"]`, `with_food: "after"`, `duration_days: 5`.
2. Python maps times to clock times (defaults below), creates 10 reminders.
3. Card shows the plan. Munimji reads it back: *"Maa ke liye BP ki goli: subah aur shaam, khaane ke baad, 5 din. Main yaad dilaunga."*
4. Footer disclaimer shown; voice adds *"Dose ke baare mein doctor se hi poochiye."* on first save only.

Default time mapping (editable in settings): morning 08:00 · afternoon 13:30 · evening 19:30 · night 21:30 · "khaane ke baad" shifts to 30 min after the usual meal slot.

### 4.2 Daily use

| Moment | Behaviour |
|---|---|
| A dose is due and the app is open | Card border turns marigold; Munimji says *"Maa ki BP ki goli ka waqt ho gaya."* |
| App closed (stretch) | Browser notification if permitted |
| User says "de di" / "ho gaya" | `mark_dose_done` for the most recent due dose |
| User says "10 minute baad yaad dilana" | Snooze 10 min |
| "Aaj kaunsi dawa leni hai?" | Reads out today's remaining doses |
| "Maa ki dawa band kar do" | Cancels the prescription after confirmation |

### 4.3 Safety behaviour

| User says | Munimji replies |
|---|---|
| "Kya yeh goli ek saath do le sakte hain?" | "Main doctor nahi hoon. Yeh sawaal doctor ya pharmacist se poochiye." No dosing information is given |
| "Dose double kar doon?" | Same refusal |
| "Bukhar ki koi dawa batao" | Same refusal; offers to save a prescription if the doctor gave one |
| Mentions an emergency (chest pain, can't breathe, etc.) | Immediately says to call a doctor or emergency services (112 in India) |

## 5. Sensex Awaaz (markets)

| User says | Munimji does |
|---|---|
| "Aaj market kaisa raha?" | Fetches snapshot, speaks 3 sentences: Sensex and Nifty moves, one watchlist highlight, freshness note |
| "Reliance ka kya hua?" | Single-stock snapshot |
| "Mere watchlist mein TCS jodo" | Adds symbol (max 8) |
| "Kya Reliance kharidun?" | *"Main nivesh salaah nahin deta. Main sirf aaj ka bhaav bata sakta hoon."* |

Freshness handling: if the live source is unavailable, Munimji says *"Yeh pichhla uplabdh bhaav hai, [time] ka"* or, for the bundled demo file, *"Yeh namuna data hai."* — and the card shows the **Sample data** badge.

## 6. Language switching

| Action | Result |
|---|---|
| Tap हिं / मरा / EN | UI, templates and TTS voice switch; Evon's `language` field is a hint to reply language |
| Say "Marathi mein bolo" / "Hindi mein bolo" | `set_language` tool |
| Auto mode | Reply language follows the detected input language (`hi`, `mr`, `en`; code-mixed defaults to Hindi unless Marathi markers dominate) |

## 7. Error and edge flows

| Situation | What the user sees and hears |
|---|---|
| Mic permission denied | Card explains how to enable it; typed input remains available |
| Nothing heard | "Kuch sunai nahi diya. Dobara boliye." Orb shakes slightly |
| Very noisy audio, empty transcript | "Awaaz saaf nahi aayi. Phone ke paas aakar boliye." |
| Network lost | Banner "Internet nahi hai". Entries are not queued silently; the turn fails clearly |
| STT or LLM down | Text input prompt; "offline parser" badge if the rules parser takes over |
| TTS down | Reply shown as text with "voice unavailable" chip |
| Evon returned invalid JSON twice | "Mujhe samajhne mein dikkat ho rahi hai. Aap type kar sakte hain?" |

## 8. Journey map (the 60-second story)

| Moment | User | Munimji |
|---|---|---|
| Morning, shop opening | "Aaj ka hisaab" | Reads yesterday's pending balances (stretch) |
| Customer buys on credit | "Ramesh ko 200 udhaar" | Writes entry, speaks balance |
| Customer pays | "Sunita ne 150 diye" | Records payment |
| Mother's prescription from the clinic | "Maa ko BP ki goli subah-shaam" | Sets reminders |
| Quiet time | "Aaj market kaisa raha?" | 3-sentence briefing |
| Customer from a Marathi-speaking village | Switches to **मरा** | Replies in Marathi voice |

## 9. Accessibility in practice

- Everything spoken is visible; everything visible can be triggered by typing.
- Large-type toggle for older users.
- High contrast by default (see `design.md`).
- Voice speed setting: slow / normal.
- No time-limited prompts shorter than 8 s.

## 10. Metrics to watch during testing

- Turns per task (target: 1).
- Correction rate (user says "nahi/galat" after a reply) — target < 10 %.
- Empty-transcript rate in noise.
- Time to first audio.
- Percentage of replies where the spoken text equals the on-screen text (must be 100 %).
