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
(uploaded to Easol), a YouTube short (`yt`, poster = YouTube's vertical thumbnail; the player only loads when the play
button is pressed, and a Watch video button appears in the hero) or a short clip (`video`, plays muted, `dur` seconds).
`hold` keeps a slide off the page (a private YouTube video shows "This video is private" to visitors).

Trips led never show how many people travelled (Oct 19 2026). Trips before 2023 come from
data/leaders/older-trips.json (HQ 2020-2022 tabs, GHL trip tags for Mantas, leaders' own lists); fix one there.

Saving the blocks: paste scripts/easol-deploy-helper.js into a signed-in Easol admin tab, then
`SYN.setPin('<commit>')` and `await SYN.deploy('trip-leaders/<key>', '<key>')` per page (it reuses the five named
blocks, adds missing ones, hides the squad page's own two blocks and saves the Inject code).

A new leader: add them to leaders.json, profiles.json and photos.json (squad photo), run
`python3 scripts/build-leaders.py` and `python3 scripts/render-leader-pages.py <key>`, then save the five
blocks and the Inject code on their squad page (leaders.json `page`).
