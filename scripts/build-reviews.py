#!/usr/bin/env python3
"""
Build small per-trip review files from data/google-reviews.json.

  python3 scripts/build-reviews.py

Writes dist/reviews/<trip>.json and dist/reviews/all.json.
Review photos saved in the repo are stored as paths relative to dist/reviews/ (photos/<id>.jpg).
Each file: {"meta": {...}, "reviews": [...]} with 5-star, text-bearing reviews only,
newest first, capped so a trip page never downloads more than it shows.
Trip keyword lists mirror the filters the Elfsight widgets used (e.g. Morocco = "morocco", "sybmorocco").
"""
import json, os, sys, datetime

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


def build(reviews, updated=None):
    """Return {file name: JSON text} for dist/reviews/. Pure function, used by scripts/refresh.py too."""
    total = len(reviews)
    rating = round(sum(r["rating"] for r in reviews) / total, 1)
    meta = {"total": total, "rating": f"{rating:.1f}", "updated": updated or datetime.date.today().isoformat()}
    good = sorted([r for r in reviews if keep(r)], key=lambda r: r["date"], reverse=True)
    out = {}

    def pack(items):
        return json.dumps({"meta": meta, "reviews": [slim(r) for r in items]}, ensure_ascii=False, separators=(",", ":"))

    # homepage / generic: newest with photos first
    withp = [r for r in good if r.get("images")]
    nop = [r for r in good if not r.get("images")]
    out["all.json"] = pack((withp + nop)[:CAP])

    for trip, kws in TRIPS.items():
        hits = [r for r in good if any(k in r["text"].lower() for k in kws)]
        # " nice" as a word only, so "nice people" doesn't count as the city of Nice
        if trip == "riviera":
            hits = [r for r in hits if any(k in r["text"].lower() for k in kws if k != "nice")
                    or " in nice" in r["text"].lower()]
        out[trip + ".json"] = pack(hits[:CAP])
    return out


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reviews = json.load(open(os.path.join(root, "data", "google-reviews.json"), encoding="utf-8"))
    out_dir = os.path.join(root, "dist", "reviews")
    os.makedirs(out_dir, exist_ok=True)
    for name, text in build(reviews).items():
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{name:<18} {len(json.loads(text)['reviews']):>3} reviews  {len(text.encode())/1024:6.1f} KB")
    print(f"\nsource: {len(reviews)} reviews")


if __name__ == "__main__":
    sys.exit(main())
