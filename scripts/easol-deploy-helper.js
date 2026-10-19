/* Leader page deploy helper v2 for the Easol admin (paste into a surfyogabeer.myeasol.com admin tab).
   SYN.setPin(sha) first: blocks come from raw.githubusercontent.com at that commit, CSS/JS from jsDelivr at it. */
(function () {
  const SID = '8fa286ea-870c-4f08-9c59-f4e0e199cdb9';
  let SHA = '', CDN = '', RAW = '';
  const FILES = ['1-hero.html', '2-trips.html', '3-reviews.html', '4-about.html', '5-end.html'];
  const NAMES = ['1. Leader page - Hero', '2. Leader page - Upcoming trips (live)', '3. Leader page - Trip reviews',
    '4. Leader page - Meet the leader + trips led', '5. Leader page - End'];
  const NATIVE_HIDE = ['[Custom] Text - Centered', '[Custom] Image with Text'];
  const token = () => document.querySelector('meta[name="csrf-token"]').content;
  const norm = s => String(s).replace(/>\s+</g, '><').replace(/\s+/g, ' ').trim();
  const parse = async u => new DOMParser().parseFromString(await (await fetch(u, { cache: 'no-store' })).text(), 'text/html');
  const enc = slug => encodeURIComponent(slug);
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  function setPin(sha) {
    SHA = sha;
    CDN = 'https://cdn.jsdelivr.net/gh/mantas-crypto/syb-widgets@' + sha + '/dist/leader/';
    RAW = 'https://raw.githubusercontent.com/mantas-crypto/syb-widgets/' + sha + '/pages/leaders/';
    return { SHA, CDN, RAW };
  }

  async function files(key) {
    const out = {};
    for (const f of FILES.concat(['head.html'])) {
      const r = await fetch(RAW + key + '/' + f, { cache: 'no-store' });
      if (!r.ok) throw new Error(key + '/' + f + ' ' + r.status);
      let t = await r.text();
      t = t.replace('@@CSS@@', CDN + 'syb-leader.min.css').replace('@@JS@@', CDN + 'syb-leader.min.js');
      if (/@@[A-Z0-9_]+@@/.test(t)) throw new Error('placeholder left in ' + key + '/' + f);
      out[f] = t.trim();
    }
    return out;
  }

  async function pageId(slug) {
    const d = await parse('/admin/site_builder/sites/' + SID + '/pages/' + enc(slug));
    const fr = d.querySelector('iframe[src*="/previews/"]');
    if (!fr) throw new Error('no preview iframe for ' + slug);
    return fr.getAttribute('src').match(/previews\/([^/?#]+)/)[1];
  }

  async function blocks(pid) {
    const d = await parse('/admin/site_builder/sites/' + SID + '/previews/' + pid);
    return [...d.querySelectorAll('.site-builder-blocks > .easol__block-container')].map((c, i) => {
      const url = c.getAttribute('data-block-edit-url') || '';
      // the toggle is a FORM (action .../toggle_visibility?state=hidden while the block is visible), not a link
      const tg = c.querySelector('a[href*="toggle_visibility"], form[action*="toggle_visibility"]');
      const v = tg ? (tg.getAttribute('href') || tg.getAttribute('action') || '') : '';
      return { i, id: (url.match(/blocks\/([0-9a-f-]{36})/) || [])[1], name: (c.getAttribute('data-block-edit-name') || '').replace(/^Edit /, ''),
        visible: tg ? /state=hidden/.test(v) : null };
    });
  }

  async function saveEmbed(bid, html) {
    const url = '/admin/site_builder/sites/' + SID + '/blocks/' + bid;
    const d = await parse(url);
    const el = d.querySelector('[name="variable_form[embed_code]"]');
    if (!el) throw new Error('no embed field on block ' + bid);
    const f = el.closest('form');
    const fd = new FormData(f); fd.set('variable_form[embed_code]', html);
    for (const [k, v] of [...fd.entries()]) if (v instanceof File) fd.delete(k);
    const r = await fetch(f.getAttribute('action'), { method: 'POST', body: fd, headers: { 'X-CSRF-Token': token(), 'Accept': 'text/html' } });
    const d2 = await parse(url);
    const v = d2.querySelector('[name="variable_form[embed_code]"]').getAttribute('value') || d2.querySelector('[name="variable_form[embed_code]"]').value || '';
    return { status: r.status, ok: norm(v) === norm(html), len: v.length };
  }

  async function saveHead(slug, html) {
    const url = '/admin/site_builder/sites/' + SID + '/pages/' + enc(slug) + '/head_html';
    const d = await parse(url);
    const ta = d.querySelector('[name="block_page[head_html]"]');
    if (!ta) throw new Error('no head_html field for ' + slug);
    const f = ta.closest('form');
    const fd = new FormData(f); fd.set('block_page[head_html]', html);
    const r = await fetch(f.getAttribute('action'), { method: 'POST', body: fd, headers: { 'X-CSRF-Token': token(), 'Accept': 'text/html' } });
    const d2 = await parse(url);
    return { status: r.status, ok: norm(d2.querySelector('[name="block_page[head_html]"]').value) === norm(html) };
  }

  async function rename(slug, bid, name) {
    const url = '/admin/sites/' + SID + '/block_pages/' + enc(slug) + '/blocks/' + bid + '/edit';
    const d = await parse(url);
    const n = d.querySelector('[name="block[name]"]');
    if (!n) throw new Error('no name field on ' + bid);
    const f = n.closest('form');
    const fd = new FormData(f); fd.set('block[name]', name);
    for (const [k, v] of [...fd.entries()]) if (v instanceof File) fd.delete(k);
    const r = await fetch(f.getAttribute('action'), { method: 'POST', body: fd, headers: { 'X-CSRF-Token': token(), 'Accept': 'text/html' } });
    return r.status;
  }

  async function hide(bid) {
    const fd = new FormData(); fd.set('_method', 'patch'); fd.set('authenticity_token', token());
    const r = await fetch('/admin/site_builder/sites/' + SID + '/blocks/' + bid + '/toggle_visibility?state=hidden',
      { method: 'POST', body: fd, headers: { 'X-CSRF-Token': token() } });
    return r.status;
  }

  async function addEmbed(slug, index) {
    const fd = new FormData(); fd.set('authenticity_token', token());
    const r = await fetch('/admin/sites/' + SID + '/block_pages/' + enc(slug) + '/blocks/create_from_key?index=' + index + '&theme_key=embed',
      { method: 'POST', body: fd, headers: { 'X-CSRF-Token': token(), 'Accept': 'text/vnd.turbo-stream.html, text/html' } });
    const m = (r.url || '').match(/blocks\/([0-9a-f-]{36})/);
    return { status: r.status, id: m && m[1], url: r.url };
  }

  /* Save the five leader blocks and the head on one page. Reuses blocks already named NAMES[i];
     adds missing ones after the last existing leader block; hides the squad page's native blocks. */
  async function deploy(slug, key) {
    if (!SHA) throw new Error('setPin first');
    const fs = await files(key);
    const pid = await pageId(slug);
    let bl = await blocks(pid);
    const log = [];
    for (let k = 0; k < FILES.length; k++) {
      let b = bl.find(x => x.name === NAMES[k]);
      if (!b) {
        const prev = k ? bl.find(x => x.name === NAMES[k - 1]) : null;
        const idx = prev ? prev.i + 1 : 0;
        const a = await addEmbed(slug, idx);
        if (!a.id) throw new Error('could not add block ' + k + ' on ' + slug + ' ' + a.status);
        await rename(slug, a.id, NAMES[k]);
        bl = await blocks(pid);
        b = bl.find(x => x.id === a.id);
      }
      const s = await saveEmbed(b.id, fs[FILES[k]]);
      log.push(k + 1 + ':' + (s.ok ? 'ok' : 'FAIL ' + s.status));
    }
    for (const b of bl) if (NATIVE_HIDE.includes(b.name) && b.visible) { await hide(b.id); log.push('hid ' + b.name); }
    const h = await saveHead(slug, fs['head.html']);
    log.push('head:' + (h.ok ? 'ok' : 'FAIL ' + h.status));
    return slug + ' ' + log.join(' ');
  }

  /* pages list rows: {name, slug, href, published} */
  async function pages() {
    const d = await parse('/admin/sites/' + SID + '/pages');
    return [...d.querySelectorAll('a[href*="/admin/site_builder/sites/"][href*="/pages/"]')].map(a => ({
      name: a.textContent.trim(), href: a.getAttribute('href'),
      slug: decodeURIComponent((a.getAttribute('href').match(/\/pages\/([^?#]+)/) || [])[1] || '')
    }));
  }

  async function publish(slug) {
    const fd = new FormData(); fd.set('_method', 'put'); fd.set('authenticity_token', token());
    const r = await fetch('/admin/sites/' + SID + '/pages/' + enc(slug) + '?block_page%5Bpublished%5D=true',
      { method: 'POST', body: fd, headers: { 'X-CSRF-Token': token(), 'Accept': 'text/html' } });
    return r.status;
  }

  async function redirect(path, target) {
    const d = await parse('/admin/sites/' + SID + '/redirects/new');
    const f = d.querySelector('form[action*="/redirects"]');
    const fd = new FormData(f); fd.set('redirect[path]', path); fd.set('redirect[target]', target);
    const r = await fetch(f.getAttribute('action'), { method: 'POST', body: fd, headers: { 'X-CSRF-Token': token(), 'Accept': 'text/html' } });
    return r.status + ' ' + path + ' -> ' + target;
  }

  window.SYN = { SID, FILES, NAMES, setPin, token, norm, parse, files, pageId, blocks, saveEmbed, saveHead, rename, hide, addEmbed, deploy, pages, publish, redirect, sleep };
})();
