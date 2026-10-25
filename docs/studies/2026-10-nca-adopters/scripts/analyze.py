import pickle, sys, logging
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
logging.basicConfig(level=logging.WARNING)
import ArticleCrawler
c = pickle.load(open(sys.argv[1], "rb"))
print(type(c))
c.generate_markdown_files()
c.analyze_and_report(save_figures=True, num_topics=12)
