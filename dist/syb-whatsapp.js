/*!
 * SYB WhatsApp button  (replaces Elfsight "WhatsApp Chat")
 * One script tag, sitewide. No dependencies. Styles live in Shadow DOM so the Easol theme can't touch them.
 *
 * Usage (Easol head_html or a sitewide custom block):
 *   <script src="https://YOUR-CDN/syb-whatsapp.js" defer></script>
 * Optional overrides BEFORE the script tag:
 *   <script>window.SYB_WHATSAPP = { phone: "19179006821", hidden: ["/waiver"] }</script>
 */
(function () {
  if (window.__sybWhatsappLoaded) return;
  window.__sybWhatsappLoaded = true;

  var cfg = Object.assign(
    {
      phone: "19179006821", // digits only, country code first
      name: "SurfYogaBeer",
      status: "Typically replies instantly",
      bubble: "WhatsApp Us",
      welcome: "Hi hi, we're a real person, hit us up!",
      button: "come on, say hello",
      prefill: "Hey SYB! I'm looking at {page} and have a question:",
      openDelayMs: 0, // e.g. 20000 to auto-open the card after 20s (once per visitor)
      // Same exclusions as the current Elfsight widget. "*" at the end = prefix match.
      hidden: [
        "/", "/waiver", "/newsletter", "/magazine", "/guide/*", "/*/guide/*", "/shop/*",
        "/checkout", "/recommendations/*", "/media-kit", "/blog", "/blog/*", "/bookings/*",
        "/products/*", "/dolomites-guide", "/nicaragua", "/croatia", "/nicaragua/nye",
        "/nicaragua/surf-yoga-beer", "/first-trip"
      ],
      hours: null // e.g. { start: 9, end: 17, tz: "America/New_York" } to only show in office hours
    },
    window.SYB_WHATSAPP || {}
  );

  function pathHidden(path) {
    path = path.replace(/\/+$/, "") || "/";
    return cfg.hidden.some(function (rule) {
      if (rule.indexOf("*") === -1) return path === (rule.replace(/\/+$/, "") || "/");
      var re = new RegExp("^" + rule.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*") + "$");
      return re.test(path);
    });
  }

  function inHours() {
    if (!cfg.hours) return true;
    try {
      var h = Number(new Intl.DateTimeFormat("en-US", { hour: "numeric", hour12: false, timeZone: cfg.hours.tz }).format(new Date()));
      return h >= cfg.hours.start && h < cfg.hours.end;
    } catch (e) { return true; }
  }

  if (pathHidden(location.pathname) || !inHours()) return;

  var WA_ICON =
    '<svg viewBox="0 0 32 32" aria-hidden="true"><path fill="currentColor" d="M16.04 3C8.86 3 3.03 8.8 3.03 15.95c0 2.29.6 4.52 1.75 6.49L3 29l6.73-1.76a13.07 13.07 0 0 0 6.3 1.6h.01c7.17 0 13-5.8 13-12.94C29.04 8.8 23.21 3 16.04 3Zm0 23.67h-.01c-1.94 0-3.85-.52-5.51-1.51l-.4-.23-4 1.04 1.07-3.88-.26-.4a10.7 10.7 0 0 1-1.65-5.74c0-5.94 4.85-10.77 10.8-10.77 2.88 0 5.59 1.12 7.63 3.16a10.68 10.68 0 0 1 3.16 7.62c0 5.94-4.85 10.71-10.83 10.71Zm5.92-8.03c-.33-.16-1.93-.95-2.23-1.06-.3-.11-.52-.16-.73.16-.22.33-.84 1.06-1.03 1.27-.19.22-.38.24-.7.08-.33-.16-1.38-.51-2.62-1.61a9.8 9.8 0 0 1-1.82-2.25c-.19-.33-.02-.5.14-.66.15-.15.33-.38.49-.57.16-.19.22-.33.33-.54.11-.22.05-.41-.03-.57-.08-.16-.73-1.76-1-2.41-.27-.63-.54-.55-.73-.56h-.62c-.22 0-.57.08-.87.41-.3.33-1.14 1.11-1.14 2.71s1.17 3.15 1.33 3.36c.16.22 2.3 3.5 5.57 4.91.78.33 1.39.53 1.86.68.78.25 1.5.21 2.06.13.63-.09 1.93-.79 2.2-1.55.27-.76.27-1.41.19-1.55-.08-.13-.3-.21-.62-.37Z"/></svg>';

  var css =
    ":host{all:initial}" +
    "*{box-sizing:border-box;font-family:Montserrat,Poppins,system-ui,-apple-system,Segoe UI,sans-serif}" +
    ".wrap{position:fixed;right:max(16px,env(safe-area-inset-right));bottom:calc(16px + env(safe-area-inset-bottom,0px));z-index:2147483000;display:flex;flex-direction:column;align-items:flex-end;gap:12px}" +
    ".pill{display:inline-flex;align-items:center;gap:8px;height:44px;padding:0 18px 0 14px;border:0;border-radius:999px;background:#111;color:#fff;font-size:13px;font-weight:600;letter-spacing:.02em;cursor:pointer;box-shadow:0 6px 24px rgba(0,0,0,.35),inset 0 0 0 1px rgba(255,255,255,.12);transition:transform .15s ease,background .15s ease}" +
    ".pill:hover{transform:translateY(-2px);background:#1a1a1a}" +
    ".pill:focus-visible,.cta:focus-visible,.x:focus-visible{outline:2px solid #E6A648;outline-offset:3px}" +
    ".pill svg{width:20px;height:20px;color:#25D366}" +
    ".card{width:min(340px,calc(100vw - 32px));background:#0D0D0D;color:#fff;border-radius:18px;overflow:hidden;box-shadow:0 18px 60px rgba(0,0,0,.5),inset 0 0 0 1px rgba(255,255,255,.08);transform-origin:bottom right;animation:pop .18s ease-out}" +
    "@keyframes pop{from{opacity:0;transform:scale(.96) translateY(6px)}}" +
    "@media (prefers-reduced-motion:reduce){.card{animation:none}.pill{transition:none}}" +
    ".head{display:flex;align-items:center;gap:12px;padding:16px 16px 14px;border-bottom:1px solid rgba(255,255,255,.08)}" +
    ".av{position:relative;width:40px;height:40px;border-radius:50%;background:#E6A648;color:#0D0D0D;display:grid;place-items:center;font-weight:800;font-size:14px;flex:none}" +
    ".av:after{content:'';position:absolute;right:0;bottom:0;width:10px;height:10px;border-radius:50%;background:#4AD504;box-shadow:0 0 0 2px #0D0D0D}" +
    ".nm{font-weight:700;font-size:14px}.st{font-size:12px;color:#bdbdbd;margin-top:2px}" +
    ".x{margin-left:auto;width:32px;height:32px;border:0;border-radius:50%;background:rgba(255,255,255,.06);color:#fff;font-size:18px;line-height:1;cursor:pointer}" +
    ".body{padding:18px 16px 16px;display:flex;flex-direction:column;gap:16px}" +
    ".msg{align-self:flex-start;max-width:88%;background:#1A1A1A;border-radius:4px 14px 14px 14px;padding:10px 12px;font-size:14px;line-height:1.45}" +
    ".cta{display:flex;align-items:center;justify-content:center;gap:8px;height:46px;border-radius:999px;background:#25D366;color:#06210f;font-weight:700;font-size:14px;text-decoration:none}" +
    ".cta svg{width:20px;height:20px}" +
    ".num{font-size:11px;color:#8a8a8a;text-align:center}";

  function mount() {
    var host = document.createElement("div");
    host.id = "syb-whatsapp";
    document.body.appendChild(host);
    var root = host.attachShadow({ mode: "open" });
    var pretty = "+" + cfg.phone.replace(/^(\d)(\d{3})(\d{3})(\d{4})$/, "$1 $2 $3 $4");
    var text = cfg.prefill.replace("{page}", document.title.split("|")[0].trim() || "your site");
    var href = "https://wa.me/" + cfg.phone + "?text=" + encodeURIComponent(text);

    root.innerHTML =
      "<style>" + css + "</style>" +
      '<div class="wrap">' +
      '<div class="card" role="dialog" aria-label="Chat with SurfYogaBeer on WhatsApp" hidden>' +
      '<div class="head"><div class="av">SYB</div><div><div class="nm"></div><div class="st"></div></div>' +
      '<button class="x" type="button" aria-label="Close">×</button></div>' +
      '<div class="body"><div class="msg"></div>' +
      '<a class="cta" target="_blank" rel="noopener">' + WA_ICON + '<span></span></a>' +
      '<div class="num"></div></div></div>' +
      '<button class="pill" type="button" aria-expanded="false">' + WA_ICON + "<span></span></button>" +
      "</div>";

    root.querySelector(".nm").textContent = cfg.name;
    root.querySelector(".st").textContent = cfg.status;
    root.querySelector(".msg").textContent = cfg.welcome;
    root.querySelector(".cta span").textContent = cfg.button;
    root.querySelector(".cta").href = href;
    root.querySelector(".num").textContent = "or text " + pretty;
    root.querySelector(".pill span").textContent = cfg.bubble;

    var card = root.querySelector(".card");
    var pill = root.querySelector(".pill");
    function setOpen(open) {
      card.hidden = !open;
      pill.setAttribute("aria-expanded", String(open));
      if (open) track("whatsapp_open");
    }
    pill.addEventListener("click", function () { setOpen(card.hidden); });
    root.querySelector(".x").addEventListener("click", function () { setOpen(false); pill.focus(); });
    root.querySelector(".cta").addEventListener("click", function () { track("whatsapp_click"); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !card.hidden) setOpen(false); });

    if (cfg.openDelayMs > 0) {
      var seen = false;
      try { seen = sessionStorage.getItem("syb_wa_seen") === "1"; } catch (e) {}
      if (!seen) setTimeout(function () {
        if (card.hidden) setOpen(true);
        try { sessionStorage.setItem("syb_wa_seen", "1"); } catch (e) {}
      }, cfg.openDelayMs);
    }
  }

  // GA4 + Meta pixel events, so we finally see how many chats the button starts
  function track(name) {
    try {
      if (typeof window.gtag === "function") window.gtag("event", name, { page_path: location.pathname });
      else if (window.dataLayer) window.dataLayer.push({ event: name, page_path: location.pathname });
    } catch (e) {}
    try { if (window.fbq && name === "whatsapp_click") window.fbq("track", "Contact"); } catch (e) {}
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
