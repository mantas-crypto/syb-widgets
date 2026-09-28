/*!
 * SYB Google Reviews carousel  (replaces Elfsight "Google Reviews")
 * No dependencies. Shadow DOM so the Easol theme can't restyle it. Loads its data only when scrolled near.
 *
 * Usage (Easol custom HTML block):
 *   <div class="syb-reviews" data-trip="morocco"></div>
 *   <script src="https://YOUR-CDN/syb-reviews.js" defer></script>
 *
 * Options (data- attributes on the div):
 *   data-trip="morocco"        loads reviews/morocco.json next to this script (built by scripts/build-reviews.py)
 *   data-src="https://..."     or point at any JSON file instead
 *   data-keywords="bali,ubud"  extra filter on top of the file (any word matches)
 *   data-limit="24"            max cards (default 24)
 *   data-sort="photos"         photos | newest | random   (default photos: reviews with photos first, then newest)
 *   data-header="true"         show the stars + count pill above the cards
 *   data-theme="dark"          dark | light
 *   data-google-url="https://g.page/r/..."   where "See all on Google" and the pill link to
 */
(function () {
  var SCRIPT = document.currentScript;
  var BASE = SCRIPT && SCRIPT.src ? SCRIPT.src.replace(/[^/]*$/, "") : "";
  var GOOGLE_URL_DEFAULT = "https://www.google.com/maps/place/?q=place_id:ChIJyTABhtFZwokRR1ZQGo0WF7Y";
  var cache = {};

  var G_ICON =
    '<svg viewBox="0 0 48 48" aria-hidden="true"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"/></svg>';
  var STAR = '<svg viewBox="0 0 20 20" aria-hidden="true"><path fill="currentColor" d="M10 1.6l2.6 5.3 5.8.8-4.2 4.1 1 5.8L10 14.9l-5.2 2.7 1-5.8L1.6 7.7l5.8-.8z"/></svg>';
  var ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>';

  var css =
    ":host{display:block;all:initial;display:block}" +
    "*{box-sizing:border-box;font-family:Montserrat,Poppins,system-ui,-apple-system,Segoe UI,sans-serif;margin:0}" +
    ".r{--bg:transparent;--card:#161616;--line:rgba(255,255,255,.08);--ink:#fff;--mute:#a7a29a;--gold:#E6A648;--gold2:#FFC24B;color:var(--ink);background:var(--bg);width:100%}" +
    ".r.light{--card:#fff;--line:rgba(0,0,0,.09);--ink:#141414;--mute:#6b665e;--gold:#C98A2B;--gold2:#E6A648}" +
    ".top{display:flex;justify-content:center;margin-bottom:22px}" +
    ".pill{display:inline-flex;align-items:center;gap:10px;padding:9px 16px;border-radius:999px;background:var(--card);box-shadow:inset 0 0 0 1px var(--line);color:var(--ink);text-decoration:none;font-size:14px;font-weight:700;letter-spacing:.02em}" +
    ".pill:hover{box-shadow:inset 0 0 0 1px var(--gold)}" +
    ".pill .g{width:18px;height:18px}" +
    ".stars{display:inline-flex;gap:2px;color:var(--gold2)}.stars svg{width:15px;height:15px}" +
    ".vp{position:relative}" +
    ".track{display:grid;grid-auto-flow:column;grid-auto-columns:calc((100% - 3*14px)/4);gap:14px;overflow-x:auto;scroll-snap-type:x mandatory;scroll-behavior:smooth;scrollbar-width:none;padding:2px 2px 6px;align-items:start}" +
    ".track::-webkit-scrollbar{display:none}" +
    "@media (max-width:1100px){.track{grid-auto-columns:calc((100% - 2*14px)/3)}}" +
    "@media (max-width:820px){.track{grid-auto-columns:calc((100% - 14px)/2)}}" +
    "@media (max-width:560px){.track{grid-auto-columns:86%}}" +
    ".card{scroll-snap-align:start;background:var(--card);border-radius:14px;box-shadow:inset 0 0 0 1px var(--line);padding:16px;display:flex;flex-direction:column;gap:10px;min-width:0}" +
    ".who{display:flex;align-items:center;gap:10px}" +
    ".av{position:relative;width:38px;height:38px;flex:none}" +
    ".av img,.av .ini{width:38px;height:38px;border-radius:50%;object-fit:cover;display:grid;place-items:center;background:#2a2a2a;color:#fff;font-weight:700;font-size:14px}" +
    ".av .g{position:absolute;right:-3px;bottom:-3px;width:17px;height:17px;background:#fff;border-radius:50%;padding:2px}" +
    ".nm{font-size:14px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
    ".dt{font-size:12px;color:var(--mute);margin-top:2px}" +
    ".tx{font-size:14px;line-height:1.5;color:var(--ink);display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden;white-space:pre-line}" +
    ".card.open .tx{display:block;-webkit-line-clamp:unset}" +
    ".more{align-self:flex-start;background:none;border:0;padding:0;color:var(--mute);font-size:13px;font-weight:600;cursor:pointer;text-decoration:underline;text-underline-offset:3px}" +
    ".more:hover{color:var(--gold)}" +
    ".ph{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:2px}" +
    ".ph button{padding:0;border:0;background:#222;border-radius:8px;overflow:hidden;aspect-ratio:1;cursor:zoom-in}" +
    ".ph img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .3s ease}" +
    ".ph button:hover img{transform:scale(1.04)}" +
    ".nav{position:absolute;top:50%;transform:translateY(-50%);width:40px;height:40px;border-radius:50%;border:0;background:rgba(10,10,10,.85);color:#fff;display:grid;place-items:center;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.35),inset 0 0 0 1px rgba(255,255,255,.14);z-index:2}" +
    ".nav svg{width:18px;height:18px}.prev{left:-12px}.prev svg{transform:rotate(180deg)}.next{right:-12px}" +
    ".nav[disabled]{opacity:0;pointer-events:none}" +
    "@media (max-width:560px){.nav{display:none}}" +
    ".foot{display:flex;justify-content:center;margin-top:18px}" +
    ".all{color:var(--mute);font-size:13px;font-weight:600;text-decoration:none;letter-spacing:.04em;text-transform:uppercase}" +
    ".all:hover{color:var(--gold)}" +
    "button:focus-visible,a:focus-visible{outline:2px solid var(--gold);outline-offset:3px}" +
    ".lb{position:fixed;inset:0;background:rgba(0,0,0,.92);display:grid;place-items:center;z-index:2147483600;padding:24px;cursor:zoom-out}" +
    ".lb img{max-width:100%;max-height:90vh;border-radius:10px}" +
    ".skel{height:230px;border-radius:14px;background:linear-gradient(90deg,var(--card),rgba(255,255,255,.06),var(--card));background-size:200% 100%;animation:sh 1.2s infinite}" +
    "@keyframes sh{to{background-position:-200% 0}}" +
    "@media (prefers-reduced-motion:reduce){.track{scroll-behavior:auto}.skel{animation:none}.ph img{transition:none}}";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function ago(iso) {
    var d = (Date.now() - new Date(iso).getTime()) / 864e5;
    if (d < 1) return "today";
    if (d < 7) return Math.floor(d) + (Math.floor(d) === 1 ? " day ago" : " days ago");
    if (d < 31) return Math.floor(d / 7) + (Math.floor(d / 7) === 1 ? " week ago" : " weeks ago");
    if (d < 365) return Math.floor(d / 30.4) + (Math.floor(d / 30.4) === 1 ? " month ago" : " months ago");
    var y = Math.floor(d / 365);
    return y + (y === 1 ? " year ago" : " years ago");
  }

  function load(src) {
    if (!cache[src]) {
      cache[src] = fetch(src, { credentials: "omit" }).then(function (r) {
        if (!r.ok) throw new Error("reviews " + r.status);
        return r.json();
      });
    }
    return cache[src];
  }

  function pick(list, opt) {
    var kws = (opt.keywords || "").toLowerCase().split(",").map(function (s) { return s.trim(); }).filter(Boolean);
    var out = list.filter(function (r) {
      if ((r.rating || 0) < opt.minRating) return false;
      if (!r.text || r.text.length < 40) return false;
      if (!kws.length) return true;
      var t = r.text.toLowerCase();
      return kws.some(function (k) { return t.indexOf(k) !== -1; });
    });
    if (opt.sort === "random") {
      for (var i = out.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var x = out[i]; out[i] = out[j]; out[j] = x; }
    } else {
      out.sort(function (a, b) {
        if (opt.sort === "photos") {
          var pa = a.images && a.images.length ? 1 : 0, pb = b.images && b.images.length ? 1 : 0;
          if (pa !== pb) return pb - pa;
        }
        return a.date < b.date ? 1 : a.date > b.date ? -1 : 0;
      });
    }
    return out.slice(0, opt.limit);
  }

  function stars(n) {
    var s = "";
    for (var i = 0; i < Math.round(n); i++) s += STAR;
    return '<span class="stars" aria-label="' + n + ' out of 5 stars">' + s + "</span>";
  }

  function card(r, i) {
    var ini = esc((r.name || "?").trim().charAt(0).toUpperCase());
    var av = r.avatar
      ? '<img src="' + esc(r.avatar) + '" alt="" loading="lazy" referrerpolicy="no-referrer" data-ini="' + ini + '">'
      : '<span class="ini">' + ini + "</span>";
    var photos = (r.images || []).slice(0, 2).map(function (src) {
      // Google serves 150px thumbs by default; ask for 400px and fall back to the original if refused
      var sharp = src.replace(/=w\d+-h\d+/, "=w400-h400");
      return '<button type="button" data-full="' + esc(src) + '" aria-label="Open photo from ' + esc(r.name) + '"><img src="' + esc(sharp) + '" data-orig="' + esc(src) + '" alt="Trip photo from ' + esc(r.name) + '" loading="lazy" referrerpolicy="no-referrer"></button>';
    }).join("");
    return (
      '<article class="card" data-i="' + i + '">' +
      '<div class="who"><div class="av">' + av + '<span class="g">' + G_ICON + "</span></div>" +
      '<div style="min-width:0"><div class="nm">' + esc(r.name) + '</div><div class="dt">' + ago(r.date) + "</div></div></div>" +
      stars(r.rating) +
      '<p class="tx">' + esc(r.text) + "</p>" +
      '<button type="button" class="more" hidden>Read more</button>' +
      (photos ? '<div class="ph">' + photos + "</div>" : "") +
      "</article>"
    );
  }

  function render(host) {
    if (host.__sybDone) return;
    host.__sybDone = true;
    var ds = host.dataset;
    var opt = {
      src: ds.src || (ds.trip ? BASE + "reviews/" + ds.trip + ".json" : BASE + "reviews/all.json"),
      keywords: ds.keywords || "",
      limit: Number(ds.limit || 24),
      sort: ds.sort || "photos",
      minRating: Number(ds.minRating || 5),
      header: ds.header !== "false",
      theme: ds.theme || "dark",
      googleUrl: ds.googleUrl || GOOGLE_URL_DEFAULT
    };
    var root = host.shadowRoot || host.attachShadow({ mode: "open" });
    root.innerHTML = "<style>" + css + '</style><div class="r ' + esc(opt.theme) + '"><div class="track"><div class="skel"></div><div class="skel"></div><div class="skel"></div><div class="skel"></div></div></div>';

    var data = window.SYB_REVIEWS && !ds.src && !ds.trip ? Promise.resolve(window.SYB_REVIEWS) : load(opt.src);
    data.then(function (payload) {
      var list = Array.isArray(payload) ? payload : payload.reviews || [];
      var meta = Array.isArray(payload) ? {} : payload.meta || {};
      var items = pick(list, opt);
      if (!items.length) { host.style.display = "none"; return; }

      var count = meta.total || list.length;
      var rating = meta.rating || (list.reduce(function (s, r) { return s + (r.rating || 0); }, 0) / list.length).toFixed(1);
      var countLabel = count >= 100 ? Math.floor(count / 100) * 100 + "+" : String(count);

      root.innerHTML =
        "<style>" + css + "</style>" +
        '<div class="r ' + esc(opt.theme) + '">' +
        (opt.header
          ? '<div class="top"><a class="pill" href="' + esc(opt.googleUrl) + '" target="_blank" rel="noopener"><span class="g">' + G_ICON + "</span>" + stars(5) + "<span>" + esc(rating) + " · " + countLabel + " Google reviews</span></a></div>"
          : "") +
        '<div class="vp"><button class="nav prev" type="button" aria-label="Previous reviews" disabled>' + ARROW + "</button>" +
        '<div class="track" tabindex="0" aria-label="Google reviews">' + items.map(card).join("") + "</div>" +
        '<button class="nav next" type="button" aria-label="Next reviews">' + ARROW + "</button></div>" +
        '<div class="foot"><a class="all" href="' + esc(opt.googleUrl) + '" target="_blank" rel="noopener">See all reviews on Google →</a></div>' +
        "</div>";

      // Broken avatar -> initial; broken photo -> drop it
      root.addEventListener("error", function (e) {
        var img = e.target;
        if (!img || img.tagName !== "IMG") return;
        if (img.dataset.ini) {
          var s = document.createElement("span");
          s.className = "ini";
          s.textContent = img.dataset.ini;
          img.replaceWith(s);
        } else if (img.dataset.orig && img.src !== img.dataset.orig) {
          img.src = img.dataset.orig;
        } else if (img.closest(".ph button")) {
          img.closest(".ph button").remove();
        }
      }, true);

      var track = root.querySelector(".track");
      var prev = root.querySelector(".prev");
      var next = root.querySelector(".next");

      // Only show "Read more" where the text is actually clipped
      requestAnimationFrame(function () {
        root.querySelectorAll(".card").forEach(function (c) {
          var tx = c.querySelector(".tx");
          if (tx.scrollHeight > tx.clientHeight + 2) c.querySelector(".more").hidden = false;
        });
        sync();
      });

      function step() { var c = track.querySelector(".card"); return c ? c.getBoundingClientRect().width + 14 : 300; }
      function sync() {
        prev.disabled = track.scrollLeft < 8;
        next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 8;
      }
      prev.addEventListener("click", function () { track.scrollBy({ left: -step() * Math.max(1, Math.floor(track.clientWidth / step())), behavior: "smooth" }); });
      next.addEventListener("click", function () { track.scrollBy({ left: step() * Math.max(1, Math.floor(track.clientWidth / step())), behavior: "smooth" }); });
      track.addEventListener("scroll", sync, { passive: true });
      window.addEventListener("resize", sync);

      root.addEventListener("click", function (e) {
        var more = e.target.closest(".more");
        if (more) {
          var c = more.closest(".card");
          var open = c.classList.toggle("open");
          more.textContent = open ? "Show less" : "Read more";
          return;
        }
        var ph = e.target.closest("[data-full]");
        if (ph) {
          var lb = document.createElement("div");
          lb.className = "lb";
          lb.setAttribute("role", "dialog");
          lb.innerHTML = '<img src="' + esc(ph.dataset.full.replace(/=w\d+-h\d+.*$|=s\d+.*$/, "=s1600")) + '" data-orig="' + esc(ph.dataset.full) + '" alt="" referrerpolicy="no-referrer">';
          lb.addEventListener("click", function () { lb.remove(); });
          root.appendChild(lb);
        }
      });
    }).catch(function (err) {
      console.warn("[syb-reviews]", err);
      host.style.display = "none";
    });
  }

  function boot() {
    var els = Array.prototype.slice.call(document.querySelectorAll(".syb-reviews"));
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

  window.SYBReviews = { render: render, boot: boot };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
