#!/usr/bin/env python3
"""
One-time seed of data/leaders/history.json from SYB HQ (done Oct 14 2026).

SYB HQ is private, so the daily job cannot read it. It reads the public Leader Hub Feed instead
(TRIPS tab, which only holds recent and upcoming trips) and adds every trip it sees to history.json.
This script filled history.json with every trip before that, from two HQ tabs exported as JSON
(the Sheets API values.get answer, {"values": [[...], ...]}):

    python3 scripts/seed-leader-history.py MASTER.json EASOL.json

MASTER gives tab, status, destination, dates, leaders and booked; EASOL gives the Easol product name
and the product's own dates. Trips already in history.json keep what the daily job wrote.
Only whether a trip ran (had bookings) is kept, never the number of travelers (since Oct 19 2026).
"""
import datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "leaders", "history.json")


def day(s, year=None):
    s = (s or "").strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    if year:
        try:
            return datetime.datetime.strptime("%s %s" % (s, year), "%b %d %Y").date().isoformat()
        except ValueError:
            pass
    return ""


def num(s):
    try:
        return int(float(str(s).replace(",", "").replace("$", "")))
    except ValueError:
        return 0


def main(master_path, easol_path):
    master = json.load(open(master_path))
    master = master.get("values", master)
    easol = json.load(open(easol_path))
    easol = easol.get("values", easol)
    prod = {}
    for r in easol:
        r = list(r) + [""] * 6
        tab = r[0].strip()
        if tab and not tab.startswith(("▸", "TAB")) and r[1].strip():
            prod[tab] = {"trip": re.sub(r"^RETIRED - ", "", r[1].strip()).split(" (do not")[0],
                         "start": day(r[2]), "end": day(r[3]), "booked": num(r[4])}
    trips, kind = {}, "trip"
    for r in master:
        r = list(r) + [""] * 14
        a = r[0].strip()
        if a.startswith("▸"):
            kind = "event" if "EVENTS" in a else "trip"
            continue
        if not a or a.startswith(("▶", "TAB")) or not r[1].strip().isdigit():
            continue
        yr = r[8].strip()
        start, end = day(r[6], yr), day(r[7], yr)
        if start and end and end < start:          # Dec 27 to Jan 2 crosses the year
            end = day(r[7], str(int(yr) + 1))
        end = end or start
        p = prod.get(a, {})
        if p.get("start") and p.get("end"):
            span = (datetime.date.fromisoformat(p["end"]) - datetime.date.fromisoformat(p["start"])).days
            if span <= 21 or not start:              # multi-month programs keep the HQ dates
                start, end = p["start"], p["end"]
        if not start:
            continue
        trips[a] = {
            "trip": p.get("trip") or re.sub(r"\s*'\d\d$", "", a),
            "start": start, "end": end,
            "dest": r[5].strip(),
            "ran": (num(r[12]) or p.get("booked", 0)) > 0,
            "leaders": [x.strip() for x in r[9].split("/") if x.strip()],
            "kind": kind,
            "status": r[4].strip(),
        }
    hist = {"trips": {}}
    if os.path.exists(OUT):
        hist = json.load(open(OUT))
    for tab, t in trips.items():
        hist["trips"].setdefault(tab, t)
    hist["trips"] = dict(sorted(hist["trips"].items(), key=lambda kv: (kv[1]["start"], kv[0])))
    with open(OUT, "w") as f:
        json.dump(hist, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")
    print("history.json: %d trips (%d from HQ)" % (len(hist["trips"]), len(trips)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
