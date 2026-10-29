"""Resolve every evidence paper (cited by any source, or a checklist source) to all OpenAlex versions."""
import json, re, time, urllib.parse, urllib.request
from pathlib import Path
ENV = Path("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
KEY = next((l.split("=", 1)[1].strip().strip('"') for l in ENV.read_text().splitlines() if l.startswith("OPENALEX_API_KEY")), "")
norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())

# (key, title, arXiv, cited by) — cited-by codes: G1 ChatGPT AI prompt, G2 ChatGPT gist, NB NotebookLM, CS Claude search, CL pre-registered checklist
E = [
 ("MAI", "Memorize, Adapt, Ignore: Diagnosing Robot Learning Mechanisms under Training Data Variation", "2609.38401", "G1"),
 ("FACTR", "FACTR: Force-Attending Curriculum Training for Contact-Rich Policy Learning", "2502.17432", "G1 CL"),
 ("robomimic", "What Matters in Learning from Offline Human Demonstrations for Robot Manipulation", "2108.03298", "G1 CL"),
 ("MINT", "Learning to Act under Visual Interruptions with Vision-Language-Action Models", "2609.35003", "G1"),
 ("UnpackDP", "Unpacking the Individual Components of Diffusion Policy", "2412.00084", "G1"),
 ("MiTaS", "Multi-Resolution Tactile Imitation Learning for Contact-Rich Robotic Manipulation", "2606.06281", "G2"),
 ("Kim-M2R", "Training Robots Without Robots: Deep Imitation Learning for Master-to-Robot Policy Transfer", "2202.09574", "G2"),
 ("RDP", "Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation", "2503.02881", "G2 CS CL"),
 ("DP", "Diffusion Policy: Visuomotor Policy Learning via Action Diffusion", "2303.04137", "NB CL"),
 ("MTIL", "MTIL: Encoding Full History with Mamba for Temporal Imitation Learning", "2505.12410", "NB"),
 ("Noising", "Much Ado About Noising: Dispelling the Myths of Generative Robotic Control", "2512.01809", "NB CS CL"),
 ("GPI", "Geometry-aware Policy Imitation", "2510.08787", "NB"),
 ("MatchLight", "On the Importance of Tactile Sensing for Imitation Learning: A Case Study on Robotic Match Lighting", "2504.13618", "NB"),
 ("MILE", "MILE: Model-based Intervention Learning", "2502.13519", "NB"),
 ("DiscoDemo", "DiscoDemo: Discovering Efficient and Diverse Robot Demonstrations for Imitation Learning", "2610.32093", "NB"),
 ("ForceFlow", "ForceFlow: Learning to Feel and Act via Contact-Driven Flow Matching", "2605.11048", "NB"),
 ("MinInter", "MinInter: Minimizing Trajectory Interpolation During Data Augmentation for Imitation Learning", "2606.24078", "NB"),
 ("H3DP", "Triply-Hierarchical Diffusion Policy for Visuomotor Learning", None, "NB"),
 ("IntervenGen", "IntervenGen: Interventional Data Generation for Robust and Data-Efficient Robot Imitation Learning", None, "NB"),
 ("EquiDiff", "Equivariant Diffusion Policy", None, "NB"),
 ("ACT", "Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware", "2304.13705", "NB CL"),
 ("FTP1", "FTP-1: A Generalist Foundation Tactile Policy Across Tactile Sensors for Contact-Rich Manipulation", None, "NB"),
 ("DexTac", "DexTac: Learning Contact-aware Visuotactile Policies via Hand-by-hand Teaching", "2601.21474", "CS"),
 ("DexForce", "DexForce: Extracting Force-informed Actions from Kinesthetic Demonstrations for Dexterous Manipulation", "2501.10356", "CS"),
 ("TacForeSight", "TacForeSight: Force-Guided Tactile World Model for Contact-Rich Manipulation", "2606.11184", "CS"),
 ("QDP", "Query-Centric Diffusion Policy for Generalizable Robotic Assembly", "2509.18686", "CS"),
 ("ContactDP", "ContactDP: Contact-Guided Diffusion Policy for Tight Insertion Tasks", "2609.23800", "CS"),
 ("Gasket", "Automating Deformable Gasket Assembly", "2408.12593", "CS"),
 ("ACP", "Adaptive Compliance Policy: Learning Approximate Compliance for Diffusion Guided Control", "2410.09309", "CS CL"),
 ("PTP", "Learning Long-Context Diffusion Policies via Past-Token Prediction", "2505.09561", "CS CL"),
 ("BID", "Bidirectional Decoding: Improving Action Chunking via Guided Test-Time Sampling", "2408.17355", "CL"),
 ("RTC", "Real-Time Execution of Action Chunking Flow Policies", "2506.07339", "CL"),
 ("Shortcut", "Shortcut Learning in Generalist Robot Policies: The Role of Dataset Diversity and Fragmentation", "2508.06426", "CL"),
 ("Scaling", "Data Scaling Laws in Imitation Learning for Robotic Manipulation", "2410.18647", "CL"),
 ("Pitfalls", "The Pitfalls of Imitation Learning when Actions are Continuous", "2503.09722", "CL"),
]
def get(url): return json.load(urllib.request.urlopen(url + f"&api_key={KEY}", timeout=30))
out = []
for key, title, arxiv, by in E:
    q = urllib.parse.quote(title.split(":")[0] if len(title.split(":")[0]) > 15 else title)
    res = get(f"https://api.openalex.org/works?filter=title.search:{q}&per-page=25&select=id,display_name,publication_year,referenced_works_count,cited_by_count")["results"]
    vs = [r for r in res if norm(r["display_name"])[:35] == norm(title)[:35]]
    if arxiv:
        try:
            w = get(f"https://api.openalex.org/works/doi:10.48550/arXiv.{arxiv}?select=id,display_name,publication_year,referenced_works_count,cited_by_count")
            if w["id"] not in {v["id"] for v in vs}: vs.append(w)
        except Exception: pass
    out.append(dict(key=key, title=title, arxiv=arxiv, cited_by=by.split(),
        versions=[dict(id=v["id"].rsplit("/",1)[1], year=v["publication_year"], refs=v["referenced_works_count"], cites=v["cited_by_count"]) for v in vs]))
    print(f'{key:12} {len(vs)} versions  refs={[v["referenced_works_count"] for v in vs]} cites={[v["cited_by_count"] for v in vs]}')
    time.sleep(0.1)
Path("data/evidence.json").write_text(json.dumps(out, indent=1))
