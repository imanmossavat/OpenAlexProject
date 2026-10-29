<div id="tip" hidden></div>
<script>
const RD = __RD__;
(function () {
const NS = "http://www.w3.org/2000/svg";
const tip = document.getElementById("tip");
const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function showTip(ev, html) { tip.innerHTML = html; tip.hidden = false; const w = tip.offsetWidth, h = tip.offsetHeight; let x = ev.clientX + 14, y = ev.clientY + 14; if (x + w > innerWidth - 8) x = ev.clientX - w - 14; if (y + h > innerHeight - 8) y = ev.clientY - h - 14; tip.style.left = Math.max(8, x) + "px"; tip.style.top = Math.max(8, y) + "px"; }
const hideTip = () => { tip.hidden = true; };
const niceMax = v => { for (const x of [4, 8, 20, 40, 60, 80, 100, 120, 160, 200, 300, 400, 500, 600, 800]) if (v <= x) return x; return Math.ceil(v / 100) * 100; };
const sw = (c, l, ring) => `<span><i class="sw" style="${ring ? "border:2px solid var(" + c + ");background:transparent;border-radius:50%" : "background:var(" + c + ")"}"></i>${l}</span>`;

function stacked(id, rows, keys, dots, label) {
  const W = 460, H = 250, m = { l: 36, r: 8, t: 10, b: 26 };
  const host = document.getElementById(id);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": label }, host);
  const tot = rows.map(r => keys.reduce((s, k) => s + r[k[0]], 0));
  const max = niceMax(Math.max(...tot));
  const iw = W - m.l - m.r, ih = H - m.t - m.b, bw = iw / rows.length, y = v => m.t + ih - v / max * ih;
  for (let i = 0; i <= 4; i++) { const v = max / 4 * i; el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), stroke: "var(--rule)" }, svg); el("text", { x: m.l - 6, y: y(v) + 4, "text-anchor": "end" }, svg).textContent = v; }
  rows.forEach((r, i) => {
    const x = m.l + i * bw + bw * 0.2, w = bw * 0.6; let acc = 0;
    keys.forEach((k, j) => { const v = r[k[0]]; if (!v) return; el("rect", { x, y: y(acc + v), width: w, height: Math.max(0, y(acc) - y(acc + v) - (j ? 1.5 : 0)), fill: `var(${k[1]})`, rx: 2 }, svg); acc += v; });
    (dots || []).forEach((d, di) => { const cx = x + w / 2 + (di - (dots.length - 1) / 2) * 12, cy = y(r[d.k]);
      if (d.diamond) el("path", { d: `M${cx},${cy - 6} L${cx + 6},${cy} L${cx},${cy + 6} L${cx - 6},${cy} Z`, fill: `var(${d.c})`, stroke: "var(--panel)", "stroke-width": 2 }, svg);
      else el("circle", { cx, cy, r: 5, fill: `var(${d.c})`, stroke: "var(--panel)", "stroke-width": 2 }, svg); });
    el("text", { x: x + w / 2, y: H - 8, "text-anchor": "middle" }, svg).textContent = r.year;
    const hit = el("rect", { x: m.l + i * bw, y: m.t, width: bw, height: ih, fill: "transparent" }, svg);
    hit.addEventListener("mousemove", ev => showTip(ev, `<b>${r.year}</b><br>` + keys.map(k => `${k[2]}: <b>${r[k[0]]}</b>`).join("<br>") + (dots || []).map(d => `<br>${d.l}: <b>${r[d.k]}</b>`).join("") + `<br>Total: <b>${tot[i]}</b>`));
    hit.addEventListener("mouseleave", hideTip);
  });
}
const FK = [["eng", "--t0", "Engineering"], ["cs", "--t1", "Computer science"], ["life", "--t2", "Life sciences, medicine"], ["phys", "--t3", "Physical sciences, maths"], ["other", "--t10", "Other"]];
document.getElementById("lg-field").innerHTML = FK.map(k => sw(k[1], k[2])).join("");
stacked("ch-field", RD.citers_by_year, FK, null, "Seed citers per year by field");

const CK = [["refs", "--t0", "References indexed"], ["norefs", "--t1", "No references in OpenAlex"]];
const CD = [{ k: "A", c: "--ink", l: "Reached by crawl A" }, { k: "B", c: "--t2", l: "Reached by crawl B", diamond: 1 }];
document.getElementById("lg-cov").innerHTML = CK.map(k => sw(k[1], k[2])).join("") + `<span><i class="sw" style="background:var(--ink);border-radius:50%"></i>Reached by crawl A</span><span><i class="sw" style="background:var(--t2);transform:rotate(45deg) scale(.85)"></i>Reached by crawl B</span>`;
stacked("ch-cov", RD.coverage, CK, CD, "Field-set works per year by reference coverage");
document.getElementById("tbl-cov").innerHTML = `<table><thead><tr><th>Year</th><th class="num">References indexed</th><th class="num">No references</th><th class="num">Dark (no links)</th><th class="num">Crawl A</th><th class="num">Crawl B</th></tr></thead><tbody>${RD.coverage.map(r => `<tr><td>${r.year}</td><td class="num">${r.refs}</td><td class="num">${r.norefs}</td><td class="num">${r.dark}</td><td class="num">${r.A}</td><td class="num">${r.B}</td></tr>`).join("")}</tbody></table>`;

(function inst() {
  const rows = RD.inst_field.slice(0, 12), W = 460, rh = 24, m = { l: 230, r: 34, t: 4, b: 4 }, H = m.t + m.b + rows.length * rh;
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Field-set works per institution" }, document.getElementById("ch-inst"));
  const max = rows[0].n, iw = W - m.l - m.r;
  const short = n => n.replace("University of Chinese Academy of Sciences", "Univ. of Chinese Acad. of Sciences").replace("Huazhong University of Science and Technology", "Huazhong Univ. of Sci. & Tech.").replace("South China University of Technology", "South China Univ. of Tech.");
  rows.forEach((r, i) => { const y = m.t + i * rh;
    el("text", { x: m.l - 8, y: y + rh / 2 + 4, "text-anchor": "end" }, svg).textContent = short(r.name);
    el("rect", { x: m.l, y: y + 5, width: r.n / max * iw, height: rh - 10, rx: 3, fill: "var(--t0)" }, svg);
    el("text", { x: m.l + r.n / max * iw + 6, y: y + rh / 2 + 4 }, svg).textContent = r.n; });
})();

const TOP = RD.topics, TC = TOP.clusters;
const tcol = c => `var(--t${c})`;
let active = null;
const lg = document.getElementById("lg-map");
lg.innerHTML = TC.map(c => `<button type="button" class="pick" data-c="${c.c}"><i class="sw" style="background:${tcol(c.c)}"></i>${esc(c.label)}</button>`).join("");
document.getElementById("lg-map2").innerHTML = `<span><i class="sw" style="background:var(--ink-3);border-radius:50%"></i>in crawl data</span><span><i class="sw" style="border:2px solid var(--ink-3);border-radius:50%;background:transparent"></i>in neither crawl</span><span><i class="sw" style="background:var(--ink);transform:rotate(45deg) scale(.8)"></i>evidence paper</span>`;
(function map() {
  const W = 760, H = 520, pad = 18, P = TOP.points;
  const xs = P.map(p => p.x), ys = P.map(p => p.y), x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const X = v => pad + (v - x0) / (x1 - x0) * (W - 2 * pad), Y = v => pad + (v - y0) / (y1 - y0) * (H - 2 * pad);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Topic map of 1,622 works" }, document.getElementById("ch-map"));
  const g = el("g", {}, svg), marks = [];
  P.forEach(p => { const cx = X(p.x), cy = Y(p.y); let m;
    if (p.ev) m = el("path", { d: `M${cx},${cy - 5} L${cx + 5},${cy} L${cx},${cy + 5} L${cx - 5},${cy} Z`, fill: tcol(p.c), stroke: "var(--ink)", "stroke-width": 1.2 }, g);
    else if (p.cr) m = el("circle", { cx, cy, r: 3, fill: tcol(p.c), "fill-opacity": .8 }, g);
    else m = el("circle", { cx, cy, r: 3.2, fill: "var(--panel)", stroke: tcol(p.c), "stroke-width": 1.4 }, g);
    m.addEventListener("mousemove", ev => showTip(ev, `<b>${esc(p.t)}</b><br>${esc(p.a)}${p.yr ? " · " + p.yr : ""}<br>${esc(TC.find(c => c.c === p.c).label)}${p.ev ? "<br>Evidence paper: " + esc(p.ev) : ""}<br>${p.cr ? "In crawl data" : "In neither crawl"}${p.fs ? " · field set" : ""}`));
    m.addEventListener("mouseleave", hideTip); marks.push([m, p.c]); });
  const cen = {}; P.forEach(p => { (cen[p.c] ||= [0, 0, 0]); cen[p.c][0] += X(p.x); cen[p.c][1] += Y(p.y); cen[p.c][2]++; });
  for (const c in cen) { const [sx, sy, n] = cen[c]; const t = el("text", { x: sx / n, y: sy / n, "text-anchor": "middle", class: "cl" }, svg); t.textContent = TC.findIndex(k => k.c == c) + 1; }
  const apply = () => { marks.forEach(([m, c]) => m.setAttribute("opacity", active === null || active === c ? 1 : .12));
    lg.querySelectorAll(".pick").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.c === active))); };
  lg.addEventListener("click", e => { const b = e.target.closest(".pick"); if (!b) return; const c = +b.dataset.c; active = active === c ? null : c; apply(); });
  apply();
})();
document.querySelector("#tbl-topics tbody").innerHTML = TC.map((c, i) => `<tr><td><i class="sw" style="background:${tcol(c.c)}"></i> <b>${i + 1}.</b> ${esc(c.label)}</td><td class="num">${c.n}</td><td class="num">${c.field}</td><td class="mono" style="font-size:.78rem">${esc(c.kw.join(", "))}</td><td>${esc(c.ev.join(", ")) || "—"}</td><td>${esc(c.inst.join("; "))}</td></tr>`).join("");
(function heat() {
  const max = Math.max(...TC.flatMap(c => c.years));
  document.getElementById("tbl-heat").innerHTML = `<table class="heat"><thead><tr><th>Topic</th>${TOP.years.map(y => `<th class="num">${y}</th>`).join("")}</tr></thead><tbody>${TC.map((c, i) => `<tr><td>${i + 1}. ${esc(c.label)}</td>${c.years.map(v => { const p = Math.round(v / max * 85); return `<td class="num" style="background:color-mix(in srgb, var(--accent) ${p}%, var(--panel));color:${p > 45 ? "var(--panel)" : "var(--ink)"}">${v}</td>`; }).join("")}</tr>`).join("")}</tbody></table>`;
})();

(function net() {
  const N = RD.network.nodes, E = RD.network.edges, W = 760, H = 560, pad = 16;
  const X = v => pad + v * (W - 2 * pad), Y = v => pad + v * (H - 2 * pad);
  const idx = Object.fromEntries(N.map(n => [n.id, n]));
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Citation network of 246 works" }, document.getElementById("ch-net"));
  const ge = el("g", {}, svg);
  E.forEach(([a, b]) => { const u = idx[a], v = idx[b]; el("line", { x1: X(u.x), y1: Y(u.y), x2: X(v.x), y2: Y(v.y), stroke: "var(--ink-3)", "stroke-opacity": .45, "stroke-width": .8 }, ge); });
  N.slice().sort((a, b) => a.deg - b.deg).forEach(n => {
    const r = 2.5 + Math.min(8, Math.sqrt(n.c || 0) / 2.2);
    const c = el("circle", { cx: X(n.x), cy: Y(n.y), r, fill: n.tc >= 0 ? tcol(n.tc) : "var(--ink-3)", "fill-opacity": n.deg ? .9 : .3,
      stroke: n.ev ? "var(--ink)" : "var(--panel)", "stroke-width": n.ev ? 2 : 1 }, svg);
    c.addEventListener("mousemove", ev => showTip(ev, `<b>${esc(n.t)}</b><br>${esc(n.a)}${n.yr ? " · " + n.yr : ""}${n.i ? "<br>" + esc(n.i) : ""}<br>${n.c} citations · ${n.deg} links in this set${n.ev ? "<br>Evidence paper: " + esc(n.ev) : ""}`));
    c.addEventListener("mouseleave", hideTip);
  });
  const used = [...new Set(N.map(n => n.tc).filter(x => x >= 0))];
  document.getElementById("lg-net").innerHTML = TC.filter(c => used.includes(c.c)).map(c => sw("--t" + c.c, c.label)).join("") + `<span><i class="sw" style="border:2px solid var(--ink);border-radius:50%;background:transparent"></i>evidence paper</span>`;
})();
})();
</script>
