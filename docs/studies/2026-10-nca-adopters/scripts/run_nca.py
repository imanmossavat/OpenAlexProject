import logging, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
from ArticleCrawler import Crawler
from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
from ArticleCrawler.config import (APIConfig, SamplingConfig, TextProcessingConfig,
    StorageAndLoggingConfig, GraphConfig, RetractionConfig, StoppingConfig)
from ArticleCrawler.config.crawler_initialization import CrawlerParameters

here = Path(__file__).parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
params = CrawlerParameters(seed_paperid_file=str(here / "seeds.txt"), keywords=[
    "(cellular AND automata)", "(cellular AND automaton)", "morphogenesis",
    "(self AND organizing)", "(self AND organising)", "regeneration", "(reaction AND diffusion)"])
storage = StorageAndLoggingConfig(experiment_file_name="nca_crawl", root_folder=here / "out", log_level="INFO")
crawler = Crawler(
    crawl_initial_condition=params,
    stopping_criteria_config=StoppingConfig(max_iter=3, max_df_size=1e9),
    api_config=APIConfig(provider_type="openalex", retries=3),
    sampling_config=SamplingConfig(num_papers=25, no_key_word_lambda=0.3,
        hyper_params={"year": 0.3, "centrality": 1}, ignored_venues=[""]),
    text_config=TextProcessingConfig(abstract_min_length=120, num_topics=12, stemmer="Porter",
        default_topic_model_type="NMF", save_figures=True, random_state=42),
    storage_config=storage,
    graph_config=GraphConfig(ignored_venues=[""], include_author_nodes=False),
    retraction_config=RetractionConfig(enable_retraction_watch=True,
        avoid_retraction_in_sampler=False, avoid_retraction_in_reporting=False),
    md_generator=MarkdownFileGenerator(storage),
)
crawler.crawl()
crawler.generate_markdown_files()
crawler.analyze_and_report(save_figures=True, num_topics=12)
print("VAULT", storage.vault_folder)
