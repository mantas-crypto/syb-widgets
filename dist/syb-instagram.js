/*!
 * SYB Instagram grid  (replaces Elfsight "Instagram Feed" hashtag widgets)
 * No dependencies. Shadow DOM. Loads its data only when scrolled near.
 *
 * Usage (Easol custom HTML block):
 *   <div class="syb-instagram" data-tag="sybibiza"></div>
 *   <script src="https://YOUR-CDN/syb-instagram.js" defer></script>
 *
 * Reads instagram/<tag>.json next to this script:
 *   { "tag": "sybibiza", "posts": [ { "code": "ChxqyxEJLia", "user": "someone", "img": "sybibiza/ChxqyxEJLia.jpg" } ] }
 * img paths are relative to the instagram/ folder. Every tile links to the real post on Instagram.
 *
 * Options: data-rows="2" (1 or 2), data-follow="true" (show the Follow button)
 */
(function () {
  var SCRIPT = document.currentScript;
  var BASE = SCRIPT && SCRIPT.src ? SCRIPT.src.replace(/[^/]*$/, "") : "";

  var IG_ICON =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2.2c3.2 0 3.6 0 4.8.1 1.2.1 1.8.2 2.2.4.6.2 1 .5 1.4.9.4.4.7.8.9 1.4.2.4.4 1.1.4 2.2.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.8c-.1 1.2-.2 1.8-.4 2.2-.2.6-.5 1-.9 1.4-.4.4-.8.7-1.4.9-.4.2-1.1.4-2.2.4-1.3.1-1.6.1-4.8.1s-3.6 0-4.8-.1c-1.2-.1-1.8-.2-2.2-.4-.6-.2-1-.5-1.4-.9-.4-.4-.7-.8-.9-1.4-.2-.4-.4-1.1-.4-2.2C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.8c.1-1.2.2-1.8.4-2.2.2-.6.5-1 .9-1.4.4-.4.8-.7 1.4-.9.4-.2 1.1-.4 2.2-.4C8.4 2.2 8.8 2.2 12 2.2zm0 1.8c-3.1 0-3.5 0-4.7.1-1.1.1-1.7.2-2.1.4-.5.2-.9.4-1.3.8-.4.4-.6.8-.8 1.3-.2.4-.3 1-.4 2.1C2.6 9.9 2.6 10.3 2.6 12s0 3.5.1 4.7c.1 1.1.2 1.7.4 2.1.2.5.4.9.8 1.3.4.4.8.6 1.3.8.4.2 1 .3 2.1.4 1.2.1 1.6.1 4.7.1s3.5 0 4.7-.1c1.1-.1 1.7-.2 2.1-.4.5-.2.9-.4 1.3-.8.4-.4.6-.8.8-1.3.2-.4.3-1 .4-2.1.1-1.2.1-1.6.1-4.7s0-3.5-.1-4.7c-.1-1.1-.2-1.7-.4-2.1-.2-.5-.4-.9-.8-1.3-.4-.4-.8-.6-1.3-.8-.4-.2-1-.3-2.1-.4C15.5 4 15.1 4 12 4zm0 3.1a4.9 4.9 0 1 1 0 9.8 4.9 4.9 0 0 1 0-9.8zm0 8.1a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4zm5.1-8.3a1.1 1.1 0 1 1 0-2.3 1.1 1.1 0 0 1 0 2.3z"/></svg>';
  var ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>';

  var css =
    ":host{all:initial;display:block}" +
    "*{box-sizing:border-box;font-family:Montserrat,Poppins,system-ui,-apple-system,Segoe UI,sans-serif;margin:0}" +
    ".w{position:relative;width:100%}" +
    ".track{display:grid;grid-auto-flow:column;gap:4px;overflow-x:auto;scroll-snap-type:x mandatory;scroll-behavior:smooth;scrollbar-width:none}" +
    ".track::-webkit-scrollbar{display:none}" +
    ".track.r2{grid-template-rows:1fr 1fr}" +
    ".track{grid-auto-columns:calc((100% - 5*4px)/6)}" +
    "@media (max-width:900px){.track{grid-auto-columns:calc((100% - 3*4px)/4)}}" +
    "@media (max-width:560px){.track{grid-auto-columns:calc((100% - 2*4px)/3)}}" +
    ".t{position:relative;display:block;aspect-ratio:1;overflow:hidden;background:#161616;scroll-snap-align:start}" +
    ".t img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .4s ease}" +
    ".t:after{content:'';position:absolute;inset:0;background:rgba(0,0,0,0);transition:background .2s ease}" +
    ".t:hover img{transform:scale(1.05)}.t:hover:after{background:rgba(0,0,0,.25)}" +
    ".t .u{position:absolute;left:8px;bottom:8px;z-index:1;color:#fff;font-size:11px;font-weight:600;letter-spacing:.02em;text-shadow:0 1px 4px rgba(0,0,0,.7);opacity:0;transition:opacity .2s ease}" +
    ".t:hover .u,.t:focus-visible .u{opacity:1}" +
    ".t:focus-visible{outline:2px solid #E6A648;outline-offset:-2px}" +
    ".nav{position:absolute;top:50%;transform:translateY(-50%);width:40px;height:40px;border-radius:50%;border:0;background:rgba(10,10,10,.85);color:#fff;display:grid;place-items:center;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.35),inset 0 0 0 1px rgba(255,255,255,.14);z-index:2}" +
    ".nav svg{width:18px;height:18px}.prev{left:8px}.prev svg{transform:rotate(180deg)}.next{right:8px}" +
    ".nav[disabled]{opacity:0;pointer-events:none}" +
    ".nav:focus-visible,.fol:focus-visible{outline:2px solid #E6A648;outline-offset:3px}" +
    "@media (max-width:560px){.nav{display:none}}" +
    ".foot{display:flex;justify-content:center;margin-top:20px}" +
    ".fol{display:inline-flex;align-items:center;gap:8px;padding:11px 20px;border-radius:999px;background:#fff;color:#0D0D0D;font-size:13px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;text-decoration:none}" +
    ".fol svg{width:18px;height:18px}.fol:hover{background:#E6A648}" +
    "@media (prefers-reduced-motion:reduce){.track{scroll-behavior:auto}.t img,.t:after{transition:none}}";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function render(host) {
    if (host.__sybDone) return;
    host.__sybDone = true;
    var ds = host.dataset;
    var tag = (ds.tag || "surfyogabeer").replace(/^#/, "").toLowerCase();
    var src = ds.src || BASE + "instagram/" + tag + ".json";
    var dir = src.replace(/[^/]*$/, "");
    var rows = ds.rows === "1" ? 1 : 2;
    var root = host.shadowRoot || host.attachShadow({ mode: "open" });

    fetch(src, { credentials: "omit" }).then(function (r) {
      if (!r.ok) throw new Error("instagram " + r.status);
      return r.json();
    }).then(function (data) {
      var posts = (data.posts || []).filter(function (p) { return p.img && p.code; });
      if (!posts.length) { host.style.display = "none"; return; }
      var tiles = posts.map(function (p) {
        var img = /^https?:/.test(p.img) ? p.img : dir + p.img;
        return '<a class="t" href="https://www.instagram.com/p/' + esc(p.code) + '/" target="_blank" rel="noopener" aria-label="Open @' + esc(p.user) + ' on Instagram">' +
          '<img src="' + esc(img) + '" alt="#' + esc(tag) + ' photo by @' + esc(p.user) + '" loading="lazy" width="360" height="360"><span class="u">@' + esc(p.user) + "</span></a>";
      }).join("");
      root.innerHTML =
        "<style>" + css + '</style><div class="w">' +
        '<button class="nav prev" type="button" aria-label="Previous photos" disabled>' + ARROW + "</button>" +
        '<div class="track' + (rows === 2 ? " r2" : "") + '" tabindex="0" aria-label="#' + esc(tag) + ' on Instagram">' + tiles + "</div>" +
        '<button class="nav next" type="button" aria-label="More photos">' + ARROW + "</button></div>" +
        (ds.follow !== "false" ? '<div class="foot"><a class="fol" href="https://www.instagram.com/surfyogabeer/" target="_blank" rel="noopener">' + IG_ICON + "Follow @surfyogabeer</a></div>" : "");

      var track = root.querySelector(".track");
      var prev = root.querySelector(".prev");
      var next = root.querySelector(".next");
      function sync() {
        prev.disabled = track.scrollLeft < 8;
        next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 8;
      }
      prev.addEventListener("click", function () { track.scrollBy({ left: -track.clientWidth, behavior: "smooth" }); });
      next.addEventListener("click", function () { track.scrollBy({ left: track.clientWidth, behavior: "smooth" }); });
      track.addEventListener("scroll", sync, { passive: true });
      window.addEventListener("resize", sync);
      requestAnimationFrame(sync);
      root.addEventListener("error", function (e) {
        var t = e.target && e.target.closest && e.target.closest(".t");
        if (t) t.remove();
      }, true);
    }).catch(function (err) {
      console.warn("[syb-instagram]", err);
      host.style.display = "none";
    });
  }

  function boot() {
    var els = Array.prototype.slice.call(document.querySelectorAll(".syb-instagram"));
    if (!els.length) return;
    function near(el) {
      var r = el.getBoundingClientRect();
      var h = window.innerHeight || document.documentElement.clientHeight;
      return r.top < h + 600 && r.bottom > -600;
    }
    function check() {
      els = els.filter(function (el) {
        if (el.__sybDone) return false;
        if (near(el)) { render(el); return false; }
        return true;
      });
      if (!els.length) stop();
    }
    var io = null, t = null, pending = false;
    function onScroll() {
      if (pending) return;
      pending = true;
      setTimeout(function () { pending = false; check(); }, 150);
    }
    function stop() {
      if (io) io.disconnect();
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      clearTimeout(t);
    }
    // 1) IntersectionObserver when it works
    if ("IntersectionObserver" in window) {
      io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) { io.unobserve(en.target); render(en.target); } });
      }, { rootMargin: "600px 0px" });
      els.forEach(function (el) { io.observe(el); });
    }
    // 2) plain scroll/resize check as a backup
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    check();
    // 3) never stay blank: render everything left 4s after load
    function late() { t = setTimeout(function () { els.forEach(render); stop(); }, 4000); }
    if (document.readyState === "complete") late();
    else window.addEventListener("load", late);
  }

  window.SYBInstagram = { render: render, boot: boot };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
