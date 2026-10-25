from dotenv import load_dotenv; load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
import logging; logging.basicConfig(level=logging.WARNING)
from ArticleCrawler.api.zotero.exporter import ZoteroExportService, PaperExportPayload, ZoteroExportOptions
P={"seed paper":["W3006201994","W3130408838","W3199753215","W3180899834"],
 "survey":["W4416818787","W7157701221","W7214021387"],
 "medical imaging":["W4379660320","W4404341782"],
 "microscopy":["W4403071100"],
 "developmental biology":["W7148826719"],
 "robotics":["W3151337059","W3138886030"],
 "graphics":["W4400820364","W4386076170","W7168679437"],
 "photonic hardware":["W4403229727","W4385356390"],
 "materials":["W4396553883","W4383032390","W4390986637","W7169558435"],
 "edge vision":["W7164000886","W7213322770"],
 "physical simulation":["W7220892747","W4408224315","W2809252620"],
 "reasoning":["W4417124902","W7214964112"],
 "language models":["W7135075179","W7172384256"],
 "theory":["W4413217444"],
 "molecular computing":["W4413946390"]}
papers=[PaperExportPayload(paper_id=i,tags=[t]) for t,ids in P.items() for i in ids]
r=ZoteroExportService().export_papers(papers,ZoteroExportOptions(collection_name="NCA adopters study (Oct 2026)",create_collection=True,dedupe=True,extra_tags=["nca-study-2026-10"]))
print("created",len(r.created),"skipped",r.skipped,"failed",r.failed)
