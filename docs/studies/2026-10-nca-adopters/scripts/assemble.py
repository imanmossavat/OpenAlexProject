# Builds the report: nca_study.html (artifact body) and the standalone page given as argv[1].
import json, sys
C=json.load(open("compare.json")); R=C["runs"]; TOT=C["totals"]
img=json.load(open("native_imgs.json")); nlp=json.load(open("nlp_report.json"))
K=["small","big","agentic"]
def row(name,f,fmt="{:,}"): return f"<tr><td>{name}</td>"+"".join(f'<td class="num">{fmt.format(f(R[k]))}</td>' for k in K)+"</tr>"
rows="".join([row("Papers in the crawl",lambda r:r["papers"]),
  row("Abstracts reaching the NMF topic model",lambda r:r["abstracts"]),
  row(f"NCA-titled works reached (of {TOT['nca']})",lambda r:r["nca"]),
  row(f"… with references in OpenAlex (of {TOT['nca_refs']})",lambda r:r["nca_refs"]),
  row(f"… without references (of {TOT['nca_norefs']})",lambda r:r["nca_norefs"]),
  row("2026 NCA-titled works reached (of 71)",lambda r:r["nca2026"]),
  row(f"Topic-model corpus reached (of {TOT['corpus']})",lambda r:r["corpus"]),
  row("Seed citers reached (of 239)",lambda r:r["citers"])])
DOM=C["dom"]
V={"ok":'<span class="v ok">Yes</span>',"part":'<span class="v part">Partly</span>',"bad":'<span class="v bad">No</span>',"given":'<span class="v na">Given</span>'}
# Search columns: from Claude's search notes and the ChatGPT claim check (see report text).
S={"Surveys and reviews":(("ok","Lemke 2026, Hartl 2025"),("bad","said none exist")),
 "Medical imaging":(("ok","Med-NCA"),("ok","TU Darmstadt")),
 "Microscopy / blood cells":(("bad",""),("bad","")),
 "Developmental biology":(("ok","Levin lab, BraiNCA"),("part","\"limited\"")),
 "Robotics":(("ok","soft robots"),("ok","wrong affiliation")),
 "Graphics and textures":(("ok","MeshNCA, DyNCA, Cells2Pixels"),("ok","Cells2Pixels")),
 "Games":(("given","in the brief"),("given","in the brief")),
 "Photonic hardware":(("bad",""),("bad","")),
 "Gold nanoparticles / materials":(("part","metamaterials, microstructure; not gold"),("part","\"limited\"")),
 "Edge vision":(("bad",""),("bad","")),
 "Physical simulation":(("bad",""),("bad","")),
 "Reasoning":(("part","ARC-AGI paper; not Google 2026"),("ok","Google 2026")),
 "Language models":(("bad",""),("ok","MIT 2026")),
 "DNA computing":(("bad",""),("bad",""))}
def cell(s,note=""): return f"<td>{V[s]}"+(f'<br><span class="cap">{note}</span>' if note else "")+"</td>"
drows=""; score={k:{"ok":0,"part":0,"bad":0,"given":0} for k in ["claude","gpt"]+K}
for name,ids in DOM:
    c,g=S[name]; score["claude"][c[0]]+=1; score["gpt"][g[0]]+=1
    cr=""
    for k in K:
        got=R[k]["domains"][name]; s="ok" if len(got)==len(ids) else "part" if got else "bad"; score[k][s]+=1
        cr+=cell(s,f"{len(got)} of {len(ids)}" if s=="part" else "")
    drows+=f'<tr><td>{name}<br><span class="mono cap">{" ".join(ids)}</span></td>'+cell(*c)+cell(*g)+cr+"</tr>"
def tot(k): s=score[k]; return f'{s["ok"]} yes · {s["part"]} partly'+(f' · {s["given"]} given' if s["given"] else "")
drows+='<tr><td><b>Total (of 14)</b></td>'+"".join(f"<td><b>{tot(k)}</b></td>" for k in ["claude","gpt"]+K)+"</tr>"
drows+='<tr><td>Time</td><td>~3 min</td><td>not recorded</td><td>~5 min</td><td>~18 min</td><td>~17 min after the search</td></tr>'
drows+='<tr><td>Cost</td><td>within the Claude session</td><td>ChatGPT subscription</td><td>free key, ~4% of daily allowance</td><td>free key, ~9%</td><td>free key, ≤ 9%</td></tr>'
drows+='<tr><td>Factual errors found</td><td>not checked claim by claim; all 14 papers it named resolve in OpenAlex</td><td>at least 4</td><td colspan="3">n/a: the crawls only collect OpenAlex records</td></tr>'
print({k:tot(k) for k in score})
t=open("part_css.html").read()+open("part_body.html").read()+open("part_js.js").read()
t=t.replace("__DATA__",open("report_data.json").read()).replace("__NLP__",json.dumps(nlp,separators=(",",":")))
t=t.replace("__IMG_TOPWORDS__",img["topwords"]).replace("__CRAWL_ROWS__",rows).replace("__DOMAIN_ROWS__",drows)
assert "__" not in t.replace("__init__",""), [l[:80] for l in t.splitlines() if "__" in l][:3]
open("nca_study.html","w").write(t)
head='<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
i=t.index("<div class=\"wrap\">")
open(sys.argv[1],"w").write(head+t[:i]+"</head>\n<body>\n"+t[i:]+"\n</body>\n</html>\n")
print("ok", len(t)//1024, "KB")
