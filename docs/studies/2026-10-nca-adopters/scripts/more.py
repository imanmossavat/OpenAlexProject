import os, json, requests
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
key=os.environ["OPENALEX_API_KEY"]
for wid in ["W7214964112","W7135075179","W3138886030"]:
    w=requests.get(f"https://api.openalex.org/works/{wid}",params={"api_key":key}).json()
    print(wid, w["title"], "|", [(a["author"]["display_name"], [i["display_name"] for i in a["institutions"]], a.get("raw_affiliation_strings")) for a in w["authorships"]])
for q in ["Cells2Pixels","high-resolution neural cellular automata implicit decoder","A New Kind of Network review reference implementation neural cellular automata"]:
    r=requests.get("https://api.openalex.org/works",params={"search":q,"per_page":3,"api_key":key,"select":"id,title,publication_year,primary_location"}).json()
    print("Q:",q, [(w["id"][-11:],w["publication_year"],w["title"][:90]) for w in r["results"]])
# refs of citers for network
ids=[w["id"].split("/")[-1] for w in json.load(open("citers.json"))]
refs={}
for i in range(0,len(ids),50):
    r=requests.get("https://api.openalex.org/works",params={"filter":"openalex:"+"|".join(ids[i:i+50]),"per_page":50,"api_key":key,"select":"id,referenced_works"}).json()
    for w in r["results"]: refs[w["id"].split("/")[-1]]=[x.split("/")[-1] for x in w["referenced_works"]]
json.dump(refs,open("citer_refs.json","w")); print("refs fetched",len(refs))
