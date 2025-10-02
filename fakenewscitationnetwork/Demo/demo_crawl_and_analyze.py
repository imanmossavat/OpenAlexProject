import os
import sys

current_directory = os.path.dirname(os.path.abspath(__file__))  # Demo folder
parent_directory = os.path.abspath(os.path.join(current_directory, '..'))  # Project root

if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

print(f"Project root: {parent_directory}")
print(f"ArticleCrawler location: {os.path.join(parent_directory, 'ArticleCrawler')}")

import logging
from pathlib import Path

try:
    import ArticleCrawler
    print(f" ArticleCrawler package found at: {ArticleCrawler.__file__}")
except ImportError as e:
    print(f" Cannot import ArticleCrawler: {e}")
    print(f"Make sure ArticleCrawler folder exists at: {parent_directory}")
    sys.exit(1)

from ArticleCrawler import Crawler
from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
from ArticleCrawler.config import (
    APIConfig, SamplingConfig, TextProcessingConfig,
    StorageAndLoggingConfig, GraphConfig, RetractionConfig, StoppingConfig
)
from ArticleCrawler.config.crawler_initialization import CrawlerParameters


def run_crawler_new_architecture():
    """Demo using the NEW refactored SOLID architecture"""
    
    print("\n" + "=" * 70)
    print(" ARTICLE CRAWLER DEMO - NEW SOLID ARCHITECTURE")
    print("=" * 70)
    

    max_iter = 1
    num_papers = 1
    experiment_file_name = 'demo_new_arch'
    
    paper_ids_file = Path(current_directory) / "demo.txt"
    
    if not paper_ids_file.exists():
        print(f"\n ERROR: Paper IDs file not found at: {paper_ids_file}")
        print("\nPlease create Demo/demo.txt with paper IDs, one per line. Example:")
        print("W2964239844")
        print("W2950636114")
        print("W2963159028")
        return

    keywords = [
        "(science OR scientific) AND ((summary AND generation) OR summarization)",
        "(science OR scientific) AND (recommendation OR (recommend OR recommender))",
        "(scientific AND question AND answering)",
        "(scientific AND ((retrieval AND (augmented AND generation)) OR RAG))",
        "(science OR scientific) AND (BERT OR (transformer OR (embedding OR embedding)))",
    ]
    
    print(f"\n Loading paper IDs from: {paper_ids_file}")
    crawl_initial_condition = CrawlerParameters(
        seed_paperid_file=str(paper_ids_file),
        keywords=keywords
    )
    print(f" Loaded {len(crawl_initial_condition.seed_paperid)} seed papers")
    print(f" Using {len(keywords)} keyword filters")

    print("\n" + "-" * 70)
    print("CONFIGURING CRAWLER WITH NEW SOLID ARCHITECTURE")
    print("-" * 70)
    
    api_config = APIConfig(
        provider_type='openalex',
        retries=3
    )
    print(f" API Provider: {api_config.provider_type}")
    
    sampling_config = SamplingConfig(
        num_papers=num_papers,
        no_key_word_lambda=0.2,
        hyper_params={'year': 0.3, 'centrality': 1},
        ignored_venues=['', 'ArXiv', 'medRxiv', 'WWW']
    )
    print(f" Sampling: {sampling_config.num_papers} papers per iteration")
    
    text_config = TextProcessingConfig(
        abstract_min_length=120,
        num_topics=20,
        stemmer='Porter',
        default_topic_model_type='NMF',
        save_figures=True,
        random_state=42
    )
    print(f" Topic Modeling Strategy: {text_config.default_topic_model_type}")
    print(f" Number of topics: {text_config.num_topics}")
    
    storage_config = StorageAndLoggingConfig(
        experiment_file_name=experiment_file_name,
        root_folder=Path(parent_directory) / 'data' / 'crawler_experiments',
        log_level='INFO'
    )
    print(f" Experiment: {storage_config.experiment_file_name}")
    print(f" Output folder: {storage_config.experiment_folder}")
    
    graph_config = GraphConfig(
        ignored_venues=['', 'ArXiv', 'medRxiv', 'WWW'],
        include_author_nodes=False
    )
    print(f" Graph nodes: Papers + Venues")
    
    retraction_config = RetractionConfig(
        enable_retraction_watch=True,
        avoid_retraction_in_sampler=False,
        avoid_retraction_in_reporting=True
    )
    print(f" Retraction Watch: enabled")
    
    stopping_config = StoppingConfig(
        max_iter=max_iter,
        max_df_size=1E9
    )
    print(f" Max iterations: {stopping_config.max_iter}")

    md_generator = MarkdownFileGenerator(storage_config)
    print(" Markdown generator initialized")

    print("\n" + "-" * 70)
    print("INITIALIZING CRAWLER WITH DEPENDENCY INJECTION")
    print("-" * 70)
    
    crawler = Crawler(
        crawl_initial_condition=crawl_initial_condition,
        stopping_criteria_config=stopping_config,
        api_config=api_config,
        sampling_config=sampling_config,
        text_config=text_config,
        storage_config=storage_config,
        graph_config=graph_config,
        retraction_config=retraction_config,
        md_generator=md_generator
    )
    
    print(" Crawler initialized with SOLID architecture")
    

    print("\n" + "=" * 70)
    print("PHASE 1: CRAWLING")
    print("=" * 70)
    
    try:
        crawler.crawl()
        print("\n Crawling completed successfully!")
    except Exception as e:
        print(f"\n Crawling failed: {e}")
        raise
    
    print("\n" + "=" * 70)
    print("PHASE 2: GENERATING MARKDOWN FILES")
    print("=" * 70)
    
    try:
        crawler.generate_markdown_files()
        print(f"\n Markdown files generated at: {storage_config.vault_folder}")
    except Exception as e:
        print(f"\n Markdown generation failed: {e}")
    

    print("\n" + "=" * 70)
    print("PHASE 3: SAVING CRAWLER STATE")
    print("=" * 70)
    
    print(f"\n Crawler object saved at:")
    print(f"   {crawler.storage_config.filepath_final_pkl}")
    
    print("\n" + "=" * 70)
    print("PHASE 4: ANALYSIS AND REPORTING")
    print("=" * 70)
    
    try:
        crawler.analyze_and_report(save_figures=True, num_topics=20)
        print("\n Analysis and reporting completed successfully!")
    except Exception as e:
        print(f"\n Analysis failed: {e}")
        raise
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE - SUMMARY")
    print("=" * 70)
    print(f" API Provider: {api_config.provider_type}")
    print(f" Topic Model: {text_config.default_topic_model_type}")
    print(f" Outputs:")
    print(f"   - PKL: {storage_config.pkl_folder}")
    print(f"   - Logs: {storage_config.log_folder}")
    print(f"   - Vault: {storage_config.vault_folder}")
    print(f"   - Reports: {storage_config.xlsx_folder}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, 
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    try:
        run_crawler_new_architecture()
    except KeyboardInterrupt:
        print("\n\n  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n{'='*70}")
        print(" ERROR OCCURRED")
        print("="*70)
        print(f"\nError: {e}\n")
        import traceback
        traceback.print_exc()
        print("="*70)