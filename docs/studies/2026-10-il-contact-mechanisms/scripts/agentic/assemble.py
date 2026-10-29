"""Splice the agentic-analysis sections, CSS and JS into index.html (idempotent: replaces a previous splice)."""
import re
from pathlib import Path
R = Path(__file__).resolve().parents[2]; H = R / "index.html"; A = Path(__file__).parent
s = H.read_text()
s = re.sub(r"\n/\* AGENTIC-CSS \*/.*?/\* /AGENTIC-CSS \*/\n", "\n", s, flags=re.S)
s = re.sub(r"<!-- AGENTIC-SECTIONS -->.*?<!-- /AGENTIC-SECTIONS -->\n", "", s, flags=re.S)
s = re.sub(r"<!-- AGENTIC-JS -->.*?<!-- /AGENTIC-JS -->\n?", "", s, flags=re.S)
css = """
/* AGENTIC-CSS */
:root { --t0:#2a78d6; --t1:#eb6834; --t2:#1baf7a; --t3:#a35bd6; --t4:#c9921a; --t5:#d63f6c; --t6:#3a9ea5; --t7:#7a8b2a; --t8:#8a6248; --t9:#5b6bd6; --t10:#9aa3ad; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --t0:#5598e7; --t1:#f08a5d; --t2:#3cc792; --t3:#bb84e6; --t4:#e0b04a; --t5:#e86b8e; --t6:#5bbcc3; --t7:#a3b54e; --t8:#b98a6e; --t9:#8592ea; --t10:#7d858f; } }
:root[data-theme="dark"] { --t0:#5598e7; --t1:#f08a5d; --t2:#3cc792; --t3:#bb84e6; --t4:#e0b04a; --t5:#e86b8e; --t6:#5bbcc3; --t7:#a3b54e; --t8:#b98a6e; --t9:#8592ea; --t10:#7d858f; }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
.grid2 > * { min-width: 0; }
.chart { width: 100%; overflow-x: auto; }
.chart svg { display: block; width: 100%; height: auto; min-width: 320px; }
svg text { fill: var(--ink-2); font: 12px var(--f-body); }
svg text.cl { font: 600 15px var(--f-mono); fill: var(--ink); paint-order: stroke; stroke: var(--panel); stroke-width: 3px; }
.sw { width: 12px; height: 12px; border-radius: 3px; display: inline-block; vertical-align: middle; }
.pick { font: inherit; font-size: .82rem; color: var(--ink-2); background: transparent; border: 1px solid var(--rule); border-radius: 999px; padding: 3px 10px; cursor: pointer; display: inline-flex; gap: 6px; align-items: center; }
.pick[aria-pressed="true"] { border-color: var(--ink); color: var(--ink); background: var(--accent-soft); }
table.heat td { padding: 6px 10px; }
#tip { position: fixed; pointer-events: none; background: var(--panel); color: var(--ink); border: 1px solid var(--rule); border-radius: 6px; padding: 8px 10px; font-size: .82rem; max-width: 320px; box-shadow: 0 4px 16px rgb(0 0 0 / .15); z-index: 20; line-height: 1.4; }
/* /AGENTIC-CSS */
"""
s = s.replace("</style>", css + "</style>", 1)
anchor = "<section>\n  <h2>The crawler's own topic output</h2>"
assert anchor in s
s = s.replace(anchor, "<!-- AGENTIC-SECTIONS -->\n" + (A / "part_sections.html").read_text() + "<!-- /AGENTIC-SECTIONS -->\n" + anchor)
js = (A / "part_js.js").read_text().replace("__RD__", (R / "data/agentic/report_data.json").read_text())
s = s.rstrip() + "\n<!-- AGENTIC-JS -->\n" + js + "<!-- /AGENTIC-JS -->\n"
H.write_text(s); print("index.html", round(len(s) / 1e3), "kB")
