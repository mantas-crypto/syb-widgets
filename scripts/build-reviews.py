#!/usr/bin/env python3
"""
Build small per-trip review files from data/google-reviews.json.

  python3 scripts/build-reviews.py

Writes dist/reviews/<trip>.json and dist/reviews/all.json.
Each file: {"meta": {...}, "reviews": [...]} with 5-star, text-bearing reviews only,
newest first, capped so a trip page never downloads more than it shows.
Trip keyword lists mirror the filters the Elfsight widgets used (e.g. Morocco = "morocco", "sybmorocco").
"""
import json, os, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "google-reviews.json")
OUT = os.path.join(ROOT, "dist", "reviews")
CAP = 40  # max reviews per trip file

TRIPS = {
    "morocco":     ["morocco", "sybmorocco", "sahara", "marrakech"],
    "croatia":     ["croatia", "sybcroatia", "hvar", "split", "dubrovnik", "lopud"],
    "bali":        ["bali", "sybali", "ubud", "canggu"],
    "egypt":       ["egypt", "sybegypt", "cairo", "nile", "pyramid"],
    "nicaragua":   ["nicaragua", "sybnicaragua", "nica", "maderas", "san juan del sur"],
    "nye":         ["nye", "new year"],
    "philippines": ["philippines", "palawan", "el nido", "coron", "sybpalawan"],
    "iceland":     ["iceland", "sybiceland", "reykjavik", "fire and ice", "fire & ice"],
    "kenya":       ["kenya", "sybkenya", "safari", "masai", "nairobi"],
    "amalfi":      ["amalfi", "sybamalfi", "positano", "capri", "sorrento"],
    "dolomites":   ["dolomites", "sybdolomites", "yolo-mites", "cortina"],
    "turkey":      ["turkey", "sybturkey", "cappadocia", "istanbul", "fethiye"],
    "japan":       ["japan", "sybjapan", "tokyo", "kyoto"],
    "belize":      ["belize", "sybelize"],
    "chamonix":    ["chamonix", "sybchamonix"],
    "greece":      ["greece", "sybgreece", "athens", "hydra", "saronic"],
    "ibiza":       ["ibiza", "sybibiza", "eivissa"],
    "riviera":     ["riviera", "cote d'azur", "côte d'azur", "nice", "cannes", "south of france"],
}


def keep(r):
    return r.get("rating") == 5 and len((r.get("text") or "").strip()) >= 40


def slim(r):
    return {
        "name": r["name"],
        "avatar": r.get("avatar", ""),
        "rating": r["rating"],
        "date": r["date"],
        "text": r["text"].strip(),
        "images": [i for i in (r.get("images") or []) if i][:2],
    }


def main():
    reviews = json.load(open(SRC, encoding="utf-8"))
    total = len(reviews)
    rating = round(sum(r["rating"] for r in reviews) / total, 1)
    meta = {"total": total, "rating": f"{rating:.1f}", "updated": datetime.date.today().isoformat()}
    good = sorted([r for r in reviews if keep(r)], key=lambda r: r["date"], reverse=True)

    os.makedirs(OUT, exist_ok=True)

    def write(name, items):
        path = os.path.join(OUT, name + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"meta": meta, "reviews": [slim(r) for r in items]}, f, ensure_ascii=False, separators=(",", ":"))
        return os.path.getsize(path)

    # homepage / generic: newest with photos first
    withp = [r for r in good if r.get("images")]
    nop = [r for r in good if not r.get("images")]
    size = write("all", (withp + nop)[:CAP])
    print(f"all            {min(CAP, len(good)):>3} reviews  {size/1024:6.1f} KB")

    for trip, kws in TRIPS.items():
        hits = [r for r in good if any(k in r["text"].lower() for k in kws)]
        # " nice" as a word only, so "nice people" doesn't count as the city of Nice
        if trip == "riviera":
            hits = [r for r in hits if any(k in r["text"].lower() for k in kws if k != "nice")
                    or " in nice" in r["text"].lower()]
        size = write(trip, hits[:CAP])
        print(f"{trip:<14} {min(CAP, len(hits)):>3} reviews  {size/1024:6.1f} KB")

    print(f"\nsource: {total} reviews, rating {meta['rating']}")


if __name__ == "__main__":
    sys.exit(main())
