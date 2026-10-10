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

Elfsight is off surfyogabeer.com. Reviews and Instagram grids are ours on every published page that had them.
The WhatsApp button is ours too: Google Tag Manager version 38 paused the Elfsight "Whatsapp" tag and added
"SYB WhatsApp button (syb-widgets)" (All Pages) loading dist/syb-whatsapp.min.js at the pinned commit.
nicasurfcamp.com (GoHighLevel) runs the Instagram grid too (data-tag="nicaragua"). Elfsight auto-renewal was cancelled Oct 8 2026; the plan ends Oct 28 2026.
Since Oct 10 2026 the reviews come straight from Google (Business Profile API), so nothing here depends on Elfsight.

## Auto refresh

Pages load widget CODE pinned to a commit SHA and DATA from the main branch (`data-ref="main"` on the div), so a data
commit updates the site without touching Easol.

`scripts/refresh.py` does the refresh. It runs in GitHub Actions: `.github/workflows/refresh.yml`, every day at
10:12 UTC (6:12am New York in summer), no computer needed. A run with nothing new makes no commit.

- Keys: the job commits with its own GitHub token. Instagram is read through Composio, using one repo secret,
  `COMPOSIO_API_KEY` (Settings, Secrets and variables, Actions). It is the personal key from Composio's app
  (Settings, Sessions & API Key; it starts with `ck_`), which reaches the same connections Claude uses.
  Regenerating that key in Composio kills the old one, so update the secret if you ever do.
  Composio holds two Instagram connections; the job picks the one that answers as @surfyogabeer.
  Google reviews use two more secrets, `GOOGLE_CLIENT_SECRET` and `GOOGLE_REFRESH_TOKEN`: the OAuth client
  "SYB widgets daily refresh" in Google Cloud project syb-website-widgets (Google Auth Platform, user type
  Internal) and the one-time sign-in as mantas@surfyogabeer.com, done Oct 10 2026 in the OAuth Playground with
  scope business.manage. Revoking that sign-in, or deleting the client, stops the Google read; the log then
  says "Google sign-in failed" and the fix is the same one-time sign-in again.
  Instagram is read 10 posts per call: Composio Connect does not send back a larger answer (it saves it to
  a file on its side instead), which is what failed every run from Oct 8 to Oct 10 2026.
- Safety stop: a daily run that would delete more than 40 files stops without committing (a cut-short
  Instagram answer looks like mass deletion). Real clean-ups go through a "full" run.
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
  Source: the Google Business Profile API (access approved Oct 7 2026, case 7-4355000041774), straight from
  Google, every review on every run. The profile is found by its Maps place id, so no account ids live here.
  Reviews saved in the Elfsight era are matched to Google's by reviewer name and date, then by Google's id.
  If Google cannot be read, the run falls back to Elfsight's endpoint (until the plan ends Oct 28 2026) and
  logs `google_error`; after that date a Google failure means reviews stay as they are until it is fixed.
- jsDelivr caches @main for up to 12 hours; the script purges the changed JSON files after each commit.

To add a trip grid: add its words to DEST_WORDS and its name to GRIDS in scripts/refresh.py, then run
the workflow by hand with "full" ticked.

## Review photos

Google's photo links expire, so every photo is copied into dist/reviews/photos/ the first time it is seen.
On Oct 7 2026 only 156 of 631 Elfsight-era links still worked (42 reviews had photos). Google's API does send review
photos (reviewMediaItems: a thumbnail link; the same link ending in =s1200 gives the full picture), so new reviews
keep theirs, and older reviews that lost their photos get them back, 40 reviews per run (`reviews_photos_back`
in the log), until every one has been tried once (`g_media` on the review).

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
