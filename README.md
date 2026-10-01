# SYB widgets (Elfsight replacement)

Built Sep 28 2026. Replaces the Elfsight widgets that are live on surfyogabeer.com.

## What Elfsight is doing for us today

Plan: All Apps Premium Pack, $72 a month ($864 a year), next charge Oct 28 2026.
Account has about 95 widgets across 18 apps. Only these are on a public page:

| Widget | Where | Replacement |
|---|---|---|
| WhatsApp Chat | every page except the exclusion list | src/syb-whatsapp.js (built) |
| Google Reviews | homepage, /newbie, /morocco, /croatia, /bali, /egypt, /nicaragua/classic, /philippines | src/syb-reviews.js (built) |
| Instagram Feed (hashtag) | /morocco, /croatia, /bali, /egypt, /nicaragua/classic, /philippines, nicasurfcamp.com | Cursor prompt 3 |
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

To ship a change: edit src/, run `npm run build`, commit, push, then put the new commit SHA in the Easol blocks. Old SHAs keep working forever, so rolling back is just pointing a block at the previous SHA.

Loading: each widget renders when it scrolls near (IntersectionObserver), with a scroll/resize check as backup and a forced render 4 seconds after page load, so it can never stay blank.

## Test page

surfyogabeer.com/ibiza (Ibiza-ly Does It, Aug 15-21 2028, waitlist only) is the first page running these widgets.

surfyogabeer.com/belize runs the Instagram grid (data-tag="sybbelize", added Oct 1 2026). Its 29 tiles are hand-picked #SYBBelize and #SYBelize posts (2017 to 2026), all Belize, none repeating a photo already on the page. Its Google reviews were never on Elfsight.

## Embed snippets

Reviews, one per trip page (swap the trip name):

    <div class="syb-reviews" data-trip="morocco"></div>
    <script src="https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@<SHA>/dist/syb-reviews.min.js" defer></script>

Trip names with a review file: ibiza, morocco, croatia, bali, egypt, nicaragua, nye, philippines, iceland, kenya, amalfi, dolomites, turkey, japan, belize, chamonix, greece, riviera. No data-trip = the 40 newest reviews with photos (homepage).

Instagram grid, one per trip page (the file lists the posts and their photos, which live in the repo):

    <div class="syb-instagram" data-tag="sybibiza"></div>
    <script src="https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@<SHA>/dist/syb-instagram.min.js" defer></script>

WhatsApp, once in Easol head HTML (sitewide):

    <script src="https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@<SHA>/dist/syb-whatsapp.min.js" defer></script>

## Rebuild the review files

    python3 scripts/build-reviews.py
