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
HTML here only matters if that file cannot load. A new leader: copy pages/erin, change the words, photos
and `data-leader`, add them to data/leaders/leaders.json.
