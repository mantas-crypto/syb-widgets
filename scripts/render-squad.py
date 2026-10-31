#!/usr/bin/env python3
"""
The Leaders page (surfyogabeer.com/squad, "Leaders" in the site menu). Writes:
  data/leaders/squad-static.json   who is on the page: names, the line under the name, photos, story slides
  dist/leaders/squad.json          the same plus live trips (build-leaders.py rewrites it twice a day)
  pages/squad/1-leaders.html       the Easol embed block (the whole page)
  pages/squad/head.html            the page's Inject code (loads syb-squad.js)

    python3 scripts/render-squad.py

Everyone in data/leaders/leaders.json with a leader page is on it. Team members who do not lead trips
(profiles.json leads: false) get a card at the end of the grid and show under SYB HQ, but no face in the wall of
stories and no place in the leader count (Mantas, Oct 19 2026). Story slides are the same photos
and videos as the reel on their own page (read from pages/leaders/<key>/1-hero.html), so render the leader pages
first. syb-squad.js reads dist/leaders/squad.json on every visit: next trips, trips led and the order stay current
without saving the block again. @@CSS@@, @@SQCSS@@ and @@SQJS@@ are filled in with the pinned jsDelivr files when
the block is saved.
"""
import base64, datetime, html, importlib.util, json, os, re
from urllib.parse import quote
from zoneinfo import ZoneInfo

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data", "leaders")
OUT = os.path.join(ROOT, "pages", "squad")
TODAY = datetime.datetime.now(ZoneInfo("America/New_York")).date()
MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

# Easol makes resized copies on request: the size part of the address is signed, the same for every photo.
# Read off the srcset of any squad profile page (webp, Oct 19 2026).
SIZE_SIG = {405: "5022e26755fcd481c46bb5e675cd43a94857271f", 540: "2ef123a85fd1d3d1cf4485308252785619b3574f",
            720: "59d0de8cdb039124d45c96ce2206d281785da420", 960: "b743abef227918992fbefa917012fddd265a9bce",
            1140: "f94b0c5e7d9ccc4d00da4fb53ee6cd31cb74f94c"}
# SYB HQ whose own page is not under /hq/ or /management/: Bradford and Santiago since Oct 26 2026 (their /management/
# pages forward to their leader pages), Mantas, Kaia and Shriner since Oct 31 2026 (moved to /trip-leaders/).
HQ_TOO = {"eli", "bradford", "santiago", "mantas", "kaia", "shriner"}
HQ_PAGES = ("/hq/", "/management/")   # Sara and Danielle moved to /hq/ on Oct 31 2026; Steph is still on /management/
STORY_MAX = 8               # slides per story (Bradford's reel has 19)


def load(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except FileNotFoundError:
        return d


def e(s):
    return html.escape(str(s), quote=False).replace('"', "&quot;")


def sized(p, w):
    """webp copy of an Easol photo, w pixels wide at most."""
    blob = base64.b64encode(('{"_rails":{"data":"%s","pur":"blob_id"}}' % p["uuid"]).encode()).decode()
    var = base64.b64encode(('{"_rails":{"data":{"format":"webp","resize_to_limit":[%d,null],"saver":{"strip":true,'
                            '"quality":85}},"pur":"variation"}}' % w).encode()).decode()
    return "https://static.myeasol.net/rails/active_storage/representations/proxy/%s--%s/%s--%s/%s" % (
        blob, p["hex"], var, SIZE_SIG[w], quote(p["name"]))


def tags_of(key, conf, prof):
    pages = [conf["page"]] + conf.get("also", [])
    t = []
    if prof.get("leads", True):
        t.append("lead")
    if any(p.startswith("/photographers/") for p in pages):
        t.append("photo")
    if any(p.startswith(HQ_PAGES) for p in pages) or key in HQ_TOO:
        t.append("hq")
    return t


def label_of(prof, tags):
    """The line under the name: their job for the team, otherwise trip leader (photographers lead trips too)."""
    if prof.get("squad_label"):
        return prof["squad_label"]
    role = prof.get("role") or ""
    if role and role != "SYB trip leader":
        r = re.sub(r"^SYB ", "", role)
        return r[:1].upper() + r[1:]
    base = "Senior leader" if (prof.get("title") or "").lower() == "senior leader" else "Trip leader"
    return base + (" and photographer" if "photo" in tags else "")


FIG = re.compile(r'<figure class="syl-slide[^"]*" data-cap="([^"]*)"([^>]*)>(.*?)</figure>', re.S)


def attr(a, name):
    m = re.search(r'(?<![\w-])%s="([^"]*)"' % name, a)
    return html.unescape(m.group(1)) if m else ""


def story_of(key):
    """The slides of their reel, as on their own page."""
    h = open(os.path.join(ROOT, "pages", "leaders", key, "1-hero.html")).read()
    out = []
    for cap, fattrs, inner in FIG.findall(h):
        s = {"c": html.unescape(cap)}
        v = re.search(r"<video ([^>]*)>", inner)
        i = re.search(r"<img ([^>]*)>", inner)
        a = v.group(1) if v else (i.group(1) if i else "")
        if not a:
            continue
        pos = re.search(r"--pos:([^\"]+)\"", a)
        s["pos"] = pos.group(1).strip() if pos else "50% 35%"
        if v:
            s["v"], s["p"] = attr(a, "data-src") or attr(a, "src"), attr(a, "poster")
            if "data-audio" in a:
                s["a"] = 1
        else:
            s["i"] = attr(a, "data-src") or attr(a, "src")
            s["alt"] = attr(a, "alt")
        out.append(s)
    return out


def rank(p):
    """Founder first, then whoever leaves soonest (or is away now), then everyone else by trips led."""
    if p["key"] == "mantas":
        return (0, "", 0, "")
    if p.get("up"):
        return (1, p["up"][0]["s"], 0, p["name"])
    return (2, "", -p.get("led", 0), p["name"])


def mday(s):
    d = datetime.date.fromisoformat(s)
    return "%s %d" % (MON[d.month - 1], d.day)


def pill(p):
    if not p.get("up"):
        return ""
    u = p["up"][0]
    s, en = datetime.date.fromisoformat(u["s"]), datetime.date.fromisoformat(u["e"])
    if s <= TODAY <= en:
        return '<span class="sys-pill is-now">On a trip now</span>'
    cls = " is-soon" if (s - TODAY).days <= 21 else ""
    return '<span class="sys-pill%s"><span class="sys-f" aria-hidden="true">%s</span>%s</span>' % (cls, e(u["f"]), e(mday(u["s"])))


def stat(p):
    if "lead" not in p["tags"]:
        return '<span class="sys-stat"><span><b>SYB HQ</b></span></span>'
    if p.get("led"):
        n = p["led"]
        return ('<span class="sys-stat"><span><b>%d</b> trip%s</span><span class="sys-flags" aria-hidden="true">%s</span></span>' % (
            n, "" if n == 1 else "s", e("".join(f for f, _c in p["flags"][:4]))))
    if p.get("up"):
        return '<span class="sys-stat"><span>First trip coming up</span></span>'
    return ""


def name_html(p):
    lines = [x for x in p["h1"] if x]
    if len(lines) == 1:
        return '<span class="syl-g">%s</span>' % e(lines[0])
    return '<span>%s</span> <span class="syl-g">%s</span>' % (e(lines[0]), e(lines[1]))


def card(p):
    alt = "%s, %s" % (p["name"], p["label"][:1].lower() + p["label"][1:])
    return ('<li class="sys-card" data-key="%s" data-tags="%s" data-first="%s"><a href="%s" data-syl="squad-card-%s">'
            '<img class="sys-pic" src="%s" alt="%s" loading="lazy" decoding="async" style="--pos:%s">%s'
            '<span class="sys-body"><span class="sys-name">%s</span><span class="sys-label">%s</span>'
            '<span class="sys-where" hidden></span>%s</span></a></li>') % (
        p["key"], " ".join(p["tags"]), e(p["first"]), e(p["page"]), p["key"], e(p["img"]), e(alt), p["pos"], pill(p),
        name_html(p), e(p["label"]), stat(p))


def short_names(people):
    """First names under the faces; a first name two leaders share gets the last initial (Adam F., Adam T.)."""
    count = {}
    for p in people:
        count[p["first"]] = count.get(p["first"], 0) + 1
    for p in people:
        last = (p["name"].split() + [""])[1] if " " in p["name"] else ""
        p["short"] = p["first"] + (" " + last[0] + "." if count[p["first"]] > 1 and last else "")


def ring(p):
    now = ""
    if p.get("up"):
        u = p["up"][0]
        if datetime.date.fromisoformat(u["s"]) <= TODAY <= datetime.date.fromisoformat(u["e"]):
            now = '<span class="sys-ring-now">On a trip</span>'
    img = '<img src="%s" alt="" loading="lazy" decoding="async">' % e(p["av"])
    if p.get("avzoom"):           # photos.json "ring": a face photo, zoomed in (the circles are small)
        img = '<span class="sys-ring-crop"><img src="%s" alt="" loading="lazy" decoding="async" style="--o:%s;--z:%s"></span>' % (
            e(p["av"]), p["avpos"], p["avzoom"])
    return ('<li><button class="sys-ring" type="button" data-story="%s" data-syl="squad-story-%s" aria-label="Watch %s’s story">'
            '<span class="sys-ring-pic">%s%s</span>'
            '<span class="sys-ring-name">%s</span></button></li>') % (
        p["key"], p["key"], e(p["first"]), img, now, e(p["short"]))


def chips(people):
    seen = {}
    for p in people:
        for c in set(list(p.get("cc", {})) + [u["c"] for u in p.get("up", []) if u.get("c")]):
            seen.setdefault(c, [0, ""])[0] += 1
        for f, c in p.get("flags", []):
            seen.setdefault(c, [0, ""])[1] = f
        for u in p.get("up", []):
            if u.get("c"):
                seen[u["c"]][1] = seen[u["c"]][1] or u["f"]
    out = []
    for c in sorted(seen, key=lambda c: (-seen[c][0], c)):
        out.append('<button class="sys-chip" type="button" data-f="c:%s" data-syl="squad-filter-%s" aria-pressed="false">'
                   '<span class="sys-f" aria-hidden="true">%s</span>%s</button>' % (e(c), re.sub(r"[^a-z]+", "-", c.lower()), e(seen[c][1]), e(c)))
    return "".join(out)


def names(crew):
    return " and ".join(t["first"] for t in crew) if len(crew) <= 2 else "%d more" % len(crew)


def status_all(n, crew):
    """Same words as syb-squad.js setFilter('all')."""
    return "All <b>%d</b> leaders%s" % (n, ", plus %s from SYB HQ" % e(names(crew)) if crew else "")


def page_html(doc):
    people = sorted(doc["people"], key=rank)
    n = len(people)
    return "\n".join([
        '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&display=swap" rel="stylesheet">'
        '<link rel="stylesheet" href="@@CSS@@"><link rel="stylesheet" href="@@SQCSS@@">',
        '<section class="syl sys" id="sys" data-squad>',
        '<div class="sys-top">',
        '<div class="syl-wrap sys-hero">',
        '<h1 class="syl-name sys-h1"><span>Meet the</span> <span class="syl-g">leaders.</span></h1>',
        '<p class="sys-lede">They run the trips, start the parties and turn a group of strangers into a crew. '
        'Tap a face to see them in action.</p>',
        '</div>',
        '<ul class="sys-rail" data-sys-rail aria-label="Leader stories">%s</ul>' % "".join(ring(p) for p in people),
        '</div>',
        '<div class="sys-lineup">',
        '<div class="sys-bar"><div class="sys-chips" data-sys-chips role="group" aria-label="Show leaders">'
        '<button class="sys-chip is-on" type="button" data-f="all" data-syl="squad-filter-all" aria-pressed="true">Everyone</button>'
        '<button class="sys-chip" type="button" data-f="soon" data-syl="squad-filter-soon" aria-pressed="false">Leading soon</button>'
        '<button class="sys-chip" type="button" data-f="photo" data-syl="squad-filter-photo" aria-pressed="false">Photographers</button>'
        '<button class="sys-chip" type="button" data-f="hq" data-syl="squad-filter-hq" aria-pressed="false">SYB HQ</button>'
        '<span class="sys-chip-sep" aria-hidden="true"></span><span data-sys-places>%s</span></div></div>' % chips(people),
        '<div class="syl-wrap">',
        '<p class="sys-status syl-sr" data-sys-status aria-live="polite">%s</p>' % status_all(n, doc["team"]),
        '<ul class="sys-grid" data-sys-grid>%s</ul>' % "".join(card(p) for p in people + doc["team"]),
        '</div>',
        '</div>',
        '<div class="syl-wrap">',
        '<div class="sys-end"><h2 class="syl-h"><span>Your crew</span> <span class="syl-g">is waiting.</span></h2>'
        '<p class="syl-body">Pick a trip, pick a leader, or both.</p>'
        '<div class="syl-actions"><a class="syl-btn" href="/calendar" data-syl="squad-end-calendar">Find your trip</a>'
        '<a class="syl-btn syl-btn-ghost" href="/join-our-team" data-syl="squad-end-join">Become a leader</a></div></div>',
        '</div>',
        '</section>',
    ])


def main():
    conf = load(os.path.join(DATA, "leaders.json"))["leaders"]
    profs = load(os.path.join(DATA, "profiles.json"))["leaders"]
    phdoc = load(os.path.join(DATA, "photos.json"))
    photos, about, rings = phdoc["squad"], phdoc.get("about", {}), phdoc.get("ring", {})
    people, team = [], []
    for key, c in conf.items():
        prof, sq = profs[key], photos[key]
        tags = tags_of(key, c, prof)
        item = {"key": key, "name": prof["name"], "first": prof["first"], "h1": [x for x in prof["h1"]],
                "page": c["page"], "label": label_of(prof, tags), "tags": tags, "city": prof.get("city", ""),
                "av": sized(sq, 405)}
        r = rings.get(key)
        if r:                             # a face photo for the small circle (and the story header)
            item.update({"av": sized(about[r["about"]], 405), "avpos": r.get("pos", "50% 30%"), "avzoom": r.get("zoom", 1)})
        item.update({"img": sized(sq, 540), "pos": "50% 30%" if sq.get("h", 1) >= sq.get("w", 1) else "50% 40%"})
        if "lead" not in tags:          # SYB HQ, not a trip leader: a card, no story
            team.append(item)
            continue
        item["story"] = story_of(key)[:STORY_MAX]
        people.append(item)
    short_names(people)
    static = {"_about": "Written by scripts/render-squad.py from leaders.json, profiles.json, photos.json and each "
                        "leader's rendered reel. build-leaders.py adds live trips and writes dist/leaders/squad.json.",
              "people": people, "team": team}
    with open(os.path.join(DATA, "squad-static.json"), "w") as f:
        json.dump(static, f, ensure_ascii=False, indent=1)
        f.write("\n")
    spec = importlib.util.spec_from_file_location("build_leaders", os.path.join(ROOT, "scripts", "build-leaders.py"))
    bl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bl)
    bl.write_squad(TODAY)
    doc = load(os.path.join(ROOT, "dist", "leaders", "squad.json"))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "1-leaders.html"), "w") as f:
        f.write(page_html(doc) + "\n")
    with open(os.path.join(OUT, "head.html"), "w") as f:
        f.write('<script src="@@SQJS@@" defer></script>\n')
    print(json.dumps({"people": len(people), "team": len(team), "slides": sum(len(p["story"]) for p in people),
                      "block_chars": len(page_html(doc))}))


if __name__ == "__main__":
    main()
