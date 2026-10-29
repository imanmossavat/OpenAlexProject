"""Step 1 of verification: does each cited paper exist, with the claimed title? (arXiv API, then OpenAlex)"""
import json, re, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

ENV = Path("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
KEY = next((l.split("=", 1)[1].strip().strip('"') for l in ENV.read_text().splitlines()
            if l.startswith("OPENALEX_API_KEY")), "")
norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())

CLAIMS = [  # (source, arXiv id or None, claimed title)
    ("gpt_structured", "2609.38401", "Memorize, Adapt, Ignore: Diagnosing Robot Learning"),
    ("gpt_structured", "2502.17432", "FACTR: Force-Attending Curriculum Training"),
    ("gpt_structured", "2108.03298", "What Matters in Learning from Offline Human Demonstrations"),
    ("gpt_structured", "2609.35003", "Learning to Act under Visual Interruptions with VLA Models"),
    ("gpt_structured", "2412.00084", "Unpacking Individual Components of Diffusion Policy"),
    ("gpt_gist", None, "MiTaS tactile Krohn"),
    ("gpt_gist", None, "Li Brock environmental constraints single demonstration insertion"),
    ("gpt_gist", None, "Kim force transformer bottle cap opening gaze imitation"),
    ("gpt_gist", None, "Shukla diffusion bimanual battery cover assembly force"),
    ("gpt_gist", "2503.02881", "Reactive Diffusion Policy"),
    ("notebooklm", "2303.04137", "Diffusion Policy: Visuomotor Policy Learning via Action Diffusion"),
    ("notebooklm", "2505.12410", "MTIL: Encoding Full History with Mamba for Temporal Imitation Learning"),
    ("notebooklm", "2512.01809", "Much Ado About Noising"),
    ("notebooklm", "2510.08787", "Geometry-aware Policy Imitation"),
    ("notebooklm", "2504.13618", "On the Importance of Tactile Sensing for Imitation Learning: A Case Study on Robotic Match Lighting"),
    ("notebooklm", "2502.13519", "MILE: Model-based Intervention Learning"),
    ("notebooklm", "2610.32093", "DiscoDemo: Discovering Efficient and Diverse Robot Demonstrations for Imitation Learning"),
    ("notebooklm", "2610.32525", "From Freehand Demonstrations to Autonomous Robotic Ultrasound"),
    ("notebooklm", "2409.07343", "Learning Robotic Manipulation Policies from Point Clouds with Conditional Flow Matching"),
    ("notebooklm", "2410.14040", "Latent Weight Diffusion: Generating policies from trajectories"),
    ("notebooklm", "2608.15938", "Revisiting Open-Loop Execution in Robotics"),
    ("notebooklm", "2609.21369", "ProTracer: Proprioception-Guided Failure Diagnosis in Robot Manipulation"),
    ("notebooklm", "2605.11048", "ForceFlow: Learning to Feel and Act via Contact-Driven Flow Matching"),
    ("notebooklm", "2606.13232", "WT-UMI: Tactile-based Whole-Body Manipulation"),
    ("notebooklm", "2606.24078", "MinInter: Minimizing Trajectory Interpolation During Data Augmentation"),
    ("notebooklm", None, "Triply-Hierarchical Diffusion Policy for Visuomotor Learning"),
    ("notebooklm", None, "Interventional Data Generation for Robust and Data-Efficient Robot Imitation Learning"),
    ("notebooklm", None, "AgenticTactileVLA Contact-Guided Execution-Time Supervision"),
    ("notebooklm", None, "FTP-1 Generalist Foundation Tactile Policy Across Tactile Sensors"),
    ("notebooklm", None, "Equivariant Diffusion Policy"),
    ("notebooklm", None, "Spatially Conditioned Diffusion Policy single RGB camera"),
    ("notebooklm", None, "ConceptACT Episode-Level Concepts"),
    ("notebooklm", None, "InterACT Inter-dependency Aware Action Chunking"),
    ("notebooklm", None, "ViTacFormer Cross-Modal Representation Visuo-Tactile"),
]

def arxiv_titles(ids):
    url = "http://export.arxiv.org/api/query?max_results=100&id_list=" + ",".join(ids)
    root = ET.fromstring(urllib.request.urlopen(url, timeout=60).read())
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = {}
    for e in root.findall("a:entry", ns):
        aid = e.find("a:id", ns).text.rsplit("/", 1)[1].split("v")[0]
        t = e.find("a:title", ns)
        if t is not None and t.text and t.text.strip() != "Error":
            first = e.find("a:author/a:name", ns)
            out[aid] = (" ".join(t.text.split()), first.text if first is not None else "",
                        e.find("a:published", ns).text[:10])
    return out

def openalex(q):
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(q) +
           f"&per-page=1&select=id,display_name,publication_year,authorships&api_key={KEY}")
    r = json.load(urllib.request.urlopen(url, timeout=30))["results"]
    if not r: return None
    a = r[0]["authorships"]
    return r[0]["display_name"], a[0]["author"]["display_name"] if a else "", r[0]["publication_year"], r[0]["id"].rsplit("/",1)[1]

found = arxiv_titles([c[1] for c in CLAIMS if c[1]])
rows = []
for src, aid, claim in CLAIMS:
    if aid:
        hit = found.get(aid)
        status = "missing" if not hit else ("title ok" if norm(claim)[:25] in norm(hit[0]) else "TITLE MISMATCH")
        rows.append(dict(source=src, arxiv=aid, claimed=claim, status=status,
                         actual=hit and hit[0], first_author=hit and hit[1], date=hit and hit[2]))
    else:
        hit = openalex(claim); time.sleep(0.2)
        rows.append(dict(source=src, arxiv=None, claimed=claim, status="openalex top hit" if hit else "missing",
                         actual=hit and hit[0], first_author=hit and hit[1], date=hit and hit[2], openalex=hit and hit[3]))
for r in rows:
    print(f'{r["source"]:15} {str(r["arxiv"]):11} {r["status"]:16} {r["date"]} {r["first_author"]} | {r["actual"]}')
Path("data/verify_ids.json").write_text(json.dumps(rows, indent=1))
