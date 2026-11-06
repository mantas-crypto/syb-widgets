
(function(){
"use strict";

/* ===== settings ===== */
var MODE = "live"; // the live build sets this to "live"
var IMG = (function(){ var s = document.currentScript; return s && s.src ? s.src.replace(/[^\/?#]*([?#].*)?$/, "").replace(/live\/$/, "") + "img/" : "img/"; })();      // the live build points this at the CDN copy of the photos
var CONTACT = {
  name: "Sarah Gagne",
  // Stand-ins until Sarah has her own address and number. Swap these two lines.
  email: "support@surfyogabeer.com",
  phone: "+1 917 900 6821"
};
var DEFAULT_COMPANY = "Example Company"; // on the live page, ?for=F45%20Toronto shows that name instead
var BASE = 1950, MIN_PEOPLE = 8, BASE_NIGHTS = 5, MAX_EXTRA_NIGHTS = 3, EXTRA_NIGHT = 250, DEPOSIT = 0.2;

var ROOMS = {
  shared:   { label:"Shared rooms",  add:0,   max:25 },
  twin:     { label:"Twin rooms",    add:300, max:20 },
  "private":{ label:"Private rooms", add:700, max:12 }
};
/* step 3: the compound. big = the large first tile. pos = where to center the crop. */
var STAY = [
  { img:"villa-infinity-pool.jpg", name:"Infinity pool", note:"On the cliff edge, facing the sunset", alt:"The infinity pool at sunset with the bay behind it", big:true },
  { img:"villa-cliff.jpg", name:"Gated and private", note:"Security on site 24 hours a day", alt:"The villas on the jungle cliff above the bay" },
  { img:"stay-wifi.jpg", name:"Fast wifi", note:"Fiber, usually 100 Mbps or more, with a backup generator", alt:"A laptop on the villa deck showing a 290 Mbps speed test" },
  { img:"villa-plunge-pool.jpg", name:"Plunge pool", note:"Made for golden hour", alt:"Two people in the plunge pool at sunset" },
  { img:"stay-yoga-deck.jpg", name:"Yoga deck", note:"Facing the Pacific", alt:"A group doing yoga on the deck over the ocean" },
  { img:"villa-jungle-gym.jpg", name:"Jungle gym", note:"TRX straps, wooden weights and ropes", alt:"Guys lifting wooden weights in the jungle gym" },
  { img:"stay-beach-path.jpg", name:"Path to the beach", note:"Private stairs down to the surf", alt:"The jungle path down to Playa Maderas, with horses on the sand" },
  { img:"villa-dining.jpg", name:"Dining room", note:"One long table for the whole team", alt:"A long dining table under arched windows", pos:"50% 62%" },
  { img:"villa-terrace.jpg", name:"Terrace", note:"Rocking chairs over the bay", alt:"Rocking chairs on a covered terrace over the jungle and the bay" }
];
/* step 4: included in the base */
var INCLUDED = [
  { img:"inc-airport.jpg",   name:"Airport pickups",   note:"Not in the back of a pickup, promise", alt:"An SYB guest riding in the back of a pickup truck on the dirt road to Maderas" },
  { img:"inc-breakfast.jpg", name:"5 breakfasts",      alt:"Breakfast plates: eggs, bacon, gallo pinto, plantains and tortillas" },
  { img:"inc-dinner.jpg",    name:"4 chef dinners",    alt:"A chef's spread of dinner dishes on the villa table" },
  { img:"inc-surf.jpg",      name:"Surf lessons",      alt:"Surf lesson on the sand at Playa Maderas" },
  { img:"inc-yoga.jpg",      name:"Yoga",              alt:"Yoga under the Surf Yoga Beer palapa" },
  { img:"inc-workout.jpg",   name:"Workouts and jungle gym", alt:"Group workout on the turf in the jungle gym" },
  { img:"inc-catamaran.jpg", name:"Catamaran day",     alt:"The catamaran with the crew swimming beside it" },
  { img:"inc-openbar.jpg",   name:"Villa open bar",    note:"This photo was just for fun", alt:"A guest pouring a beer straight into her mouth at sunset" },
  { img:"inc-bonfire.jpg",   name:"Beach bonfire",     alt:"Group around a bonfire on the beach" },
  { img:"inc-karaoke.jpg",   name:"Karaoke night",     note:"Not mandatory to sing, but encouraged", alt:"Guys singing on the karaoke stage" },
  { img:"inc-theme.jpg",     name:"Theme parties",     note:"Could include a DJ, live music, entertainment or salsa instructors", alt:"A theme party dance floor under neon lights" },
  { img:"inc-leaders.jpg",   name:"SYB leaders",       note:"Trained through the SYB academy. With the group 24 hours a day.", alt:"An SYB crew with surfboards and the SYB banner" }
];
/* step 5: pick one food package and one drinks package */
var FOOD = {
  none:    { label:"Lunches on your own", add:0, img:"pk-own.jpg", alt:"A beach restaurant on the sand near the villas", desc:"Grab lunch at the beach spots nearby. Breakfast and dinner are already in." },
  regular: { label:"Regular food package", add:75, img:"pk-regular.jpg", alt:"The group at a long lunch table", desc:"Lunch every day for 5 days, made by our chef." },
  deluxe:  { label:"Deluxe BBQ food package", add:165, img:"pk-deluxe.jpg", alt:"The crew around a big spread of food by the ocean", desc:"Everything in the regular package, plus a tomahawk steak night, a local catch fish BBQ, huevos de toro ceviche to try, and any other food requests." }
};
var DRINKS = {
  none:    { label:"Villa open bar only", add:0, img:"pk-bar.jpg", alt:"The villa bar with wooden stools and a jungle view", desc:"Already included, same as our public trips." },
  beer:    { label:"Unlimited beer package", add:85, img:"pk-beer.jpg", alt:"Three beers raised at sunset on the beach", desc:"Ice-cold Nicaraguan beer all week, at the villa and on the beach." },
  fullbar: { label:"Full bar package", add:145, img:"pk-fullbar.jpg", alt:"The crew at a beach bar with drinks", desc:"All the beer, plus Nicaraguan 7-year aged rum, dark and white, and tequila. All week." }
};
/* step 5 extras, in the order they show. img = photo tile; no img = the emoji tile.
   type: pp = per person | ppq = per person, per unit | unit = per unit | flat = once for the group */
var ADDONS = [
  { id:"dj", img:"add-dj.jpg", icon:"🎧", name:"DJ for the night", desc:"Your own DJ at the villa for the big night.", price:450, type:"unit", u:["night","nights"], qmax:3, qdef:1 },
  { id:"sjds", img:"add-sjds.jpg", icon:"🦞", name:"San Juan del Sur night", desc:"Lobster dinner on the bay, time to shop in town, then karaoke.", price:90, type:"pp" },
  { id:"espejo", img:"add-espejo.jpg", icon:"🌅", name:"Sunset dinner at Espejo", desc:"Happy hour, then dinner at Espejo over the surf. Transport included.", price:70, type:"pp" },
  { id:"sxs", img:"add-sxs.jpg", icon:"🛻", name:"Side-by-side rental", desc:"Off-road side-by-sides for the dirt roads and hidden beaches.", price:225, type:"unit", u:["vehicle day","vehicle days"], unitLabel:"per vehicle, per day", qmax:12, qdef:2 },
  { id:"jesus", img:"add-jesus.jpg", icon:"⛰️", name:"Jesus statue hike", desc:"Hike up to the giant statue over San Juan del Sur bay. Transport included.", price:40, type:"pp" },
  { id:"horses", img:"add-horses.jpg", icon:"🐎", name:"Sunset horseback ride", desc:"Horses on the beach at golden hour. No experience needed.", price:60, type:"pp" },
  { id:"surf1on1", img:"add-surf.jpg", icon:"🏄", name:"One-on-one surf lessons", desc:"An hour with a Beach Break Surf School coach all to yourself.", price:70, type:"ppq", u:["lesson","lessons"], qmax:5, qdef:1 },
  { id:"theme", img:"add-theme.jpg", icon:"🎉", name:"Custom theme party", desc:"Your theme, decor and props. Company colors welcome.", price:600, type:"unit", u:["party","parties"], qmax:2, qdef:1 },
  { id:"salsa", img:"add-salsa.jpg", icon:"💃", name:"Salsa lesson", desc:"A local instructor teaches the whole team at the villa.", price:250, type:"unit", u:["lesson","lessons"], qmax:3, qdef:1 },
  { id:"olympics", img:"add-olympics.jpg", icon:"🏆", name:"Beach olympics", desc:"Team games on the beach with brackets, a scoreboard and trophies.", price:300, type:"flat" },
  { id:"yogalive", img:"add-yoga.jpg", icon:"🎸", name:"Sunset yoga with live music", desc:"Yoga on the deck at sunset with live musicians playing.", price:400, type:"unit", u:["session","sessions"], qmax:4, qdef:1 },
  { id:"shirts", img:"add-shirts.jpg", icon:"👕", name:"Team shirts", desc:"Shirts with your logo, one for everyone.", price:40, type:"pp" },
  { id:"headshots", img:"add-headshots.jpg", icon:"📸", name:"Team headshots", desc:"Our photographer shoots profile-ready headshots for everyone.", price:45, type:"pp" },
  { id:"massage", icon:"💆", name:"1-hour massage", desc:"At the villa, on top of the 30 minute massage everyone gets.", price:70, type:"ppq", u:["massage","massages"], qmax:5, qdef:1 },
  { id:"juice", icon:"🧃", name:"Fresh juice package", desc:"Three fresh local juices every morning and afternoon.", price:55, type:"pp" },
  { id:"ceviche", icon:"🥑", name:"Sunset ceviche and guac", desc:"Fresh ceviche, guac and chips on the deck at sunset.", price:12, type:"ppq", u:["evening","evenings"], qmax:5, qdef:2 },
  { id:"rum", icon:"🥃", name:"Rum tasting", desc:"A guided tasting of Nicaraguan aged rums before dinner.", price:35, type:"pp" },
  { id:"pizza", icon:"🍕", name:"Pizza night with live music", desc:"Pizza at a local pizzeria with a live band.", price:40, type:"pp" },
  { id:"fishing", icon:"🎣", name:"Sport fishing trip", desc:"Half a day offshore with a local captain. The chef cooks your catch. Up to 6 per boat.", price:650, type:"unit", u:["boat","boats"], qmax:4, qdef:1 },
  { id:"zipline", icon:"🌳", name:"Zipline canopy tour", desc:"A morning in the treetops near San Juan del Sur. Transport included.", price:65, type:"pp" },
  { id:"icebath", icon:"🧊", name:"Ice bath session", desc:"Ice baths at the villa with a guided breathing warm-up.", price:30, type:"ppq", u:["session","sessions"], qmax:5, qdef:1 },
  { id:"work", icon:"🧠", name:"Work sessions setup", desc:"For breakouts and whiteboarding: projector, whiteboards, sticky notes, coffee and snacks.", price:250, type:"unit", u:["day","days"], qmax:5, qdef:2 },
  { id:"speaker", icon:"🎤", name:"Speaker night", desc:"Mic, screen and seats for a talk or fireside chat, with drinks and bites.", price:400, type:"unit", u:["night","nights"], qmax:3, qdef:1 },
  { id:"film", icon:"🎬", name:"Team recap film", desc:"A 60 second film of your week to share with the whole company.", price:750, type:"flat" }
];
var BYID = {}; ADDONS.forEach(function(a){ BYID[a.id] = a; });

// Sarah's starting package. people: null = the extra covers the whole group.
var PROPOSAL = { v:2, people:14, start:"2027-04-12", flexible:false, extra:0, room:"twin", food:"deluxe", drinks:"fullbar",
  addons:{ juice:{on:true,people:null}, massage:{on:true,qty:1,people:null}, work:{on:true,qty:2}, film:{on:true} } };

/* ===== helpers ===== */
var ROOT = document.getElementById("sybp");
function $(id){ return document.getElementById(id); }
function money(n){ return "$" + Math.round(n).toLocaleString("en-US"); }
function clone(o){ return JSON.parse(JSON.stringify(o)); }
function plural(n, u){ return n === 1 ? u[0] : u[1]; }
function cap(s){ return s.charAt(0).toUpperCase() + s.slice(1); }
function esc(s){ return String(s).replace(/[&<>"']/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]; }); }
var MINUS = '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="7.2" width="12" height="1.6" fill="currentColor"/></svg>';
var PLUS = '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="7.2" width="12" height="1.6" fill="currentColor"/><rect x="7.2" y="2" width="1.6" height="12" fill="currentColor"/></svg>';
var CHECK = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';
function sget(k){ try { return window.localStorage.getItem(k); } catch(e){ return null; } }
function sset(k, v){ try { window.localStorage.setItem(k, v); return true; } catch(e){ return false; } }
function parseISO(s){ var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || ""); if (!m) return null; var d = new Date(Date.UTC(+m[1], +m[2]-1, +m[3])); return isNaN(d) ? null : d; }
function addDays(d, n){ return new Date(d.getTime() + n*86400000); }
function fmtDay(d, withYear){ var w = d.toLocaleDateString("en-US", { weekday:"short", timeZone:"UTC" }), md = d.toLocaleDateString("en-US", { month:"short", day:"numeric", timeZone:"UTC" }); return w + " " + md + (withYear ? ", " + d.getUTCFullYear() : ""); }
function fmtDate(d){ return d.toLocaleDateString("en-US", { month:"short", day:"numeric", year:"numeric", timeZone:"UTC" }); }
function todayUTC(){ var n = new Date(); return new Date(Date.UTC(n.getFullYear(), n.getMonth(), n.getDate())); }

/* ===== company name and state ===== */
var COMPANY = DEFAULT_COMPANY;
try { var q = new URLSearchParams(window.location.search).get("for"); if (q && q.trim()) COMPANY = q.trim().slice(0, 60); } catch(e){}
var KEY = "syb-team-trip:v2:" + COMPANY.toLowerCase().replace(/[^a-z0-9]+/g, "-");
var S = load();

function sanitize(s){
  var o = clone(PROPOSAL);
  if (!s || typeof s !== "object" || s.v !== 2) return o;
  if (ROOMS[s.room]) o.room = s.room;
  o.people = Math.max(MIN_PEOPLE, Math.min(ROOMS[o.room].max, parseInt(s.people, 10) || o.people));
  o.start = parseISO(s.start) ? s.start : "";
  o.flexible = !!s.flexible;
  o.extra = Math.max(0, Math.min(MAX_EXTRA_NIGHTS, parseInt(s.extra, 10) || 0));
  o.food = FOOD[s.food] ? s.food : "none";
  o.drinks = DRINKS[s.drinks] ? s.drinks : "none";
  o.addons = {};
  var a = s.addons || {};
  Object.keys(a).forEach(function(id){
    var d = BYID[id], v = a[id]; if (!d || !v || !v.on) return;
    var e = { on:true };
    if (d.type === "ppq" || d.type === "unit") e.qty = Math.max(1, Math.min(d.qmax, parseInt(v.qty, 10) || d.qdef || 1));
    if (d.type === "pp" || d.type === "ppq") e.people = (v.people == null) ? null : Math.max(1, parseInt(v.people, 10) || 1);
    o.addons[id] = e;
  });
  return o;
}
function load(){ var raw = sget(KEY); if (raw) { try { return sanitize(JSON.parse(raw)); } catch(e){} } return clone(PROPOSAL); }
function save(){ $("save-msg").textContent = sset(KEY, JSON.stringify(S)) ? "Your changes save on this device." : "Changes won't be saved on this device, so send your package to Sarah before you close the page."; }

/* ===== pricing ===== */
function nights(){ return BASE_NIGHTS + S.extra; }
function pplFor(e){ return e.people == null ? S.people : Math.min(e.people, S.people); }
function people(n){ return n + " " + (n === 1 ? "person" : "people"); }
function addonLine(d, e){
  var p = pplFor(e), q = e.qty || 1;
  if (d.type === "pp")   return { a: d.price * p, m: people(p) + " x " + money(d.price) };
  if (d.type === "ppq")  return { a: d.price * p * q, m: people(p) + ", " + q + " " + plural(q, d.u) + " each, " + money(d.price) + " per " + d.u[0] };
  if (d.type === "unit") return { a: d.price * q, m: q + " " + plural(q, d.u) + " x " + money(d.price) };
  return { a: d.price, m: "Once, for the whole group" };
}
function lines(){
  var N = S.people, L = [];
  L.push({ t:"Nicaragua team trip, " + BASE_NIGHTS + " nights", m: people(N) + " x " + money(BASE), a: N * BASE });
  if (S.extra) L.push({ t:"Extra " + plural(S.extra, ["night","nights"]), m: people(N) + ", " + S.extra + " " + plural(S.extra, ["night","nights"]) + " each, " + money(EXTRA_NIGHT) + " per night", a: N * S.extra * EXTRA_NIGHT });
  var r = ROOMS[S.room]; if (r.add) L.push({ t: r.label, m: people(N) + " x " + money(r.add), a: N * r.add });
  var f = FOOD[S.food]; if (f.add) L.push({ t: f.label, m: people(N) + " x " + money(f.add), a: N * f.add });
  var dr = DRINKS[S.drinks]; if (dr.add) L.push({ t: dr.label, m: people(N) + " x " + money(dr.add), a: N * dr.add });
  ADDONS.forEach(function(d){ var e = S.addons[d.id]; if (e && e.on) { var x = addonLine(d, e); L.push({ t: d.name, m: x.m, a: x.a }); } });
  return L;
}
function totals(){ var L = lines(), t = 0; L.forEach(function(l){ t += l.a; }); var dep = Math.round(t * DEPOSIT); return { L:L, total:t, pp:t / S.people, dep:dep, bal:t - dep }; }
function balanceLabel(){
  var d = parseISO(S.start); if (!d) return "Balance, due 6 weeks before the trip";
  var due = addDays(d, -42);
  return due <= todayUTC() ? "Balance, due at booking (trip is under 6 weeks away)" : "Balance, due " + fmtDate(due);
}

/* ===== render ===== */
function tile(t, included){
  return '<figure class="tile' + (t.big ? " big" : "") + '"><img src="' + IMG + t.img + '" alt="' + esc(t.alt) + '" width="700" height="700" loading="lazy"' + (t.pos ? ' style="object-position:' + t.pos + '"' : "") + '>' +
    (included ? '<span class="t-badge">' + CHECK + 'Included</span>' : "") +
    '<figcaption><span class="t-name">' + esc(t.name) + '</span>' + (t.note ? '<span class="t-note">' + esc(t.note) + '</span>' : "") + '</figcaption></figure>';
}
function renderTiles(){
  $("stay-grid").innerHTML = STAY.map(function(t){ return tile(t, false); }).join("");
  $("inc-grid").innerHTML = INCLUDED.map(function(t){ return tile(t, true); }).join("");
}
function renderGroup(){
  var max = ROOMS[S.room].max;
  $("people-out").textContent = S.people;
  ROOT.querySelector('[data-act="people"][data-d="-1"]').disabled = S.people <= MIN_PEOPLE;
  ROOT.querySelector('[data-act="people"][data-d="1"]').disabled = S.people >= max;
  var h = $("people-hint"); h.classList.remove("warn");
  if (S.people >= max) { h.textContent = ROOMS[S.room].label + " fit up to " + max + " people." + (S.room !== "shared" ? " Shared rooms fit up to 25." : ""); h.classList.add("warn"); }
  else if (S.people <= MIN_PEOPLE) { h.textContent = "Team trips start at " + MIN_PEOPLE + " people."; }
  else { h.textContent = MIN_PEOPLE + " to " + max + " people with " + ROOMS[S.room].label.toLowerCase() + "."; }
  $("nights-out").textContent = nights();
  ROOT.querySelector('[data-act="nights"][data-d="-1"]').disabled = S.extra <= 0;
  ROOT.querySelector('[data-act="nights"][data-d="1"]').disabled = S.extra >= MAX_EXTRA_NIGHTS;
  $("nights-hint").textContent = S.extra ? "Each extra night is " + money(EXTRA_NIGHT) + " per person, with breakfast and dinner." : "5 nights is the standard trip. Extra nights are " + money(EXTRA_NIGHT) + " per person.";
  var di = $("start-date"); if (di.value !== S.start) di.value = S.start || "";
  $("flexible").checked = S.flexible;
  var d = parseISO(S.start);
  $("range-out").textContent = d ? fmtDay(d) + " to " + fmtDay(addDays(d, nights()), true) + " (" + (nights() + 1) + " days)" : "Pick a first day, or tick flexible and Sarah will suggest weeks.";
  ROOT.querySelectorAll('input[name="room"]').forEach(function(r){ r.checked = (r.value === S.room); });
}
function pkgCards(name, opts, cur){
  return Object.keys(opts).map(function(k){
    var o = opts[k];
    return '<label class="pkg"><input type="radio" name="' + name + '" value="' + k + '"' + (k === cur ? " checked" : "") + '>' +
      '<span class="p-media"><img src="' + IMG + o.img + '" alt="' + esc(o.alt) + '" width="900" height="675" loading="lazy"><span class="p-check">' + CHECK + '</span></span>' +
      '<span class="p-body"><span class="p-name">' + esc(o.label) + '</span><span class="p-price">' + (o.add ? "+" + money(o.add) + " per person" : "Included") + '</span><span class="p-desc">' + esc(o.desc) + '</span></span></label>';
  }).join("");
}
function renderPkgs(){ $("pk-food").innerHTML = pkgCards("food", FOOD, S.food); $("pk-drinks").innerHTML = pkgCards("drinks", DRINKS, S.drinks); }
function stepper(act, id, val, min, max, label){
  return '<div class="stepper" role="group" aria-label="' + esc(label) + '">' +
    '<button type="button" data-act="' + act + '" data-id="' + id + '" data-d="-1" aria-label="Fewer ' + esc(label) + '"' + (val <= min ? " disabled" : "") + '>' + MINUS + '</button>' +
    '<output>' + val + '</output>' +
    '<button type="button" data-act="' + act + '" data-id="' + id + '" data-d="1" aria-label="More ' + esc(label) + '"' + (val >= max ? " disabled" : "") + '>' + PLUS + '</button></div>';
}
function priceLabel(d){
  if (d.type === "pp") return "per person";
  if (d.type === "ppq") return "per " + d.u[0] + ", per person";
  if (d.type === "unit") return d.unitLabel || ("per " + d.u[0]);
  return "for the group";
}
function addonCard(d){
  var e = S.addons[d.id], on = !!(e && e.on), ctrl = "";
  if (on) {
    var parts = [];
    if (d.type === "ppq") parts.push('<div class="mini"><span class="label">' + cap(d.u[1]) + ' each</span>' + stepper("qty", d.id, e.qty, 1, d.qmax, d.u[1]) + '</div>');
    if (d.type === "unit") parts.push('<div class="mini"><span class="label">' + cap(d.u[1]) + '</span>' + stepper("qty", d.id, e.qty, 1, d.qmax, d.u[1]) + '</div>');
    if (d.type === "pp" || d.type === "ppq") parts.push('<div class="mini"><span class="label">People</span>' + stepper("ppl", d.id, pplFor(e), 1, S.people, "people") + '</div>');
    parts.push('<div class="a-line"><small>On your quote</small>' + money(addonLine(d, e).a) + '</div>');
    ctrl = '<div class="a-ctrl">' + parts.join("") + '</div>';
  }
  var media = d.img ? '<img src="' + IMG + d.img + '" alt="" width="900" height="675" loading="lazy">' : '<span class="a-emoji" aria-hidden="true">' + d.icon + '</span>';
  return '<article class="addon' + (on ? " on" : "") + '" data-id="' + d.id + '">' +
    '<button type="button" class="a-hit" data-act="toggle" data-id="' + d.id + '" aria-pressed="' + on + '">' +
      '<span class="a-media">' + media + '<span class="a-name">' + esc(d.name) + '</span><span class="a-check">' + CHECK + '</span></span>' +
      '<span class="a-body"><span class="a-price">' + money(d.price) + ' <small>' + priceLabel(d) + '</small></span><span class="a-desc">' + esc(d.desc) + '</span></span>' +
      '<span class="sr">' + (on ? "Added. Tap to remove." : "Tap to add.") + '</span>' +
    '</button>' + ctrl + '</article>';
}
function renderExtras(){ $("extras").innerHTML = ADDONS.map(addonCard).join(""); renderCount(); }
function renderCount(){
  var n = 0; ADDONS.forEach(function(a){ if (S.addons[a.id] && S.addons[a.id].on) n++; });
  var c = $("x-count"); c.hidden = !n; c.textContent = n + " added";
}
function renderQuote(){
  var T = totals(), d = parseISO(S.start);
  var trip = [
    ["Where", "Playa Maderas, Nicaragua"],
    ["Dates", d ? fmtDay(d) + " to " + fmtDay(addDays(d, nights()), true) + (S.flexible ? ", flexible" : "") : (S.flexible ? "Flexible" : "To be set")],
    ["Group", people(S.people) + ", " + ROOMS[S.room].label.toLowerCase()],
    ["Length", (nights() + 1) + " days, " + nights() + " nights"]
  ];
  $("q-trip").innerHTML = trip.map(function(r){ return '<div><span>' + r[0] + '</span><span>' + esc(r[1]) + '</span></div>'; }).join("");
  $("q-lines").innerHTML = T.L.map(function(l){ return '<li><span class="ql-t">' + esc(l.t) + '</span><span class="ql-a">' + money(l.a) + '</span><span class="ql-m">' + esc(l.m) + '</span></li>'; }).join("");
  $("q-total").textContent = money(T.total);
  $("q-pp").textContent = money(T.pp);
  $("q-dep").textContent = money(T.dep);
  $("q-bal-l").textContent = balanceLabel();
  $("q-bal").textContent = money(T.bal);
  $("tb-total").textContent = money(T.total);
  $("tb-sub").textContent = people(S.people) + ", " + money(T.pp) + " each";
}
function refresh(keepCards){ renderGroup(); if (!keepCards) { renderPkgs(); renderExtras(); } renderQuote(); save(); }

/* ===== interactions ===== */
function setPeople(n){ S.people = Math.max(MIN_PEOPLE, Math.min(ROOMS[S.room].max, n)); }
function rerenderCard(id, focusAct, focusD){
  var el = ROOT.querySelector('.addon[data-id="' + id + '"]'); if (!el) { renderExtras(); return; }
  var tmp = document.createElement("div"); tmp.innerHTML = addonCard(BYID[id]); var nu = tmp.firstChild;
  el.parentNode.replaceChild(nu, el);
  if (focusAct) {
    var f = nu.querySelector('[data-act="' + focusAct + '"]' + (focusD ? '[data-d="' + focusD + '"]' : ""));
    if (!f || f.disabled) f = nu.querySelector('[data-act="toggle"]');
    if (f) f.focus({ preventScroll:true });
  }
  renderCount();
}
function scrollToId(id){ var t = $(id); if (!t) return; t.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block:"start" }); }

ROOT.addEventListener("click", function(ev){
  var b = ev.target.closest("[data-act],[data-scroll]"); if (!b || !ROOT.contains(b)) return;
  if (b.dataset.scroll) { ev.preventDefault(); scrollToId(b.dataset.scroll); return; }
  var act = b.dataset.act, id = b.dataset.id, d = parseInt(b.dataset.d || "0", 10);
  if (act === "dest") return;
  if (act === "people") { setPeople(S.people + d); $("room-hint").textContent = ""; refresh(); return; }
  if (act === "nights") { S.extra = Math.max(0, Math.min(MAX_EXTRA_NIGHTS, S.extra + d)); refresh(true); return; }
  if (act === "toggle") {
    var def = BYID[id];
    if (S.addons[id] && S.addons[id].on) delete S.addons[id];
    else { var e = { on:true }; if (def.type === "ppq" || def.type === "unit") e.qty = def.qdef || 1; if (def.type === "pp" || def.type === "ppq") e.people = null; S.addons[id] = e; }
    rerenderCard(id, "toggle"); renderQuote(); save(); return;
  }
  if (act === "qty" && S.addons[id]) { var e1 = S.addons[id]; e1.qty = Math.max(1, Math.min(BYID[id].qmax, (e1.qty || 1) + d)); rerenderCard(id, "qty", b.dataset.d); renderQuote(); save(); return; }
  if (act === "ppl" && S.addons[id]) { var e2 = S.addons[id]; var n = Math.max(1, Math.min(S.people, pplFor(e2) + d)); e2.people = (n >= S.people) ? null : n; rerenderCard(id, "ppl", b.dataset.d); renderQuote(); save(); return; }
  if (act === "reset-proposal") { S = clone(PROPOSAL); $("room-hint").textContent = ""; refresh(); return; }
  if (act === "reset-base") { S = { v:2, people:S.people, start:S.start, flexible:S.flexible, extra:0, room:"shared", food:"none", drinks:"none", addons:{} }; setPeople(S.people); $("room-hint").textContent = ""; refresh(); return; }
  if (act === "copy-package") { copyPackage(); return; }
  if (act === "copy-contact") { copyContact(b.dataset.which); return; }
});
ROOT.addEventListener("change", function(ev){
  var t = ev.target;
  if (t.name === "room") {
    var before = S.people; S.room = ROOMS[t.value] ? t.value : S.room; setPeople(S.people);
    var h = $("room-hint"); h.classList.toggle("warn", before !== S.people);
    h.textContent = before !== S.people ? ROOMS[S.room].label + " fit up to " + ROOMS[S.room].max + " people, so your group is now " + S.people + "." : "";
    refresh(); return;
  }
  if (t.name === "food") { S.food = FOOD[t.value] ? t.value : "none"; renderQuote(); save(); return; }
  if (t.name === "drinks") { S.drinks = DRINKS[t.value] ? t.value : "none"; renderQuote(); save(); return; }
  if (t.id === "start-date") { S.start = parseISO(t.value) ? t.value : ""; refresh(true); return; }
  if (t.id === "flexible") { S.flexible = t.checked; renderQuote(); save(); return; }
});

/* ===== send to Sarah: build the package, copy it, offer the email app ===== */
function packageText(){
  var T = totals(), d = parseISO(S.start), out = [];
  var name = $("f-name").value.trim(), company = $("f-company").value.trim() || COMPANY, email = $("f-email").value.trim(), notes = $("f-notes").value.trim();
  out.push("Hi Sarah, here is our team trip package.");
  out.push("");
  out.push("Company: " + company);
  if (name || email) out.push("From: " + [name, email].filter(Boolean).join(", "));
  out.push("Destination: Playa Maderas, Nicaragua");
  out.push("Dates: " + (d ? fmtDay(d) + " to " + fmtDay(addDays(d, nights()), true) : "not set yet") + (S.flexible ? " (flexible)" : ""));
  out.push("Group: " + people(S.people) + ", " + ROOMS[S.room].label.toLowerCase() + ", " + nights() + " nights");
  out.push("");
  T.L.forEach(function(l){ out.push("- " + l.t + ": " + money(l.a) + " (" + l.m + ")"); });
  out.push("");
  out.push("Total: " + money(T.total) + " (about " + money(T.pp) + " per person)");
  out.push("Deposit (20%): " + money(T.dep));
  out.push(balanceLabel() + ": " + money(T.bal));
  if (notes) { out.push(""); out.push("Notes: " + notes); }
  if (MODE === "live") { out.push(""); out.push("Built at " + window.location.href.split("#")[0]); }
  return out.join("\n");
}
function setCopyState(ok){
  var s = $("copy-state");
  s.classList.toggle("warn", !ok);
  s.textContent = ok ? "Copied. Paste it into an email or a text to Sarah." : "Your browser didn't let us copy. Press and hold the text below, then copy it.";
  if (!ok) { var box = $("send-text"); try { box.focus({ preventScroll:true }); box.select(); } catch(e){} }
}
function copyText(text, done){
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(text).then(function(){ done(true); }, function(){ done(fallbackCopy(text)); }); return; }
  } catch(e){}
  done(fallbackCopy(text));
}
function fallbackCopy(text){
  var ta = document.createElement("textarea"), ok = false;
  ta.value = text; ta.setAttribute("readonly", ""); ta.style.cssText = "position:fixed;top:0;left:-9999px;opacity:0";
  document.body.appendChild(ta);
  try { ta.select(); ta.setSelectionRange(0, text.length); ok = !!(document.execCommand && document.execCommand("copy")); } catch(e){ ok = false; }
  document.body.removeChild(ta);
  return ok;
}
function copyPackage(){ var t = $("send-text").value || packageText(); copyText(t, setCopyState); }
function copyContact(which){
  var v = which === "email" ? CONTACT.email : CONTACT.phone, msg = $("copy-msg");
  copyText(v, function(ok){
    if (ok) { msg.textContent = "Copied " + v; return; }
    var el = $(which === "email" ? "c-email" : "c-phone"), r = document.createRange(); r.selectNodeContents(el); var sel = getSelection(); sel.removeAllRanges(); sel.addRange(r);
    msg.textContent = "Selected. Copy it with your keyboard or a long press.";
  });
}
$("send-form").addEventListener("submit", function(ev){
  ev.preventDefault();
  var email = $("f-email").value.trim(), err = $("f-err");
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { err.textContent = "That email doesn't look right. Fix it or leave it blank."; err.hidden = false; $("f-email").focus(); return; }
  err.hidden = true;
  var text = packageText();
  $("send-text").value = text;
  $("send-email").textContent = CONTACT.email;
  $("send-mailto").href = "mailto:" + CONTACT.email + "?subject=" + encodeURIComponent("Team trip: " + ($("f-company").value.trim() || COMPANY)) + "&body=" + encodeURIComponent(text);
  var out = $("send-out"); out.hidden = false;
  $("copy-state").textContent = "";
  copyText(text, setCopyState);
  setTimeout(function(){ out.scrollIntoView({ behavior:"smooth", block:"center" }); }, 30);
});

/* ===== live site: line up with the site's own header ===== */
function fitSiteHeader(){
  if (MODE !== "live") return;
  // Easol's menu bar is nav.js-navigation. Fixed = it floats over the page, so push the hero down and offset sticky bits.
  var nav = document.querySelector(".js-navigation"), h = 0, top = 0, stick = 0;
  if (nav && !ROOT.contains(nav)) {
    var pos = getComputedStyle(nav).position, inner = nav.querySelector(".navigation__inner") || nav;
    h = Math.round(inner.getBoundingClientRect().height);
    if (pos === "fixed") { top = h; stick = h; }
    else if (pos === "absolute") { top = h; }
    else if (pos === "sticky") { stick = h; }
  }
  ROOT.style.setProperty("--navh", stick + "px");
  ROOT.style.setProperty("--herotop", top + "px");
}

/* ===== phone total bar: show it while building, hide it once the quote is on screen ===== */
(function(){
  var tb = $("totalbar"), inBuild = false, quoteSeen = false;
  function upd(){ var off = !inBuild || quoteSeen; tb.classList.toggle("off", off); document.documentElement.classList.toggle("sybp-bar", !off); }
  if (!("IntersectionObserver" in window)) { tb.classList.remove("off"); return; }
  new IntersectionObserver(function(es){ inBuild = es[es.length - 1].isIntersecting; upd(); }, { rootMargin:"0px 0px -35% 0px" }).observe(ROOT.querySelector(".builder"));
  new IntersectionObserver(function(es){ quoteSeen = es[es.length - 1].isIntersecting; upd(); }, { threshold:0.2 }).observe($("quote-col"));
})();

/* ===== boot ===== */
if (MODE === "live") { ROOT.classList.remove("is-artifact"); ROOT.classList.add("is-live"); fitSiteHeader(); window.addEventListener("resize", fitSiteHeader); window.addEventListener("load", fitSiteHeader); setTimeout(fitSiteHeader, 1200); }
$("b-for").textContent = "Prepared for " + COMPANY;
$("q-sub").innerHTML = "SYB Travel<br>For " + esc(COMPANY);
$("f-company").value = COMPANY === DEFAULT_COMPANY ? "" : COMPANY;
$("f-company").placeholder = COMPANY;
$("c-name").textContent = CONTACT.name; $("c-email").textContent = CONTACT.email; $("c-phone").textContent = CONTACT.phone;
$("start-date").min = addDays(todayUTC(), 21).toISOString().slice(0, 10);
renderTiles();
renderGroup(); renderPkgs(); renderExtras(); renderQuote();
})();
