"""
SYB widgets data refresh. Runs inside the Composio workbench (not on a laptop, not in GitHub Actions).

Why there: the workbench already holds the connected Instagram account (@surfyogabeer) and a GitHub
connection with push access to this repo, so no token or key ever lives in this repo.

One workbench cell:

    import requests
    exec(requests.get("https://raw.githubusercontent.com/mantas-crypto/syb-widgets/main/scripts/refresh.py").text)
    print(refresh())                 # daily
    print(refresh(full=True))        # re-read every Instagram post (after changing DEST_WORDS);
                                     # run it in a cell of its own, twice, the second run finishes the photos

What it does
  Instagram  our own posts, matched to trips by caption words (same idea as the old Elfsight filters,
             but stricter: one destination per caption, no repeated caption, no repeated picture),
             newest 24 per trip, images copied into dist/instagram/p/ (Instagram's own links expire).
  Reviews    merged into data/google-reviews.json, photos copied into dist/reviews/photos/ while Google's
             links still work, then per-trip files rebuilt with scripts/build-reviews.py.
             Source today: Elfsight's public endpoint (works until Elfsight is cancelled).
             Source later: Google Business Profile API (waiting on Google, case 7-4355000041774).
  Commit     one commit on main through the GitHub API, then a jsDelivr purge for changed JSON.

Pages load widget code pinned to a commit SHA and data from @main (data-ref="main"), so a commit here
updates the site without touching Easol. A run with nothing new makes no commit.
"""
import base64, datetime, hashlib, io, json, time
from concurrent.futures import ThreadPoolExecutor

import requests

REPO = "mantas-crypto/syb-widgets"
BRANCH = "main"
PER_TRIP = 24
IMG_PX = 480
PLACE = "ChIJyTABhtFZwokRR1ZQGo0WF7Y"  # SYB on Google Maps

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
        d = r["data"]
        items += d.get("data", [])
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
        cache = "/home/user/syb-ig-full.json"
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
            key = lambda r: r.get("url") or (r["name"] + "|" + r["date"])
            have = {key(r): r for r in data}
            new = 0
            for r in _elfsight_reviews():
                cur = have.get(key(r))
                if cur is None:
                    r["images"] = []
                    have[key(r)] = cur = r
                    new += 1
                else:
                    for k in ("name", "avatar", "rating", "date", "text"):
                        cur[k] = r[k]
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
    for p in changed_json:
        try:
            purged += requests.get("https://purge.jsdelivr.net/gh/%s@%s/%s" % (REPO, BRANCH, p), timeout=15).status_code == 200
        except Exception:
            pass
    log["purged"] = purged
    log["seconds"] = round(time.time() - t0)
    return log
