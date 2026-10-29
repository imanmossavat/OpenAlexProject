"""Analysis 3 (citation network of field set + evidence) and assembly of data/agentic/report_data.json for index.html."""
import json, re, collections
from pathlib import Path
import networkx as nx
D = Path(__file__).resolve().parents[2] / "data/agentic"
A = json.loads((D / "crawl_analysis.json").read_text()); T = json.loads((D / "topics.json").read_text())
F = json.loads((D / "field_set.json").read_text()); corpus = json.loads((D / "corpus.json").read_text())
LABELS = {0: "Tactile and force-aware policies", 1: "Visual and 3D representations, datasets", 2: "General manipulation, adaptation, surveys",
          3: "Assembly and insertion in manufacturing", 4: "Diffusion for planning and offline RL", 5: "Contact-rich and bimanual compliant policies",
          6: "IL theory, data and interventions", 7: "Surgical robotics", 8: "Vision-language-action and language grounding",
          9: "Teleoperation and data-collection hardware", 10: "Embodied AI and VLA surveys"}
norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())[:80]
topic_by_title = {norm(p["t"]): p["c"] for p in T["points"]}
# --- network: field set + evidence records
ev = [d for d in corpus if "evidence" in d["srcs"]]
nodes = {w["id"]: dict(w, ev=None) for w in F}
for d in ev:
    nodes.setdefault(d["id"], dict(d))
    nodes[d["id"]]["ev"] = d.get("evidence")
G = nx.Graph(); G.add_nodes_from(nodes)
for i, w in nodes.items():
    for r in w["refs"]:
        if r in nodes and r != i: G.add_edge(i, r)
# Layout: spring layout on the full graph fails here (65% isolated nodes form a wide ring and squeeze the
# connected part into the centre). So lay out only connected nodes: Kamada-Kawai per component, components
# placed side by side (largest first); isolated works are listed under the figure instead.
comps = sorted((c for c in nx.connected_components(G) if len(c) > 1), key=len, reverse=True)
pos, xoff = {}, 0.0
for comp in comps:
    sub = G.subgraph(comp)
    if len(comp) > 2:  # Kamada-Kawai, then a fisheye (radius r -> r**0.6 around the centroid) to open the dense hub
        kk = nx.kamada_kawai_layout(sub); cx = sum(v[0] for v in kk.values()) / len(kk); cy = sum(v[1] for v in kk.values()) / len(kk)
        pc = {}
        for n, (x, y) in kk.items():
            dx, dy = x - cx, y - cy; r = (dx * dx + dy * dy) ** 0.5
            f = r ** 0.6 / r if r > 0 else 0; pc[n] = (dx * f, dy * f)
    else: pc = {n: (i * 0.4, 0.0) for i, n in enumerate(comp)}
    xs_ = [v[0] for v in pc.values()]; ys_ = [v[1] for v in pc.values()]
    w = (max(xs_) - min(xs_)) or 0.4; h = (max(ys_) - min(ys_)) or 0.4
    sc = 1.0 if len(comp) == len(comps[0]) else 0.18
    for n, (x, y) in pc.items(): pos[n] = (xoff + (x - min(xs_)) / w * sc, (y - min(ys_)) / h * sc)
    xoff += sc + 0.06
xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
nxv = lambda v: (v - min(xs)) / (max(xs) - min(xs)); nyv = lambda v: (v - min(ys)) / ((max(ys) - min(ys)) or 1)
net_nodes, isolated = [], []
for i, w in nodes.items():
    rec = dict(id=i, t=w["title"], yr=w["year"], c=w["cites"], tc=topic_by_title.get(norm(w["title"]), -1), ev=w.get("ev"), deg=G.degree(i),
               a=", ".join(w["authors"][:3]) + (" et al." if len(w["authors"]) > 3 else ""), i="; ".join(sorted({x[0] for x in w["inst"]})[:2]),
               norefs=not w["refs"])
    if i in pos: net_nodes.append(dict(rec, x=round(nxv(pos[i][0]), 4), y=round(nyv(pos[i][1]), 4)))
    else: isolated.append(rec)
print("drawn", len(net_nodes), "isolated", len(isolated), "of which no refs in OpenAlex", sum(r["norefs"] for r in isolated))
iso = sum(1 for n in G if G.degree(n) == 0)
print("network nodes", G.number_of_nodes(), "edges", G.number_of_edges(), "isolated", iso, "components>1", sum(1 for c in nx.connected_components(G) if len(c) > 1))
comp = max(nx.connected_components(G), key=len); print("largest component", len(comp))
top_deg = sorted(G.degree, key=lambda x: -x[1])[:8]; print("hubs", [(nodes[n]["title"][:60], d) for n, d in top_deg])
# --- topics for report
years = ["≤2022", "2023", "2024", "2025", "2026"]
clusters = []
for c in T["clusters"]:
    row = collections.Counter()
    for y, n in c["years"].items():
        y = int(y) if y not in (None, "None") else 0
        row["≤2022" if y <= 2022 else str(y)] += n
    clusters.append(dict(c=c["c"], label=LABELS[c["c"]], n=c["n"], field=c["field"], inc=c["incrawl"], kw=c["kw"][:6], rep=c["rep"][:2],
                         inst=[i for i, _ in c["inst"]], ev=c["evidence"], years=[row[y] for y in years]))
clusters.sort(key=lambda c: -c["n"])
out = dict(A, topics=dict(k=T["k"], silhouette=T["silhouette"], years=years, clusters=clusters,
           points=[dict(x=p["x"], y=p["y"], c=p["c"], t=p["t"], yr=p["yr"], a=p["a"], cr=p["cr"], fs=p["fs"], ev=p["ev"]) for p in T["points"]]),
           network=dict(nodes=net_nodes, edges=[[u, v] for u, v in G.edges], isolated=iso, largest=len(comp), isolated_list=isolated))
(D / "report_data.json").write_text(json.dumps(out, separators=(",", ":"), default=str))
print("report_data.json", round((D / "report_data.json").stat().st_size / 1e3), "kB")
