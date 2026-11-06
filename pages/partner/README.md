# Team trip builder (surfyogabeer.com/partner)

The B2B page Sarah sends to companies. A company picks group size, dates, rooms, a food package, a drinks package
and extras, and the paper quote on the right updates as they go. "Send to Sarah" builds a text package, copies it
and offers an email to Sarah.

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
- `FOOD`, `DRINKS`: the pick-one packages. `ADDONS`: the extras, in the order they show; an extra with `img` gets a photo tile, one without gets its emoji.
- `PROPOSAL`: Sarah's starting package (14 people, Apr 12 2027, twin, deluxe BBQ, full bar, juice, massage, 2 work days, recap film = $38,840).

## Ship a change

    cd pages/partner
    python3 build/build.py            # index.html preview
    python3 build/build.py assets     # live/partner.css and live/partner.js
    git add . && git commit && git push
    python3 build/build.py embed <SHA of that commit>   # live/embed.html, one line

Paste live/embed.html into the Embed Code block on the Easol /partner page and save. Every URL in it is pinned to
that commit, so the live page never changes until the block points at a new SHA, and rolling back is pasting the
previous embed.

Easol rules the embed already follows: one line, ASCII only, no HTML comments. All CSS is scoped to `#sybp` so the
theme and the page don't touch each other.
