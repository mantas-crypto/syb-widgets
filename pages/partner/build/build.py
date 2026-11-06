#!/usr/bin/env python3
"""Builds the team trip page from src/page.html.

  python3 build/build.py                 -> index.html (the Claude preview, photos in img/)
  python3 build/build.py assets          -> live/partner.css, live/partner.js (no commit inside, commit these first)
  python3 build/build.py embed <SHA>     -> live/embed.html, the one line for the Easol embed block, pinned to SHA

Source markers:
  <style data-artifact-only>  preview-only global CSS (html, body)
  <style data-scoped>         page CSS, written plainly; every selector gets #sybp in front here
  <!--A--> ... <!--/A-->      preview-only markup (the top bar and footer; the live site has its own)
"""
import re, sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src", "page.html")
REPO_PATH = "pages/partner"   # where the live files sit in mantas-crypto/syb-widgets
CDN = "https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@{sha}/" + REPO_PATH + "/"
FONTS = "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap"

src = open(SRC, encoding="utf-8").read()

def grab(pattern, text, flags=re.S):
    m = re.search(pattern, text, flags)
    if not m:
        sys.exit("build: could not find " + pattern)
    return m

head_m = grab(r"^(.*?)<style data-artifact-only>", src)
head = head_m.group(1)
art_css = grab(r"<style data-artifact-only>(.*?)</style>", src).group(1)
css = grab(r"<style data-scoped>(.*?)</style>", src).group(1)
markup = grab(r'(<div id="sybp".*?</div>)\s*<script>', src).group(1)
js = grab(r"<script>(.*?)</script>\s*$", src).group(1)

# ---------- CSS scoping ----------
def strip_comments(c):
    return re.sub(r"/\*.*?\*/", "", c, flags=re.S)

def split_top(c):
    """Split CSS into top-level chunks: ('rule', selectors, body) or ('at', prelude, inner)."""
    out, i, n = [], 0, len(c)
    while i < n:
        j = c.find("{", i)
        if j == -1:
            break
        prelude = c[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            if c[k] == "{": depth += 1
            elif c[k] == "}": depth -= 1
            k += 1
        inner = c[j + 1:k - 1]
        out.append(("at" if prelude.startswith("@") else "rule", prelude, inner))
        i = k
    return out

def split_selectors(s):
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([": depth += 1
        if ch in ")]": depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur); cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]

def scope_sel(sel):
    if sel.startswith("#sybp"):
        return sel
    return "#sybp " + sel

def scope(c):
    out = []
    for kind, pre, inner in split_top(strip_comments(c)):
        if kind == "at":
            if pre.startswith("@media") or pre.startswith("@supports"):
                out.append(pre + "{" + scope(inner) + "}")
            else:
                out.append(pre + "{" + inner + "}")
        else:
            sels = ",".join(scope_sel(s) for s in split_selectors(pre))
            out.append(sels + "{" + inner.strip() + "}")
    return "\n".join(out)

def minify_css(c):
    c = strip_comments(c)
    c = re.sub(r"\s+", " ", c)
    c = re.sub(r"\s*([{};,>])\s*", r"\1", c)
    c = c.replace(";}", "}")
    return c.strip()

scoped = scope(css)

# ---------- markup ----------
def drop_blocks(m, tag):
    return re.sub(r"<!--" + tag + r"-->.*?<!--/" + tag + r"-->", "", m, flags=re.S)

def keep_blocks(m, tag):
    return m.replace("<!--" + tag + "-->", "").replace("<!--/" + tag + "-->", "")

def strip_html_comments(m):
    return re.sub(r"<!--.*?-->", "", m, flags=re.S)

def ascii_html(s):
    return s.encode("ascii", "xmlcharrefreplace").decode("ascii")

def build_preview():
    m = strip_html_comments(keep_blocks(markup, "A"))
    page = (head.rstrip() + "\n<style>\n" + art_css.strip() + "\n" + scoped + "\n</style>\n\n" +
            m + "\n\n<script>" + js + "</script>\n")
    out = os.path.join(ROOT, "index.html")
    open(out, "w", encoding="utf-8").write(page)
    print("preview:", out, len(page), "bytes")

def build_live_assets():
    """partner.css and partner.js: these never mention a commit, so they can be committed first."""
    outdir = os.path.join(ROOT, "live")
    os.makedirs(outdir, exist_ok=True)
    live_global = open(os.path.join(ROOT, "src", "live-global.css"), encoding="utf-8").read()
    css_out = minify_css(scoped + "\n" + live_global)
    open(os.path.join(outdir, "partner.css"), "w", encoding="utf-8").write(css_out)
    j = js.replace('var MODE = "artifact";', 'var MODE = "live";')
    j = j.replace('var IMG = "img/";',
                  'var IMG = (function(){ var s = document.currentScript; return s && s.src ? s.src.replace(/[^\\/?#]*([?#].*)?$/, "").replace(/live\\/$/, "") + "img/" : "img/"; })();')
    assert 'var MODE = "live";' in j and "currentScript" in j, "build: MODE/IMG lines not found"
    open(os.path.join(outdir, "partner.js"), "w", encoding="utf-8").write(j)
    print("live assets:", outdir, "css", len(css_out), "js", len(j))

def build_embed(sha):
    """embed.html: one line for the Easol embed block, pinned to the commit that holds the assets."""
    base = CDN.format(sha=sha)
    outdir = os.path.join(ROOT, "live")
    os.makedirs(outdir, exist_ok=True)
    m = strip_html_comments(drop_blocks(markup, "A"))
    m = m.replace('<div id="sybp" class="is-artifact">', '<div id="sybp" class="is-live">')
    m = m.replace('src="img/', 'src="' + base + 'img/')
    m = re.sub(r"\s+", " ", m).strip()
    embed = ('<link rel="stylesheet" href="' + FONTS.replace("&", "&amp;") + '">' +
             '<link rel="stylesheet" href="' + base + 'live/partner.css">' +
             m +
             '<script src="' + base + 'live/partner.js"></script>')
    embed = ascii_html(embed)
    assert "\n" not in embed and "<!--" not in embed
    open(os.path.join(outdir, "embed.html"), "w", encoding="ascii").write(embed)
    print("embed:", len(embed), "bytes, pinned to", sha)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "assets":
        build_live_assets()
    elif len(sys.argv) > 2 and sys.argv[1] == "embed":
        build_embed(sys.argv[2])
    else:
        build_preview()
