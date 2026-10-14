/*
  SYB leader pages (surfyogabeer.com/trip-leaders/<name>): the story reel at the top, and the parts that
  update themselves. Nothing on a leader page has to be retyped when a trip sells, ends or is added.

  Where the numbers come from
    #syl-live   printed by Easol on every visit (product_search in the trips block): dates, link, spots left,
                sold out, price and photo of every upcoming departure. Always current.
    <key>.json  dist/leaders/ in this repo, rebuilt twice a day from SYB HQ (which trips this leader leads,
                trips led and travelers, reviews that name them). See scripts/build-leaders.py.
  The block HTML holds the same content as of the day it was saved, so the page still reads right if
  the JSON cannot load.
*/
(function () {
  'use strict';
  var CDN = 'https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@main/dist/leaders/';
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var MONTH = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function day(s) { var p = String(s || '').split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function today() { var d = new Date(); d.setHours(0, 0, 0, 0); return d; }
  function days(a, b) { return Math.round((a - b) / 864e5); }
  function norm(s) {
    s = String(s || '');
    if (s.normalize) s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
    return s.toLowerCase().replace(/[‘’]/g, "'").replace(/\s+/g, ' ').trim();
  }
  function slug(s) { return norm(s).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); }
  function iso(d) { return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }

  /* ---------- live departures printed by Easol ---------- */
  function liveFrom(doc) {
    var m = {}, n = 0;
    Array.prototype.forEach.call(doc.querySelectorAll('#syl-live i'), function (i) {
      var d = i.getAttribute('data-d'), r = i.getAttribute('data-r');
      var o = {
        name: i.getAttribute('data-n'), start: d, url: i.getAttribute('data-u') || '',
        left: r === '' || r == null ? null : +r, soldOut: i.getAttribute('data-so') === '1',
        price: i.getAttribute('data-p') || '', img: i.getAttribute('data-img') || ''
      };
      m[norm(o.name) + '|' + d] = o;
      (m[norm(o.name)] = m[norm(o.name)] || []).push(o);
      n++;
    });
    return n ? m : null;
  }
  // Live departures: printed in this page by the trips block, or read from the shared data page.
  function getLive(root) {
    var here = liveFrom(document);
    if (here) return Promise.resolve(here);
    var url = (root && root.getAttribute('data-live')) || '/leader-live-data', key = 'syl_live_v1';
    try {
      var c = JSON.parse(sessionStorage.getItem(key) || 'null');
      if (c && Date.now() - c.t < 5 * 60e3) return Promise.resolve(liveFrom(new DOMParser().parseFromString(c.h, 'text/html')));
    } catch (e) {}
    return fetch(url, { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.text() : ''; }).then(function (t) {
      var box = t && new DOMParser().parseFromString(t, 'text/html').getElementById('syl-live');
      if (!box) return null;
      try { sessionStorage.setItem(key, JSON.stringify({ t: Date.now(), h: box.outerHTML })); } catch (e) {}
      return liveFrom(new DOMParser().parseFromString(box.outerHTML, 'text/html'));
    }).catch(function () { return null; });
  }
  function findLive(live, name, start) {
    if (!live) return null;
    var hit = live[norm(name) + '|' + start];
    if (hit) return hit;
    var near = (live[norm(name)] || []).filter(function (o) { return Math.abs(days(day(o.start), day(start))) <= 3; });
    return near[0] || null;
  }
  function money(p) { return String(p || '').replace(/\.00(?=\D*$)/, '').replace(/\s?USD$/, ''); }

  /* ---------- trips ---------- */
  function holiday(s, e) {
    var y = s.getFullYear();
    var nov1 = new Date(y, 10, 1), thx = new Date(y, 10, 1 + ((11 - nov1.getDay()) % 7) + 21);
    if (thx >= s && thx <= e) return 'Thanksgiving week';
    var nye = new Date(y, 11, 31);
    if (nye >= s && nye <= e) return 'New Year’s Eve';
    return '';
  }
  function range(s, e) {
    var a = MON[s.getMonth()] + ' ' + s.getDate();
    if (!e || +e === +s) return a;
    return a + ' to ' + (e.getMonth() === s.getMonth() ? '' : MON[e.getMonth()] + ' ') + e.getDate();
  }
  function soonText(n) {
    if (n === 0) return 'Leaves today';
    if (n === 1) return 'Leaves tomorrow';
    return n > 0 && n <= 30 ? 'Leaves in ' + n + ' days' : '';
  }
  function status(t0, s, e, lv) {
    var n = days(s, t0);
    if (n < 0 && days(e, t0) >= 0) return { cls: 'syl-pill-now', text: 'Happening now', soon: '' };
    var soon = soonText(n);
    if (lv && lv.soldOut) return { cls: 'syl-pill-out', text: 'Sold out', soon: soon, out: true };
    if (lv && lv.left != null && lv.left > 0 && lv.left <= 8) {
      return { cls: lv.left <= 4 ? 'syl-pill-hot' : '', text: lv.left === 1 ? '1 spot left' : lv.left + ' spots left', soon: soon };
    }
    return { cls: '', text: '', soon: soon };
  }
  function poster(u, lv, t0, first) {
    var s = day(u.start), e = day(u.end), st = status(t0, s, e, lv);
    var hol = holiday(s, e), where = u.place + (hol ? ', ' + hol : '');
    var href = lv && lv.url ? lv.url : (u.page || '/calendar');
    var img = lv && lv.img ? '<img src="' + esc(lv.img) + '" alt="' + esc(u.trip + ', SYB’s trip to ' + u.place) + '" loading="lazy">' : '';
    var pills = (st.text ? '<span class="syl-pill ' + st.cls + '">' + st.text + '</span>' : '<span></span>') +
      (st.soon ? '<span class="syl-pill syl-soon">' + st.soon + '</span>' : '');
    var price = st.out ? 'Sold out' : (lv && lv.price ? 'From ' + esc(money(lv.price)) : '');
    var cta = st.out ? '<span class="syl-cta syl-cta-ghost">Join Waitlist</span>' : '<span class="syl-cta">See the trip</span>';
    return '<a class="syl-poster" data-name="' + esc(u.trip) + '" data-start="' + u.start + '" data-end="' + u.end +
      '" data-syl="trip-' + slug(u.tag || u.place) + '-' + u.start + '" href="' + esc(href) + '">' + img +
      '<span class="syl-poster-top">' + pills + '</span><span class="syl-poster-body"><span class="syl-date">' +
      MON[s.getMonth()] + ' ' + s.getDate() + '<i>' + s.getFullYear() + '</i></span><span class="syl-trip">' + esc(u.trip) +
      '</span><span class="syl-place">' + esc(where) + '. ' + range(s, e) + '</span><span class="syl-poster-foot"><span class="syl-price">' +
      price + '</span>' + cta + '</span></span></a>';
  }
  function renderTrips(data, live) {
    var box = $('.syl [data-trips]');
    if (!box) return;
    var t0 = today();
    var list = data.upcoming.filter(function (u) { return day(u.end) >= t0; });
    if (!list.length) {
      box.outerHTML = '<p class="syl-empty syl-body" data-trips>No trips on ' + esc(data.first) + '’s calendar right now. New dates drop on the <a class="syl-link" href="/calendar" data-syl="calendar-empty">SYB calendar</a> first.</p>';
      return;
    }
    box.innerHTML = list.map(function (u) { return poster(u, findLive(live, u.trip, u.start), t0, data.first); }).join('');
    box.setAttribute('data-n', list.length);
  }
  // The trip cards saved in the block: same live data, without the JSON
  function tidyStatic(live) {
    var t0 = today();
    $$('.syl [data-trips] .syl-poster[data-start]').forEach(function (a) {
      var s = day(a.getAttribute('data-start')), e = day(a.getAttribute('data-end') || a.getAttribute('data-start'));
      if (days(e, t0) < 0) { a.hidden = true; return; }
      var lv = findLive(live, a.getAttribute('data-name'), a.getAttribute('data-start'));
      var st = status(t0, s, e, lv), top = $('.syl-poster-top', a);
      if (top) top.innerHTML = (st.text ? '<span class="syl-pill ' + st.cls + '">' + st.text + '</span>' : '<span></span>') +
        (st.soon ? '<span class="syl-pill syl-soon">' + st.soon + '</span>' : '');
      if (lv && lv.url) a.setAttribute('href', lv.url);
      var pr = $('.syl-price', a);
      if (pr && lv) pr.textContent = st.out ? 'Sold out' : (lv.price ? 'From ' + money(lv.price) : pr.textContent);
    });
  }

  /* ---------- hero line and trips led ---------- */
  function ledList(data) {
    var t0 = today();
    var ended = data.upcoming.filter(function (u) { return u.kind === 'trip' && day(u.end) < t0; })
      .map(function (u) { var o = {}; for (var k in u) o[k] = u[k]; o.travelers = 0; return o; });
    return ended.reverse().concat(data.led);
  }
  function renderLede(data) {
    var el = $('.syl [data-lede]');
    if (!el) return;
    var t0 = today(), led = ledList(data), trav = 0;
    led.forEach(function (o) { trav += o.travelers || 0; });
    var up = data.upcoming.filter(function (u) { return u.kind === 'trip' && day(u.end) >= t0; });
    var out = [];
    if (led.length) {
      out.push(esc(data.first) + ' has led <b>' + led.length + ' SYB ' + (led.length === 1 ? 'trip' : 'trips') + '</b>' +
        (trav ? ' and <b>' + trav + ' travelers</b>' : '') + '.');
    } else {
      out.push(esc(data.first) + ' leads active and social group trips for SYB.');
    }
    var nx = up[0];
    if (nx) {
      var n = days(day(nx.start), t0);
      out.push(n < 0 ? 'Right now: <b>' + esc(nx.tag) + '</b>, with a crew.' :
        'Next up: <b>' + esc(nx.tag) + '</b>, ' + (n === 0 ? 'leaving today' : n === 1 ? 'leaving tomorrow' : n <= 45 ? 'leaving in ' + n + ' days' :
          MONTH[day(nx.start).getMonth()] + ' ' + day(nx.start).getFullYear()) + '.');
    }
    el.innerHTML = out.join(' ');
  }
  function renderLed(data) {
    var box = $('.syl [data-led]');
    if (!box) return;
    var led = ledList(data), trav = 0;
    led.forEach(function (o) { trav += o.travelers || 0; });
    box.innerHTML = led.map(function (o) {
      var s = day(o.start), inner = '<span class="syl-led-when">' + MON[s.getMonth()] + ' ' + s.getFullYear() +
        '</span><span class="syl-led-what"><strong>' + esc(o.trip) + '</strong><span>' + esc(o.place) + '</span></span><span class="syl-led-n">' +
        (o.travelers ? '<b>' + o.travelers + '</b>travelers' : '') + '</span>';
      return '<li>' + (o.page ? '<a href="' + esc(o.page) + '" data-syl="led-' + slug(o.tag) + '-' + o.start.slice(0, 7) + '">' + inner + '</a>' : '<span>' + inner + '</span>') + '</li>';
    }).join('');
    var sum = $('.syl [data-led-sum]');
    if (sum) sum.textContent = led.length + (led.length === 1 ? ' trip, ' : ' trips, ') + trav + ' travelers so far.';
  }

  /* ---------- reviews ---------- */
  function mark(text, names) {
    var t = esc(text);
    names.forEach(function (n) {
      t = t.replace(new RegExp('(^|[^\\w])(' + n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')(?![\\w])', 'g'), '$1<span class="syl-hl">$2</span>');
    });
    return t;
  }
  function tagHtml(first, r) {
    var s = day(r.trip_start);
    return '<b>' + esc(first) + '’s ' + esc(r.tag) + ' trip</b>, ' + MONTH[s.getMonth()] + ' ' + s.getFullYear();
  }
  function renderReviews(data) {
    var box = $('.syl [data-reviews]');
    if (!box || !data.reviews || !data.reviews.length) return;
    var f = $('.syl [data-review-id]'), fid = f && f.getAttribute('data-review-id');
    var names = [data.first];
    if (f) {
      var tg = $('.syl-tag', f), fr = data.reviews.filter(function (r) { return r.id === fid; })[0];
      if (tg && fr) tg.innerHTML = tagHtml(data.first, fr);
    }
    var list = data.reviews.filter(function (r) { return r.id !== fid; });
    if (!list.length) return;
    box.innerHTML = list.map(function (r) {
      var qs = [r.q].concat(r.more || []).map(function (q) { return '<p>“' + mark(q, names) + '”</p>'; }).join('');
      var who = esc(r.who) + (r.url ? ' on <a data-syl="review-' + slug(r.who) + '" href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.src) + '</a>' : '');
      return '<figure class="syl-card"><p class="syl-tag">' + tagHtml(data.first, r) + '</p><div class="syl-stars" role="img" aria-label="5 out of 5 stars">★★★★★</div><blockquote>' + qs +
        '</blockquote><figcaption class="syl-who">' + who + '</figcaption></figure>';
    }).join('');
  }

  /* ---------- the story reel ---------- */
  function reel(root) {
    var slides = $$('.syl-slide', root), bars = $$('.syl-bars i', root), cap = $('.syl-cap', root);
    if (!slides.length) return;
    var i = 0, held = false, user = false, seen = true, skipClick = false;
    var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (still) root.classList.add('is-still');
    function load(k) {
      var el = $('img,video', slides[k]);
      if (el && el.getAttribute('data-src')) { el.src = el.getAttribute('data-src'); el.removeAttribute('data-src'); }
    }
    function sync() {
      var paused = held || user || !seen || document.hidden;
      root.classList.toggle('is-paused', paused);
      root.classList.toggle('is-held', user);
      var v = $('video', slides[i]);
      if (v) { if (paused) v.pause(); else if (v.play) v.play().catch(function () {}); }
    }
    function show(k) {
      i = (k + slides.length) % slides.length;
      slides.forEach(function (s, n) {
        s.classList.toggle('is-on', n === i);
        s.setAttribute('aria-hidden', n === i ? 'false' : 'true');
        var v = $('video', s);
        if (v && n !== i) v.pause();
      });
      bars.forEach(function (b, n) { b.classList.toggle('is-done', n < i); b.classList.remove('is-on'); });
      if (bars[i]) { void bars[i].offsetWidth; bars[i].classList.add('is-on'); }
      if (cap) cap.textContent = slides[i].getAttribute('data-cap') || '';
      load(i);
      load((i + 1) % slides.length);
      sync();
    }
    bars.forEach(function (b) {
      var fill = $('b', b);
      if (fill) fill.addEventListener('animationend', function () { if (b.classList.contains('is-on') && !still) show(i + 1); });
    });
    var prev = $('.syl-tap-prev', root), next = $('.syl-tap-next', root), pause = $('.syl-pause', root);
    if (prev) prev.addEventListener('click', function () { if (skipClick) { skipClick = false; return; } show(i - 1); });
    if (next) next.addEventListener('click', function () { if (skipClick) { skipClick = false; return; } show(i + 1); });
    if (pause) pause.addEventListener('click', function () {
      user = !user;
      pause.setAttribute('aria-label', user ? 'Play the photos' : 'Pause the photos');
      sync();
    });
    var x0 = null, y0 = 0, holdT = null;
    root.addEventListener('pointerdown', function (e) {
      if (e.target.closest('.syl-pause')) return;
      x0 = e.clientX; y0 = e.clientY;
      holdT = setTimeout(function () { held = true; sync(); }, 260);
    });
    function up(e) {
      clearTimeout(holdT);
      if (x0 == null) return;
      var dx = e.clientX - x0, dy = e.clientY - y0;
      if (held) { held = false; skipClick = true; sync(); }
      else if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) { skipClick = true; show(dx < 0 ? i + 1 : i - 1); }
      x0 = null;
      if (skipClick) setTimeout(function () { skipClick = false; }, 400);
    }
    root.addEventListener('pointerup', up);
    root.addEventListener('pointercancel', function () { clearTimeout(holdT); held = false; x0 = null; sync(); });
    root.addEventListener('contextmenu', function (e) { e.preventDefault(); });
    root.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { show(i + 1); e.preventDefault(); }
      if (e.key === 'ArrowLeft') { show(i - 1); e.preventDefault(); }
    });
    document.addEventListener('visibilitychange', sync);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) { seen = es[0].isIntersecting; sync(); }, { threshold: 0.25 }).observe(root);
    }
    show(0);
  }

  /* ---------- the name always fits its column ---------- */
  function textWidth(el) { var r = document.createRange(); r.selectNodeContents(el); return r.getBoundingClientRect().width; }
  function fitName() {
    $$('.syl .syl-name').forEach(function (h) {
      h.style.removeProperty('font-size');
      var avail = h.getBoundingClientRect().width, need = 0;
      $$('span', h).forEach(function (s) { need = Math.max(need, textWidth(s)); });
      if (need > avail && need > 0) {
        var fs = parseFloat(getComputedStyle(h).fontSize);
        h.style.setProperty('font-size', Math.floor(fs * avail / need * 0.97) + 'px', 'important');
      }
    });
  }

  /* ---------- start ---------- */
  function getJSON(url, ms) {
    return new Promise(function (res) {
      var done = false, t = setTimeout(function () { done = true; res(null); }, ms);
      fetch(url, { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) { if (!done) { clearTimeout(t); res(j); } })
        .catch(function () { if (!done) { clearTimeout(t); res(null); } });
    });
  }
  function init() {
    $$('.syl [data-reel]').forEach(reel);
    fitName();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitName);
    var rt = null;
    window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(fitName, 150); });
    var root = $('.syl[data-leader]');
    var key = root && root.getAttribute('data-leader');
    var liveP = getLive(root);
    liveP.then(function (live) { if (live) tidyStatic(live); });
    if (!key) return;
    var dataP = getJSON(root.getAttribute('data-feed') || CDN + key + '.json', 6000);
    dataP.then(function (data) {
      if (!data || !data.upcoming) return;
      [renderLede, renderLed, renderReviews].forEach(function (f) { try { f(data); } catch (e) { if (window.console) console.warn('syb-leader', e); } });
      document.documentElement.setAttribute('data-syl-feed', data.built || 'ok');
      return liveP.then(function (live) {
        if (!live) return;   // no live departures: keep the cards saved in the block (they have photos and links)
        try { renderTrips(data, live); } catch (e) { if (window.console) console.warn('syb-leader', e); }
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
