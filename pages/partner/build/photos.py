# Crops the round 3 photos into the page's img folder.
# spec: out name -> (source, aspect w/h, output width, focus x 0..1, focus y 0..1)
from PIL import Image, ImageOps
import os, sys
U = "/mnt/user-data/uploads/SurfYogaBeer Stuff/"
H = "/tmp/claude-0/-home-claude/9e139bdb-22f3-55e9-9bab-f41b73ed9372/scratchpad/heic/"
IMG = "/home/claude/syb-partners/img/"
SPEC = {
  # round 5: corporate retreat (hero, Ontario card, retreat elements)
  "hero-team-arch.jpg":  (U+"Trip Photos/_web/iceland/i011.jpg", 16/9, 1200, .5, .45),
  "dest-ontario.jpg":    (U+"Trip Photos/_web/dolomites/d081.jpg", 2/1, 900, .5, 0),
  "el-wellness.jpg":     (U+"Trip Photos/_web/ski/s009.jpg", 4/3, 900, .5, .5),
  "el-workshop.jpg":     (U+"Trip Photos/_web/dolomites/d071.jpg", 4/3, 675, .5, .42),
  "el-dinners.jpg":      (U+"Claude outputs/Summit Deck 2026/img/p14.jpg", 4/3, 900, .5, .5),
  "el-activity.jpg":     (U+"Trip Photos/_web/dolomites/d068.jpg", 4/3, 563, .5, .55),
  "el-quiet.jpg":        (U+"Trip Photos/_web/iceland/i013.jpg", 4/3, 900, .5, .5),
  # step 1: the Custom card (Dolomites crew on a peak)
  "dest-custom.jpg":     (U+"Trip Photos/_web/dolomites/d049.jpg", 3/2, 900, .5, .5),
  # step 3
  "stay-yoga-deck.jpg":  (U+"Villas Playa Maderas photos/vpm-yoga-deck.jpg", 1, 700, .5, .5),
  "stay-beach-path.jpg": (U+"Villas Playa Maderas photos/vpm-beach-path.jpg", 1, 700, .5, .5),
  # step 4
  "inc-dinner.jpg":      (U+"Nicaragua Assets/mens_1f.webp", 1, 600, .5, .66),
  "inc-breakfast.jpg":   (U+"nicasurfcamp/rev/nsc-rev-9239e37dc419c1.jpg", 1, 540, .5, .5),
  "inc-karaoke.jpg":     (U+"Trip Photos/_web/nica/n071.jpg", 1, 640, .62, .5),
  # step 5 packages
  "pk-own.jpg":          (U+"Nicaragua Assets/DSC05059 copy.webp", 4/3, 800, .5, .5),
  "pk-regular.jpg":      (U+"Reset-Recharge-Assets/activities/sAzAS_XQ.jpeg", 4/3, 900, .5, .45),
  "pk-deluxe.jpg":       (U+"Reset-Recharge-Assets/activities/SYB-NIC-DAY-1-10.jpg", 4/3, 900, .5, .5),
  "pk-beer.jpg":         (H+"../heic/IMG_7775.jpg" if False else U+"_tmp-contact-sheet/b2b-r3/heic/IMG_7775.jpg", 4/3, 900, .5, .42),
  "pk-fullbar.jpg":      (U+"Trip Photos/_web/nica/n015.jpg", 4/3, 900, .5, .5),
  # step 5 extras
  "add-dj.jpg":          (U+"Trip Photos/Sams Hero Shots/SYB NYE 2024_2025_Day 4_LQ-166.jpg", 4/3, 900, .38, .5),
  "add-sjds.jpg":        (U+"Trip Photos/_web/nica/n106.jpg", 4/3, 900, .5, .5),
  "add-espejo.jpg":      (U+"Trip Photos/Sams Hero Shots/SK109070.jpg", 4/3, 900, .5, .5),
  "add-sxs.jpg":         (U+"Trip Photos/_web/nica/n040.jpg", 4/3, 900, .45, .5),
  "add-jesus.jpg":       (U+"Claude outputs/_may2026_photos_oct19/SYB_NicaMay-861.jpg", 4/3, 900, .5, .5),
  "add-surf.jpg":        (U+"Claude outputs/_may2026_photos_oct19/SYB_NicaMay-722.jpg", 4/3, 900, .5, .52),
  "add-theme.jpg":       (U+"Trip Photos/Sams Hero Shots/SK107526.jpg", 4/3, 900, .5, .5),
  "add-salsa.jpg":       (U+"Trip Photos/Sams Hero Shots/2.2-2.7_SYB NICA_LQ-253.jpg", 4/3, 900, .5, .5),
  "add-olympics.jpg":    (U+"Trip Photos/_web/nica/n086.jpg", 4/3, 900, .4, .45),
  "add-yoga.jpg":        (U+"Trip Photos/_web/nica/n042.jpg", 4/3, 900, .45, .5),
  "add-shirts.jpg":      (U+"Trip Photos/Sams Hero Shots/SYB NYE 2024_2025_Day 5_LQ-38.jpg", 4/3, 900, .5, .5),
  "add-headshots.jpg":   (U+"Reset-Recharge-Assets/leaders/Sam.webp", 4/3, 900, .5, .38),
}
def crop(src, aspect, outw, fx, fy):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    w, h = im.size
    if w / h > aspect:   # too wide: cut the sides
        cw, ch = int(round(h * aspect)), h
    else:                # too tall: cut top and bottom
        cw, ch = w, int(round(w / aspect))
    x = int(round(min(max(fx * w - cw / 2, 0), w - cw)))
    y = int(round(min(max(fy * h - ch / 2, 0), h - ch)))
    im = im.crop((x, y, x + cw, y + ch))
    if im.size[0] > outw:
        im = im.resize((outw, int(round(outw / aspect))), Image.LANCZOS)
    return im
only = sys.argv[1:]
for name, (src, a, ow, fx, fy) in SPEC.items():
    if only and name not in only: continue
    im = crop(src, a, ow, fx, fy)
    im.save(IMG + name, quality=82, optimize=True, progressive=True)
    print(name, im.size, os.path.getsize(IMG + name) // 1024, "KB")
# the step 3 lounge photo is no longer used
p = IMG + "villa-yoga-deck.jpg"
if os.path.exists(p) and not only: os.remove(p); print("removed villa-yoga-deck.jpg")
