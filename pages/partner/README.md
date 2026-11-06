# Team trip builder (surfyogabeer.com/partner)

The B2B page Sarah sends to companies. A company picks Nicaragua, then group size, dates, rooms, a food package,
an optional drinks upgrade and extras, and the paper quote on the right updates as they go. Or they pick Custom and
tell Sarah where, how many, how long and what they want (no price on the page; Sarah quotes it). "Send to Sarah"
builds a text package, copies it and offers an email to Sarah.

Live on Easol at /partner as one Embed Code block. sybtravel.com/partner forwards there.
Personalised link: `surfyogabeer.com/partner?for=F45+Toronto` shows "Prepared for F45 Toronto".

## Files

| Path | What |
|---|---|
| src/page.html | The whole page: CSS, markup and script. Edit this. |
| src/live-global.css | The few site-wide rules /partner needs (hides the dashed overview line; moves the WhatsApp pill aside while the phone total bar is up). |
| build/build.py | Builds everything from src/page.html. |
| build/photos.py | How each photo was cropped and where it came from (paths are from the build session). |
| img/ | The photos. No photo is used twice on the page. |
| live/partner.css, live/partner.js | What the live page loads from jsDelivr. |
| index.html | The same page as a standalone preview (also published as a Claude artifact). |

## Settings (top of the script in src/page.html)

- `CONTACT`: Sarah's email and phone. Still stand-ins (support@surfyogabeer.com and the SYB WhatsApp) until she has her own.
- `BASE` 1950, `MIN_PEOPLE` 8, `EXTRA_NIGHT` 250, `DEPOSIT` 0.2, `ROOMS` (shared max 25, twin +300 max 20, private +700 max 12).
- `FOOD`: pick one. `DRINKS`: optional upgrades, pick one or none (the villa open bar is already included).
- `ADDONS`: the extras, in the order they show; an extra with `img` gets a photo tile, one without gets its emoji.
  `qauto:"per6"` starts the amount at one per 6 people (side-by-sides).
- Custom: `CUSTOM_MAX_PEOPLE` 100, nights 2 to 14, `WANTS` = the chips on the Custom form.
- `PROPOSAL`: Sarah's starting package (14 people, Apr 12 2027, twin, deluxe BBQ, full bar, juice, massage, 2 work days, recap film = $38,210).

## Ship a change

jsDelivr will not serve files from this repo's main branch (the whole repo is over its 50 MB limit, so it answers
403 for some files). The live page therefore loads from a small branch, `partner-cdn`, that holds only
live/partner.css, live/partner.js and img/. Do not delete that branch.

    cd pages/partner
    python3 build/build.py            # index.html preview
    python3 build/build.py assets     # live/partner.css and live/partner.js
    # 1. commit and push to main (source of truth)
    # 2. copy live/partner.css, live/partner.js and img/ into a checkout of partner-cdn
    #    (same paths: pages/partner/...), commit, push, note that commit's SHA
    python3 build/build.py embed <partner-cdn SHA>   # live/embed.html, one line
    # 3. commit live/embed.html to main

Paste live/embed.html into the Embed Code block on the Easol /partner page and save. Every URL in it is pinned to
that partner-cdn commit, so the live page never changes until the block points at a new SHA, and rolling back is
pasting the previous embed.

Easol rules the embed already follows: one line, ASCII only, no HTML comments. All CSS is scoped to `#sybp` so the
theme and the page don't touch each other.

## Easol

Page "B2B - Team Trip Builder", slug `partner`, one Embed Code block (padding 0). Hidden from search engines.
