"""Run one crawl of the study: python run_crawl.py brief|search"""
import logging, sys
from pathlib import Path
import numpy as np
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
from ArticleCrawler import Crawler
from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
from ArticleCrawler.config import (APIConfig, SamplingConfig, TextProcessingConfig,
    StorageAndLoggingConfig, GraphConfig, RetractionConfig, StoppingConfig)
from ArticleCrawler.config.crawler_initialization import CrawlerParameters

KEYWORDS = [  # case-insensitive substring match on titles; every term is paired with a robotics term
    "(imitation AND (robot OR manipulat OR polic))",
    "((behavior OR behaviour) AND cloning)",
    "(learning AND from AND demonstration)",
    "(diffusion AND polic)",
    "(flow AND matching AND polic)",
    "visuomotor",
    "(contact AND rich)",
    "(insertion AND (robot OR peg OR polic OR manipulat))",
    "(assembly AND (robot OR polic OR manipulat))",
    "(tactile AND (robot OR polic OR manipulat))",
    "(force AND (polic OR manipulat) AND NOT reinforcement)",
    "(complian AND (robot OR polic OR manipulat))",
    "(impedance AND (polic OR learning))",
    "(action AND chunk)",
]

name = sys.argv[1]
here = Path(__file__).parent
np.random.seed(20261029)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
params = CrawlerParameters(seed_paperid_file=str(here / f"seeds_{name}.txt"), keywords=KEYWORDS)
storage = StorageAndLoggingConfig(experiment_file_name=f"il_crawl_{name}", root_folder=here / "out", log_level="INFO")
crawler = Crawler(
    crawl_initial_condition=params,
    stopping_criteria_config=StoppingConfig(max_iter=6, max_df_size=1e9),
    api_config=APIConfig(provider_type="openalex", retries=3),
    sampling_config=SamplingConfig(num_papers=50, no_key_word_lambda=0.3,
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
