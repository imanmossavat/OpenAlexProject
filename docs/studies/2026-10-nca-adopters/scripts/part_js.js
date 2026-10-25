<script>
const D = __DATA__;
const NS = "http://www.w3.org/2000/svg";
const tip = document.getElementById("tip");
function el(tag, attrs, parent) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
function showTip(ev, html) { tip.innerHTML = html; tip.hidden = false; const w = tip.offsetWidth, h = tip.offsetHeight; let x = ev.clientX + 14, y = ev.clientY + 14; if (x + w > innerWidth - 8) x = ev.clientX - w - 14; if (y + h > innerHeight - 8) y = ev.clientY - h - 14; tip.style.left = Math.max(8, x) + "px"; tip.style.top = Math.max(8, y) + "px"; }
function hideTip() { tip.hidden = true; }
function esc(s) { return String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function legend(id, items) { document.getElementById(id).innerHTML = items.map(([c, l, ring]) => `<span><i class="sw" style="background:${ring ? "transparent" : `var(${c})`};${ring ? `border:2px solid var(--ink)` : ""};border-radius:${ring ? "50%" : "3px"}"></i>${l}</span>`).join(""); }
function niceMax(v) { const s = [4, 8, 20, 40, 60, 80, 100]; for (const x of s) if (v <= x) return x; return Math.ceil(v / 50) * 50; }
function roundTopRect(g, x, y, w, h, r, fill, tipHtml) {
  r = Math.min(r, h, w / 2);
  const p = `M${x},${y + h} V${y + r} Q${x},${y} ${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h} Z`;
  const path = el("path", { d: p, fill }, g);
  return path;
}

const FIELDS = [["cs", "--s1", "Computer science"], ["eng", "--s3", "Engineering & physical sci."], ["life", "--s2", "Life sciences & medicine"], ["other", "--s4", "Other"]];
legend("lg-field", FIELDS.map(f => [f[1], f[2]]));

function stacked(id, rows, keys, opts) {
  const W = 460, H = 260, m = { l: 34, r: 8, t: 10, b: 26 };
  const host = document.getElementById(id); host.innerHTML = "";
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.label }, host);
  const tot = rows.map(r => keys.reduce((s, k) => s + r[k[0]], 0));
  const dots = opts.dots || [];
  const max = niceMax(Math.max(...tot, ...dots.flatMap(d => rows.map(r => r[d.k]))));
  const iw = W - m.l - m.r, ih = H - m.t - m.b, bw = iw / rows.length;
  const y = v => m.t + ih - v / max * ih;
  const grid = el("g", { class: "grid" }, svg);
  for (let i = 0; i <= 4; i++) { const v = max / 4 * i; el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v) }, grid); el("text", { x: m.l - 6, y: y(v) + 4, "text-anchor": "end" }, svg).textContent = v; }
  rows.forEach((r, i) => {
    const g = el("g", {}, svg); const x = m.l + i * bw + bw * 0.18, w = bw * 0.64; let acc = 0;
    const segs = keys.filter(k => r[k[0]] > 0);
    segs.forEach((k, j) => {
      const v = r[k[0]]; const y0 = y(acc), y1 = y(acc + v); acc += v;
      const top = j === segs.length - 1; const gap = j > 0 ? 2 : 0;
      if (top) roundTopRect(g, x, y1, w, y0 - y1 - gap, 4, `var(${k[1]})`);
      else el("rect", { x, y: y1, width: w, height: Math.max(0, y0 - y1 - gap), fill: `var(${k[1]})` }, g);
    });
    dots.forEach((d, di) => { const cx = x + w / 2 + (di - (dots.length - 1) / 2) * 11, cy = y(r[d.k]);
      if (d.shape === "diamond") el("path", { d: `M${cx},${cy - 6} L${cx + 6},${cy} L${cx},${cy + 6} L${cx - 6},${cy} Z`, fill: `var(${d.c})`, stroke: "var(--panel)", "stroke-width": 2 }, g);
      else el("circle", { cx, cy, r: 5, fill: `var(${d.c})`, stroke: "var(--panel)", "stroke-width": 2 }, g); });
    el("text", { x: x + w / 2, y: H - 8, "text-anchor": "middle" }, svg).textContent = r.year;
    const hit = el("rect", { x: m.l + i * bw, y: m.t, width: bw, height: ih, fill: "transparent" }, svg);
    hit.addEventListener("mousemove", ev => showTip(ev, `<b>${r.year}</b><br>` + keys.map(k => `${k[2]}: <b>${r[k[0]]}</b>`).join("<br>") + dots.map(d => `<br>${d.l}: <b>${r[d.k]}</b>`).join("") + `<br>Total: <b>${tot[i]}</b>`));
    hit.addEventListener("mouseleave", hideTip);
  });
}
stacked("ch-field", D.citers_by_year, FIELDS.map(f => [f[0], f[1], f[2]]), { label: "Seed citers per year by field" });

const COV = [["refs", "--s1", "References indexed"], ["norefs", "--s2", "No references in OpenAlex"]];
const CDOTS = [{ k: "crawl", c: "--ink", l: "Reached by small crawl" }, { k: "ag", c: "--s3", l: "Reached by search-seeded crawl", shape: "diamond" }];
legend("lg-cov", [["--s1", "References indexed"], ["--s2", "No references in OpenAlex"]]);
document.getElementById("lg-cov").insertAdjacentHTML("beforeend", `<span><i class="sw" style="background:var(--ink);border-radius:50%"></i>Reached by small crawl</span><span><i class="sw" style="background:var(--s3);transform:rotate(45deg) scale(.85);border-radius:2px"></i>Reached by search-seeded crawl</span>`);
stacked("ch-cov", D.coverage, COV, { label: "NCA-titled works per year by reference coverage", dots: CDOTS });
document.getElementById("tbl-cov").innerHTML = `<table><thead><tr><th>Year</th><th>References indexed</th><th>No references</th><th>Small crawl</th><th>Big crawl</th><th>Search-seeded crawl</th></tr></thead><tbody>${D.coverage.map(r => `<tr><td>${r.year}</td><td class="num">${r.refs}</td><td class="num">${r.norefs}</td><td class="num">${r.crawl}</td><td class="num">${r.big}</td><td class="num">${r.ag}</td></tr>`).join("")}</tbody></table>`;

(function inst() {
  const rows = D.institutions, W = 460, rh = 26, m = { l: 210, r: 40, t: 4, b: 4 }, H = m.t + m.b + rows.length * rh;
  const host = document.getElementById("ch-inst");
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Citing papers per institution" }, host);
  const max = niceMax(rows[0].n), iw = W - m.l - m.r;
  const short = n => n.replace("Technische Universität", "TU").replace("École Polytechnique Fédérale de Lausanne", "EPFL").replace("Wyss Institute for Biologically Inspired Engineering", "Wyss Institute").replace("OsloMet – Oslo Metropolitan University", "OsloMet").replace("California Institute of Technology", "Caltech").replace("Google (United States)", "Google").replace("Østfold University of Applied Sciences", "Østfold UAS");
  rows.forEach((r, i) => {
    const y = m.t + i * rh, w = r.n / max * iw;
    el("text", { x: m.l - 8, y: y + rh / 2 + 4, "text-anchor": "end" }, svg).textContent = short(r.name);
    const p = `M${m.l},${y + 5} H${m.l + w - 4} Q${m.l + w},${y + 5} ${m.l + w},${y + 9} V${y + rh - 9} Q${m.l + w},${y + rh - 5} ${m.l + w - 4},${y + rh - 5} H${m.l} Z`;
    el("path", { d: p, fill: "var(--s1)" }, svg);
    el("text", { x: m.l + w + 6, y: y + rh / 2 + 4 }, svg).textContent = `${r.n} · ${r.seeds}/4`;
    const hit = el("rect", { x: 0, y, width: W, height: rh, fill: "transparent" }, svg);
    hit.addEventListener("mousemove", ev => showTip(ev, `<b>${esc(r.name)}</b><br>${r.n} citing papers<br>cites ${r.seeds} of 4 seeds`));
    hit.addEventListener("mouseleave", hideTip);
  });
})();

const T = __NLP__;
(function topics() {
  const tb = document.querySelector("#tbl-topics tbody");
  tb.innerHTML = T.clusters.map((c, i) => `<tr><td class="num">${i + 1}</td><td><b>${esc(c.label)}</b></td><td class="num">${c.n}</td><td class="num">${c.inc}</td><td class="mono" style="font-size:.8rem">${c.kw.map(esc).join(", ")}</td><td>${c.inst.map(esc).join("; ")}</td><td>${esc(c.rep[0])}</td></tr>`).join("");
  const num = Object.fromEntries(T.clusters.map((c, i) => [c.c, i + 1]));
  // topic map
  const W = 900, H = 560, pad = 24, host = document.getElementById("ch-map");
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Topic map of 361 NCA papers" }, host);
  const xs = T.points.map(p => p.x), ys = T.points.map(p => p.y);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const X = v => pad + (v - x0) / (x1 - x0) * (W - 2 * pad), Y = v => pad + (v - y0) / (y1 - y0) * (H - 2 * pad);
  const dots = T.points.map(p => { const c = el("circle", { cx: X(p.x), cy: Y(p.y), r: 4.5, fill: "var(--s4)", "fill-opacity": .75, stroke: "var(--panel)", "stroke-width": 1 }, svg); if (!p.cr) c.dataset.out = "1";
    c.addEventListener("mousemove", ev => showTip(ev, `<b>${esc(p.t)}</b><br>${esc(p.a)} (${p.yr})<br>Topic ${num[p.c]}: ${esc(T.clusters[num[p.c] - 1].label)}<br>${p.cr ? "In crawler data" : "<i>Not in any crawl (title search only)</i>"}`)); c.addEventListener("mouseleave", hideTip); return { c, p }; });
  const lg = el("g", {}, svg);
  T.clusters.forEach((c, i) => { const m = T.points.filter(p => p.c === c.c); const cx = m.reduce((s, p) => s + X(p.x), 0) / m.length, cy = m.reduce((s, p) => s + Y(p.y), 0) / m.length;
    el("circle", { cx, cy, r: 11, fill: "var(--panel)", stroke: "var(--ink)", "stroke-width": 1.5 }, lg);
    el("text", { x: cx, y: cy + 4, "text-anchor": "middle", style: "font-weight:600;fill:var(--ink);font-size:11px" }, lg).textContent = i + 1; });
  const legendEl = document.getElementById("lg-map");
  let active = null;
  function paint() { dots.forEach(({ c, p }) => { const on = active === null || p.c === active, col = active !== null && on ? "var(--s1)" : "var(--s4)";
    if (p.cr) { c.setAttribute("fill", col); c.setAttribute("stroke", "var(--panel)"); } else { c.setAttribute("fill", "var(--panel)"); c.setAttribute("stroke", col); c.setAttribute("stroke-width", 1.5); }
    c.setAttribute("fill-opacity", on ? (active === null ? .75 : 1) : .25); c.setAttribute("stroke-opacity", on ? 1 : .3); if (active !== null && on) svg.insertBefore(c, lg); });
    legendEl.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.c === active))); }
  legendEl.innerHTML = T.clusters.map((c, i) => `<button type="button" data-c="${c.c}" aria-pressed="false" style="font:inherit;font-size:.82rem;border:1px solid var(--rule);background:var(--panel);color:var(--ink-2);border-radius:999px;padding:3px 10px;cursor:pointer">${i + 1} · ${esc(c.label)}</button>`).join("");
  legendEl.addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; active = active === +b.dataset.c ? null : +b.dataset.c; paint(); });
  document.getElementById("lg-map2").innerHTML = `<span><i class="sw" style="background:var(--s4);border-radius:50%"></i>In crawler data (268)</span><span><i class="sw" style="background:transparent;border:1.5px solid var(--s4);border-radius:50%"></i>Title search only, not in any crawl (93)</span>`;
  paint();
  const st = document.createElement("style"); st.textContent = `#lg-map button[aria-pressed="true"]{background:var(--accent-soft)!important;color:var(--accent)!important;border-color:var(--accent)!important}`; document.head.appendChild(st);
  // heatmap
  const ramp = ["--h0", "--h1", "--h2", "--h3", "--h4", "--h5"];
  const max = Math.max(...T.clusters.flatMap(c => c.years));
  const hw = 900, lw = 250, cw = (hw - lw - 10) / T.years.length, rh = 26, hh = 30 + T.clusters.length * rh;
  const hs = el("svg", { viewBox: `0 0 ${hw} ${hh}`, role: "img", "aria-label": "Papers per topic per year" }, document.getElementById("ch-heat"));
  T.years.forEach((y, j) => el("text", { x: lw + j * cw + cw / 2, y: 16, "text-anchor": "middle" }, hs).textContent = y);
  T.clusters.forEach((c, i) => { const yy = 26 + i * rh;
    el("text", { x: lw - 8, y: yy + rh / 2 + 4, "text-anchor": "end" }, hs).textContent = `${i + 1} · ${c.label}`;
    c.years.forEach((v, j) => { const step = v === 0 ? 0 : Math.min(5, 1 + Math.floor((v / max) * 4.999));
      const r = el("rect", { x: lw + j * cw + 1, y: yy + 1, width: cw - 2, height: rh - 2, rx: 3, fill: `var(${ramp[step]})` }, hs);
      if (v) el("text", { x: lw + j * cw + cw / 2, y: yy + rh / 2 + 4, "text-anchor": "middle", style: `fill:var(${step >= 4 ? "--h-ink-dark" : "--h-ink"});font-variant-numeric:tabular-nums` }, hs).textContent = v;
      r.addEventListener("mousemove", ev => showTip(ev, `<b>${esc(c.label)}</b><br>${T.years[j]}: <b>${v}</b> papers`)); r.addEventListener("mouseleave", hideTip); }); });
})();

(function net() {
  const NET = [["cs", "--s1", "Computer science"], ["eng", "--s3", "Engineering & physical sci."], ["life", "--s2", "Life sciences & medicine"], ["other", "--s4", "Other"]];
  legend("lg-net", [...NET.map(f => [f[1], f[2]]), ["--ink", "Seed paper", true]]);
  const col = Object.fromEntries(NET.map(f => [f[0], `var(${f[1]})`]));
  const W = 900, H = 600, pad = 30, host = document.getElementById("ch-net");
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Citation network of papers citing the four NCA seed papers" }, host);
  const P = {}; D.nodes.forEach(n => P[n.id] = { x: pad + n.x * (W - 2 * pad), y: pad + n.y * (H - 2 * pad), n });
  const eg = el("g", { stroke: "var(--edge)", "stroke-width": 0.6, "stroke-opacity": 0.7 }, svg);
  D.edges.forEach(([a, b]) => el("line", { x1: P[a].x, y1: P[a].y, x2: P[b].x, y2: P[b].y }, eg));
  const ng = el("g", {}, svg);
  const order = D.nodes.slice().sort((a, b) => (a.seed - b.seed) || (a.c - b.c));
  order.forEach(n => {
    const p = P[n.id];
    if (n.seed) {
      el("circle", { cx: p.x, cy: p.y, r: 13, fill: "var(--panel)", stroke: "var(--ink)", "stroke-width": 3 }, ng);
      const t = el("text", { x: p.x, y: p.y - 19, "text-anchor": "middle", style: "font-weight:600;fill:var(--ink)" }, ng); t.textContent = n.t;
    } else {
      const r = Math.max(3, Math.min(11, 2 + Math.sqrt(n.c) * 0.9));
      const c = el("circle", { class: "node", cx: p.x, cy: p.y, r, fill: col[n.g], stroke: "var(--panel)", "stroke-width": 1.5 }, ng);
      c.addEventListener("mousemove", ev => showTip(ev, `<b>${esc(n.t)}</b><br>${esc(n.a)} (${n.y_})<br>${esc(n.i) || "<i>no institution in record</i>"}<br>${n.c} citations`));
      c.addEventListener("mouseleave", hideTip);
    }
  });
})();
</script>
