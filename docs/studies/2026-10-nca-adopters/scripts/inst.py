import os, json, collections, requests
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
key = os.environ["OPENALEX_API_KEY"]
seeds = {"W3006201994":"GrowingNCA","W3130408838":"Textures","W3199753215":"Earle","W3180899834":"RD"}
works = {}
for s in seeds:
    cursor="*"
    while cursor:
        r = requests.get("https://api.openalex.org/works", params={"filter":f"cites:{s}","per_page":200,"cursor":cursor,"api_key":key,
            "select":"id,title,publication_year,cited_by_count,authorships,primary_location,primary_topic,is_retracted,type"}).json()
        for w in r["results"]:
            works.setdefault(w["id"], {**w, "seeds":set()})["seeds"].add(seeds[s])
        cursor = r["meta"].get("next_cursor") if r["results"] else None
print("unique citers", len(works), "retracted:", [w["title"] for w in works.values() if w["is_retracted"]])
auth = collections.defaultdict(lambda: {"n":0,"seeds":set(),"inst":collections.Counter()})
inst = collections.Counter(); inst_seed = collections.defaultdict(set); field = collections.Counter(); venue = collections.Counter(); ctry=collections.Counter()
for w in works.values():
    pt = w.get("primary_topic") or {}
    field[(pt.get("field") or {}).get("display_name","?")] += 1
    venue[((w.get("primary_location") or {}).get("source") or {}).get("display_name","?")] += 1
    wi=set()
    for a in w["authorships"]:
        nm = a["author"]["display_name"]; d = auth[nm]; d["n"]+=1; d["seeds"] |= w["seeds"]
        for i in a.get("institutions",[]):
            d["inst"][i["display_name"]]+=1; wi.add((i["display_name"], i.get("country_code")))
    for i,cc in wi: inst[i]+=1; inst_seed[i] |= w["seeds"]; ctry[cc]+=1
print("\nFIELDS", field.most_common(15))
print("\nVENUES", venue.most_common(15))
print("\nINSTITUTIONS (papers)", [(i,n,sorted(inst_seed[i])) for i,n in inst.most_common(25)])
print("\nCOUNTRIES", ctry.most_common(10))
print("\nAUTHORS", [(a,d["n"],sorted(d["seeds"]),d["inst"].most_common(1)) for a,d in sorted(auth.items(), key=lambda x:-x[1]["n"])[:30]])
print("\nMULTI-SEED AUTHORS", [(a,d["n"],sorted(d["seeds"])) for a,d in auth.items() if len(d["seeds"])>=2 and d["n"]>=2])
print("\nTOP-CITED CITERS")
for w in sorted(works.values(), key=lambda w:-w["cited_by_count"])[:20]:
    print(w["cited_by_count"], w["publication_year"], w["title"][:90], "|", ", ".join(a["author"]["display_name"] for a in w["authorships"][:3]))
json.dump([{k:(list(v) if isinstance(v,set) else v) for k,v in w.items()} for w in works.values()], open("citers.json","w"))
