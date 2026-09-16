# Maverix design system — how it was applied, and where it wasn't

The design system is written for maverixmedical.com: a marketing site, read once,
on a desk, on good wifi. This is a field tool: read a hundred times a day, on a
phone, at arm's length, in a lit exhibit hall, often with no signal. Where those
two pull apart, the tool wins and the deviation is recorded here.

Everything not listed below follows the system literally.

## Applied as written

- All colour tokens from §13. No hex outside the token set.
- Framed centre column (§0) with 1px `--frame-line` hairlines left and right.
- Dark header, `--surface-dark #0D1418`, 62px (§7.3).
- Square containers of text, rounded containers of photos (§4). Cards, tables,
  filter bar, notices and form controls are all `--radius-none`; only the
  physician photo panel is rounded, at `--radius-photo 18px`.
- Chips use `--radius-sm 8px`. `--radius-pill` is untouched — it belongs to the
  Narwhal badge and nothing else.
- No card carries a coloured left border. The talk-track block uses a 1px
  `--border-strong` left rule, which is the big-stat label pattern from §7.10.
- Eyebrows and labels: display face, uppercase, `.28em`/`.35em` tracking.
- Italic as a real device (§2.6) — CTA labels, the physician count, talk tracks,
  regulatory notes, the empty state.
- Bullets are 10px `--mvx-sky` circles (§7.12), not icons.
- The double chevron in a circle is the only icon (§10). **No emoji** — the old
  badge-capture button carried a 📷; it now reads as plain text. Verified: zero
  emoji across all nine pages.
- Stat cells, spec tables and the tab-bar surface reused as specified.
- Rx note (§11.5) on the target list, event info and landing pages.
- Voice (§11): no exclamation marks, "physicians" not "users", em dashes for the
  attribute→benefit hinge.

## Deviations, with reasons

**1. Root type is 15px / weight 400, not 14px / weight 300 (§2.2).**
14px at weight 300 is a marketing body size read on a desk. Reps scan this at
arm's length under hall lighting. Prose keeps weight 300; dense lists take 400.

**2. Data pages widen the framed column to 1440px (§0).**
The hairlines and the centred column stay — that is the structural idea — but
1000px fits two physician cards, and someone working 44 of them needs three.
Marketing-shaped pages (landing, event info, invites, happy hour) stay at 1000px.

**3. Band padding is 3.2rem/40px, not 6rem/72px (§3.2).**
6rem of vertical padding per band is one and a half phone screens of nothing
before the first card.

**4. Physician photos are full colour, not greyscale (§9).**
The system greyscales pathway photos 35% and modal headshots 100%. The entire
purpose of this photo is recognising a face across a booth. Greyscale would
actively damage the one job it does.

**5. Nav scrolls horizontally instead of collapsing below 920px (§8.2).**
The system hides nav links on small screens behind a menu. Nine destinations and
a rep mid-conversation means one tap to any page, not two.

**6. 44px minimum tap target on every control.**
Not in the system, which has no touch spec. Required here.

**7. Poppins Bold stands in for Clash Display (§13.1).**
The licensed OTFs live in the design-system export, which is not one of this
session's connected folders, so they could not be embedded. Poppins 700 is the
sanctioned fallback and display type is set at 700 throughout. Neither Futura
nor Jost appears anywhere in the stack. **To fix:** connect the design-system
export folder, run the base64 loop from §13.1, and paste the three `@font-face`
rules at the top of `theme.css`; nothing else changes.

**8. Poppins is self-hosted, not linked from Google Fonts (§13.1).**
The system permits Google Fonts as an external host. A cross-origin stylesheet
never arrives on dead exhibit-hall wifi, so the seven woff2 files (68KB total)
ship with the site and the service worker precaches them same-origin.

**9. Orange is used as a highlight throughout — a directed override of §1.2.**
§1.2 reserves `--thoracent-orange #FF4D00` for sub-brand surfaces and keeps it off
Maverix parent surfaces. Overridden by direction for this tool. It is applied as a
highlight only: it marks attention and current position, never category, and blue
stays structural.

Contrast governs where it can go. Measured against the three brand oranges:

| Token | on #FFF | on --page-bg | on --surface-dark | white on it |
|---|---|---|---|---|
| `--thoracent-orange #FF4D00` | 3.33 | 2.98 | 5.59 | 3.33 |
| `--mvx-narwhal-dot #F26A3D` | 3.04 | 2.72 | 6.11 | 3.04 |
| `--mvx-narwhal-evidence #C2632F` | 4.10 | 3.67 | 4.53 | 4.10 |

None reaches 4.5:1 on light ground, so **orange never carries small text on white.**
It is a fill, a rule or a mark there; it carries text only on dark, where #FF4D00
reaches 5.59:1. Chips that fill orange take near-black ink (5.59:1), not white
(3.33:1, which would fail).

Applied to: the active nav item and its 3px underline, the brand mark's full stop,
the leading rule on every eyebrow and section label, the left rail on notices, the
top rail on cards, tables, stat grids and day cards, the Cryo Target chip, the
"no rep on site" flag, the TBA marker, tile eyebrows on dark, and the button
underline sweep. `--mvx-highlight-deep #C2632F` is declared for any future case
needing more contrast on light ground.

Not applied to: connected/emailed state (green and blue stay semantic), the demo
room chip (keeps intervention blue so category stays distinct from attention), or
stat numerals (§7.10 shifts those to `--accent`).

**10. Motion is reduced to what survives on touch (§6).**
No hover-expand (there is no hover on a phone, and the system itself disables it
below 920px), no count-up on the coverage stats — a number that animates every
six seconds while someone is reading it is a distraction, not a flourish. The
underline sweep, the arrow-circle nudge and the -3px tile lift are all kept.

## Not yet on the system

**`chest-tips.html`** is the ported AABIP reference page — 336KB with nine
embedded images. It has been given the brand header, the theme stylesheet and a
type/colour overlay, but its internal layout CSS is still the original. A proper
port is a separate pass. Its content is unchanged, so its August regulatory
clearance still stands; if any claim or IFU has moved since, it needs another
`regulatory-review` pass before going live.
