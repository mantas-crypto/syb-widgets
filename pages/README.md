# Leader page blocks

Each leader page on Easol is five Embed Code blocks plus the page's Inject code, on the person's own squad page:
/trip-leaders/<name> for the trip leaders (Oct 16 2026), /management/<name> and /photographers/<name> for the team
and photographers (Oct 19 2026; Santiago's two squad pages and Bradford's /management page carry the same blocks).
These files are what goes in them. `@@NAME@@` marks a photo address or the pinned CSS/JS address,
filled in when the block is saved.

| File | Easol block | Notes |
|---|---|---|
| 1-hero.html | Leader page - Hero | loads the fonts and dist/leader/syb-leader.min.css; the story reel |
| 2-trips.html | Leader page - Upcoming trips | saved trip cards with photos; live spots and prices fill in after the page opens |
| 3-reviews.html | Leader page - Trip reviews | the big quote is fixed; the cards come from the data file |
| 4-about.html | Leader page - Meet the leader | Q&A, what they bring, trips led (by year, a flag per country, See all after 6) |
| 5-end.html | Leader page - End | |
| head.html | page Inject code | tracking, share button, loads dist/leader/syb-leader.min.js |

Live departures (spots left, sold out, price, link) are read after the page opens, in the background, from the
full calendar (/calendar prints every departure as an `article.sc-card` with data attributes), and kept for
15 minutes in the visitor's session. The leader pages print nothing from Easol themselves: Easol's
product_search Liquid made each page take 8 to 12 seconds to open (Oct 16 2026), so it was taken out.
`live-departures.liquid` is kept for a page that wants the list printed in place (the script reads a
`#syl-live` list on the page first); it is not used on the leader pages.

The cards, the hero line, trips led and review cards rewrite themselves from dist/leaders/<key>.json, so the
HTML here only matters if that file cannot load.

City chats: every leader's page links their city's SYB WhatsApp chat (`city_chats` in profiles.json, set per
leader with `chat`); a leader with no city chat gets an Instagram DM button instead.

## Every leader (pages/leaders/<key>/)

`scripts/render-leader-pages.py` writes the same five blocks plus the Inject code for every leader in
data/leaders/leaders.json, from data/leaders/profiles.json (name, city, Instagram, bio, Q&A, specialties;
`placeholder` marks words we made up until the leader sends their own), data/leaders/photos.json and
dist/leaders/<key>.json. Photo addresses are written in; `@@CSS@@` and `@@JS@@` are filled with the pinned
commit when the blocks are saved. pages/erin is the hand-made original those templates came from.

Per person, profiles.json can also set: `role` (the line above the name, default "SYB trip leader"), `leads: false`
(team members who do not lead trips: Travel with SYB), `lede` (a fixed line under the name that the script leaves alone),
`where` (the line under their title) and an empty `city`. photos.json squad[key].url can point at Easol's resized copy.

photos.json `reel` (Oct 19 2026) gives a leader their own story reel, in order: their squad photo, photos they sent
(uploaded to Easol) and videos. A video (`video` + `poster`, an mp4 in the Easol content library) plays by itself, muted,
with no play button (Mantas, Oct 19: "the video just plays"); its bar follows the video and the reel moves on when it
ends. `audio: true` adds a speaker button that turns the sound on (it stays on for the next video). A video that cannot
play (autoplay off, low power mode) becomes a normal timed slide. Encode them like the ones in Mantas's Drive folder
"Claude Docs/SurfYogaBeer Stuff/Leader page videos": 576x1024 H.264, CRF 27-28, maxrate about 800k, AAC 64k, faststart,
under 10 MB each. `yt` (a YouTube short behind a play button) still works but is no longer used.
`feature` puts their own landscape photo above their trip reviews. `hold` keeps a slide off the page.

Trips led never show how many people travelled (Oct 19 2026). Trips before 2023 come from
data/leaders/older-trips.json (HQ 2020-2022 tabs, GHL trip tags for Mantas, leaders' own lists, and what Mantas told
us: the first SYB trip was Costa Rica, Nov 2014); fix one there.

Saving the blocks: paste scripts/easol-deploy-helper.js into a signed-in Easol admin tab, then
`SYN.setPin('<commit>')` and `await SYN.deploy('trip-leaders/<key>', '<key>')` per page (it reuses the five named
blocks, adds missing ones, hides the squad page's own two blocks and saves the Inject code).

A new leader: add them to leaders.json, profiles.json and photos.json (squad photo), run
`python3 scripts/build-leaders.py` and `python3 scripts/render-leader-pages.py <key>`, then save the five
blocks and the Inject code on their squad page (leaders.json `page`). Then re-render and save the Leaders page
(below) so their face and card show up there too.

Headings print a space between their two lines (Oct 19 2026), so the text reads "Ryan Green." rather than
"RyanGreen." to search engines and screen readers. Pages saved before that pick it up with their next save.

## The Leaders page (/squad, pages/squad/)

"Leaders" in the site menu goes straight to /squad. The page is one Embed Code block, "Leaders page (live)"
(id 6779a804-7707-43e4-ba37-d9ad41ec5c8b), plus the page's Inject code. The page's own two blocks
("[Custom] Text - Centered" and "[Custom] Tabbed Image and Text Grid") are hidden, not deleted: show them and hide
the new block to go back.

`scripts/render-squad.py` writes pages/squad/1-leaders.html (the block), pages/squad/head.html (the Inject code,
loads dist/leader/syb-squad.min.js), data/leaders/squad-static.json and dist/leaders/squad.json. `@@CSS@@`,
`@@SQCSS@@` (dist/leader/syb-leader.min.css, syb-squad.min.css) and `@@SQJS@@` are filled with the pinned commit when
the block is saved.

- The wall of faces: each face plays that leader's story, the slides of their own page's reel (up to 8), so render
  their leader page first. Seen faces turn grey (kept in the visitor's browser).
- Filters: everyone, leading soon, photographers, SYB HQ, and one per country they have led or are leading.
- A card per leader links to their page, with "On a trip now" or the next departure, and trips led.
- People with `leads: false` (Sara, Danielle) get a card at the end of the grid with "SYB HQ" under their job, and
  show under the SYB HQ filter (Mantas, Oct 19 2026: no separate "crew behind the crew" section). They have no face
  in the wall and are not in the leader count. Cards carry `data-tags`, so SYB HQ and Photographers filter even
  before the live data loads. profiles.json `squad_label` overrides the line under a name (Bradford: Training director).
- `npm run squad` copies and minifies src/syb-squad.js and src/syb-squad.css into dist/leader/.
- dist/leaders/squad.json is rebuilt by the twice-daily job (build-leaders.py, `write_squad`); the page re-sorts
  from it: Mantas first, then the next departure soonest, then most trips led.

Saving: with the deploy helper loaded, fetch pages/squad/1-leaders.html from raw.githubusercontent.com at the commit,
fill the three placeholders, `SYN.saveEmbed('6779a804-7707-43e4-ba37-d9ad41ec5c8b', html)`, and
`SYN.saveHead('squad', html)` for the Inject code.

The menu (Oct 19 2026): Site > Header has a group LEADERS with one item, "Leaders" (page /squad). The Header
template prints a group with exactly one link as a plain link with no dropdown. Give the group a second item and
it becomes a dropdown again. Save Site > Header only the safe way (claude/menu-photo-fix-oct-5-2026.md).
