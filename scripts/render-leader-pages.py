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
ICON_PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4.5v15l13-7.5z"/></svg>'
ICON_CLOSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>'
LED_SHOWN = 6    # trips shown before "See all" (same number as syb-leader.js); a list of up to 8 shows in full
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


def role(prof):
    """The line above the name. Trip leaders: "SYB trip leader"; the team: their job (profiles.json "role")."""
    return prof.get("role") or "SYB trip leader"


def leads(prof):
    """False for team members who do not lead trips (no "Travel with <name>", no trips-led line)."""
    return prof.get("leads", True)


def blob_url(p):
    if p.get("url"):              # an Easol resized copy (representations/proxy) read off the squad page
        return p["url"]
    sig = base64.b64encode(('{"_rails":{"data":"%s","pur":"blob_id"}}' % p["uuid"]).encode()).decode()
    from urllib.parse import quote
    return "https://static.myeasol.net/rails/active_storage/blobs/proxy/%s--%s/%s" % (sig, p["hex"], quote(p["name"]))


def holiday(s, en):
    if (en - s).days > 21:          # a months-long program (the Academy) is not a holiday trip
        return ""
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


# ---------- SYB's next trips (saved on the page of a leader with nothing coming up; the script redraws them live) ----------
def _builder():
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_leaders", os.path.join(ROOT, "scripts", "build-leaders.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def next_sbyb_trips(n):
    b = _builder()
    hist = load(os.path.join(DATA, "history.json"), {"trips": {}})["trips"]
    rows = sorted(hist.items(), key=lambda kv: (kv[1]["start"], kv[0]))
    out, seen = [], set()
    for tab, t in rows:
        if t.get("status") != "LIVE" or t.get("kind", "trip") != "trip" or day(t["start"]) < TODAY:
            continue
        if (day(t["end"]) - day(t["start"])).days > 21 or t["trip"] in seen:     # no months-long programs, one card per trip
            continue
        seen.add(t["trip"])
        out.append(b.trip_out(tab, t))
        if len(out) == n:
            break
    return out


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


def poster_photos(trips, ph, taken):
    """A trip photo for each saved trip card, never one already on the page: {(trip, start): (url, alt)}"""
    out = {}
    for u in trips:
        tag = u.get("tag")
        p = ph.pick(tag, taken, portrait=True) if tag in POOL_PAGES else None
        if p:
            out[(u["trip"], u["start"])] = (blob_url(p), "%s, SYB’s trip to %s" % (u["trip"], u.get("place") or CAPTION.get(tag, tag)))
    return out


def plan_photos(key, prof, data, ph, card_trips):
    """reel: [(url, caption, alt, pos)], about: (url, alt) or None, feature: (url, alt) or None,
    cards: {(trip, start): (url, alt)} for the trip cards saved in the block"""
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
        return reel, about, feature, poster_photos(card_trips, ph, taken)
    sq = ph.doc["squad"][key]
    pos = "50% 30%" if sq.get("h", 1) >= sq.get("w", 1) else "50% 40%"
    squad_slide = (blob_url(sq), "Hi, I’m %s." % first, "%s, %s" % (prof["name"], role(prof)), pos)
    reel = [squad_slide]
    if key == "alex":
        a2 = ph.doc["about"]["alex-ski"]
        reel.append((blob_url(a2), "Ski week, French Alps", "Alex Marks in an SYB ski bib and a penguin helmet", "50% 30%"))
    target = None
    own = (ph.doc.get("reel") or {}).get(key)
    if own:                       # their own photos and videos (photos.json "reel"), in their order
        reel = []
        for x in own["slides"]:
            if x.get("hold"):
                continue
            if x.get("squad"):
                reel.append((squad_slide[0], x.get("cap") or squad_slide[1], x.get("alt") or squad_slide[2], x.get("pos") or squad_slide[3]))
            elif x.get("yt"):
                reel.append((x.get("poster") or "https://i.ytimg.com/vi/%s/oardefault.jpg" % x["yt"], x["cap"], x["alt"], x.get("pos", "50% 35%"), {"yt": x["yt"]}))
            elif x.get("about"):
                a = ph.doc["about"][x["about"]]
                reel.append((blob_url(a), x["cap"], x["alt"], x.get("pos", "50% 30%")))
                taken.add(a.get("uuid", ""))
            elif x.get("video"):
                reel.append((x["poster"], x["cap"], x["alt"], x.get("pos", "50% 35%"), {"video": x["video"], "dur": x.get("dur")}))
            else:
                reel.append((blob_url(x), x["cap"], x["alt"], x.get("pos", "50% 35%")))
                if x.get("uuid"):
                    taken.add(x["uuid"])
        target = own.get("total", len(reel))
    tags = leader_tags(data)
    general = not tags
    if general:
        tags = GENERAL_PHOTOS
    want = 6 - len(reel)
    i = 0
    while (len(reel) < target if target is not None else len(reel) < 1 + want) and i < 30 and tags:
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
    cards = poster_photos(card_trips, ph, taken)
    feature = None
    if data.get("reviews"):
        ftag = data["reviews"][0].get("tag")
        for tag in ([ftag] if ftag in POOL_PAGES else []) + tags:
            p = ph.pick(tag, taken, portrait=False)
            if p and not p["portrait"]:
                feature = (blob_url(p), "SYB trip photo, %s" % CAPTION.get(tag, tag))
                break
    return reel, about, feature, cards


# ---------- trips led (the same rows syb-leader.js draws) ----------
def countries(led):
    seen, out = {}, []
    for o in led:
        if not o.get("flag"):
            continue
        if o["flag"] not in seen:
            seen[o["flag"]] = {"flag": o["flag"], "name": o.get("country") or o["place"], "n": 0}
            out.append(seen[o["flag"]])
        seen[o["flag"]]["n"] += 1
    return sorted(out, key=lambda c: -c["n"])          # stable: ties keep the order first led


def since(led):
    ys = [o["start"][:4] for o in led if o.get("start")]
    return min(ys) if ys else ""


def led_row(o, more):
    bold = o["trip"] or o["place"]
    small = o["place"] if o["trip"] else (o.get("note") or "")
    when = "" if o.get("date") in ("year", "none") or not o.get("start") else MON[day(o["start"]).month - 1]
    if o.get("n", 1) > 1:
        small = (small + ", " if small else "") + "%d trips" % o["n"]
    inner = ('<span class="syl-led-flag"%s aria-hidden="true">%s</span><span class="syl-led-what"><strong>%s</strong>%s</span>'
             '<span class="syl-led-when">%s</span>') % ((' title="%s"' % e(o["country"])) if o.get("country") else "", e(o.get("flag", "")),
                                                      e(bold), ("<span>%s</span>" % e(small)) if small else "", when)
    cls = ' class="is-more"' if more else ""
    if o.get("page"):
        return '<li%s><a href="%s" data-syl="led-%s-%s">%s</a></li>' % (cls, e(o["page"]), slug(o["tag"]), o["start"][:7] if o.get("start") else "undated", inner)
    return "<li%s><span>%s</span></li>" % (cls, inner)


def led_rows(led):
    dated = [o for o in led if o.get("start")]
    undated, order = {}, []
    for o in led:
        if o.get("start"):
            continue
        k = (o["trip"], o["place"], o.get("note", ""))
        if k not in undated:
            undated[k] = dict(o, n=0)
            order.append(k)
        undated[k]["n"] += 1
    cut = LED_SHOWN if len(led) > LED_SHOWN + 2 else len(led)
    out, year, shown = [], "", 0
    for o in dated:
        y, more = o["start"][:4], shown >= cut
        if y != year:
            year = y
            out.append('<li class="syl-led-y%s">%s</li>' % (" is-more" if more else "", y))
        out.append(led_row(o, more))
        shown += 1
    if order:
        more = shown >= cut
        out.append('<li class="syl-led-y%s">More trips</li>' % (" is-more" if more else ""))
        for k in order:
            out.append(led_row(undated[k], more))
            shown += undated[k]["n"]
    return "".join(out)


def flags_html(cs):
    return "".join('<li title="%s"><span aria-hidden="true">%s</span><span class="syl-sr">%s</span></li>' % (e(c["name"]), c["flag"], e(c["name"])) for c in cs)


# ---------- blocks ----------
def lede(data, prof=None):
    first = data["first"]
    led = [o for o in data["led"]]
    nc = len(countries(led))
    up = [u for u in data["upcoming"] if u.get("kind") == "trip" and day(u["end"]) >= TODAY]
    out = []
    if prof and prof.get("lede"):
        return e(prof["lede"])        # their own line (team members, the founder); the page script leaves it alone (no data-lede)
    if led:
        out.append("%s has led <b>%d SYB %s</b>%s." % (e(first), len(led), "trip" if len(led) == 1 else "trips",
                                                      (" in <b>%d countries</b>" % nc) if nc > 1 else ""))
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


def chat_row(prof, chats, where):
    c = chats.get(prof["chat"])
    if c:
        return ('<a class="syl-chat" data-syl="whatsapp-%s-%s" href="%s" target="_blank" rel="noopener"><span class="syl-chat-ic">%s</span>'
                '<span class="syl-chat-t">Join me in the SYB %s chat</span><span class="syl-chat-go">Join</span></a>') % (
            prof["chat"], where, e(c["url"]), ICON_WA, e(c["label"]))
    return ('<a class="syl-chat" data-syl="instagram-dm-%s" href="https://ig.me/m/%s" target="_blank" rel="noopener"><span class="syl-chat-ic is-ig">%s</span>'
            '<span class="syl-chat-t">Questions about a trip? Message me on Instagram</span><span class="syl-chat-go">Message</span></a>') % (where, e(prof["ig"]), ICON_IG)


def hero(key, prof, data, reel, chats):
    first = prof["first"]
    n = len(reel)
    slides, has_yt, has_video = [], False, False
    for i, r in enumerate(reel):
        url, cap, alt, pos = r[:4]
        x = r[4] if len(r) > 4 else {}
        on = ' class="syl-slide is-on"' if i == 0 else ' class="syl-slide"'
        hide = "" if i == 0 else ' aria-hidden="true"'
        src = ('src="%s" fetchpriority="high"' % e(url)) if i == 0 else ('data-src="%s"' % e(url))
        if x.get("yt"):
            has_yt = True
            slides.append('<figure%s data-cap="%s" data-yt="%s" data-dur="8"%s><img %s alt="%s" style="--pos:%s">'
                          '<button class="syl-play" type="button" data-syl="video-play" aria-label="Play %s">%s</button></figure>' % (
                              on, e(cap), e(x["yt"]), hide, src, e(alt), pos, e(alt), ICON_PLAY))
        elif x.get("video"):
            has_video = True
            vsrc = ('src="%s" autoplay' % e(x["video"])) if i == 0 else ('data-src="%s"' % e(x["video"]))
            slides.append('<figure%s data-cap="%s"%s%s><video %s poster="%s" muted playsinline loop preload="none" aria-label="%s" style="--pos:%s"></video></figure>' % (
                on, e(cap), (' data-dur="%s"' % x["dur"]) if x.get("dur") else "", hide, vsrc, e(url), e(alt), pos))
        else:
            slides.append('<figure%s data-cap="%s"%s><img %s alt="%s" style="--pos:%s"></figure>' % (on, e(cap), hide, src, e(alt), pos))
    up = [u for u in data["upcoming"] if u.get("kind") == "trip" and day(u["end"]) >= TODAY]
    btn = ("See %s trips" % poss(first)) if up else "See upcoming trips"
    # first line plain, second in the gradient; a one-name leader (h1 ["", "Maxime."]) gets the gradient line only
    h1 = "".join(('<span class="syl-g">%s</span>' if i else '<span>%s</span>') % e(t) for i, t in enumerate(prof["h1"]) if t)
    city =('<span class="syl-city">%s%s</span>' % (ICON_PIN, e(prof["city"]))) if prof.get("city") else ""
    return "\n".join([
        '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&display=swap" rel="stylesheet"><link rel="stylesheet" href="@@CSS@@">',
        '<section class="syl syl-hero" id="syl-hero" data-leader="%s">' % key,
        '<div class="syl-hero-grid">',
        '<div class="syl-reel" data-reel role="region" aria-roledescription="carousel" aria-label="%s in action, %d %s" tabindex="0">' % (
            e(first), n, "photos and videos" if (has_yt or has_video) else "photos"),
        '<div class="syl-bars" aria-hidden="true">%s</div>' % ("<i><b></b></i>" * n),
        '<p class="syl-cap" aria-live="polite">%s</p>' % e(reel[0][1]),
        "\n".join(slides),
        '<button class="syl-tap syl-tap-prev" type="button" aria-label="Previous photo"></button>',
        '<button class="syl-tap syl-tap-next" type="button" aria-label="Next photo"></button>',
        '<button class="syl-pause" type="button" aria-label="Pause the photos">%s</button>' % ICON_PAUSE,
        ('<button class="syl-yt-close" type="button" aria-label="Close the video">%s</button>' % ICON_CLOSE) if has_yt else "",
        '</div>',
        '<div class="syl-hero-copy">',
        '<p class="syl-role">%s</p>' % e(role(prof)),
        '<h1 class="syl-name">%s</h1>' % h1,
        '<div class="syl-home">',
        '<div class="syl-home-top">',
        city,
        '<a class="syl-ig" data-syl="instagram-hero" href="https://www.instagram.com/%s" target="_blank" rel="noopener">%s@%s</a>' % (e(prof["ig"]), ICON_IG, e(prof["ig"])),
        '</div>',
        chat_row(prof, chats, "hero"),
        '</div>',
        '<p class="syl-lede"%s>%s</p>' % ("" if prof.get("lede") else " data-lede", lede(data, prof)),
        '<div class="syl-actions">',
        '<a class="syl-btn" data-syl="hero-trips" href="#syl-trips">%s</a>' % e(btn),
        ('<a class="syl-btn syl-btn-ghost syl-watch" href="#syl-hero" data-watch data-syl="video-hero">%sWatch video</a>' % ICON_PLAY) if has_yt else "",
        '<button class="syl-btn syl-btn-ghost" type="button" data-syl="share-hero" data-share>Share</button>',
        '</div>',
        '</div>',
        '</div>',
        '</section>',
    ])


def poster(u, img=None):
    s, en = day(u["start"]), day(u["end"])
    hol = holiday(s, en)
    where = (u.get("place") or "") + ((", " + hol) if hol and u.get("place") else (hol or ""))
    pic = ('<img src="%s" alt="%s" loading="lazy">' % (e(img[0]), e(img[1]))) if img else ""
    return ('<a class="syl-poster" data-name="%s" data-start="%s" data-end="%s" data-place="%s" data-syl="trip-%s-%s" href="%s">' + pic +
            '<span class="syl-poster-top"><span></span></span><span class="syl-poster-body"><span class="syl-date">%s %d<i>%d</i></span>'
            '<span class="syl-trip">%s</span><span class="syl-place">%s%s</span><span class="syl-poster-foot"><span class="syl-price"></span>'
            '<span class="syl-cta">See the trip</span></span></span></a>') % (
        e(u["trip"]), u["start"], u["end"], e(u.get("place") or ""), slug(u.get("tag") or u.get("place") or u["trip"]), u["start"],
        e(u.get("page") or "/calendar"), MON[s.month - 1], s.day, s.year, e(u["trip"]), (e(where) + ". ") if where else "", rng(s, en))


def card_trips(data, general_list):
    up = [u for u in data["upcoming"] if day(u["end"]) >= TODAY]
    return up if up else general_list


def trips(key, prof, data, cards, general_list):
    first = prof["first"]
    up = [u for u in data["upcoming"] if day(u["end"]) >= TODAY]
    general = not up
    head = '<h2 class="syl-h" data-trips-h><span>Travel</span><span class="syl-g">with %s.</span></h2>' % e("SYB" if general else first)
    sub = '<p class="syl-trips-sub" data-trips-sub%s>%s</p>' % ("" if general else " hidden", (
        "%s isn’t on a trip right now. Here’s where SYB goes next." % e(first)) if leads(prof) else "Here’s where SYB goes next.")
    if general:
        box = '<div class="syl-posters" data-trips data-general data-n="%d">%s</div>' % (
            len(general_list), "".join(poster(u, cards.get((u["trip"], u["start"]))) for u in general_list))
    else:
        box = '<div class="syl-posters" data-trips data-n="%d">%s</div>' % (len(up), "".join(poster(u, cards.get((u["trip"], u["start"]))) for u in up))
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


def about(key, prof, data, about_img):
    first = prof["first"]
    led = data["led"]
    cs = countries(led)
    if about_img:
        side = '<figure class="syl-about-photo"><img src="%s" alt="%s" loading="lazy" style="--pos:50%% 25%%"></figure>' % (e(about_img[0]), e(about_img[1]))
    else:
        where = prof.get("where") or (("%s, based in %s" % (role(prof), prof["city"])) if prof.get("city") else role(prof))
        side = ('<aside class="syl-stats"><p class="syl-stats-t">%s</p><p class="syl-stats-where">%s</p>'
                '<dl data-stats-nums%s><div><dt>trips led</dt><dd data-stat="led">%d</dd></div><div><dt>countries</dt><dd data-stat="countries">%d</dd></div>'
                '<div><dt>leading since</dt><dd data-stat="since">%s</dd></div></dl></aside>') % (
                    e(prof["title"]), e(where), "" if led else " hidden", len(led), len(cs), since(led))
    bio = prof["bio"]
    qa = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (e(q), e(a)) for q, a, _src in prof["qa"])
    qa += "<div><dt>What are your specialties?</dt><dd><ul class=\"syl-chips\">%s</ul></dd></div>" % "".join("<li>%s</li>" % e(c) for c in prof["chips"])
    nled = len(led)
    ledbox = ('<div data-led-box%s><h3 class="syl-led-h">Trips %s has led</h3><p class="syl-led-sum" data-led-sum>%d %s%s so far.</p>'
              '<ul class="syl-flags" data-led-flags aria-label="Countries"%s>%s</ul>'
              '<ol class="syl-led" data-led>%s</ol>'
              '<button class="syl-btn syl-btn-ghost syl-led-all" type="button" data-led-all data-total="%d" aria-expanded="false" data-syl="led-all" hidden>See all %d trips</button></div>') % (
                  "" if led else " hidden", e(first), nled, "trip" if nled == 1 else "trips", (" in %d countries" % len(cs)) if len(cs) > 1 else "",
                  "" if len(cs) > 1 else " hidden", flags_html(cs), led_rows(led), nled, nled)
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


def end(key, prof, chats):
    first = prof["first"]
    body = ("SYB has run active and social group trips out of NYC since 2014. Every SYB leader, %s included, graduates our Academy in Nicaragua before leading a trip." % first) \
        if key in ACADEMY else "SYB has run active and social group trips out of NYC since 2014. Most people come solo. By the last night, nobody feels like it."
    c = chats.get(prof["chat"])
    if c:
        chat = '<a class="syl-btn syl-btn-ghost" data-syl="whatsapp-%s-end" href="%s" target="_blank" rel="noopener">Join the %s chat</a>' % (
            prof["chat"], e(c["url"]), e(c["short"]))
    else:
        chat = '<a class="syl-btn syl-btn-ghost" data-syl="instagram-dm-end" href="https://ig.me/m/%s" target="_blank" rel="noopener">Message %s</a>' % (e(prof["ig"]), e(first))
    return "\n".join([
        '<section class="syl syl-end" id="syl-end"><div class="syl-wrap"><div class="syl-end-box">',
        '<h2 class="syl-h"><span>Come solo.</span><span class="syl-g">Leave with a crew.</span></h2>',
        '<p class="syl-body">%s</p>' % e(body),
        '<div class="syl-actions">',
        '<a class="syl-btn" data-syl="end-trips" href="#syl-trips">Travel with %s</a>' % e(first if leads(prof) else "SYB"),
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
    var data={title:%(share_title)s,text:%(share_text)s,url:url};
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
    want = set(sys.argv[1:]) or set(conf["leaders"])
    # erin first: her photos are her own; then the rest share the trip photo pool fairly, the first 22 (Oct 16) before
    # the pages added later ("added" in leaders.json). Every page's photos are planned in that order even when only
    # some pages are written, so a page gets the same photos whichever pages are rendered with it.
    keys = sorted(conf["leaders"], key=lambda k: (conf["leaders"][k].get("added", ""), k != "erin", k))
    chats = profs["city_chats"]
    general_list = next_sbyb_trips(4)
    report = []
    for key in keys:
        prof = profs["leaders"][key]
        data = load(os.path.join(ROOT, "dist", "leaders", key + ".json"))
        if not data:
            print("no data for", key, file=sys.stderr)
            continue
        reel, about_img, feature_img, cards = plan_photos(key, prof, data, ph, card_trips(data, general_list))
        if key not in want:
            continue
        blocks = {
            "1-hero.html": hero(key, prof, data, reel, chats),
            "2-trips.html": trips(key, prof, data, cards, general_list),
            "3-reviews.html": reviews(key, prof, data, feature_img),
            "4-about.html": about(key, prof, data, about_img),
            "5-end.html": end(key, prof, chats),
            "head.html": HEAD % {"key": key, "name": prof["name"].replace("'", "\\'"),
                                 "share_title": ("'Travel with '+LEADER_NAME+' | SYB'" if leads(prof) else "'Meet '+LEADER_NAME+' | SYB'"),
                                 "share_text": ("'Trips led by '+LEADER_NAME+', %s'" if leads(prof) else "LEADER_NAME+', %s'") % role(prof).replace("'", "\\'")},
        }
        d = os.path.join(OUT, key)
        os.makedirs(d, exist_ok=True)
        for fn, txt in blocks.items():
            with open(os.path.join(d, fn), "w") as f:
                f.write(txt.strip() + "\n")
        report.append("%-10s reel %d  cards %d  about %s  feature %s  reviews %d  upcoming %d  led %d" % (
            key, len(reel), len(cards), "photo" if about_img else "stats", "img" if feature_img else "-", len(data.get("reviews") or []),
            len([u for u in data["upcoming"] if day(u["end"]) >= TODAY]), len(data["led"])))
    print("\n".join(report))


if __name__ == "__main__":
    main()
