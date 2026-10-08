# SYB widgets (Elfsight replacement)

Built Sep 28 2026. Replaces the Elfsight widgets that are live on surfyogabeer.com.

## What Elfsight is doing for us today

Plan: All Apps Premium Pack, $72 a month ($864 a year), next charge Oct 28 2026.
Account has about 95 widgets across 18 apps. Only these are on a public page:

| Widget | Where | Replacement |
|---|---|---|
| WhatsApp Chat | every page except the exclusion list | src/syb-whatsapp.js (built) |
| Google Reviews | homepage, /newbie, /morocco, /croatia, /bali, /belize, /egypt, /nicaragua/classic, /philippines | src/syb-reviews.js (built) |
| Instagram Feed (hashtag) | /morocco, /croatia, /bali, /egypt, /nicaragua/classic, /philippines, nicasurfcamp.com (/belize swapped Oct 1 2026) | Cursor prompt 3 |
| Testimonials Slider, Photo Gallery, Number Counter | /book-it | Cursor prompt 4 |
| (one dead widget id, status 0) | /book-it | delete |

Everything else in the Elfsight account (popups, timelines, banners, countdowns, contact forms, AI chatbot, maps, logo showcase and so on) is not on any page in the sitemap.
Password-protected guide pages were not scanned; check them before cancelling.

## Where it is hosted

Public repo github.com/mantas-crypto/syb-widgets, served by jsDelivr and pinned to a commit SHA, so a page never changes unless we point it at a new commit.
(Tags could not be pushed from the build session. If you create a release like v1.0.0 on GitHub, you can swap the SHA for the tag.)

    https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@<SHA>/dist/syb-reviews.min.js
    https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@<SHA>/dist/syb-instagram.min.js
    https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@<SHA>/dist/syb-whatsapp.min.js

To ship a CODE change: edit src/, run `npm run build`, commit, push, then put the new commit SHA in the Easol blocks. Data changes need no Easol edit (see Auto refresh). Old SHAs keep working forever, so rolling back is just pointing a block at the previous SHA.

Loading: each widget renders when it scrolls near (IntersectionObserver), with a scroll/resize check as backup and a forced render 4 seconds after page load, so it can never stay blank.

## Test page

surfyogabeer.com/ibiza (Ibiza-ly Does It, Aug 15-21 2028, waitlist only) is the first page running these widgets.

surfyogabeer.com/belize runs the Instagram grid (data-tag="sybbelize", added Oct 1 2026). Its 29 tiles are hand-picked #SYBBelize and #SYBelize posts (2017 to 2026), all Belize, none repeating a photo already on the page. Belize's Google reviews block is still Elfsight on purpose (see below).

## Status (Oct 8 2026)

Elfsight is off every published page except the sitewide WhatsApp button, which lives in Google Tag Manager
(tag "Whatsapp"), not in Easol. Swapped pages: homepage, /newbie, /testimonials, /morocco, /croatia, /bali, /egypt,
/philippines, /nicaragua/classic, /nicaragua/surf-camp, /nicaragua/reset-recharge, /nicaragua/nye, /france/chamonix,
/turkey, /japan, /kenya, /iceland, /iceland-north, /amalfi, /dolomites, /belize, /ibiza, /book-it.
Full live re-check on Oct 8: all pages pass on desktop and at phone width.

## Auto refresh

Pages load widget CODE pinned to a commit SHA and DATA from the main branch (`data-ref="main"` on the div), so a data
commit updates the site without touching Easol.

`scripts/refresh.py` does the refresh. It runs in GitHub Actions: `.github/workflows/refresh.yml`, every day at
10:12 UTC (6:12am New York in summer), no computer needed. A run with nothing new makes no commit.

- Keys: the job commits with its own GitHub token. Instagram is read through Composio, using one repo secret,
  `COMPOSIO_API_KEY` (Settings, Secrets and variables, Actions). Nothing secret is written in this repo.
  If Composio ever holds more than one Instagram connection, put the right one's id in the repo variable
  `COMPOSIO_IG_ACCOUNT`.
- Run it by hand: Actions, "Widgets data refresh", Run workflow. Tick "dry" to test without committing.
- GitHub's own schedule can run hours late or skip a day, so a Claude cloud scheduled task also starts the job each
  morning and checks that it ran. Two runs on one day are harmless: the second finds nothing new.
- A failed run means the site keeps yesterday's data; nothing breaks.
- The script can still be run by hand in the Composio workbench (see the top of scripts/refresh.py).

- Instagram: our own @surfyogabeer posts, matched to a trip by caption words. A post lands on a trip grid only when
  its caption names that one destination, and never twice with the same caption or the same picture. Newest 24 per
  trip. Images are copied to dist/instagram/p/ because Instagram's own links expire.
- Reviews: merged into data/google-reviews.json, guest photos copied to dist/reviews/photos/ while Google's links
  still work (they die within days), per-trip files rebuilt by scripts/build-reviews.py.
  Source today: Elfsight's public endpoint, which stops when Elfsight is cancelled.
  Source later: Google Business Profile API (access request case 7-4355000041774, project syb-website-widgets).
  Until that lands, reviews stay as the last snapshot after the cancel.
- jsDelivr caches @main for up to 12 hours; the script purges the changed JSON files after each commit.

To add a trip grid: add its words to DEST_WORDS and its name to GRIDS in scripts/refresh.py, then run
the workflow by hand with "full" ticked.

## Known gap: review photos

Google's photo links expire. On Oct 7 2026, 156 of 631 were still alive and are saved in dist/reviews/photos/
(42 reviews have photos); the rest are gone for good. Elfsight only ever kept tiny cached copies. Google's official
API returns no review photos at all, so new photos are only caught while the Elfsight endpoint still answers.

## Embed snippets

Reviews, one per trip page (swap the trip name):

    <div class="syb-reviews" data-trip="morocco" data-ref="main"></div>
    <script src="https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@<SHA>/dist/syb-reviews.min.js" defer></script>

Trip names with a review file: ibiza, morocco, croatia, bali, egypt, nicaragua, nye, philippines, iceland, kenya, amalfi, dolomites, turkey, japan, belize, chamonix, greece, riviera. No data-trip = the 40 newest reviews with photos (homepage).

Instagram grid, one per trip page (the file lists the posts and their photos, which live in the repo):

    <div class="syb-instagram" data-tag="morocco" data-ref="main"></div>
    <script src="https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@<SHA>/dist/syb-instagram.min.js" defer></script>

WhatsApp, once in Easol head HTML (sitewide):

    <script src="https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@<SHA>/dist/syb-whatsapp.min.js" defer></script>

## Rebuild the review files

    python3 scripts/build-reviews.py
