# Cursor prompts for SYB widgets

Open the `elfsight-replacement` folder in Cursor, then paste Prompt 1 into Cursor chat (Agent mode).
Prompts 2 to 4 are for later, one at a time.

---

## Prompt 1: ship the two widgets that are already built

```
This folder replaces Elfsight widgets on surfyogabeer.com (an Easol-hosted site; we can only paste HTML/script into Easol blocks, there is no server on our side).

What is already here:
- src/syb-reviews.js: Google Reviews carousel. Vanilla JS, Shadow DOM, no dependencies. Embed = <div class="syb-reviews" data-trip="morocco"></div> + <script src=".../syb-reviews.js" defer>. It loads reviews/<trip>.json from the same folder as the script.
- src/syb-whatsapp.js: floating WhatsApp button + chat card, sitewide, with a page exclusion list.
- data/google-reviews.json: all 315 of our Google reviews (export taken Sep 28 2026).
- scripts/build-reviews.py: turns that export into dist/reviews/<trip>.json files (5-star only, keyword-matched per trip, max 40 each).

Do this:
1. Make it a proper repo: git init, .gitignore, package.json with scripts:
   - "build": run scripts/build-reviews.py, then copy src/*.js to dist/ and minify each to dist/*.min.js with terser.
   - "dev": serve the project root on localhost:5173 (use "serve" or "http-server").
2. Add demo/index.html: a dark page (#0D0D0D background, Montserrat from Google Fonts) that shows the reviews widget three times (data-trip="morocco", data-trip="croatia", and the default all.json with no data-trip) and loads the WhatsApp button. Point the scripts at ../dist/. Add a small form at the top of the page to switch the trip, so I can check every trip file quickly.
3. Add vercel.json so Vercel serves dist/ as static files with:
   - Access-Control-Allow-Origin: * on /reviews/*.json
   - Cache-Control: public, max-age=3600, stale-while-revalidate=86400 on everything in dist
4. Review both widgets for bugs and accessibility (keyboard, focus, screen reader labels, reduced motion). Keep them dependency-free and under 15 KB minified each. Do not add a framework.
5. Test in the browser at 375px, 768px and 1280px widths. Check: the carousel arrows page correctly, "Read more" only shows when text is clipped, photos open in the lightbox, the WhatsApp card opens and closes (Escape key too), and the WhatsApp button is hidden on the paths in its exclusion list.
6. Write a short README section "How to put this on a page in Easol" with the exact snippet for each trip, using the final Vercel URL.
7. Help me create the GitHub repo (private is fine) and deploy to Vercel. Tell me the production URL at the end.

Rules: plain vanilla JS (ES2018 is fine), no build step inside the widgets, no cookies, no tracking beyond the existing gtag/dataLayer/fbq calls in syb-whatsapp.js.
```

---

## Prompt 2: keep Google reviews fresh without Elfsight

```
Right now dist/reviews/*.json is built from a one-off export (data/google-reviews.json). Once we cancel Elfsight, new Google reviews stop flowing in.

Add a Vercel Cron job (daily) that pulls all reviews for our Google Business Profile and rewrites the review files:
- Use the Google Business Profile API (mybusiness v4 accounts.locations.reviews.list), with an OAuth refresh token stored in Vercel env vars (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, GBP_ACCOUNT_ID, GBP_LOCATION_ID).
- Store the output in Vercel Blob (or KV) and serve it from /reviews/<trip>.json through a serverless route, falling back to the static files in dist/reviews if the API fails.
- Reuse the same trip keyword map and filtering rules as scripts/build-reviews.py (move that map into one shared JSON file so both use it).
- Add a one-time script that walks me through getting the refresh token (local OAuth consent flow on localhost).
- Walk me through requesting Business Profile API access from Google. It needs an approved Google Cloud project, and approval can take a few days.
```

---

## Prompt 3: Instagram feed (replaces the Elfsight hashtag feeds on 6 trip pages and nicasurfcamp.com)

```
Build src/syb-instagram.js, same style as syb-reviews.js (vanilla JS, Shadow DOM, lazy-loaded, dark theme).
Embed: <div class="syb-instagram" data-tag="sybmorocco"></div>

Data: a Vercel serverless route /api/instagram?tag=sybmorocco that
- calls the Instagram Graph API for our Business account (@surfyogabeer) and returns our own recent media whose caption contains that hashtag (media_url, thumbnail_url for videos, permalink, caption, timestamp), max 24;
- caches the result for 6 hours (Vercel KV or Blob);
- uses a long-lived token from env (IG_USER_ID, IG_ACCESS_TOKEN) and includes a cron that refreshes the token before it expires.

Layout: 2 rows of square tiles that scroll sideways (6 across on desktop, 3 on mobile), video tiles get a small play icon, clicking opens the post on Instagram. Add a "Follow @surfyogabeer" link at the end.
Note: guest posts from other accounts with the hashtag need Meta's Public Content Access review, so version 1 shows only our own posts. Tell me if you think it is worth applying for.
```

---

## Prompt 4: the /book-it page widgets (stats counter, testimonial slider, photo gallery)

```
Build three small widgets in the same style as the others:
- src/syb-counter.js: animated number counters (count up when scrolled into view, respect reduced motion). Config via data attributes: data-items='[{"value":12,"label":"years of trips"},{"value":16,"label":"destinations"}]'
- src/syb-testimonials.js: one-at-a-time testimonial slider with photo, quote, name and trip. Reads an inline JSON <script type="application/json"> inside the div.
- src/syb-gallery.js: responsive photo grid with a lightbox (arrow keys and swipe). Reads image URLs from an inline JSON block.
Add all three to demo/index.html.
```
