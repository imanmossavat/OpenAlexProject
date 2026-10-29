"""Resolve the study's seed papers to OpenAlex work IDs (by arXiv DOI, else by title)."""
import json, os, sys, urllib.parse, urllib.request
from pathlib import Path

ENV = Path("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
KEY = next((l.split("=", 1)[1].strip().strip('"') for l in ENV.read_text().splitlines()
            if l.startswith("OPENALEX_API_KEY")), "")

BRIEF = [  # named in the question, plus DP and ACT (pre-registration section 8)
    ("FACTR", None, "FACTR: Force-Attending Curriculum Training for Contact-Rich Policy Learning"),
    ("robomimic", None, "What Matters in Learning from Offline Human Demonstrations for Robot Manipulation"),
    ("Much Ado About Noising", "2512.01809", None),
    ("Diffusion Policy", "2303.04137", None),
    ("ACT", "2304.13705", None),
]
SEARCH = [  # named by Claude's web search, 2026-10-29 08:02 UTC
    ("DexTac", "2601.21474", None),
    ("DexForce", "2501.10356", None),
    ("Reactive Diffusion Policy", "2503.02881", None),
    ("TacForeSight", "2606.11184", None),
    ("Query-Centric Diffusion Policy", "2509.18686", None),
    ("ContactDP", "2609.23800", None),
    ("Deformable gasket assembly", "2408.12593", None),
    ("Adaptive Compliance Policy", "2410.09309", None),
    ("Stiffness Copilot", "2603.14068", None),
    ("VIDP", "2608.06210", None),
    ("Direction Matters", "2602.14174", None),
    ("Past-Token Prediction", "2505.09561", None),
    ("Foresight for 3D Diffusion Policies", "2609.20669", None),
]

def get(url):
    sep = "&" if "?" in url else "?"
    with urllib.request.urlopen(f"{url}{sep}api_key={KEY}", timeout=30) as r:
        return json.load(r)

def resolve(arxiv, title):
    if arxiv:
        try:
            w = get(f"https://api.openalex.org/works/doi:10.48550/arXiv.{arxiv}")
            return w, "arxiv-doi"
        except Exception:
            pass
    q = title or arxiv
    res = get("https://api.openalex.org/works?search=" + urllib.parse.quote(q) + "&per-page=3")["results"]
    return (res[0], "title-search") if res else (None, "not found")

out = []
for group, items in (("brief", BRIEF), ("search", SEARCH)):
    for name, arxiv, title in items:
        w, how = resolve(arxiv, title)
        row = {"group": group, "name": name, "arxiv": arxiv, "how": how,
               "id": w and w["id"].rsplit("/", 1)[1], "title": w and w["display_name"],
               "year": w and w["publication_year"],
               "n_refs": w and len(w.get("referenced_works", [])),
               "cited_by": w and w["cited_by_count"]}
        out.append(row)
        print(f'{group:6} {name:36} {how:12} {row["id"]} {row["year"]} refs={row["n_refs"]} cites={row["cited_by"]} | {row["title"]}')
Path(sys.argv[1] if len(sys.argv) > 1 else "../data/seeds.json").parent.mkdir(exist_ok=True)
Path(sys.argv[1] if len(sys.argv) > 1 else "../data/seeds.json").write_text(json.dumps(out, indent=1))
