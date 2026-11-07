# Munimji — Design System

Warm, trustworthy, ledger-like. Calm silver canvas, deep aubergine ink, marigold for the one thing that matters on screen.

---

## 1. Palette

| Role | Name | Hex | Use |
|---|---|---|---|
| **Primary / background** | Ice Silver | `#DDE3E8` | Page background, large surfaces |
| **Secondary / ink** | Deep Aubergine | `#3A0F34` | Text, icons, buttons, filled objects, borders on emphasis |
| **Highlight / accent** | Marigold | `#EAAA00` | Active state, balance chips, key numbers, mic ring, focus accents |

### Derived tints (computed from the three above)

| Token | Hex | Use |
|---|---|---|
| `--ice-50` | `#EEF1F4` | Cards on the silver background |
| `--ice-200` | `#CBD3DA` | Hairlines, dividers, disabled fills |
| `--ice-400` | `#A9B4BE` | Placeholder text on large type only |
| `--aubergine-70` | `#6B4A66` | Secondary text |
| `--aubergine-900` | `#2A0A26` | Pressed state, night-mode background |
| `--marigold-600` | `#C48F00` | Pressed state of marigold fills |
| `--marigold-100` | `#F6E3A6` | Soft highlight wash behind marigold content |

### Functional colour (outside the brand palette, used sparingly)

| Token | Hex | Use |
|---|---|---|
| `--danger` | `#A63A2E` | Destructive confirmation, error text. Always paired with an icon and words |

### Contrast (approximate WCAG ratios — re-check with a tool before the final build)

| Foreground on background | Ratio | Verdict |
|---|---|---|
| Aubergine on Ice Silver | ≈ 12.5 : 1 | AAA for all text |
| Aubergine on Marigold | ≈ 7.9 : 1 | AAA for all text |
| Aubergine-70 on Ice Silver | ≈ 5.8 : 1 | AA for body text |
| Marigold on Ice Silver | ≈ 1.6 : 1 | **Fails. Never use marigold text or thin icons on silver** |
| Marigold on Aubergine | ≈ 7.9 : 1 | AAA — use for night mode and the filled mic button |
| Ice Silver on Aubergine | ≈ 12.5 : 1 | AAA |

**Rule:** marigold is a *fill* or a *large shape*, with aubergine content on top. On silver it appears as chips, rings, underline bars, and filled buttons — never as small text.

## 2. CSS tokens

The same tokens live in `frontend/styles/tokens.css`.

```css
:root {
  --ice-silver: #DDE3E8;
  --ice-50: #EEF1F4;
  --ice-200: #CBD3DA;
  --aubergine: #3A0F34;
  --aubergine-70: #6B4A66;
  --aubergine-900: #2A0A26;
  --marigold: #EAAA00;
  --marigold-600: #C48F00;
  --marigold-100: #F6E3A6;
  --danger: #A63A2E;

  --bg: var(--ice-silver);
  --surface: var(--ice-50);
  --text: var(--aubergine);
  --text-muted: var(--aubergine-70);
  --accent: var(--marigold);
  --border: var(--ice-200);
}
```

## 3. Typography

| Use | Font | Fallback | Notes |
|---|---|---|---|
| Display / headings | **Fraunces** (Latin) + **Noto Serif Devanagari** | Georgia, serif | Warm ledger feel |
| Body / UI | **Noto Sans** + **Noto Sans Devanagari** | system-ui, sans-serif | One family covers Latin, Devanagari (Hindi and Marathi) |
| Numbers (balances) | Noto Sans, `font-variant-numeric: tabular-nums` | — | Align digits in the ledger |

Scale (mobile-first, 16 px base):

| Token | Size / line | Weight | Use |
|---|---|---|---|
| `display` | 32 / 38 | 600 | App title, big balance |
| `h1` | 24 / 30 | 600 | Section titles |
| `h2` | 20 / 26 | 600 | Card titles |
| `body` | 16 / 24 | 400 | Default text. **Never below 16 px** |
| `small` | 14 / 20 | 400 | Meta, timestamps |
| `numeric-lg` | 40 / 44 | 600 | Balance chip value |

Devanagari needs about 10 % more line height than Latin. Set `line-height: 1.6` for Hindi/Marathi blocks and add `lang` attributes (`hi`, `mr`, `en`) on every text element so browsers select the right glyphs.

## 4. Spacing, shape, elevation

- 4-px grid: `4, 8, 12, 16, 24, 32, 48`.
- Radius: `12` (inputs, chips), `20` (cards), `999` (pills, mic orb).
- Shadow: tinted aubergine, never black — `0 8px 24px rgba(58,15,52,0.12)`.
- Borders: 1 px `--border`; emphasis border 2 px aubergine.
- Touch targets ≥ 48 × 48 px.

## 5. Components

### 5.1 Mic orb (hero element)
- Diameter 96 px (mobile), 120 px (desktop). Centre-bottom of the screen.
- **Idle:** aubergine fill, silver mic icon, soft shadow.
- **Listening:** aubergine fill + animated **marigold ring** whose radius follows input amplitude.
- **Thinking:** ring turns into a marigold arc spinner; label "समझ रहा हूँ…" / "Samajh raha hoon…".
- **Speaking:** marigold fill, aubergine speaker icon, concentric ripples.
- **Error:** aubergine fill, danger-coloured badge with "!" and text under the orb.
- Interaction: press-and-hold **or** tap to start/tap to stop. Space bar on desktop.

### 5.2 Status strip
Four steps: **Listening → Understanding → Doing → Speaking**. Current step has a marigold dot and aubergine label; completed steps are aubergine; upcoming are `--ice-200`. Also shows latency in dev mode.

### 5.3 Conversation bubbles
- **User:** aubergine fill, silver text, right-aligned, radius 20 20 4 20.
- **Munimji:** `--ice-50` fill, aubergine text, **4 px marigold left bar**, left-aligned.
- Each Munimji bubble has a replay icon button and shows the exact text that was spoken.
- Detected language chip (हिं / मरा / EN) at the bubble corner in dev mode.

### 5.4 Khata card (ledger)
- Header: customer name in `h2`, last activity as `small`.
- **Balance chip:** marigold fill, aubergine text, `numeric-lg`, label "बाकी / baaki".
- Entry rows: `+₹200 udhaar` / `−₹150 jama` with explicit words, not only colour. Credit rows use an up-arrow icon, payments use a down-arrow icon.
- Undo snackbar: aubergine fill, silver text, marigold "Undo" action, visible 8 s.
- Top-debtors list: horizontal bars in aubergine on `--ice-200`, amount at the bar end.

### 5.5 Parchi card (prescription)
- Title: patient label ("Maa") + short note.
- Medicine row: name in bold, dose text as spoken, **time chips** (marigold pills with aubergine text, e.g. `सुबह 8:00`).
- Duration progress: aubergine bar on `--ice-200` with day count.
- Persistent footer line, `small`, aubergine-70: "Yeh sirf aapki bataayi jaankari hai. Dawa ke baare mein doctor se poochiye."
- Reminder due state: card border switches to 2 px marigold, bell icon pulses once.

### 5.6 Bazaar card (market)
- Index tiles (Sensex, Nifty): value in `numeric-lg`, change with **▲/▼ and signed percentage in text**. Never rely on colour alone.
- Watchlist rows with sparkline in aubergine.
- **Freshness badge:** "Live · 14:32" in marigold chip, or "Sample data" in outlined chip when fallback is used.
- Footer: "Jaankari ke liye. Nivesh salaah nahin."

### 5.7 Language switch
Segmented control with three options: **हिं · मरा · EN**. Selected segment is aubergine with silver text; marigold underline bar below. "Auto" is the default; switching changes TTS voice and templates.

### 5.8 Toasts and dialogs
- Toast: aubergine, silver text, marigold icon, bottom-centre.
- Confirmation dialog: surface card, two buttons — primary aubergine filled, secondary outlined. Danger actions use `--danger` text with a trash icon.

### 5.9 Empty states
Each panel has a one-line example the user can say, in the selected language: *"Bolkar dekhiye: 'Ramesh ko 200 udhaar likh de.'"* Marigold underline on the example phrase.

## 6. Layout

**Mobile (default, 360–430 px):** single column.
1. Top bar: logo, language switch, settings icon.
2. Result panel (scrollable): latest card on top, conversation below.
3. Bottom dock: status strip + mic orb + text-input toggle.

**Desktop (≥ 960 px):** two panes.
- Left 40 %: conversation + mic dock.
- Right 60 %: tabs **Khata · Parchi · Bazaar** with the live data views.

The three module tabs use aubergine underlines, with marigold marking the active tab indicator.

## 7. Iconography and logo

- Icons: 24 px grid, 2 px stroke, rounded caps (Lucide or Phosphor), aubergine.
- **Logo mark:** the Devanagari letter **म** inside an aubergine circle; a marigold dot at the end of the headline stroke (reads as a pen touching a ledger line). Wordmark "Munimji" in Fraunces 600.
- Favicon: marigold circle with aubergine **म**.

## 8. Motion

| Interaction | Duration | Easing |
|---|---|---|
| Card enter | 220 ms | `cubic-bezier(.2,.8,.2,1)`, translateY 12 px → 0 |
| Mic ring amplitude | live | direct |
| Chip balance update | 300 ms count-up | ease-out |
| Snackbar | 180 ms | ease-out |

`@media (prefers-reduced-motion: reduce)` removes pulses and count-ups; state changes are instant but still visible.

## 9. Accessibility

- All spoken replies are also visible as text. No information exists only in audio.
- Colour is never the only signal: arrows, words, icons accompany colours.
- Visible focus ring: 3 px marigold outline with 2 px aubergine inner outline (so it is visible on both silver and aubergine).
- `aria-live="polite"` on the Munimji reply area; `aria-pressed` on the mic button.
- Text scaling up to 200 % without layout breakage.
- Large-type mode toggle in settings (+25 %).
- Keyboard: Space = hold to talk, `Z` = undo, `1/2/3` = switch tabs.

## 10. Night-shop mode (stretch)

Swap roles: `--bg: #2A0A26`, `--surface: #3A0F34`, `--text: #DDE3E8`, `--accent: #EAAA00`. Marigold on aubergine is AAA, so this mode is arguably the most readable of the two.

## 11. Voice and tone of copy

- Short, respectful, first-person: "Ramesh ke khaate mein ₹200 likh diya."
- Use *aap*, not *tum*. Suggested name for the assistant: **Munimji**.
- Confirm numbers by saying them back: "Do sau rupaye."
- Never blame the user for misrecognition: "Samajh nahi aaya, dobara boliye?"

## 12. Demo visuals checklist

- Mic orb centred, ring clearly marigold in the first frame of the video.
- Balance chip large enough to read in a 360 p thumbnail.
- Language chip changes visibly when switching to Marathi.
- No dev panel in the recorded take except a small latency line, if it helps credibility.
