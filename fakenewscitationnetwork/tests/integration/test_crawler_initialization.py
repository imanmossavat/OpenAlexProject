import pytest
from unittest.mock import Mock, patch
from ArticleCrawler import Crawler
from ArticleCrawler.config.crawler_initialization import CrawlerParameters


@pytest.mark.integration
class TestCrawlerInitialization:
    
    def test_crawler_initializes_with_all_configs(
        self,
        sample_seed_papers,
        sample_keywords,
        integration_configs
    ):
        crawl_params = CrawlerParameters(
            seed_paperid=sample_seed_papers,
            keywords=sample_keywords
        )
        
        stopping_criteria_config = integration_configs.pop('stopping_config')
        
        with patch('ArticleCrawler.api.create_api_provider'):
            crawler = Crawler(
                crawl_initial_condition=crawl_params,
                stopping_criteria_config=stopping_criteria_config,
                **integration_configs
            )
            
            assert crawler.data_coordinator is not None
            assert crawler.sampler is not None
            assert crawler.text_processor is not None
    
    def test_crawler_backward_compatibility_with_old_options(
        self,
        sample_seed_papers,
        sample_keywords,
        temp_dir
    ):
        from ArticleCrawler.config.crawler_initialization import (
            SamplingOptions, TextOptions, StorageAndLoggingOptions,
            GraphOptions, RetractionOptions, StoppingOptions
        )
        
        crawl_params = CrawlerParameters(
            seed_paperid=sample_seed_papers,
            keywords=sample_keywords
        )
        
        with patch('ArticleCrawler.api.create_api_provider'):
            crawler = Crawler(
                crawl_initial_condition=crawl_params,
                stopping_criteria_config=StoppingOptions(max_iter=1),
                sampling_options=SamplingOptions(num_papers=5),
                nlp_options=TextOptions(),
                storage_and_logging_options=StorageAndLoggingOptions(root_folder=temp_dir),
                graph_options=GraphOptions(),
                retraction_options=RetractionOptions()
            )
            
            assert crawler.data_coordinator is not None