#!/usr/bin/env python3
"""
Leader pages data. Writes dist/leaders/<leader>.json for every leader in data/leaders/leaders.json.

Runs in GitHub Actions (.github/workflows/leaders.yml) twice a day, after SYB HQ syncs the Leader Hub Feed.
Nothing here needs a key. It reads "SYB Public Feed (no guest data)", a link-shared copy of the trip list
with no guest data in it (the Leader Hub Feed itself is private since Oct 16 2026). If that sheet cannot be
read, the pages keep their trips from history.json.

Where each part of a leader page comes from
  Upcoming trips   Leader Hub Feed, TRIPS tab (synced from SYB HQ, so adding a leader to a trip tab in HQ
                   adds the trip to their page). Spots left, sold out and prices are NOT here: the page reads
                   those live from Easol on every visit (product_search in the trips block).
  Trips led        data/leaders/history.json: every trip since 2023, seeded from SYB HQ on Oct 14 2026
                   (scripts/seed-leader-history.py) and kept current from the feed by this script. A trip is
                   added the first time the feed shows it and is never deleted, so finished trips stay.
                   data/leaders/older-trips.json adds the trips before that (HQ 2020-2022 tabs, GHL trip tags,
                   leaders' own lists); it is merged in here and never written back to history.json.
                   A trip counts once it has ended and ran (it had bookings). No traveler numbers are published.
  Reviews          data/google-reviews.json (refreshed daily by the widgets job) plus hand-added reviews in
                   data/leaders/extra-reviews.json. A Google review counts for a leader when it names them and
                   was written during or within 150 days after one of their trips. Quotes come from
                   data/leaders/picks.json when picked by hand, otherwise the sentences that name the leader.
                   Sentences naming anyone in exclude_names are never quoted.

    python3 scripts/build-leaders.py                    # read the feed, update history, write the files
    python3 scripts/build-leaders.py --feed trips.csv   # use a saved copy of the TRIPS tab
    python3 scripts/build-leaders.py --dry              # print what would change, write nothing
    python3 scripts/build-leaders.py --today 2026-11-01 # pretend it is another day
"""
import argparse, csv, datetime, io, json, os, re, sys
from zoneinfo import ZoneInfo

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data", "leaders")
OUT = os.path.join(ROOT, "dist", "leaders")
FEED_ID = "1eqR2mnjno31ODG_hMM0GR7NL9NrkjpELjiQmlsh4HYE"   # SYB Public Feed (no guest data)
FEED_GID = "1001"                                         # TRIPS tab: trip, start_on, end_on, hub_tab, booked, leaders, lead, status
FEED_URLS = [
    "https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:csv&headers=1&sheet=TRIPS" % FEED_ID,
    "https://docs.google.com/spreadsheets/d/%s/export?format=csv&gid=%s" % (FEED_ID, FEED_GID),
]
NY = ZoneInfo("America/New_York")
REVIEW_WINDOW = 45         # days after a trip ends that a review can still be about it (most land within two weeks)
MAX_REVIEWS = 9          # one big quote plus eight cards
SKIP_STATUS = {"CANCELLED", "IDEA", "NOT LAUNCHED"}

# HQ tab name start -> HQ destination (same words MASTER uses)
TAB_DEST = [
    ("cote d'azure", "France (riviera)"), ("chamonix", "France (ski)"), ("val thorens", "France (ski)"),
    ("amalfi", "Amalfi"), ("italy dolomites", "Dolomites"), ("dolomites", "Dolomites"), ("italy", "Amalfi"),
    ("red sea", "Egypt"), ("zermatt", "Switzerland"), ("la ", "LA"), ("nyc", "NYC"), ("black tie", "NYC"),
    ("pre-gala", "NYC"), ("las vegas", "Las Vegas"), ("nicaragua", "Nicaragua"),
]
# HQ destination -> (place line, short name for "Erin's ... trip", trip page, country code for the flag)
PLACES = {
    "Nicaragua": ("Nicaragua", "Nicaragua", "/nicaragua", "NI"),
    "Bali": ("Bali, Indonesia", "Bali", "/bali", "ID"),
    "Finland": ("Finnish Lapland", "Lapland", "/finland", "FI"),
    "France (riviera)": ("South of France", "Côte d’Azur", "/south-of-france", "FR"),
    "France (ski)": ("French Alps", "French Alps", "/chamonix", "FR"),
    "Amalfi": ("Amalfi Coast, Italy", "Amalfi", "/amalfi", "IT"),
    "Dolomites": ("Dolomites, Italy", "Dolomites", "/dolomites", "IT"),
    "Kenya": ("Kenya", "Kenya", "/kenya", "KE"),
    "Croatia": ("Croatia", "Croatia", "/croatia", "HR"),
    "Iceland": ("Iceland", "Iceland", "/iceland", "IS"),
    "Turkey": ("Turkey", "Turkey", "/turkey", "TR"),
    "Morocco": ("Morocco", "Morocco", "/morocco", "MA"),
    "Egypt": ("Egypt", "Egypt", "/egypt", "EG"),
    "Japan": ("Japan", "Japan", "/japan", "JP"),
    "Philippines": ("Palawan, Philippines", "Palawan", "/philippines", "PH"),
    "Belize": ("Belize", "Belize", "/belize", "BZ"),
    "Guatemala": ("Guatemala", "Guatemala", "/guatemala", "GT"),
    "Switzerland": ("Zermatt, Switzerland", "Zermatt", "/switzerland", "CH"),
    "Greece": ("Greece", "Greece", "/greece", "GR"),
    "Portugal": ("Portugal", "Portugal", "/portugal", "PT"),
    "Norway": ("Norway", "Norway", "/norway", "NO"),
    "Ireland": ("Ireland", "Ireland", "", "IE"),
    "Mexico": ("Mexico", "Mexico", "", "MX"),
    "NYC": ("New York City", "New York", "", "US"),
    "LA": ("Los Angeles", "LA", "", "US"),
    "Las Vegas": ("Las Vegas", "Las Vegas", "", "US"),
    "Miami": ("Miami", "Miami", "", "US"),
    "Ibiza": ("Ibiza, Spain", "Ibiza", "", "ES"),
    "Cuba": ("Cuba", "Cuba", "", "CU"),
    "Honduras": ("Honduras", "Honduras", "", "HN"),
    "Costa Rica": ("Costa Rica", "Costa Rica", "", "CR"),
    "Hamptons": ("The Hamptons, New York", "Hamptons", "", "US"),
    "Hudson Valley": ("Hudson Valley, New York", "Hudson Valley", "", "US"),
    "Hunter Mountain": ("Hunter Mountain, New York", "Hunter Mountain", "", "US"),
}
COUNTRY = {"NI": "Nicaragua", "ID": "Indonesia", "FI": "Finland", "FR": "France", "IT": "Italy", "KE": "Kenya", "HR": "Croatia",
           "IS": "Iceland", "TR": "Turkey", "MA": "Morocco", "EG": "Egypt", "JP": "Japan", "PH": "Philippines", "BZ": "Belize",
           "GT": "Guatemala", "CH": "Switzerland", "GR": "Greece", "PT": "Portugal", "NO": "Norway", "IE": "Ireland", "MX": "Mexico",
           "US": "United States", "ES": "Spain", "CU": "Cuba", "HN": "Honduras", "CR": "Costa Rica"}


def load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def iso(s):
    try:
        return datetime.date.fromisoformat((s or "").strip()[:10])
    except ValueError:
        return None


def num(s):
    try:
        return int(float(str(s).replace(",", "")))
    except ValueError:
        return 0


def dest_of(tab, current=""):
    if current:
        return current
    t = tab.lower()
    for start, d in TAB_DEST:
        if t.startswith(start):
            return d
    first = re.split(r"[\s,#']", tab.strip())[0]
    return first if first in PLACES else first.title()


def read_feed(path=None):
    """TRIPS rows as dicts, or None when the feed cannot be read (then nothing is changed from it)."""
    text = None
    if path:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    else:
        import requests
        for url in FEED_URLS:
            try:
                r = requests.get(url, timeout=30)
                if r.status_code == 200 and r.text.lstrip().lower().startswith(('trip,', '"trip"')):
                    text = r.text
                    break
            except requests.RequestException:
                pass
    if not text:
        return None
    rows = list(csv.DictReader(io.StringIO(text)))
    rows = [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in rows]
    if not rows or "leaders" not in rows[0] or "hub_tab" not in rows[0]:
        return None
    return rows


def update_history(hist, rows):
    """Merge feed rows into history. Returns the number of trips added or changed."""
    changed = 0
    for r in rows:
        tab = r.get("hub_tab", "")
        s, e = iso(r.get("start_on")), iso(r.get("end_on"))
        if not tab or not s:
            continue
        old = hist.get(tab)
        new = dict(old or {})
        span = (e - s).days if e else 0
        if not old or span <= 21:                  # multi-month programs (Academy) keep their HQ dates
            new["start"], new["end"] = s.isoformat(), (e or s).isoformat()
        new["trip"] = r.get("trip") or new.get("trip") or re.sub(r"\s*'\d\d$", "", tab)
        new["dest"] = dest_of(tab, new.get("dest", ""))
        new.pop("booked", None)                    # traveler numbers are not kept (they are not for the public)
        new["ran"] = num(r.get("booked")) > 0 if r.get("booked") else new.get("ran", False)
        new["leaders"] = [x.strip() for x in r.get("leaders", "").split("/") if x.strip()]
        new["kind"] = new.get("kind") or ("event" if span <= 1 else "trip")
        new["status"] = r.get("status") or new.get("status", "")
        if new != old:
            hist[tab] = new
            changed += 1
    return changed


def short_name(full):
    full = re.sub(r"\s*\(.*?\)\s*", " ", full).strip()
    parts = full.split()
    if len(parts) >= 2:
        return "%s %s." % (parts[0], parts[-1][0])
    return full


def sentences(text):
    out = []
    for para in re.split(r"\n+", text or ""):
        para = re.sub(r"([a-z])([!?.])([A-Z])", r"\1\2 \3", para.strip())   # "Beer!This" -> "Beer! This"
        out += [s.strip() for s in re.split(r"(?<=[.!?…])\s+(?=[\"“‘A-Z0-9])", para) if s.strip()]
    return out


def has_name(s, names):
    return any(re.search(r"(?<![\w])%s(?![\w])" % re.escape(n), s) for n in names)


def excerpt(text, aliases, exclude, limit=240):
    """The sentences that name the leader (else the opening ones), leaving out sentences that name excluded people."""
    sents = [s for s in sentences(text) if not has_name(s, exclude)]
    if not sents:
        return "", False
    named = [i for i, s in enumerate(sents) if has_name(s, aliases)]
    pick = named[:2] if named else [0]
    size = sum(len(sents[i]) for i in pick)
    i = max(pick) + 1
    while i < len(sents) and size + len(sents[i]) <= limit and len(pick) < 3:
        pick.append(i)
        size += len(sents[i])
        i += 1
    pick = sorted(set(pick))
    parts, prev = [], None
    for i in pick:
        if prev is not None and i != prev + 1:
            parts.append("…")
        parts.append(sents[i])
        prev = i
    return " ".join(parts), bool(named)


def is_staff(name, staff):
    n = re.sub(r"\s+", " ", (name or "").strip().lower())
    return n in staff or short_name(name).lower() in staff


def quote_score(q, aliases, names):
    """Higher = more about this leader. Every other leader or staff name in the quote costs a point;
    a quote that is a full thought (60 to 260 characters) gets one."""
    others = {n for n in names if n not in aliases and has_name(q, [n])}
    return (2 if has_name(q, aliases) else 0) - len(others) + (1 if 60 <= len(q) <= 260 else 0)


def owns_review(text, day, aliases, rivals):
    """A review naming only a name this leader shares with another leader (two Sarahs) counts only when no
    other leader with that name led a trip in the review's window. rivals: alias -> [(other key, their trips led)]."""
    own = [a for a in aliases if has_name(text, [a])]
    if any(a not in rivals for a in own):
        return True
    for a in own:
        for _, trips in rivals[a]:
            if any(exact(o) and iso(o["start"]) <= day <= iso(o["end"]) + datetime.timedelta(days=REVIEW_WINDOW) for o in trips):
                return False
    return True


def ended(t, today):
    """A trip with no date on file (date: none) counts as ended; otherwise its last day is before today."""
    if t.get("date") == "none":
        return True
    e = iso(t.get("end"))
    return bool(e and e < today)


def counts(t, today):
    """Trips that count as led: a finished trip that ran (had bookings), not cancelled, not an event."""
    return (t.get("status", "") not in SKIP_STATUS and ended(t, today) and t.get("ran")
            and t.get("kind", "trip") == "trip")


def trips_led_of(conf, hist, today):
    names = set(conf.get("feed", []))
    return [trip_out(tab, t) for tab, t in hist.items() if names & set(t.get("leaders", [])) and counts(t, today)]


def place(dest):
    return PLACES.get(dest, (dest, dest, "", ""))


def flag(cc):
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in cc) if len(cc or "") == 2 else ""


def trip_out(tab, t):
    label, tag, page, cc = place(t.get("dest", ""))
    o = {"tab": tab, "trip": t["trip"], "start": t["start"], "end": t["end"], "place": t.get("place") or label, "tag": tag,
         "page": page, "kind": t.get("kind", "trip")}
    if cc:
        o["flag"], o["country"] = flag(cc), COUNTRY.get(cc, "")
    for k in ("note", "date"):              # date: month, year or none when the exact days are not known
        if t.get(k):
            o[k] = t[k]
    return o


def exact(o):
    """Only trips with exact dates are matched to reviews."""
    return not o.get("date") and iso(o.get("start")) and iso(o.get("end"))


def merge_older(hist, older):
    """history.json plus the trips before it (older-trips.json). Returns a new dict; history.json is not changed."""
    out = dict(hist)
    for tab, t in (older.get("trips") or {}).items():
        if tab in out:
            continue
        o = {k: v for k, v in t.items() if k != "src"}
        o.update({"kind": "trip", "status": "DONE", "ran": True})
        out[tab] = o
    for tab, x in (older.get("add_leaders") or {}).items():
        if tab in out:
            o = dict(out[tab])
            o["leaders"] = o.get("leaders", []) + [n for n in x.get("leaders", []) if n not in o.get("leaders", [])]
            out[tab] = o
    return out


def newest_first(o):
    return (o["start"] or "0000", o["tab"])


def leader_view(key, conf, hist, feed, today, reviews, extras, picks, exclude, rivals=None, staff=None, known=None):
    names = set(conf.get("feed", []))
    mine = {tab: t for tab, t in hist.items() if names & set(t.get("leaders", []))
            and t.get("status", "") not in SKIP_STATUS}
    # coming up: what the feed says now (it is the live HQ list); without the feed, history
    if feed is not None:
        tabs = [r["hub_tab"] for r in feed if r.get("hub_tab") and names & {
            x.strip() for x in r.get("leaders", "").split("/")}]
    else:
        tabs = list(mine)
    upcoming = sorted([trip_out(tab, hist[tab]) for tab in set(tabs)
                       if tab in hist and iso(hist[tab]["end"]) and iso(hist[tab]["end"]) >= today
                       and hist[tab].get("status", "") not in SKIP_STATUS],
                      key=lambda o: (o["start"], o["trip"]))
    led = sorted([trip_out(tab, t) for tab, t in mine.items() if ended(t, today) and t.get("ran")],
                 key=newest_first, reverse=True)
    trips_led = [o for o in led if o["kind"] == "trip"]

    def about(day):
        cands = [o for o in trips_led if exact(o) and iso(o["start"]) <= day <= iso(o["end"]) + datetime.timedelta(days=REVIEW_WINDOW)]
        return max(cands, key=lambda o: o["start"]) if cands else None

    aliases = conf.get("aliases") or [conf.get("first", "")]
    rivals = rivals or {}
    found = []
    for r in reviews:
        d = iso(r.get("date"))
        if not d or r.get("rating") != 5 or not has_name(r.get("text", ""), aliases):
            continue
        t = about(d)
        if t and not owns_review(r.get("text", ""), d, aliases, rivals):
            continue
        if t and staff and is_staff(r.get("name", ""), staff):
            continue                      # reviews written by SYB leaders or staff are not guest reviews
        if t:
            found.append(({"id": r.get("gid") or r.get("url"), "who": short_name(r["name"]), "src": "Google",
                           "date": r["date"], "url": r.get("url", "")}, r.get("text", ""), t))
    for x in extras:
        if key not in (x.get("leaders") or [x.get("leader")]):
            continue
        t = next((o for o in trips_led if o["tab"] == x.get("tab")), None)
        if t:
            found.append(({"id": x["id"], "who": short_name(x["who"]), "src": x.get("src", ""),
                           "date": x["date"], "url": x.get("url", "")}, x.get("text", ""), t))
    out = []
    for o, text, t in found:
        p = picks.get(o["id"], {})
        if p.get("leader") and p["leader"] != key:
            p = {}                        # a hand pick belongs to the leader it was picked for
        if p.get("hide"):
            continue
        if p.get("q"):
            o["q"], o["more"] = p["q"], p.get("more", [])
        else:
            o["q"], _ = excerpt(text, aliases, exclude)
            o["more"] = []
        if not o["q"]:
            continue
        o["named"] = has_name(" ".join([o["q"]] + o["more"]), aliases)
        if not o["named"] and not p.get("q"):
            continue                      # the only lines naming them were left out (they also name someone excluded)
        o["feature"] = bool(p.get("feature"))
        o.update({"trip": t["trip"], "tag": t["tag"], "trip_start": t["start"], "page": t["page"]})
        o["_score"] = quote_score(" ".join([o["q"]] + o["more"]), aliases, known or set())
        out.append(o)
    feature = [o for o in out if o["feature"]][:1]
    if not feature and out:
        # the big quote: the one most about this leader (fewest other names, a real sentence), newest trip on a tie
        feature = [max(out, key=lambda o: (o["_score"], o["trip_start"], o["date"]))]
        f = feature[0]
        f["feature"] = True
        if not f["more"]:                 # big type: lead with the first sentence, the rest goes underneath
            parts = [x for x in sentences(f["q"]) if x != "…"]
            if len(parts) > 1 and len(parts[0]) >= 25:
                f["q"], f["more"] = parts[0], [" ".join(parts[1:]).replace(" … ", " ")]
    rest = sorted([o for o in out if o not in feature], key=lambda o: (o["trip_start"], o["date"]), reverse=True)
    out = (feature + rest)[:MAX_REVIEWS]
    for o in out:
        o.pop("_score", None)

    return {
        "key": key, "name": conf["name"], "first": conf.get("first", conf["name"].split()[0]),
        "aliases": [a for a in conf.get("aliases", []) if a != conf.get("first")],
        "upcoming": upcoming,
        "led": [o for o in led if o["kind"] == "trip"],
        "events": [o for o in led if o["kind"] == "event"],
        "stats": {"led": len(trips_led), "countries": len({o["country"] for o in trips_led if o.get("country")}),
                  "since": min([o["start"][:4] for o in trips_led if o["start"]] or [""]),
                  "upcoming": len([o for o in upcoming if o["kind"] == "trip"])},
        "reviews": out,
    }


def squad_live(view):
    """The live part of one person on the Leaders page (/squad): trips led, countries, flags, trips coming up."""
    tally, order = {}, []
    for o in view.get("led", []):
        c = o.get("country")
        if not c:
            continue
        if c not in tally:
            tally[c] = [o.get("flag", ""), 0]
            order.append(c)
        tally[c][1] += 1
    top = sorted(order, key=lambda c: -tally[c][1])          # stable: ties keep the order first led
    up = [{"t": u["trip"], "pl": u.get("place", ""), "f": u.get("flag", ""), "c": u.get("country", ""), "s": u["start"],
           "e": u["end"], "pg": u.get("page", "")} for u in view.get("upcoming", []) if u.get("kind", "trip") == "trip"]
    st = view.get("stats", {})
    return {"led": st.get("led", 0), "countries": st.get("countries", 0), "since": st.get("since", ""),
            "flags": [[tally[c][0], c] for c in top[:5]], "cc": {c: tally[c][1] for c in top}, "up": up[:6]}


def write_squad(today, dry=False):
    """dist/leaders/squad.json for the Leaders page: who is on it (data/leaders/squad-static.json, written by
    render-squad.py: names, labels, photos, story slides) plus their live trips from dist/leaders/<key>.json."""
    static = load(os.path.join(DATA, "squad-static.json"))
    if not static:
        return False
    people = []
    for p in static["people"]:
        view = load(os.path.join(OUT, p["key"] + ".json"), {})
        people.append(dict(p, **squad_live(view)))
    doc = {"people": people, "team": static.get("team", [])}
    path = os.path.join(OUT, "squad.json")
    old = load(path, {})
    if {k: v for k, v in old.items() if k != "built"} == doc:
        return False
    doc["built"] = today.isoformat()
    if not dry:
        with open(path, "w") as f:
            json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", help="saved copy of the TRIPS tab (CSV)")
    ap.add_argument("--today", help="YYYY-MM-DD")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    today = iso(a.today) if a.today else datetime.datetime.now(NY).date()

    conf = load(os.path.join(DATA, "leaders.json"))
    hist_doc = load(os.path.join(DATA, "history.json"), {"trips": {}})
    hist = hist_doc["trips"]
    feed = read_feed(a.feed)
    log = {"today": today.isoformat(), "feed_rows": len(feed) if feed is not None else "unreadable"}
    log["history_changed"] = update_history(hist, feed) if feed is not None else 0

    older = load(os.path.join(DATA, "older-trips.json"), {})
    allhist = merge_older(hist, older)

    reviews = load(os.path.join(ROOT, "data", "google-reviews.json"), [])
    extras = load(os.path.join(DATA, "extra-reviews.json"), {}).get("reviews", [])
    picks = load(os.path.join(DATA, "picks.json"), {})
    exclude = conf.get("exclude_names", [])

    led = {key: trips_led_of(c, allhist, today) for key, c in conf["leaders"].items()}
    staff = {x.lower() for x in conf.get("staff", [])}
    for c in conf["leaders"].values():
        staff |= {c["name"].lower(), short_name(c["name"]).lower()}
    names = set(conf.get("staff_first_names", []))
    for c in conf["leaders"].values():
        names |= set(c.get("aliases", [])) | {c.get("first", "")}
    by_alias = {}
    for key, c in conf["leaders"].items():
        for al in c.get("aliases") or [c.get("first", "")]:
            by_alias.setdefault(al, []).append(key)

    written = []
    for key, c in conf["leaders"].items():
        rivals = {al: [(k, led[k]) for k in ks if k != key] for al, ks in by_alias.items() if key in ks and len(ks) > 1}
        view = leader_view(key, c, allhist, feed, today, reviews, extras, picks, exclude, rivals, staff, names)
        path = os.path.join(OUT, key + ".json")
        old = load(path, {})
        if {k: v for k, v in old.items() if k != "built"} == view:
            continue
        view["built"] = today.isoformat()
        written.append(key)
        if not a.dry:
            os.makedirs(OUT, exist_ok=True)
            with open(path, "w") as f:
                json.dump(view, f, ensure_ascii=False, separators=(",", ":"))
                f.write("\n")
        else:
            print(json.dumps(view, ensure_ascii=False, indent=1)[:3000])
    if log["history_changed"] and not a.dry:
        hist_doc["trips"] = dict(sorted(hist.items(), key=lambda kv: (kv[1]["start"], kv[0])))
        with open(os.path.join(DATA, "history.json"), "w") as f:
            json.dump(hist_doc, f, ensure_ascii=False, indent=1)
            f.write("\n")
    log["written"] = written
    log["squad"] = write_squad(today, a.dry)
    print(json.dumps(log))
    if feed is None:
        print("WARNING: could not read SYB Public Feed (no guest data); pages keep their trips from history", file=sys.stderr)


if __name__ == "__main__":
    main()
