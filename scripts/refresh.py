"""
SYB widgets data refresh.

Runs every day in GitHub Actions (.github/workflows/refresh.yml, through scripts/run_in_actions.py).
It can also still run by hand inside the Composio workbench, where it was first written.

It needs two helpers from whatever runs it:
    proxy_execute(...)       GitHub API calls
    run_composio_tool(...)   the connected Instagram account (@surfyogabeer) through Composio
and uses a third one when it is there:
    google_api(...)          Google Business Profile API calls (the reviews), signed in as SYB's Google account
The workbench has the first two built in. In GitHub Actions run_in_actions.py supplies all three, using the
job's own GitHub token and repo secrets (COMPOSIO_API_KEY, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN).
No key is ever written in this repo.

By hand, one workbench cell (paste this file's contents in first):

    print(refresh())                 # daily
    print(refresh(full=True))        # re-read every Instagram post (after changing DEST_WORDS);
                                     # run it in a cell of its own, twice, the second run finishes the photos
In GitHub: Actions, "Widgets data refresh", Run workflow (tick "full" for the every-post read).

What it does
  Instagram  our own posts, matched to trips by caption words (same idea as the old Elfsight filters,
             but stricter: one destination per caption, no repeated caption, no repeated picture),
             newest 24 per trip, images copied into dist/instagram/p/ (Instagram's own links expire).
  Reviews    merged into data/google-reviews.json, photos copied into dist/reviews/photos/ while Google's
             links still work, then per-trip files rebuilt with scripts/build-reviews.py.
             Source: Google Business Profile API (access approved Oct 7 2026, case 7-4355000041774,
             signed in Oct 10 2026). If the google_api helper is missing or Google fails, it falls back
             to Elfsight's public endpoint, which only works until the Elfsight plan ends (Oct 28 2026).
             Google also sends review photos, so reviews whose photos were lost get them back, a few
             dozen reviews per run.
  Commit     one commit on main through the GitHub API, then a jsDelivr purge for changed JSON.

Pages load widget code pinned to a commit SHA and data from @main (data-ref="main"), so a commit here
updates the site without touching Easol. A run with nothing new makes no commit.
"""
import base64, datetime, hashlib, io, json, os, tempfile, time
from concurrent.futures import ThreadPoolExecutor

import requests

REPO = "mantas-crypto/syb-widgets"
BRANCH = "main"
PER_TRIP = 24
IMG_PX = 480
PLACE = "ChIJyTABhtFZwokRR1ZQGo0WF7Y"  # SYB on Google Maps
STARS = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
PHOTO_BACKFILL = 40   # older reviews per run that get their lost photos back from Google

# Caption words per destination (lowercase). A post goes on a trip's grid only when its caption names
# that destination and no other one, so roundups ("summer 2027 is live", monthly recaps) stay off.
DEST_WORDS = {
    "morocco": ["morocco"], "croatia": ["croatia"], "bali": ["bali"], "egypt": ["egypt"],
    "nicaragua": ["nicaragua"], "philippines": ["palawan", "philippines"],
    "chamonix": ["chamonix"], "turkey": ["turkey"], "japan": ["japan"], "iceland": ["iceland"],
    "kenya": ["kenya", "safari"], "amalfi": ["amalfi"], "dolomites": ["dolomites"],
    "belize": ["belize"], "greece": ["greece"], "ibiza": ["ibiza"], "riviera": ["riviera"],
    "costarica": ["costa rica", "costarica"], "portugal": ["portugal"], "colombia": ["colombia"],
    "mexico": ["mexico", "tulum"], "australia": ["australia"], "china": ["china"],
    "thailand": ["thailand"], "peru": ["peru"], "spain": ["spain", "mallorca"],
}
# Grids this job owns (dist/instagram/<name>.json). sybbelize and sybibiza are hand-picked and left alone.
GRIDS = ["morocco", "croatia", "bali", "egypt", "nicaragua", "philippines", "chamonix", "turkey",
         "japan", "iceland", "kenya", "amalfi", "dolomites"]


def _gh(method, path, body=None, query=None):
    r, e = proxy_execute(method, "/repos/" + REPO + path, "github", query_params=query, body=body)  # noqa: F821
    if e:
        raise RuntimeError("github %s %s: %s" % (method, path, e))
    d = r.get("data") if hasattr(r, "get") else None
    return d if isinstance(d, (dict, list)) and not any(k in r for k in ("sha", "tree", "object", "ref")) else r


def _blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def _jpeg(raw, px):
    """Return (jpeg bytes, 64-bit average hash as hex). The hash spots the same picture posted twice."""
    from PIL import Image
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    im.thumbnail((px, px))
    out = io.BytesIO()
    im.save(out, "JPEG", quality=80, optimize=True, progressive=True)
    g = list(im.convert("L").resize((8, 8)).getdata())
    avg = sum(g) / 64.0
    return out.getvalue(), "%016x" % int("".join("1" if v > avg else "0" for v in g), 2)


def _far(h, others):
    return all(bin(int(h, 16) ^ int(o, 16)).count("1") > 5 for o in others)


def _get(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and len(r.content) > 2000:
            return r.content
    except Exception:
        pass
    return None


def _ig_media(pages):
    items, after = [], None
    for _ in range(pages):
        a = {"ig_user_id": "me", "limit": 100,
             "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,shortcode"}
        if after:
            a["after"] = after
        r, e = run_composio_tool("INSTAGRAM_GET_IG_USER_MEDIA", a)  # noqa: F821
        if e:
            raise RuntimeError("instagram: %s" % e)
        d = r.get("data") if isinstance(r, dict) else None
        if not isinstance(d, dict) or not isinstance(d.get("data"), list):
            raise RuntimeError("instagram: the answer held no list of posts (it held: %s)"
                               % (", ".join(sorted(r)) if isinstance(r, dict) else type(r).__name__)[:200])
        items += d["data"]
        pg = d.get("paging") or {}
        after = (pg.get("cursors") or {}).get("after")
        if not after or not pg.get("next"):
            return items, True
    return items, False


def _day(v):
    if isinstance(v, (int, float)):
        return datetime.datetime.fromtimestamp(v, datetime.timezone.utc).date().isoformat()
    return str(v or "")[:10]


def _elfsight_reviews():
    out, page = [], 1
    while page < 12:
        r = requests.get("https://service-reviews-ultimate.elfsight.com/data/reviews",
                         params={"uris[]": PLACE, "page_length": 100, "order": "date", "page": page}, timeout=20)
        if r.status_code != 200:
            raise RuntimeError("elfsight %s" % r.status_code)
        rows = (r.json().get("result") or {}).get("data") or []
        if not rows:
            break
        out += rows
        if len(rows) < 100:
            break
        page += 1
    if len(out) < 100:
        raise RuntimeError("elfsight returned only %d reviews" % len(out))
    return [{
        "name": x.get("reviewer_name") or "",
        "avatar": x.get("reviewer_picture_url") or "",
        "rating": x.get("rating") or 0,
        "date": _day(x.get("published_at")),
        "text": x.get("text") or "",
        "url": x.get("url") or "",
        "src_images": [i.get("url") if isinstance(i, dict) else i for i in (x.get("images") or [])],
    } for x in out]


# ---------- Google Business Profile ----------
GBP_ACCOUNTS = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
GBP_INFO = "https://mybusinessbusinessinformation.googleapis.com/v1/"
GBP_V4 = "https://mybusiness.googleapis.com/v4/"
_gbp = {}


def _gbp_location():
    """accounts/<a>/locations/<l> of the profile whose Maps place id is PLACE, found once per run, so a move
    of the profile to another Google account or location group needs no code change."""
    if "loc" not in _gbp:
        for acct in google_api("GET", GBP_ACCOUNTS).get("accounts") or []:  # noqa: F821
            token = None
            while True:
                q = {"readMask": "name,metadata", "pageSize": 100}
                if token:
                    q["pageToken"] = token
                j = google_api("GET", GBP_INFO + acct["name"] + "/locations", q)  # noqa: F821
                for loc in j.get("locations") or []:
                    if (loc.get("metadata") or {}).get("placeId") == PLACE:
                        _gbp["loc"] = acct["name"] + "/" + loc["name"]
                        return _gbp["loc"]
                token = j.get("nextPageToken")
                if not token:
                    break
        raise RuntimeError("google: this sign-in sees no Business Profile with place id %s" % PLACE)
    return _gbp["loc"]


def _g_text(c):
    """Google sends non-English reviews as '(Translated by Google) ... (Original) ...': keep the English."""
    c = (c or "").strip()
    if "(Translated by Google)" in c:
        c = c.split("(Translated by Google)", 1)[1].split("(Original)", 1)[0]
    return c.strip()


def _g_big(u):
    """Review photos come as small thumbnails; the same link with =s1200 gives the full picture."""
    base, sep, opts = u.rpartition("=")
    return (base if sep and "/" not in opts else u) + "=s1200"


def _google_reviews():
    loc = _gbp_location()
    rows, token = [], None
    for _ in range(40):
        q = {"pageSize": 50}
        if token:
            q["pageToken"] = token
        j = google_api("GET", GBP_V4 + loc + "/reviews", q)  # noqa: F821
        rows += j.get("reviews") or []
        token = j.get("nextPageToken")
        if not token:
            break
    if len(rows) < 100:
        raise RuntimeError("google returned only %d reviews" % len(rows))
    out = []
    for x in rows:
        who = x.get("reviewer") or {}
        out.append({
            "gid": x.get("reviewId") or (x.get("name") or "").split("/")[-1],
            "name": (who.get("displayName") or "").strip() or "A Google user",
            "avatar": who.get("profilePhotoUrl") or "",
            "rating": STARS.get(x.get("starRating"), 0),
            "date": (x.get("createTime") or "")[:10],
            "text": _g_text(x.get("comment")),
            "url": "",
            "src_images": [_g_big(m["thumbnailUrl"]) for m in x.get("reviewMediaItems") or [] if m.get("thumbnailUrl")],
        })
    return out


def _norm(s):
    """Lowercase letters and digits only, single spaces: for comparing names and review words."""
    return " ".join("".join(ch if ch.isalnum() else " " for ch in (s or "").lower()).split())


def _ratio(a, b):
    import difflib
    return difflib.SequenceMatcher(None, _norm(a)[:300], _norm(b)[:300]).ratio()


def _same_words(a, b):
    """True when two texts are the same review (Elfsight and Google can differ in spacing and punctuation,
    and a reviewer may have edited a few words)."""
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return False
    n = min(len(a), len(b), 60)
    return (n >= 20 and a[:n] == b[:n]) or _ratio(a, b) >= 0.8


def _days(a, b):
    try:
        return abs((datetime.date.fromisoformat(a) - datetime.date.fromisoformat(b)).days)
    except ValueError:
        return 9999


def refresh(**kw):
    """Quiet wrapper: the workbench helpers print every API response, which would bury the summary."""
    import contextlib
    if "run_composio_tool" not in globals() or "proxy_execute" not in globals():
        # Seen Oct 8 2026: a long-lived workbench lost its helpers. A fresh workbench has them.
        return {"error": "HELPERS_MISSING", "fix": "run import os; os._exit(0) in its own cell, then run again"}
    with contextlib.redirect_stdout(io.StringIO()):
        return _refresh(**kw)


def _refresh(full=False, budget=140, reviews=True, dry=False):
    t0 = time.time()
    today = datetime.date.today().isoformat()
    log = {"date": today}

    head = _gh("GET", "/git/ref/heads/" + BRANCH)["object"]["sha"]
    base_tree = _gh("GET", "/git/commits/" + head)["tree"]["sha"]
    tree = {t["path"]: t["sha"] for t in _gh("GET", "/git/trees/" + base_tree, query={"recursive": "1"})["tree"]
            if t["type"] == "blob"}

    def read(path):
        if path not in tree:
            return None
        b = _gh("GET", "/git/blobs/" + tree[path])
        return base64.b64decode(b["content"])

    files, deletes = {}, []   # path -> bytes

    # ---------- Instagram ----------
    index = json.loads(read("data/instagram-posts.json") or b"{}")
    if full:
        # reading every post takes about 90 seconds, so keep the list for two hours:
        # call refresh(full=True) again if the first call reports "partial" or too few new images
        cache = os.path.join(tempfile.gettempdir(), "syb-ig-full.json")
        try:
            c = json.load(open(cache))
            items, complete = (c["items"], True) if time.time() - c["at"] < 7200 else (None, None)
        except Exception:
            items = None
        if items is None:
            items, complete = _ig_media(60)
            json.dump({"at": time.time(), "items": items}, open(cache, "w"))
            budget += 90      # the read itself should not eat the time meant for photos
    else:
        items, complete = _ig_media(3)
    fresh = {}
    for m in items:
        cap = (m.get("caption") or "").lower()
        code = m.get("shortcode") or m["permalink"].rstrip("/").split("/")[-1]
        fresh[code] = m.get("thumbnail_url") if m.get("media_type") == "VIDEO" else m.get("media_url")
        e = index.setdefault(code, {})
        e["date"] = m["timestamp"][:10]
        e["dest"] = [d for d, ws in DEST_WORDS.items() if any(w in cap for w in ws)]
        e["k"] = hashlib.sha1("".join(ch for ch in cap if ch.isalnum())[:60].encode()).hexdigest()[:8]
    if items:  # posts deleted on Instagram inside the window we just read
        oldest = min(m["timestamp"][:10] for m in items)
        for code in [c for c, v in index.items() if c not in fresh and (complete or v["date"] > oldest)]:
            del index[code]
    log["instagram_posts_read"] = len(items)

    def path_of(code):
        return "dist/instagram/p/%s.jpg" % code

    def ready(code):
        return path_of(code) in tree and index[code].get("h")

    cands = {t: sorted(((v["date"], c) for c, v in index.items() if v.get("dest") == [t]), reverse=True)
             for t in GRIDS}
    def fetch_ig(code):
        raw = _get(fresh[code])
        try:
            return code, _jpeg(raw, IMG_PX) if raw else None
        except Exception:
            return code, None

    got, used, changed_json, new_imgs = {}, set(), [], 0
    for t in GRIDS:
        posts, keys, hashes = [], set(), []
        for i in range(0, len(cands[t]), 16):     # small batches keep the workbench's memory low
            batch = cands[t][i:i + 16]
            want = [c for _, c in batch if c not in got and not ready(c) and fresh.get(c)]
            if want and time.time() - t0 < budget * 0.6:
                with ThreadPoolExecutor(4) as ex:
                    for code, r in ex.map(fetch_ig, want):
                        if r:
                            got[code] = r[0]
                            index[code]["h"] = r[1]
            for date, code in batch:
                v = index[code]
                if not (code in got or ready(code)):
                    continue          # image not saved and no fresh link: waits for a full run
                if v["k"] in keys or not _far(v["h"], hashes):
                    continue          # same caption or same picture as a tile already on the grid
                keys.add(v["k"])
                hashes.append(v["h"])
                posts.append({"code": code, "user": "surfyogabeer", "date": date, "img": "p/%s.jpg" % code})
                used.add(path_of(code))
                if code in got and path_of(code) not in files:
                    files[path_of(code)] = got[code]
                    new_imgs += 1
                if len(posts) >= PER_TRIP:
                    break
            if len(posts) >= PER_TRIP:
                break
        path = "dist/instagram/%s.json" % t
        old = json.loads(read(path) or b"{}")
        if old.get("posts") != posts and posts:
            files[path] = json.dumps({"tag": t, "alt": "SurfYogaBeer " + t.title(), "updated": today,
                                      "posts": posts}, indent=1).encode()
            changed_json.append(path)
    log["instagram_images_new"] = new_imgs
    deletes = [p for p in tree if p.startswith("dist/instagram/p/") and p not in used]
    files["data/instagram-posts.json"] = json.dumps(index, separators=(",", ":"), sort_keys=True).encode()

    # ---------- Reviews ----------
    if reviews:
        try:
            data = json.loads(read("data/google-reviews.json"))
            # one key per review: its Maps link (Elfsight era), else its Google id, else name and date
            key = lambda r: r.get("url") or ("g:" + r["gid"] if r.get("gid") else r["name"] + "|" + r["date"])
            have = {key(r): r for r in data}
            rows, source = None, "elfsight"
            if "google_api" in globals():
                try:
                    rows, source = _google_reviews(), "google"
                except Exception as e:  # Elfsight's endpoint still answers until Oct 28 2026
                    log["google_error"] = str(e)[:200]
            if rows is None:
                rows = _elfsight_reviews()
            log["reviews_source"] = source
            # Reviews saved from Elfsight carry its Maps link but no Google review id. Elfsight also stored
            # rough dates for older reviews, so a Google review is matched by its id, then by reviewer name
            # and the words of the review, then name and date, then the words alone (a renamed account), then
            # the name alone when that person has just one review on Google.
            by_gid = {r["gid"]: k for k, r in have.items() if r.get("gid")}
            by_name, by_words = {}, {}
            for k, r in have.items():
                by_name.setdefault(_norm(r["name"]), []).append(k)
                if len(_norm(r["text"])) >= 40:
                    by_words.setdefault(_norm(r["text"])[:60], []).append(k)
            g_names = {}
            for r in rows:
                g_names[_norm(r["name"])] = g_names.get(_norm(r["name"]), 0) + 1
            how = {}

            def match(r):
                if r.get("gid"):
                    if r["gid"] in by_gid:
                        return by_gid[r["gid"]], "id"
                    free = [k for k in by_name.get(_norm(r["name"]), []) if not have[k].get("gid")]
                    for k in free:
                        if _same_words(have[k]["text"], r["text"]):
                            return k, "name and words"
                    for k in free:
                        c = have[k]
                        if c["date"] == r["date"] or (_days(c["date"], r["date"]) <= 1 and c["rating"] == r["rating"]):
                            return k, "name and date"
                    if len(_norm(r["text"])) >= 40:
                        for k in by_words.get(_norm(r["text"])[:60], []):
                            if not have[k].get("gid"):
                                return k, "words"
                    if free and g_names.get(_norm(r["name"])) == 1:
                        return max(free, key=lambda k: (_ratio(have[k]["text"], r["text"]), have[k]["date"])), "name"
                    return None, None
                if key(r) in have:
                    return key(r), "link"
                # Elfsight fallback: a review first saved from Google has no Maps link to match on
                return next((k for k in by_name.get(_norm(r["name"]), [])
                             if not have[k].get("url") and have[k]["date"] == r["date"]), None), "name and date"

            new, backfill, new_gids = 0, 0, set()
            for r in rows:
                k, why = match(r)
                cur = have.get(k) if k else None
                how[why or "new"] = how.get(why or "new", 0) + 1
                if cur is None:
                    r["images"] = []
                    if r.get("gid"):
                        r["g_media"] = True
                        new_gids.add(r["gid"])
                        by_gid[r["gid"]] = key(r)
                    have[key(r)] = r
                    new += 1
                    continue
                for f in ("name", "avatar", "rating", "date", "text"):
                    if r[f] not in ("", 0, None):
                        cur[f] = r[f]
                if r.get("gid"):
                    cur["gid"] = r["gid"]
                    by_gid[r["gid"]] = k
                    # Elfsight-era reviews lost most guest photos (Google's old links die within days).
                    # Google's API sends them again: bring them back, a few dozen reviews per run.
                    if r["src_images"] and not cur.get("images") and not cur.get("g_media") \
                            and backfill < PHOTO_BACKFILL:
                        cur["src_images"], cur["photos_checked"], cur["g_media"] = r["src_images"], False, True
                        backfill += 1
                else:
                    cur.setdefault("src_images", r["src_images"])
            # copy guest photos while Google's links are alive (they die within days)
            todo = [(k, u) for k, r in have.items() if not r.get("photos_checked") for u in (r.get("src_images") or [])[:4]]

            def fetch_ph(ku):
                raw = _get(ku[1], 8)
                try:
                    return ku, _jpeg(raw, 720)[0] if raw else None
                except Exception:
                    return ku, None
            saved = 0
            with ThreadPoolExecutor(8) as ex:
                for (k, u), b in ex.map(fetch_ph, todo):
                    if b:
                        name = "photos/%s.jpg" % hashlib.sha1(u.encode()).hexdigest()[:14]
                        files["dist/reviews/" + name] = b
                        if name not in have[k]["images"]:
                            have[k]["images"].append(name)
                        saved += 1
            for r in have.values():
                r["photos_checked"] = True
                r.pop("src_images", None)
            data = sorted(have.values(), key=lambda r: r["date"], reverse=True)
            ns = {"__name__": "build_reviews"}
            exec(read("scripts/build-reviews.py").decode(), ns)
            old_updated = (json.loads(read("dist/reviews/all.json") or b"{}").get("meta") or {}).get("updated")
            built = ns["build"](data, old_updated)
            if any(_blob_sha(t.encode()) != tree.get("dist/reviews/" + n) for n, t in built.items()):
                built = ns["build"](data, today)
                for n, t in built.items():
                    files["dist/reviews/" + n] = t.encode()
                    changed_json.append("dist/reviews/" + n)
            files["data/google-reviews.json"] = json.dumps(data, ensure_ascii=False, indent=1).encode()
            log["reviews_total"], log["reviews_new"], log["review_photos_saved"] = len(data), new, saved
            if backfill:
                log["reviews_photos_back"] = backfill
            log["reviews_matched_by"] = how
            if source == "google":
                # on the site but not on Google any more (deleted by the reviewer, or an Elfsight duplicate)
                log["reviews_not_on_google"] = sum(1 for r in data if not r.get("gid"))
                if new:
                    log["reviews_new_list"] = ["%s %s" % (r["name"], r["date"]) for r in data
                                               if r.get("gid") and r.get("g_media") and r["gid"] in new_gids][:10]
        except Exception as e:  # the Instagram half still ships
            log["reviews_error"] = str(e)[:200]

    # ---------- Commit ----------
    files = {p: b for p, b in files.items() if _blob_sha(b) != tree.get(p)}
    log["files_changed"], log["files_deleted"] = len(files), len(deletes)
    if dry or (not files and not deletes):
        log["commit"] = None
        return log

    def blob(pb):
        p, b = pb
        if time.time() - t0 > budget:
            return p, None
        return p, _gh("POST", "/git/blobs", {"content": base64.b64encode(b).decode(), "encoding": "base64"})["sha"]
    # images first, so a file that lists a photo is never committed before the photo
    order = sorted(files.items(), key=lambda kv: (not kv[0].endswith(".jpg"), kv[0]))
    with ThreadPoolExecutor(6) as ex:
        shas = dict(ex.map(blob, order))
    if any(v is None for v in shas.values()):
        # out of time: commit only the photos that made it; the next run finishes the job
        shas = {p: s for p, s in shas.items() if s and p.endswith(".jpg")}
        deletes, changed_json = [], []
        log["partial"] = True
    entries = [{"path": p, "mode": "100644", "type": "blob", "sha": s} for p, s in shas.items()]
    entries += [{"path": p, "mode": "100644", "type": "blob", "sha": None} for p in deletes]
    if not entries:
        log["commit"] = None
        return log
    new_tree = _gh("POST", "/git/trees", {"base_tree": base_tree, "tree": entries})["sha"]
    msg = "Data refresh %s: %d files" % (today, len(entries)) + (" (partial)" if log.get("partial") else "")
    commit = _gh("POST", "/git/commits", {"message": msg, "tree": new_tree, "parents": [head]})["sha"]
    _gh("PATCH", "/git/refs/heads/" + BRANCH, {"sha": commit})
    log["commit"] = commit
    purged = 0
    # new photos first: until purged, @main can still point at the old commit and answer 404 for a new file
    for p in [x for x in shas if x.endswith(".jpg")] + changed_json:
        try:
            purged += requests.get("https://purge.jsdelivr.net/gh/%s@%s/%s" % (REPO, BRANCH, p), timeout=15).status_code == 200
        except Exception:
            pass
    log["purged"] = purged
    log["seconds"] = round(time.time() - t0)
    return log
