/* SYB Leaders page (surfyogabeer.com/squad): live trips on every card, filters, and the story player.
   The block (pages/squad/1-leaders.html) is the page as of the day it was saved; this keeps it current from
   dist/leaders/squad.json (rebuilt twice a day from SYB HQ by the leader pages job). */
(function () {
  'use strict';
  var RAW = 'https://raw.githubusercontent.com/mantas-crypto/syb-widgets/main/dist/leaders/squad.json';
  var CDN = 'https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@main/dist/leaders/squad.json';
  var MON = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');
  var PHOTO_S = 5;
  var ICON = {
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    prev: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
    next: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>',
    sound: '<svg class="is-mute" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 9.5h3.5l4.5-4v13l-4.5-4H3.5z"/><path d="M15.5 9.5l5 5M20.5 9.5l-5 5"/></svg>' +
      '<svg class="is-loud" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 9.5h3.5l4.5-4v13l-4.5-4H3.5z"/><path d="M15.5 9a4.2 4.2 0 0 1 0 6M18.3 6.3a8 8 0 0 1 0 11.4"/></svg>'
  };

  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function day(s) { var p = String(s).split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function today() { var d = new Date(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  function mday(s) { var d = day(s); return MON[d.getMonth()] + ' ' + d.getDate(); }
  function poss(n) { return n + '\u2019s'; }
  function store(k, v) { try { if (v === undefined) return JSON.parse(localStorage.getItem(k) || 'null'); localStorage.setItem(k, JSON.stringify(v)); } catch (e) { return null; } }
  function getJSON(url, ms) {
    return new Promise(function (res) {
      var done = false, t = setTimeout(function () { done = true; res(null); }, ms);
      fetch(url, { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) { if (!done) { clearTimeout(t); res(j); } })
        .catch(function () { if (!done) { clearTimeout(t); res(null); } });
    });
  }

  var root, grid, rail, chipsBox, statusEl, people = [], crew = [], byKey = {}, filter = 'all', T = today();
  // people: the trip leaders (faces, stories, the count). crew: SYB HQ team members who do not lead trips (Sara,
  // Danielle): a card at the end of the grid and under SYB HQ only (Mantas, Oct 19 2026).

  /* ---------- order, pills, stats ---------- */
  function nextTrip(p) { return p.up && p.up[0]; }
  function cardTags(c) { return (c.getAttribute('data-tags') || '').split(' '); }
  function leads(c) { var p = byKey[c.getAttribute('data-key')]; return (p ? p.tags || [] : cardTags(c)).indexOf('lead') >= 0; }
  function away(p) { var u = nextTrip(p); return !!u && day(u.s) <= T && T <= day(u.e); }
  function rank(a, b) {
    function k(p) { var u = nextTrip(p); return p.key === 'mantas' ? [0, '', 0, ''] : u ? [1, u.s, 0, p.name] : [2, '', -(p.led || 0), p.name]; }
    var x = k(a), y = k(b);
    for (var i = 0; i < 4; i++) { if (x[i] < y[i]) return -1; if (x[i] > y[i]) return 1; }
    return 0;
  }
  function pillHTML(p) {
    var u = nextTrip(p);
    if (!u) return '';
    if (away(p)) return '<span class="sys-pill is-now">On a trip now</span>';
    var soon = (day(u.s) - T) / 864e5 <= 21;
    return '<span class="sys-pill' + (soon ? ' is-soon' : '') + '"><span class="sys-f" aria-hidden="true">' + esc(u.f) + '</span>' + esc(mday(u.s)) + '</span>';
  }
  function statHTML(p) {
    if ((p.tags || []).indexOf('lead') < 0) return '<span class="sys-stat"><span><b>SYB HQ</b></span></span>';
    if (p.led) {
      return '<span class="sys-stat"><span><b>' + p.led + '</b> trip' + (p.led === 1 ? '' : 's') + '</span><span class="sys-flags" aria-hidden="true">' +
        esc((p.flags || []).slice(0, 4).map(function (f) { return f[0]; }).join('')) + '</span></span>';
    }
    if (nextTrip(p)) return '<span class="sys-stat"><span>First trip coming up</span></span>';
    return '';
  }

  /* ---------- live data onto the saved cards ---------- */
  function applyLive(doc) {
    var list = (doc && doc.people) || [];
    if (!list.length) return;
    people = list.slice().sort(rank);
    crew = ((doc && doc.team) || []).slice();
    byKey = {};
    people.concat(crew).forEach(function (p) { byKey[p.key] = p; });
    var cards = {}, rings = {};
    $$('.sys-card', grid).forEach(function (c) { cards[c.getAttribute('data-key')] = c; });
    $$('.sys-ring', rail).forEach(function (b) { rings[b.getAttribute('data-story')] = b.parentNode; });
    people.concat(crew).forEach(function (p) {
      var c = cards[p.key];
      if (c) {
        var a = $('a', c), old = $('.sys-pill', a), st = $('.sys-stat', a), body = $('.sys-body', a);
        if (old) old.parentNode.removeChild(old);
        var ph = pillHTML(p);
        if (ph) $('.sys-pic', a).insertAdjacentHTML('afterend', ph);
        if (st) st.parentNode.removeChild(st);
        var sh = statHTML(p);
        if (sh) body.insertAdjacentHTML('beforeend', sh);
        grid.appendChild(c);
      }
      var r = rings[p.key];
      if (r) {
        var now = $('.sys-ring-now', r);
        if (away(p) && !now) $('.sys-ring-pic', r).insertAdjacentHTML('beforeend', '<span class="sys-ring-now">On a trip</span>');
        if (!away(p) && now) now.parentNode.removeChild(now);
        rail.appendChild(r);
      }
    });
    var n = $('[data-sys-n]', root);
    if (n) n.textContent = people.length;
    buildPlaces();
    setFilter(filter, true);
    live();
  }
  function live() {                // the faces pop in once, after the order is final
    if (root.classList.contains('is-live')) return;
    $$('li', rail).forEach(function (li, k) { li.style.setProperty('--n', Math.min(k, 18)); });
    root.classList.add('is-live');
  }

  /* ---------- filters ---------- */
  function placesOf(p) {
    var out = {};
    Object.keys(p.cc || {}).forEach(function (c) { out[c] = 1; });
    (p.up || []).forEach(function (u) { if (u.c) out[u.c] = 1; });
    return out;
  }
  function buildPlaces() {
    var box = $('[data-sys-places]', root);
    if (!box || !people.length) return;
    var count = {}, flag = {};
    people.forEach(function (p) {
      Object.keys(placesOf(p)).forEach(function (c) { count[c] = (count[c] || 0) + 1; });
      (p.flags || []).forEach(function (f) { flag[f[1]] = f[0]; });
      (p.up || []).forEach(function (u) { if (u.c && !flag[u.c]) flag[u.c] = u.f; });
    });
    var names = Object.keys(count).sort(function (a, b) { return count[b] - count[a] || (a < b ? -1 : 1); });
    box.innerHTML = names.map(function (c) {
      return '<button class="sys-chip" type="button" data-f="c:' + esc(c) + '" data-syl="squad-filter-' + esc(c.toLowerCase().replace(/[^a-z]+/g, '-')) +
        '" aria-pressed="false"><span class="sys-f" aria-hidden="true">' + esc(flag[c] || '') + '</span>' + esc(c) + '</button>';
    }).join('');
  }
  function matches(p, f) {
    if (f === 'all') return true;
    if (f === 'soon') return !!nextTrip(p);
    if (f === 'photo' || f === 'hq') return (p.tags || []).indexOf(f) >= 0;
    if (f.indexOf('c:') === 0) return !!placesOf(p)[f.slice(2)];
    return true;
  }
  function whereLine(p, c) {
    var up = (p.up || []).filter(function (u) { return u.c === c; })[0];
    if (up) return day(up.s) <= T ? 'In ' + c + ' right now' : 'Leading ' + c + ' ' + mday(up.s);
    var n = (p.cc || {})[c] || 0;
    return n ? 'Led ' + n + ' ' + c + ' trip' + (n === 1 ? '' : 's') : '';
  }
  function setFilter(f, quiet) {
    filter = f;
    $$('.sys-chip', chipsBox).forEach(function (b) {
      var on = b.getAttribute('data-f') === f;
      b.classList.toggle('is-on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    var country = f.indexOf('c:') === 0 ? f.slice(2) : '';
    var shown = [];
    $$('.sys-card', grid).forEach(function (c) {
      var p = byKey[c.getAttribute('data-key')];
      var ok = p ? matches(p, f) : f === 'all' || ((f === 'photo' || f === 'hq') && cardTags(c).indexOf(f) >= 0);
      c.hidden = !ok;
      var w = $('.sys-where', c);
      if (w) {
        var line = ok && country && p ? whereLine(p, country) : '';
        w.textContent = line;
        w.hidden = !line;
      }
      if (ok) shown.push(c);
    });
    if (country) {                 // leading there soonest, then most trips there
      shown.sort(function (a, b) {
        var pa = byKey[a.getAttribute('data-key')], pb = byKey[b.getAttribute('data-key')];
        function k(p) { var u = (p.up || []).filter(function (x) { return x.c === country; })[0]; return u ? [0, u.s, 0] : [1, '', -((p.cc || {})[country] || 0)]; }
        var x = k(pa), y = k(pb);
        for (var i = 0; i < 3; i++) { if (x[i] < y[i]) return -1; if (x[i] > y[i]) return 1; }
        return rank(pa, pb);
      });
      shown.forEach(function (c) { grid.appendChild(c); });
    } else if (people.length) {
      people.concat(crew).forEach(function (p) { var c = $('.sys-card[data-key="' + p.key + '"]', grid); if (c) grid.appendChild(c); });
    }
    var n = shown.length, s;
    var led = shown.filter(leads).length, team = shown.filter(function (c) { return !leads(c); });
    if (f === 'all') {
      s = 'All <b>' + led + '</b> leaders';
      if (team.length) s += ', plus ' + esc(team.length <= 2 ? team.map(function (c) { return c.getAttribute('data-first'); }).join(' and ') : team.length + ' more') + ' from SYB HQ';
    }
    else if (f === 'soon') s = '<b>' + n + '</b> leaders with a trip coming up';
    else if (f === 'photo') s = '<b>' + n + '</b> photographers, and every one of them leads trips too';
    else if (f === 'hq') s = '<b>' + n + '</b> ' + (n === 1 ? 'person' : 'people') + ' at SYB HQ' +
      (!led ? '' : led === n ? ', and every one of them leads trips too' : ', and ' + led + ' of them lead trips too');
    else s = '<b>' + n + '</b> ' + (n === 1 ? 'leader has' : 'leaders have') + ' led ' + esc(country) + ' or ' + (n === 1 ? 'is' : 'are') + ' leading it next';
    statusEl.innerHTML = s;
    if (!quiet) {
      try { history.replaceState(history.state, '', f === 'all' ? location.pathname + location.search : '#' + f.replace(/^c:/, '').toLowerCase().replace(/[^a-z]+/g, '-')); } catch (e) {}
      var top = grid.getBoundingClientRect().top;       // the status line is for screen readers only
      var bar = $('.sys-bar', root), bh = bar ? bar.getBoundingClientRect().bottom : 0;
      if (top < bh || top > window.innerHeight * 0.6) window.scrollTo({ top: window.pageYOffset + top - bh - 12, behavior: 'smooth' });
    }
  }
  function filterFromHash() {
    var h = decodeURIComponent((location.hash || '').slice(1)).toLowerCase();
    if (!h) return null;
    if (h === 'soon' || h === 'photo' || h === 'hq') return h;
    var b = $$('.sys-chip', chipsBox).filter(function (x) { return (x.getAttribute('data-f') || '').slice(2).toLowerCase().replace(/[^a-z]+/g, '-') === h; })[0];
    return b ? b.getAttribute('data-f') : null;
  }

  /* ---------- names always fit their card (and the headline its column) ---------- */
  function fitNames() {
    var h1 = $('.sys-h1', root);
    if (h1) {
      h1.style.removeProperty('font-size');
      var room = h1.getBoundingClientRect().width, widest = 0;
      $$('span', h1).forEach(function (s) { var r = document.createRange(); r.selectNodeContents(s); widest = Math.max(widest, r.getBoundingClientRect().width); });
      if (widest > room && room > 0) h1.style.setProperty('font-size', Math.floor(parseFloat(getComputedStyle(h1).fontSize) * room / widest * 0.97) + 'px', 'important');
    }
    $$('.sys-name', grid).forEach(function (h) {
      h.style.removeProperty('font-size');
      var avail = h.getBoundingClientRect().width, need = 0;
      $$('span', h).forEach(function (s) { need = Math.max(need, s.scrollWidth); });
      if (need > avail && avail > 0) {
        var fs = parseFloat(getComputedStyle(h).fontSize);
        h.style.fontSize = Math.max(13, Math.floor(fs * avail / need * 0.98)) + 'px';
      }
    });
  }

  /* ---------- stories ---------- */
  var S = { el: null, i: 0, j: 0, slides: [], held: false, user: false, sound: false, raf: 0, waitT: null, opener: null, pushed: false };
  function storyDOM() {
    if (S.el) return S.el;
    var d = document.createElement('div');
    d.className = 'syl sys-story';
    d.hidden = true;
    d.setAttribute('role', 'dialog');
    d.setAttribute('aria-modal', 'true');
    d.setAttribute('aria-labelledby', 'sys-st-name');
    d.tabIndex = -1;
    d.innerHTML = '<button class="sys-st-side sys-st-side-prev" type="button" aria-label="Previous leader">' + ICON.prev + '</button>' +
      '<div class="sys-st-panel"><div class="sys-st-media"></div><div class="sys-st-bars" aria-hidden="true"></div>' +
      '<div class="sys-st-top"><img class="sys-st-av" alt=""><div class="sys-st-who"><p class="sys-st-name" id="sys-st-name"></p><p class="sys-st-label"></p></div>' +
      '<button class="sys-st-btn sys-st-sound" type="button" aria-pressed="false" aria-label="Turn the sound on" hidden>' + ICON.sound + '</button>' +
      '<button class="sys-st-btn sys-st-close" type="button" aria-label="Close the story">' + ICON.close + '</button></div>' +
      '<button class="sys-st-tap sys-st-tap-prev" type="button" aria-label="Previous"></button><button class="sys-st-tap sys-st-tap-next" type="button" aria-label="Next"></button>' +
      '<p class="sys-st-cap" aria-live="polite"></p>' +
      '<div class="sys-st-foot"><p class="sys-st-trip"></p><a class="sys-st-cta" href="#"></a></div></div>' +
      '<button class="sys-st-side sys-st-side-next" type="button" aria-label="Next leader">' + ICON.next + '</button>';
    document.body.appendChild(d);
    S.el = d;
    $('.sys-st-close', d).addEventListener('click', function (e) { e.stopPropagation(); closeStory(); });
    $('.sys-st-side-prev', d).addEventListener('click', function () { openLeader(S.i - 1, 0); });
    $('.sys-st-side-next', d).addEventListener('click', function () { openLeader(S.i + 1, 0); });
    $('.sys-st-tap-prev', d).addEventListener('click', function () { if (S.skip) { S.skip = false; return; } step(-1); });
    $('.sys-st-tap-next', d).addEventListener('click', function () { if (S.skip) { S.skip = false; return; } step(1); });
    $('.sys-st-sound', d).addEventListener('click', function (e) {
      e.stopPropagation();
      S.sound = !S.sound;
      soundBtn();
      if (S.sound) { S.user = false; clipBar(S.j); clearTimeout(S.waitT); }
      sync();
    });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.preventDefault(); closeStory(); }
      if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
      if (e.key === 'Tab') {        // keep focus inside the player
        var f = $$('button:not([hidden]),a[href]', d).filter(function (x) { return x.offsetParent !== null; });
        if (!f.length) return;
        if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
        else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
      }
    });
    var panel = $('.sys-st-panel', d), x0 = null, y0 = 0, holdT = null;
    panel.addEventListener('pointerdown', function (e) {
      if (e.target.closest('.sys-st-btn,.sys-st-cta')) return;
      x0 = e.clientX; y0 = e.clientY;
      holdT = setTimeout(function () { S.held = true; sync(); }, 220);
    });
    function up(e) {
      clearTimeout(holdT);
      if (x0 == null) return;
      var dx = e.clientX - x0, dy = e.clientY - y0;
      if (S.held) { S.held = false; S.skip = true; sync(); }
      else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) { S.skip = true; closeStory(); }
      else if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) { S.skip = true; openLeader(S.i + (dx < 0 ? 1 : -1), 0); }
      x0 = null;
      if (S.skip) setTimeout(function () { S.skip = false; }, 400);
    }
    panel.addEventListener('pointerup', up);
    panel.addEventListener('pointercancel', function () { clearTimeout(holdT); S.held = false; x0 = null; sync(); });
    panel.addEventListener('contextmenu', function (e) { e.preventDefault(); });
    document.addEventListener('visibilitychange', function () { if (!d.hidden) sync(); });
    window.addEventListener('popstate', function () { if (!d.hidden) { S.pushed = false; closeStory(true); } });
    return d;
  }
  function soundBtn() {
    var b = $('.sys-st-sound', S.el);
    b.classList.toggle('is-on', S.sound);
    b.setAttribute('aria-pressed', S.sound ? 'true' : 'false');
    b.setAttribute('aria-label', S.sound ? 'Turn the sound off' : 'Turn the sound on');
  }
  function clip(j) { var f = S.figs && S.figs[j]; return f ? $('video', f) : null; }
  function bar(j) { return S.bars && S.bars[j]; }
  function track() {
    S.raf = 0;
    var v = clip(S.j), b = bar(S.j), f = b && $('b', b);
    if (!v || !f || !b.classList.contains('is-clip')) return;
    if (v.duration) f.style.width = Math.min(100, v.currentTime / v.duration * 100) + '%';
    if (!v.paused && !v.ended) S.raf = requestAnimationFrame(track);
  }
  function clipBar(j) {
    var b = bar(j), v = clip(j);
    if (!b || !v || v.error) return;
    b.classList.add('is-clip');
    if (!S.raf && !v.paused) S.raf = requestAnimationFrame(track);
  }
  function timed(j) {
    var b = bar(j), f = b && $('b', b);
    if (j !== S.j || !b || !b.classList.contains('is-clip')) return;
    b.classList.remove('is-clip', 'is-on');
    if (f) f.style.width = '';
    b.style.setProperty('--dur', PHOTO_S + 's');
    void b.offsetWidth; b.classList.add('is-on');
    if (clip(j) && clip(j).error) $('.sys-st-sound', S.el).hidden = true;
  }
  function sync() {
    if (!S.el) return;
    var paused = S.held || S.user || document.hidden;
    S.el.classList.toggle('is-paused', paused);
    var v = clip(S.j), j = S.j;
    if (!v) return;
    v.muted = !S.sound;
    if (paused) { v.pause(); return; }
    var p = v.play && v.play();
    if (p && p.catch) p.catch(function (e) {
      if (j !== S.j || (e && e.name === 'AbortError')) return;
      if (S.sound) { S.sound = false; soundBtn(); v.muted = true; v.play().catch(function () { timed(j); }); }
      else timed(j);
    });
  }
  function showSlide(j) {
    if (S.raf) { cancelAnimationFrame(S.raf); S.raf = 0; }
    clearTimeout(S.waitT);
    S.j = j;
    S.figs.forEach(function (f, n) {
      f.classList.toggle('is-on', n === j);
      var v = $('video', f);
      if (v && n !== j) { v.pause(); try { v.currentTime = 0; } catch (e) {} }
    });
    S.bars.forEach(function (b, n) {
      b.classList.toggle('is-done', n < j); b.classList.remove('is-on', 'is-clip');
      var f = $('b', b); if (f) f.style.width = '';
    });
    var s = S.slides[j], b = bar(j);
    load(j); load(j + 1);
    var v = clip(j);
    $('.sys-st-sound', S.el).hidden = !(v && s.a);
    $('.sys-st-cap', S.el).textContent = j === 0 ? '' : (s.c || '');
    if (b) {
      b.style.setProperty('--dur', PHOTO_S + 's');
      if (v) b.classList.add('is-clip');
      void b.offsetWidth; b.classList.add('is-on');
    }
    if (v) {
      var k = j;
      S.waitT = setTimeout(function wait() {
        if (k !== S.j || v.currentTime > 0) return;
        if (S.held || S.user || document.hidden) S.waitT = setTimeout(wait, 8000);
        else timed(k);
      }, 8000);
    }
    sync();
  }
  function load(j) {
    var f = S.figs[j];
    if (!f || f.getAttribute('data-ready')) return;
    var s = S.slides[j];
    f.setAttribute('data-ready', '1');
    if (s.v) {
      var v = document.createElement('video');
      v.muted = true; v.playsInline = true; v.preload = 'auto';
      v.setAttribute('muted', ''); v.setAttribute('playsinline', '');
      v.poster = s.p || ''; v.src = s.v;
      v.style.setProperty('--pos', s.pos || '50% 35%');
      v.addEventListener('playing', function () { if (S.figs[S.j] === f && !S.raf) S.raf = requestAnimationFrame(track); });
      v.addEventListener('ended', function () { if (S.figs[S.j] === f && bar(S.j) && bar(S.j).classList.contains('is-clip')) step(1); });
      f.appendChild(v);
    } else {
      var im = document.createElement('img');
      im.alt = s.alt || '';
      im.decoding = 'async';
      im.src = s.i;
      im.style.setProperty('--pos', s.pos || '50% 35%');
      f.appendChild(im);
    }
  }
  function step(d) {
    var j = S.j + d;
    if (j < 0) openLeader(S.i - 1, 0, true);
    else if (j >= S.slides.length) openLeader(S.i + 1, 0);
    else showSlide(j);
  }
  function story(p) {
    var st = (p.story || []).slice();
    if (!st.length) st = [{ i: p.img, c: '', pos: p.pos || '50% 30%', alt: p.name }];
    return st;
  }
  function openLeader(i, j, back) {
    if (i < 0) { if (back) showSlide(0); return; }
    if (i >= people.length) { closeStory(); return; }
    var p = people[i], d = S.el;
    S.i = i;
    S.slides = story(p);
    var media = $('.sys-st-media', d), bars = $('.sys-st-bars', d);
    media.innerHTML = S.slides.map(function () { return '<figure></figure>'; }).join('');
    bars.innerHTML = S.slides.map(function () { return '<i><b></b></i>'; }).join('');
    S.figs = $$('figure', media);
    S.bars = $$('i', bars);
    S.bars.forEach(function (b) {
      var f = $('b', b);
      f.addEventListener('animationend', function () { if (b.classList.contains('is-on') && !b.classList.contains('is-clip') && S.bars === bars.__list) step(1); });
    });
    bars.__list = S.bars;
    var av = $('.sys-st-av', d);
    av.src = p.av || p.img;
    $('.sys-st-name', d).textContent = p.name;
    $('.sys-st-label', d).textContent = p.label + (p.city ? ', ' + p.city : '');
    var u = nextTrip(p), trip = $('.sys-st-trip', d);
    if (u && away(p)) trip.innerHTML = 'On a trip now: <b>' + esc(u.f + ' ' + (u.t || u.pl)) + '</b>';
    else if (u) trip.innerHTML = 'Next trip: <b>' + esc(u.f + ' ' + (u.pl || u.t) + ', ' + mday(u.s)) + '</b>';
    else if (p.led) trip.innerHTML = 'Has led <b>' + p.led + ' SYB trip' + (p.led === 1 ? '' : 's') + '</b>';
    else trip.textContent = '';
    var cta = $('.sys-st-cta', d);
    cta.href = p.page;
    cta.textContent = u ? 'Travel with ' + p.first : 'See ' + poss(p.first) + ' page';
    cta.setAttribute('data-syl', 'squad-story-cta-' + p.key);
    $('.sys-st-side-prev', d).style.visibility = i > 0 ? '' : 'hidden';
    $('.sys-st-side-next', d).style.visibility = i < people.length - 1 ? '' : 'hidden';
    seen(p.key);
    showSlide(Math.min(j || 0, S.slides.length - 1));
  }
  function seen(key) {
    var s = store('syb-squad-seen') || [];
    if (s.indexOf(key) < 0) { s.push(key); store('syb-squad-seen', s); }
    var b = $('.sys-ring[data-story="' + key + '"]', rail);
    if (b) b.classList.add('is-seen');
  }
  function openStory(key, opener) {
    var i = -1;
    for (var n = 0; n < people.length; n++) if (people[n].key === key) { i = n; break; }
    if (i < 0) return;
    var d = storyDOM();
    S.opener = opener || null;
    S.user = false; S.held = false;
    d.hidden = false;
    document.documentElement.classList.add('sys-lock');
    try { if (!S.pushed) { history.pushState({ sysStory: 1 }, ''); S.pushed = true; } } catch (e) {}
    openLeader(i, 0);
    d.focus({ preventScroll: true });
  }
  function closeStory(fromHistory) {
    var d = S.el;
    if (!d || d.hidden) return;
    if (S.raf) { cancelAnimationFrame(S.raf); S.raf = 0; }
    clearTimeout(S.waitT);
    $$('video', d).forEach(function (v) { v.pause(); v.removeAttribute('src'); v.load(); });
    $('.sys-st-media', d).innerHTML = '';
    d.hidden = true;
    document.documentElement.classList.remove('sys-lock');
    if (!fromHistory && S.pushed) { S.pushed = false; try { history.back(); } catch (e) {} }
    if (S.opener) { try { S.opener.focus({ preventScroll: true }); } catch (e) {} }
  }

  /* ---------- start ---------- */
  function init() {
    root = $('.sys[data-squad]');
    if (!root) return;
    grid = $('[data-sys-grid]', root);
    rail = $('[data-sys-rail]', root);
    chipsBox = $('[data-sys-chips]', root);
    statusEl = $('[data-sys-status]', root);
    (store('syb-squad-seen') || []).forEach(function (k) { var b = $('.sys-ring[data-story="' + k + '"]', rail); if (b) b.classList.add('is-seen'); });
    chipsBox.addEventListener('wheel', function (e) {
      if (Math.abs(e.deltaY) <= Math.abs(e.deltaX)) return;
      var max = chipsBox.scrollWidth - chipsBox.clientWidth;
      if (max <= 0 || (e.deltaY < 0 && chipsBox.scrollLeft <= 0) || (e.deltaY > 0 && chipsBox.scrollLeft >= max)) return;
      chipsBox.scrollLeft += e.deltaY;
      e.preventDefault();
    }, { passive: false });
    chipsBox.addEventListener('click', function (e) {
      var b = e.target.closest('.sys-chip');
      if (b) setFilter(b.getAttribute('data-f'));
    });
    var pending = null, loaded = false;
    rail.addEventListener('click', function (e) {
      var b = e.target.closest('.sys-ring');
      if (!b) return;
      if (loaded) openStory(b.getAttribute('data-story'), b);
      else pending = b;
    });
    fitNames();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitNames);
    var rt = null;
    window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(fitNames, 150); });
    var hf = filterFromHash();
    if (hf) setFilter(hf, true);
    setTimeout(live, 1200);         // the data is slow or missing: show the faces anyway
    getJSON(RAW, 5000).then(function (j) { return j && j.people ? j : getJSON(CDN, 5000); }).then(function (doc) {
      if (doc && doc.people) {
        applyLive(doc);
        var h2 = filterFromHash();
        if (h2) setFilter(h2, true);
        document.documentElement.setAttribute('data-sys-feed', doc.built || 'ok');
      }
      loaded = people.length > 0;
      if (pending && loaded) { openStory(pending.getAttribute('data-story'), pending); pending = null; }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
