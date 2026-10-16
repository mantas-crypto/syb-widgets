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
  // The leader data files are read from GitHub directly (fresh within 5 minutes of the twice-daily commit).
  // jsDelivr @main is only the fallback: the repo is over jsDelivr's 50 MB package limit, so @main answers some
  // requests with a 403 and others with an older copy (seen Oct 16 2026). The CSS and JS stay on jsDelivr, pinned.
  var RAW = 'https://raw.githubusercontent.com/mantas-crypto/syb-widgets/main/dist/leaders/';
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

  /* ---------- live departures ----------
     Read in the background from the full calendar (/calendar), which prints every departure as a data card
     (article.sc-card: data-name, data-s, data-e, data-url, data-left, data-st, data-price, data-img). The leader
     page itself prints nothing from Easol, so it opens fast; the cards saved in the block show until this lands.
     A page that prints its own list (#syl-live) is read first. */
  function addLive(m, o) {
    if (!o.name || !o.start) return;
    m[norm(o.name) + '|' + o.start] = o;
    (m[norm(o.name)] = m[norm(o.name)] || []).push(o);
  }
  function liveFrom(doc) {
    var m = {}, n = 0;
    Array.prototype.forEach.call(doc.querySelectorAll('#syl-live i'), function (i) {
      var r = i.getAttribute('data-r');
      addLive(m, {
        name: i.getAttribute('data-n'), start: i.getAttribute('data-d'), end: '', url: i.getAttribute('data-u') || '',
        left: r === '' || r == null ? null : +r, soldOut: i.getAttribute('data-so') === '1',
        price: i.getAttribute('data-p') || '', img: i.getAttribute('data-img') || '',
        imgs: (i.getAttribute('data-imgs') || '').split('|').filter(Boolean),
        dur: parseInt(i.getAttribute('data-dur'), 10) || 0
      });
      n++;
    });
    Array.prototype.forEach.call(doc.querySelectorAll('article.sc-card[data-s]'), function (a) {
      if (a.getAttribute('data-enq') === 'true') return;
      var l = a.getAttribute('data-left');
      addLive(m, {
        name: a.getAttribute('data-name'), start: a.getAttribute('data-s'), end: a.getAttribute('data-e') || '',
        url: (a.getAttribute('data-url') || '').replace(/^https?:\/\/(www\.)?surfyogabeer\.com/, ''),
        left: l === '' || l == null ? null : +l, soldOut: a.getAttribute('data-st') === 'out',
        price: a.getAttribute('data-price') || '', img: a.getAttribute('data-img') || '', imgs: [], dur: 0
      });
      n++;
    });
    return n ? m : null;
  }
  var LIVE_KEY = 'syl_live_v2';
  function getLive(root) {
    var here = liveFrom(document);
    if (here) return Promise.resolve(here);
    var url = (root && root.getAttribute('data-live')) || '/calendar';
    try {
      var c = JSON.parse(sessionStorage.getItem(LIVE_KEY) || 'null');
      if (c && c.u === url && Date.now() - c.t < 15 * 60e3) return Promise.resolve(liveFrom(new DOMParser().parseFromString(c.h, 'text/html')));
    } catch (e) {}
    return fetch(url, { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.text() : ''; }).then(function (t) {
      if (!t) return null;
      // keep only what is read: the #syl-live list, and each calendar card's own tag (its data, not its markup)
      var parts = $$('#syl-live, article.sc-card[data-s]', new DOMParser().parseFromString(t, 'text/html'))
        .map(function (e) { return e.cloneNode(e.id === 'syl-live').outerHTML; });
      if (!parts.length) return null;
      var h = parts.join('');
      try { sessionStorage.setItem(LIVE_KEY, JSON.stringify({ t: Date.now(), u: url, h: h })); } catch (e) {}
      return liveFrom(new DOMParser().parseFromString(h, 'text/html'));
    }).catch(function () { return null; });
  }
  // strict: same trip within 3 days only. Otherwise a long program also matches a date inside it: HQ lists the
  // Academy under a leader's own week (Dec 1 to 6) while Easol sells it as one departure (Nov 4 to Jan 31).
  function findLive(live, name, start, strict) {
    if (!live) return null;
    var hit = live[norm(name) + '|' + start];
    if (hit) return hit;
    var all = live[norm(name)] || [];
    var near = all.filter(function (o) { return Math.abs(days(day(o.start), day(start))) <= 3; });
    if (near[0] || strict) return near[0] || null;
    var d = day(start);
    return all.filter(function (o) { return o.end && day(o.start) <= d && day(o.end) >= d; })[0] || null;
  }
  function money(p) { return String(p || '').replace(/\.00(?=\D*$)/, '').replace(/\s?USD$/, ''); }
  // A photo for a trip card that no other part of the page already shows: the departure's own photo, then
  // its gallery, then photos of other departures of the same trip (a trip happening now is no longer listed).
  function pageImages() {
    var seen = {};
    $$('.syl img').forEach(function (im) {
      if (im.closest('.syl-poster')) return;
      [im.getAttribute('src'), im.getAttribute('data-src')].forEach(function (u) { if (u) seen[u] = 1; });
    });
    return seen;
  }
  function pickImg(live, name, lv, used) {
    var c = [];
    if (lv) c = c.concat(lv.img || [], lv.imgs || []);
    ((live && live[norm(name)]) || []).forEach(function (o) { c = c.concat(o.img || [], o.imgs || []); });
    for (var k = 0; k < c.length; k++) if (c[k] && !used[c[k]]) { used[c[k]] = 1; return c[k]; }
    return '';
  }

  /* ---------- trips ---------- */
  function holiday(s, e) {
    if (days(e, s) > 21) return '';   // a months-long program (the Academy) is not a holiday trip
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
  function poster(u, lv, t0, src) {
    var s = day(u.start), e = day(u.end), st = status(t0, s, e, lv);
    var hol = holiday(s, e), where = (u.place || '') + (u.place && hol ? ', ' + hol : (hol || ''));
    var href = lv && lv.url ? lv.url : (u.page || '/calendar');
    var img = src ? '<img src="' + esc(src) + '" alt="' + esc(u.trip + (u.place ? ', SYB’s trip to ' + u.place : ', an SYB trip')) + '" loading="lazy">' : '';
    var pills = (st.text ? '<span class="syl-pill ' + st.cls + '">' + st.text + '</span>' : '<span></span>') +
      (st.soon ? '<span class="syl-pill syl-soon">' + st.soon + '</span>' : '');
    var price = st.out ? 'Sold out' : (lv && lv.price ? 'From ' + esc(money(lv.price)) : '');
    var cta = st.out ? '<span class="syl-cta syl-cta-ghost">Join Waitlist</span>' : '<span class="syl-cta">See the trip</span>';
    return '<a class="syl-poster" data-name="' + esc(u.trip) + '" data-start="' + u.start + '" data-end="' + u.end +
      '" data-place="' + esc(u.place || '') + '" data-syl="trip-' + slug(u.tag || u.place || u.trip) + '-' + u.start + '" href="' + esc(href) + '">' + img +
      '<span class="syl-poster-top">' + pills + '</span><span class="syl-poster-body"><span class="syl-date">' +
      MON[s.getMonth()] + ' ' + s.getDate() + '<i>' + s.getFullYear() + '</i></span><span class="syl-trip">' + esc(u.trip) +
      '</span><span class="syl-place">' + (where ? esc(where) + '. ' : '') + range(s, e) + '</span><span class="syl-poster-foot"><span class="syl-price">' +
      price + '</span>' + cta + '</span></span></a>';
  }
  // The next SYB departures (any leader), for a leader with nothing on the calendar yet
  function nextDepartures(live, n) {
    var t0 = today(), all = [], names = {};
    Object.keys(live).forEach(function (k) {
      if (k.indexOf('|') > -1) return;
      live[k].forEach(function (o) { if (day(o.start) >= t0) all.push(o); });
    });
    all.sort(function (a, b) { return a.start < b.start ? -1 : a.start > b.start ? 1 : 0; });
    return all.filter(function (o) {
      if (o.soldOut || names[norm(o.name)]) return false;
      names[norm(o.name)] = 1;
      return true;
    }).slice(0, n).map(function (o) {
      var e = new Date(day(o.start).getTime()); e.setDate(e.getDate() + Math.max(0, (o.dur || 1) - 1));
      return { trip: o.name, start: o.start, end: o.end || iso(e), place: '', tag: o.name, page: o.url, kind: 'trip' };
    });
  }
  // Photos already on the saved cards stay put when the cards are redrawn (no swap after the page opens).
  function savedPhotos(box, used) {
    var keep = {};
    $$('.syl-poster[data-start]', box).forEach(function (a) {
      var im = a.querySelector('img');
      if (!im) return;
      keep[norm(a.getAttribute('data-name')) + '|' + a.getAttribute('data-start')] = im.getAttribute('src');
      used[im.getAttribute('src')] = 1;
    });
    return keep;
  }
  // "Where SYB goes next" (a leader with nothing coming up). The saved cards stay put while they can still be
  // booked; a departure that has gone, sold out or left the calendar is swapped for the next one, and a later
  // departure of the same trip keeps that card's photo and place, so the box barely moves once the live data lands.
  function refreshGeneral(box, live) {
    var t0 = today(), used = pageImages(), names = {}, gone = {}, n = 0;
    $$('.syl-poster', box).forEach(function (a) {
      var nm = a.getAttribute('data-name'), s = a.getAttribute('data-start'), k = norm(nm);
      var im = a.querySelector('img'), src = im && im.getAttribute('src');
      var lv = s ? findLive(live, nm, s, true) : null;
      if (!a.hidden && lv && !lv.soldOut && days(day(s), t0) >= 0 && !names[k]) {
        names[k] = 1; n++;
        if (src) used[src] = 1;
        return;
      }
      if (!gone[k]) gone[k] = { img: src, place: a.getAttribute('data-place') || '' };
      a.parentNode.removeChild(a);
    });
    if (n < 4) {
      nextDepartures(live, 40).forEach(function (u) {
        var k = norm(u.trip);
        if (n >= 4 || names[k]) return;
        names[k] = 1; n++;
        var g = gone[k] || {};
        if (g.place) u.place = g.place;
        var src = g.img && !used[g.img] ? g.img : pickImg(live, u.trip, findLive(live, u.trip, u.start), used);
        if (src) used[src] = 1;
        box.insertAdjacentHTML('beforeend', poster(u, findLive(live, u.trip, u.start), t0, src));
      });
      $$('.syl-poster', box).sort(function (a, b) {
        var x = a.getAttribute('data-start'), y = b.getAttribute('data-start');
        return x < y ? -1 : x > y ? 1 : 0;
      }).forEach(function (a) { box.appendChild(a); });
    }
    if (n) box.setAttribute('data-n', n); else box.removeAttribute('data-n');
  }
  function setTripsHead(general, first) {
    var h = $('.syl [data-trips-h]'), sub = $('.syl [data-trips-sub]');
    if (h) h.innerHTML = '<span>Travel</span><span class="syl-g">with ' + esc(general ? 'SYB' : first) + '.</span>';
    if (sub) sub.hidden = !general;
  }
  function renderTrips(data, live) {
    var box = $('.syl [data-trips]');
    if (!box) return;
    var t0 = today();
    var list = data.upcoming.filter(function (u) { return day(u.end) >= t0; });
    var general = !list.length;
    setTripsHead(general, data.first);
    if (general) {
      if (!box.hasAttribute('data-general')) { box.setAttribute('data-general', ''); }
      refreshGeneral(box, live);
      return;
    }
    box.removeAttribute('data-general');
    var used = pageImages(), keep = savedPhotos(box, used);
    box.innerHTML = list.map(function (u) {
      var lv = findLive(live, u.trip, u.start);
      return poster(u, lv, t0, keep[norm(u.trip) + '|' + u.start] || pickImg(live, u.trip, lv, used));
    }).join('');
    box.setAttribute('data-n', list.length);
  }
  // The trip cards saved in the block: same live data, without the JSON
  function tidyStatic(live) {
    var t0 = today(), used = pageImages();
    $$('.syl [data-trips] .syl-poster>img').forEach(function (im) { used[im.getAttribute('src')] = 1; });
    $$('.syl [data-trips] .syl-poster[data-start]').forEach(function (a) {
      var s = day(a.getAttribute('data-start')), e = day(a.getAttribute('data-end') || a.getAttribute('data-start'));
      if (days(e, t0) < 0) { a.hidden = true; return; }
      var lv = findLive(live, a.getAttribute('data-name'), a.getAttribute('data-start'));
      var st = status(t0, s, e, lv), top = $('.syl-poster-top', a);
      if (top) top.innerHTML = (st.text ? '<span class="syl-pill ' + st.cls + '">' + st.text + '</span>' : '<span></span>') +
        (st.soon ? '<span class="syl-pill syl-soon">' + st.soon + '</span>' : '');
      if (lv && lv.url) a.setAttribute('href', lv.url);
      var src = a.querySelector('img') ? '' : pickImg(live, a.getAttribute('data-name'), lv, used);
      if (src) {
        var im = document.createElement('img');
        im.src = src; im.alt = (a.getAttribute('data-name') || 'SYB trip') + ', SYB trip photo'; im.loading = 'lazy';
        a.insertBefore(im, a.firstChild);
      }
      var pr = $('.syl-price', a), cta = $('.syl-cta', a);
      if (pr && lv) pr.textContent = st.out ? 'Sold out' : (lv.price ? 'From ' + money(lv.price) : pr.textContent);
      if (cta && st.out) { cta.textContent = 'Join Waitlist'; cta.classList.add('syl-cta-ghost'); }
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
    var led = ledList(data), trav = 0, places = {};
    led.forEach(function (o) { trav += o.travelers || 0; if (o.place) places[o.place] = 1; });
    var st = { led: led.length, travelers: trav, places: Object.keys(places).length };
    $$('.syl [data-stat]').forEach(function (el) { var v = st[el.getAttribute('data-stat')]; if (v != null) el.textContent = v; });
    $$('.syl [data-stats-nums]').forEach(function (el) { el.hidden = !led.length; });
    var wrap = $('.syl [data-led-box]');
    if (wrap) wrap.hidden = !led.length;
    if (!box) return;
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
    if (!names.length) return t;
    var alt = names.map(function (n) { return esc(n).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }).join('|');
    return t.replace(new RegExp('(^|[^\\w])(' + alt + ')(?![\\w])', 'g'), '$1<span class="syl-hl">$2</span>');
  }
  function tagHtml(first, r) {
    var s = day(r.trip_start);
    return '<b>' + esc(first) + '’s ' + esc(r.tag) + ' trip</b>, ' + MON[s.getMonth()] + ' ' + s.getFullYear();
  }
  function cite(r) {
    return esc(r.who) + (r.url ? ' on <a data-syl="review-' + slug(r.who) + '" href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.src) + '</a>' : '');
  }
  function renderReviews(data) {
    var box = $('.syl [data-reviews]');
    if (!box || !data.reviews || !data.reviews.length) return;
    var sec = box.closest('.syl');
    if (sec) sec.hidden = false;
    var f = $('.syl .syl-feature'), fid = f && f.getAttribute('data-review-id');
    var names = [data.first].concat(data.aliases || []);
    if (data.first.split(' ').length > 1) names.push(data.first.split(' ')[0]);
    names = names.filter(function (n, k) { return n && names.indexOf(n) === k; })
      .sort(function (a, b) { return b.length - a.length; });
    var fr = data.reviews.filter(function (r) { return r.id === fid; })[0];
    if (f && !fr) {
      fr = data.reviews[0];
      fid = fr.id;
      f.setAttribute('data-review-id', fid);
      var body = f.querySelector(':scope>div');
      if (body) body.innerHTML = '<p class="syl-tag"></p><blockquote style="margin:0;padding:0;border:0"><p class="syl-q">“' + mark(fr.q, names) + '”</p>' +
        (fr.more || []).map(function (q) { return '<p class="syl-q-more">“' + mark(q, names) + '”</p>'; }).join('') +
        '</blockquote><figcaption class="syl-cite">' + cite(fr) + '</figcaption>';
    }
    if (f && fr) {
      var tg = $('.syl-tag', f);
      if (tg) tg.innerHTML = tagHtml(data.first, fr);
    }
    var list = data.reviews.filter(function (r) { return r.id !== fid; });
    box.hidden = !list.length;
    if (!list.length) return;
    box.innerHTML = list.map(function (r) {
      var qs = [r.q].concat(r.more || []).map(function (q) { return '<p>“' + mark(q, names) + '”</p>'; }).join('');
      var who = cite(r);
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
    liveP.then(function (live) {
      if (!live) return;
      tidyStatic(live);
      var gb = $('.syl [data-trips][data-general]');
      if (gb) refreshGeneral(gb, live);
    });
    if (!key) return;
    var own = root.getAttribute('data-feed');
    var dataP = own ? getJSON(own, 6000) : getJSON(RAW + key + '.json', 5000).then(function (j) {
      return j && j.upcoming ? j : getJSON(CDN + key + '.json', 5000);
    });
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
