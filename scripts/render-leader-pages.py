#!/usr/bin/env python3
"""
Leader pages: writes the five Easol blocks and the Inject code for every leader into pages/leaders/<key>/.

    python3 scripts/render-leader-pages.py            # all leaders
    python3 scripts/render-leader-pages.py erin nikki # some

Reads data/leaders/leaders.json (who), data/leaders/profiles.json (what the page says), data/leaders/photos.json
(which photos) and dist/leaders/<key>.json (trips, trips led, reviews; rebuilt twice a day by build-leaders.py).
The saved blocks are the page as of today; syb-leader.js keeps trips, trips led, the hero line and reviews current
on every visit, so the blocks only need saving again when the words or photos change.

@@CSS@@ and @@JS@@ are filled in when the blocks are saved (dist/leader/ pinned to a commit on jsDelivr).
"""
import base64, datetime, html, json, os, re, sys
from zoneinfo import ZoneInfo

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data", "leaders")
OUT = os.path.join(ROOT, "pages", "leaders")
SITE = "https://www.surfyogabeer.com"
MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
MONTH = "January February March April May June July August September October November December".split()
TODAY = datetime.datetime.now(ZoneInfo("America/New_York")).date()

# HQ trip tag -> trip pages whose photos fit it (photos.json pool)
POOL_PAGES = {
    "Nicaragua": ["/nicaragua/classic", "/nicaragua/surf-camp", "/nicaragua/nye", "/nicaragua/reset-recharge"],
    "Croatia": ["/croatia"], "Bali": ["/bali"], "Egypt": ["/egypt"], "French Alps": ["/chamonix"],
    "Morocco": ["/morocco"], "Amalfi": ["/amalfi"], "Iceland": ["/iceland"], "Dolomites": ["/dolomites"],
    "Palawan": ["/philippines"], "Belize": ["/belize"], "Kenya": ["/kenya"], "Côte d’Azur": ["/south-of-france"],
    "Greece": ["/greece"], "Zermatt": ["/switzerland"], "Turkey": ["/turkey"], "Japan": ["/japan"],
    "Guatemala": ["/guatemala"], "Lapland": ["/finland"],
}
CAPTION = {
    "Nicaragua": "Nicaragua", "Croatia": "Croatia", "Bali": "Bali, Indonesia", "Egypt": "Egypt",
    "French Alps": "Chamonix, French Alps", "Morocco": "Morocco", "Amalfi": "Amalfi Coast, Italy", "Iceland": "Iceland",
    "Dolomites": "Dolomites, Italy", "Palawan": "Palawan, Philippines", "Belize": "Belize", "Kenya": "Kenya",
    "Côte d’Azur": "South of France", "Greece": "Greece", "Zermatt": "Zermatt, Switzerland", "Turkey": "Turkey",
    "Japan": "Japan", "Guatemala": "Guatemala", "Lapland": "Finnish Lapland",
}
# Leaders whose squad bio says they graduated from (or led) the SYB Academy
ACADEMY = {"erin", "sarahcat", "courtney", "jenny", "lauren", "lizzie", "sav", "nikki", "jill", "juliana", "sarah"}
GENERAL_PHOTOS = ["Nicaragua", "Croatia", "Bali"]   # for a leader with no trips on record yet

ICON_PIN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>'
ICON_IG = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r=".6"/></svg>'
ICON_WA = '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M16.04 3C8.86 3 3.03 8.8 3.03 15.95c0 2.29.6 4.52 1.75 6.49L3 29l6.73-1.76a13.07 13.07 0 0 0 6.3 1.6h.01c7.17 0 13-5.8 13-12.94C29.04 8.8 23.21 3 16.04 3Zm0 23.67h-.01c-1.94 0-3.85-.52-5.51-1.51l-.4-.23-4 1.04 1.07-3.88-.26-.4a10.7 10.7 0 0 1-1.65-5.74c0-5.94 4.85-10.77 10.8-10.77 2.88 0 5.59 1.12 7.63 3.16a10.68 10.68 0 0 1 3.16 7.62c0 5.94-4.85 10.71-10.83 10.71Zm5.92-8.03c-.33-.16-1.93-.95-2.23-1.06-.3-.11-.52-.16-.73.16-.22.33-.84 1.06-1.03 1.27-.19.22-.38.24-.7.08-.33-.16-1.38-.51-2.62-1.61a9.8 9.8 0 0 1-1.82-2.25c-.19-.33-.02-.5.14-.66.15-.15.33-.38.49-.57.16-.19.22-.33.33-.54.11-.22.05-.41-.03-.57-.08-.16-.73-1.76-1-2.41-.27-.63-.54-.55-.73-.56h-.62c-.22 0-.57.08-.87.41-.3.33-1.14 1.11-1.14 2.71s1.17 3.15 1.33 3.36c.16.22 2.3 3.5 5.57 4.91.78.33 1.39.53 1.86.68.78.25 1.5.21 2.06.13.63-.09 1.93-.79 2.2-1.55.27-.76.27-1.41.19-1.55-.08-.13-.3-.21-.62-.37Z"/></svg>'
ICON_PAUSE = '<svg class="is-pause" viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg><svg class="is-play" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z"/></svg>'


def load(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except FileNotFoundError:
        return d


def e(s):
    return html.escape(str(s), quote=False).replace('"', "&quot;")


def day(s):
    return datetime.date.fromisoformat(s[:10])


def slug(s):
    s = re.sub(r"[‘’]", "'", s.lower())
    s = s.replace("ô", "o").replace("é", "e").replace("’", "'")
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", s))


def poss(first):
    return first + "’s"


def blob_url(p):
    sig = base64.b64encode(('{"_rails":{"data":"%s","pur":"blob_id"}}' % p["uuid"]).encode()).decode()
    from urllib.parse import quote
    return "https://static.myeasol.net/rails/active_storage/blobs/proxy/%s--%s/%s" % (sig, p["hex"], quote(p["name"]))


def holiday(s, en):
    y = s.year
    nov1 = datetime.date(y, 11, 1)
    thx = nov1 + datetime.timedelta(days=((3 - nov1.weekday()) % 7) + 21)
    if s <= thx <= en:
        return "Thanksgiving week"
    if s <= datetime.date(y, 12, 31) <= en:
        return "New Year’s Eve"
    return ""


def rng(s, en):
    a = "%s %d" % (MON[s.month - 1], s.day)
    if en == s:
        return a
    return a + " to " + ("" if en.month == s.month else MON[en.month - 1] + " ") + str(en.day)


def mark(text, names):
    t = e(text)
    if not names:
        return t
    alt = "|".join(re.escape(e(n)) for n in names)
    return re.sub(r"(^|[^\w])(%s)(?![\w])" % alt, r'\1<span class="syl-hl">\2</span>', t)


def hl_names(first, aliases):
    names = [first] + list(aliases or [])
    if " " in first:
        names.append(first.split()[0])
    out = []
    for n in names:
        if n and n not in out:
            out.append(n)
    return sorted(out, key=len, reverse=True)


# ---------- photos ----------
class Photos:
    def __init__(self, doc):
        self.doc = doc
        self.pool = doc["pool"]
        self.used = {}           # uuid -> times used across pages (spread them around)

    def pick(self, tag, taken, portrait=True):
        pages = POOL_PAGES.get(tag, [])
        cands = [p for p in self.pool if p["page"] in pages and p["uuid"] not in taken]
        if not cands:
            return None
        order = {pg: i for i, pg in enumerate(pages)}
        rank = {id(p): i for i, p in enumerate(cands)}
        cands.sort(key=lambda p: (self.used.get(p["uuid"], 0), (not p["portrait"]) if portrait else p["portrait"],
                                  order.get(p["page"], 9), rank[id(p)]))
        p = cands[0]
        self.used[p["uuid"]] = self.used.get(p["uuid"], 0) + 1
        taken.add(p["uuid"])
        return p


def leader_tags(data):
    tags = []
    for o in [u for u in data["upcoming"] if u.get("kind") == "trip"] + data["led"]:
        if o["tag"] in POOL_PAGES and o["tag"] not in tags:
            tags.append(o["tag"])
    return tags


def plan_photos(key, prof, data, ph):
    """reel: [(url, caption, alt, pos)], about: (url, alt) or None, feature: (url, alt) or None"""
    first = prof["first"]
    taken = set()
    if key == "erin":
        E = ph.doc["erin"]
        reel = [
            (blob_url(E["reel-1"]), "Hi, I’m Erin.", "Erin MacLeod in an SYB tank top, standing on a quad bike above the sea", "50% 35%"),
            (blob_url(E["reel-2"]), "Shellona day, Saint-Tropez", "Erin’s Côte d’Azur crew raising their glasses at Shellona beach club", "50% 35%"),
            (blob_url(E["reel-3"]), "Morning yoga, Côte d’Azur", "Morning yoga on the harbor during Erin’s Côte d’Azur trip", "50% 35%"),
            (blob_url(E["reel-4"]), "Nicaragua, 2025", "Erin on the beach in Nicaragua with a pink surfboard", "50% 35%"),
            (blob_url(E["reel-5"]), "Her Côte d’Azur crew, July 2026", "A selfie of Erin’s Côte d’Azur crew at the beach club", "50% 35%"),
            (blob_url(E["reel-6"]), "Lavender fields, July 2026", "Erin’s crew in a lavender field in Provence", "50% 35%"),
        ]
        about = (blob_url(ph.doc["about"]["erin"]), "Erin MacLeod smiling on a beach at golden hour")
        feature = (blob_url(E["shellona"]), "Erin’s Côte d’Azur crew at one long table at Shellona beach club, Saint-Tropez")
        return reel, about, feature
    sq = ph.doc["squad"][key]
    pos = "50% 30%" if sq.get("h", 1) >= sq.get("w", 1) else "50% 40%"
    reel = [(blob_url(sq), "Hi, I’m %s." % first, "%s, SYB trip leader" % prof["name"], pos)]
    if key == "alex":
        a2 = ph.doc["about"]["alex-ski"]
        reel.append((blob_url(a2), "Ski week, French Alps", "Alex Marks in an SYB ski bib and a penguin helmet", "50% 30%"))
    tags = leader_tags(data)
    general = not tags
    if general:
        tags = GENERAL_PHOTOS
    want = 6 - len(reel)
    i = 0
    while len(reel) < 1 + want and i < 30 and tags:
        tag = tags[i % len(tags)]
        p = ph.pick(tag, taken, portrait=True)
        i += 1
        if not p:
            continue
        cap = ("SYB in " if general else "") + CAPTION.get(tag, tag)
        reel.append((blob_url(p), cap, "SYB trip photo, %s" % CAPTION.get(tag, tag), "50% 40%"))
    about = None
    if key in ph.doc["about"] and key != "alex-ski":
        about = (blob_url(ph.doc["about"][key]), "%s on an SYB trip" % prof["name"])
    feature = None
    if data.get("reviews"):
        ftag = data["reviews"][0].get("tag")
        for tag in ([ftag] if ftag in POOL_PAGES else []) + tags:
            p = ph.pick(tag, taken, portrait=False)
            if p and not p["portrait"]:
                feature = (blob_url(p), "SYB trip photo, %s" % CAPTION.get(tag, tag))
                break
    return reel, about, feature


# ---------- blocks ----------
def lede(data):
    first = data["first"]
    led = [o for o in data["led"]]
    trav = sum(o.get("travelers", 0) for o in led)
    up = [u for u in data["upcoming"] if u.get("kind") == "trip" and day(u["end"]) >= TODAY]
    out = []
    if led:
        out.append("%s has led <b>%d SYB %s</b>%s." % (e(first), len(led), "trip" if len(led) == 1 else "trips",
                                                      (" and <b>%d travelers</b>" % trav) if trav else ""))
    else:
        out.append("%s leads active and social group trips for SYB." % e(first))
    if up:
        nx = up[0]
        n = (day(nx["start"]) - TODAY).days
        if n < 0:
            out.append("Right now: <b>%s</b>, with a crew." % e(nx["tag"]))
        else:
            when = "leaving today" if n == 0 else "leaving tomorrow" if n == 1 else ("leaving in %d days" % n) if n <= 45 \
                else "%s %d" % (MONTH[day(nx["start"]).month - 1], day(nx["start"]).year)
            out.append("Next up: <b>%s</b>, %s." % (e(nx["tag"]), when))
    return " ".join(out)


def chat_row(prof, nyc, where):
    if prof["chat"] == "nyc":
        return ('<a class="syl-chat" data-syl="whatsapp-nyc-%s" href="%s" target="_blank" rel="noopener"><span class="syl-chat-ic">%s</span>'
                '<span class="syl-chat-t">Join me in the SYB New York City chat</span><span class="syl-chat-go">Join</span></a>') % (where, e(nyc), ICON_WA)
    return ('<a class="syl-chat" data-syl="instagram-dm-%s" href="https://ig.me/m/%s" target="_blank" rel="noopener"><span class="syl-chat-ic is-ig">%s</span>'
            '<span class="syl-chat-t">Questions about a trip? Message me on Instagram</span><span class="syl-chat-go">Message</span></a>') % (where, e(prof["ig"]), ICON_IG)


def hero(key, prof, data, reel, nyc):
    first = prof["first"]
    n = len(reel)
    slides = []
    for i, (url, cap, alt, pos) in enumerate(reel):
        if i == 0:
            slides.append('<figure class="syl-slide is-on" data-cap="%s"><img src="%s" alt="%s" fetchpriority="high" style="--pos:%s"></figure>' % (e(cap), e(url), e(alt), pos))
        else:
            slides.append('<figure class="syl-slide" data-cap="%s" aria-hidden="true"><img data-src="%s" alt="%s" style="--pos:%s"></figure>' % (e(cap), e(url), e(alt), pos))
    up = [u for u in data["upcoming"] if u.get("kind") == "trip" and day(u["end"]) >= TODAY]
    btn = ("See %s trips" % poss(first)) if up else "See upcoming trips"
    return "\n".join([
        '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&display=swap" rel="stylesheet"><link rel="stylesheet" href="@@CSS@@">',
        '<section class="syl syl-hero" id="syl-hero" data-leader="%s">' % key,
        '<div class="syl-hero-grid">',
        '<div class="syl-reel" data-reel role="region" aria-roledescription="carousel" aria-label="%s in action, %d photos" tabindex="0">' % (e(first), n),
        '<div class="syl-bars" aria-hidden="true">%s</div>' % ("<i><b></b></i>" * n),
        '<p class="syl-cap" aria-live="polite">%s</p>' % e(reel[0][1]),
        "\n".join(slides),
        '<button class="syl-tap syl-tap-prev" type="button" aria-label="Previous photo"></button>',
        '<button class="syl-tap syl-tap-next" type="button" aria-label="Next photo"></button>',
        '<button class="syl-pause" type="button" aria-label="Pause the photos">%s</button>' % ICON_PAUSE,
        '</div>',
        '<div class="syl-hero-copy">',
        '<p class="syl-role">SYB trip leader</p>',
        '<h1 class="syl-name"><span>%s</span><span class="syl-g">%s</span></h1>' % (e(prof["h1"][0]), e(prof["h1"][1])),
        '<div class="syl-home">',
        '<div class="syl-home-top">',
        '<span class="syl-city">%s%s</span>' % (ICON_PIN, e(prof["city"])),
        '<a class="syl-ig" data-syl="instagram-hero" href="https://www.instagram.com/%s" target="_blank" rel="noopener">%s@%s</a>' % (e(prof["ig"]), ICON_IG, e(prof["ig"])),
        '</div>',
        chat_row(prof, nyc, "hero"),
        '</div>',
        '<p class="syl-lede" data-lede>%s</p>' % lede(data),
        '<div class="syl-actions">',
        '<a class="syl-btn" data-syl="hero-trips" href="#syl-trips">%s</a>' % e(btn),
        '<button class="syl-btn syl-btn-ghost" type="button" data-syl="share-hero" data-share>Share</button>',
        '</div>',
        '</div>',
        '</div>',
        '</section>',
    ])


def poster(u):
    s, en = day(u["start"]), day(u["end"])
    hol = holiday(s, en)
    where = (u.get("place") or "") + ((", " + hol) if hol and u.get("place") else (hol or ""))
    return ('<a class="syl-poster" data-name="%s" data-start="%s" data-end="%s" data-syl="trip-%s-%s" href="%s">'
            '<span class="syl-poster-top"><span></span></span><span class="syl-poster-body"><span class="syl-date">%s %d<i>%d</i></span>'
            '<span class="syl-trip">%s</span><span class="syl-place">%s%s</span><span class="syl-poster-foot"><span class="syl-price"></span>'
            '<span class="syl-cta">See the trip</span></span></span></a>') % (
        e(u["trip"]), u["start"], u["end"], slug(u.get("tag") or u.get("place") or u["trip"]), u["start"], e(u.get("page") or "/calendar"),
        MON[s.month - 1], s.day, s.year, e(u["trip"]), (e(where) + ". ") if where else "", rng(s, en))


def trips(key, prof, data):
    first = prof["first"]
    up = [u for u in data["upcoming"] if day(u["end"]) >= TODAY]
    general = not up
    head = '<h2 class="syl-h" data-trips-h><span>Travel</span><span class="syl-g">with %s.</span></h2>' % e("SYB" if general else first)
    sub = '<p class="syl-trips-sub" data-trips-sub%s>%s isn’t on a trip right now. Here’s where SYB goes next.</p>' % ("" if general else " hidden", e(first))
    if general:
        box = '<div class="syl-posters" data-trips data-general></div>'
    else:
        box = '<div class="syl-posters" data-trips data-n="%d">%s</div>' % (len(up), "".join(poster(u) for u in up))
    note = '<p class="syl-note" data-trips-note><strong>Booking because of %s?</strong> Type %s in the “Who sent you?” box at checkout.</p>' % (e(first), e(prof["name"]))
    return "\n".join(['<section class="syl syl-trips" id="syl-trips"><div class="syl-wrap">', head, sub, box, note, '</div></section>'])


def tag_html(first, r):
    s = day(r["trip_start"])
    return "<b>%s %s trip</b>, %s %d" % (e(poss(first)), e(r["tag"]), MON[s.month - 1], s.year)


def cite(r):
    return "%s on <a data-syl=\"review-%s\" href=\"%s\" target=\"_blank\" rel=\"noopener\">%s</a>" % (e(r["who"]), slug(r["who"]), e(r["url"]), e(r["src"])) if r.get("url") else e(r["who"])


def reviews(key, prof, data, feature_img):
    first = prof["first"]
    names = hl_names(first, data.get("aliases"))
    revs = data.get("reviews") or []
    out = ['<section class="syl syl-crew" id="syl-reviews"%s><div class="syl-wrap">' % ("" if revs else " hidden"),
           '<h2 class="syl-h"><span>Trip reviews</span><span class="syl-g">with %s.</span></h2>' % e(first)]
    if revs:
        f = revs[0]
        img = ('<img class="syl-feature-img" src="%s" alt="%s" loading="lazy">' % (e(feature_img[0]), e(feature_img[1]))) if feature_img else ""
        more = "".join('<p class="syl-q-more">“%s”</p>' % mark(q, names) for q in f.get("more", []))
        out.append('<figure class="syl-feature%s" data-review-id="%s">%s<div><p class="syl-tag">%s</p>'
                   '<blockquote style="margin:0;padding:0;border:0"><p class="syl-q">“%s”</p>%s</blockquote>'
                   '<figcaption class="syl-cite">%s</figcaption></div></figure>' % (
                       "" if feature_img else " no-img", e(f["id"]), img, tag_html(first, f), mark(f["q"], names), more, cite(f)))
        cards = []
        for r in revs[1:]:
            qs = "".join("<p>“%s”</p>" % mark(q, names) for q in [r["q"]] + r.get("more", []))
            cards.append('<figure class="syl-card"><p class="syl-tag">%s</p><div class="syl-stars" role="img" aria-label="5 out of 5 stars">★★★★★</div>'
                         '<blockquote>%s</blockquote><figcaption class="syl-who">%s</figcaption></figure>' % (tag_html(first, r), qs, cite(r)))
        out.append('<div class="syl-quotes" data-reviews%s>%s</div>' % ("" if cards else " hidden", "".join(cards)))
    else:
        out.append('<figure class="syl-feature no-img"><div></div></figure>')
        out.append('<div class="syl-quotes" data-reviews hidden></div>')
    out.append('<p class="syl-proof">SYB has a 4.9 on Google from 300+ reviews. <a data-syl="reviews-all" href="/testimonials">Read more</a></p>')
    out.append('</div></section>')
    return "\n".join(out)


def led_item(o):
    s = day(o["start"])
    inner = ('<span class="syl-led-when">%s %d</span><span class="syl-led-what"><strong>%s</strong><span>%s</span></span>'
             '<span class="syl-led-n">%s</span>') % (MON[s.month - 1], s.year, e(o["trip"]), e(o["place"]),
                                                     ("<b>%d</b>travelers" % o["travelers"]) if o.get("travelers") else "")
    if o.get("page"):
        return '<li><a href="%s" data-syl="led-%s-%s">%s</a></li>' % (e(o["page"]), slug(o["tag"]), o["start"][:7], inner)
    return "<li><span>%s</span></li>" % inner


def about(key, prof, data, about_img):
    first = prof["first"]
    led = data["led"]
    trav = sum(o.get("travelers", 0) for o in led)
    places = len({o["place"] for o in led if o.get("place")})
    if about_img:
        side = '<figure class="syl-about-photo"><img src="%s" alt="%s" loading="lazy" style="--pos:50%% 25%%"></figure>' % (e(about_img[0]), e(about_img[1]))
    else:
        side = ('<aside class="syl-stats"><p class="syl-stats-t">%s</p><p class="syl-stats-where">SYB trip leader, based in %s</p>'
                '<dl><div><dt>trips led</dt><dd data-stat="led">%d</dd></div><div><dt>travelers</dt><dd data-stat="travelers">%d</dd></div>'
                '<div><dt>destinations</dt><dd data-stat="places">%d</dd></div></dl></aside>') % (e(prof["title"]), e(prof["city"]), len(led), trav, places)
    bio = prof["bio"]
    qa = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (e(q), e(a)) for q, a, _src in prof["qa"])
    qa += "<div><dt>What are your specialties?</dt><dd><ul class=\"syl-chips\">%s</ul></dd></div>" % "".join("<li>%s</li>" % e(c) for c in prof["chips"])
    ledbox = ('<div data-led-box%s><h3 class="syl-led-h">Trips %s has led</h3><p class="syl-led-sum" data-led-sum>%d %s, %d travelers so far.</p>'
              '<ol class="syl-led" data-led>%s</ol></div>') % ("" if led else " hidden", e(first), len(led), "trip" if len(led) == 1 else "trips", trav,
                                                             "".join(led_item(o) for o in led))
    return "\n".join([
        '<section class="syl syl-about" id="syl-about"><div class="syl-wrap">',
        '<h2 class="syl-h"><span>Meet</span><span class="syl-g">%s.</span></h2>' % e(first),
        '<div class="syl-about-grid">', side, '<div>',
        '<p class="syl-vibe%s">%s</p>' % (" is-long" if len(bio) > 260 else "", e(bio)),
        ('<p class="syl-nick">On the SYB squad: <b>%s</b></p>' % e(prof["title"])) if about_img else "",
        '<dl class="syl-qa">%s</dl>' % qa,
        ledbox,
        '</div>', '</div>', '</div></section>',
    ])


def end(key, prof, nyc):
    first = prof["first"]
    body = ("SYB has run active and social group trips out of NYC since 2014. Every SYB leader, %s included, graduates our Academy in Nicaragua before leading a trip." % first) \
        if key in ACADEMY else "SYB has run active and social group trips out of NYC since 2014. Most people come solo. By the last night, nobody feels like it."
    if prof["chat"] == "nyc":
        chat = '<a class="syl-btn syl-btn-ghost" data-syl="whatsapp-nyc-end" href="%s" target="_blank" rel="noopener">Join the NYC chat</a>' % e(nyc)
    else:
        chat = '<a class="syl-btn syl-btn-ghost" data-syl="instagram-dm-end" href="https://ig.me/m/%s" target="_blank" rel="noopener">Message %s</a>' % (e(prof["ig"]), e(first))
    return "\n".join([
        '<section class="syl syl-end" id="syl-end"><div class="syl-wrap"><div class="syl-end-box">',
        '<h2 class="syl-h"><span>Come solo.</span><span class="syl-g">Leave with a crew.</span></h2>',
        '<p class="syl-body">%s</p>' % e(body),
        '<div class="syl-actions">',
        '<a class="syl-btn" data-syl="end-trips" href="#syl-trips">Travel with %s</a>' % e(first),
        chat,
        '<button class="syl-btn syl-btn-ghost" type="button" data-syl="share-end" data-share>Share %s page</button>' % e(poss(first)),
        '</div>',
        '<a class="syl-link" data-syl="calendar" href="/calendar">See every SYB trip</a>',
        '</div></div></section>',
    ])


HEAD = """<script>
(function(){
  var LEADER='%(key)s', LEADER_NAME='%(name)s';
  var host=location.hostname.replace(/^www\\./,'');
  var ref=document.referrer||'';
  var internal=false;
  try{ if(ref){ var ru=new URL(ref), rh=ru.hostname.replace(/^www\\./,''), rp=decodeURIComponent(ru.pathname); internal=((rh===host)||/myeasol\\.com$/.test(rh)) && !/\\/password\\/?$/.test(rp); } }catch(e){}
  var entry=!internal;
  window.dataLayer=window.dataLayer||[];
  if(entry){
    var days=90, jar='coo'+'kie';
    try{ document[jar]='syb_leader='+LEADER+';path=/;max-age='+(days*86400)+';SameSite=Lax'+(/surfyogabeer\\.com$/.test(host)?';domain=.surfyogabeer.com':''); }catch(e){}
    try{ localStorage.setItem('syb_leader',JSON.stringify({l:LEADER,t:Date.now(),p:location.pathname})); }catch(e){}
  }
  window.dataLayer.push({event:'leader_page_view',leader:LEADER,leader_entry:entry?'yes':'no'});
  function share(btn){
    var url=location.origin+location.pathname;
    var data={title:'Travel with '+LEADER_NAME+' | SYB',text:'Trips led by '+LEADER_NAME+', SYB trip leader',url:url};
    if(navigator.share){ navigator.share(data).catch(function(){}); return; }
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(url).then(function(){ var t=btn.textContent; btn.textContent='Link copied'; setTimeout(function(){ btn.textContent=t; },2200); },function(){});
    }
  }
  document.addEventListener('click',function(e){
    var el=e.target&&e.target.closest?e.target.closest('.syl [data-syl]'):null;
    if(!el) return;
    var href=el.getAttribute('href')||'';
    window.dataLayer.push({event:'leader_click',leader:LEADER,leader_click:el.getAttribute('data-syl'),link_url:href?String(el.href||href).split('?')[0]:''});
    if(el.hasAttribute('data-share')){ e.preventDefault(); share(el); }
  },true);
})();
</script>
<script src="@@JS@@" defer></script>
"""


def main():
    conf = load(os.path.join(DATA, "leaders.json"))
    profs = load(os.path.join(DATA, "profiles.json"))
    ph = Photos(load(os.path.join(DATA, "photos.json")))
    keys = sys.argv[1:] or list(conf["leaders"].keys())
    # erin first: her photos are her own; then the rest share the trip photo pool fairly
    keys = sorted(keys, key=lambda k: (k != "erin", k))
    nyc = profs["nyc_chat"]
    report = []
    for key in keys:
        prof = profs["leaders"][key]
        data = load(os.path.join(ROOT, "dist", "leaders", key + ".json"))
        if not data:
            print("no data for", key, file=sys.stderr)
            continue
        reel, about_img, feature_img = plan_photos(key, prof, data, ph)
        blocks = {
            "1-hero.html": hero(key, prof, data, reel, nyc),
            "2-trips.html": trips(key, prof, data),
            "3-reviews.html": reviews(key, prof, data, feature_img),
            "4-about.html": about(key, prof, data, about_img),
            "5-end.html": end(key, prof, nyc),
            "head.html": HEAD % {"key": key, "name": prof["name"].replace("'", "\\'")},
        }
        d = os.path.join(OUT, key)
        os.makedirs(d, exist_ok=True)
        for fn, txt in blocks.items():
            with open(os.path.join(d, fn), "w") as f:
                f.write(txt.strip() + "\n")
        report.append("%-10s reel %d  about %s  feature %s  reviews %d  upcoming %d  led %d" % (
            key, len(reel), "photo" if about_img else "stats", "img" if feature_img else "-", len(data.get("reviews") or []),
            len([u for u in data["upcoming"] if day(u["end"]) >= TODAY]), len(data["led"])))
    print("\n".join(report))


if __name__ == "__main__":
    main()
