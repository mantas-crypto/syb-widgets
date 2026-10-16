# Leader page blocks

Each leader page on Easol (/trip-leaders/<name>) is five Embed Code blocks plus the page's Inject code.
These files are what goes in them. `@@NAME@@` marks a photo address or the pinned CSS/JS address,
filled in when the block is saved.

| File | Easol block | Notes |
|---|---|---|
| 1-hero.html | Leader page - Hero | loads the fonts and dist/leader/syb-leader.min.css; the story reel |
| 2-trips.html | Leader page - Upcoming trips | its Liquid also gets live-departures.liquid (see below) |
| 3-reviews.html | Leader page - Trip reviews | the big quote is fixed; the cards come from the data file |
| 4-about.html | Leader page - Meet the leader | Q&A, what they bring, trips led |
| 5-end.html | Leader page - End | |
| head.html | page Inject code | tracking, share button, loads dist/leader/syb-leader.min.js |

`live-departures.liquid` is appended to the trips block's Liquid (not its embed code). Easol prints every
upcoming departure with spots left, sold out, price and photo on each visit; the script picks this
leader's trips from it. Without it the script reads the same list from /leader-live-data.

The cards, the hero line, trips led and review cards rewrite themselves from dist/leaders/<key>.json, so the
HTML here only matters if that file cannot load. 
## Every leader (pages/leaders/<key>/)

`scripts/render-leader-pages.py` writes the same five blocks plus the Inject code for every leader in
data/leaders/leaders.json, from data/leaders/profiles.json (name, city, Instagram, bio, Q&A, specialties;
`placeholder` marks words we made up until the leader sends their own), data/leaders/photos.json and
dist/leaders/<key>.json. Photo addresses are written in; `@@CSS@@` and `@@JS@@` are filled with the pinned
commit when the blocks are saved. pages/erin is the hand-made original those templates came from.

A new leader: add them to leaders.json, profiles.json and photos.json (squad photo), run
`python3 scripts/build-leaders.py` and `python3 scripts/render-leader-pages.py <key>`, then save the five
blocks and the Inject code on their /trip-leaders/<key> page.
