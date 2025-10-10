
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from ArticleCrawler.usecases.topic_modeling_usecase import TopicModelingOrchestrator
from ArticleCrawler.library.library_manager import LibraryManager
from ArticleCrawler.library.paper_file_reader import PaperFileReader
from ArticleCrawler.library.models import PaperData, LibraryConfig


@pytest.mark.integration
class TestTopicModelingIntegration:
    
    @pytest.fixture
    def library_manager(self, mock_logger):
        return LibraryManager(logger=mock_logger)
    
    @pytest.fixture
    def paper_reader(self, mock_logger):
        return PaperFileReader(logger=mock_logger)
    
    @pytest.fixture
    def sample_library(self, temp_dir, library_manager):
        library_path = temp_dir / "test_library"
        library_manager.create_library_structure(library_path, "test_library")
        
        config = LibraryConfig(
            name="test_library",
            base_path=library_path
        )
        library_manager.save_library_config(config)
        
        papers_dir = library_manager.get_papers_directory(library_path)
        
        for i in range(5):
            paper_content = f"""---
paper_id: W{i}
title: Paper {i}
authors: []
abstract: This is test abstract number {i} about machine learning and neural networks.
concepts:
  - id: C1
    display_name: Machine Learning
    level: 2
    score: 0.9
---

# Paper {i}

## Abstract

This is test abstract number {i} about machine learning.
"""
            (papers_dir / f"paper{i}.md").write_text(paper_content)
        
        return library_path
    
    def test_topic_modeling_full_workflow(self, sample_library, library_manager, paper_reader, mock_logger):
        import pandas as pd
        
        with patch('ArticleCrawler.usecases.topic_modeling_usecase.TextPreProcessing') as mock_preprocessor_class:
            with patch('ArticleCrawler.usecases.topic_modeling_usecase.TextTransformation') as mock_vectorizer_class:
                with patch('ArticleCrawler.usecases.topic_modeling_usecase.TopicModeling') as mock_topic_model_class:
                    with patch('ArticleCrawler.usecases.topic_modeling_usecase.TopicLabeler') as mock_labeler_class:
                        mock_preprocessor = Mock()
                        mock_preprocessor.process_abstracts.return_value = pd.DataFrame({
                            'paperId': ['W0', 'W1', 'W2', 'W3', 'W4'],
                            'abstract': ['abstract'] * 5
                        })
                        mock_preprocessor.filter_and_stem_abstracts_by_language.return_value = pd.DataFrame({
                            'paperId': ['W0', 'W1', 'W2', 'W3', 'W4'],
                            'abstract': ['abstract'] * 5
                        })
                        mock_preprocessor_class.return_value = mock_preprocessor
                        
                        mock_vectorizer = Mock()
                        mock_vectorizer_class.return_value = mock_vectorizer
                        
                        mock_model_instance = Mock()
                        mock_model_instance.results = {
                            'NMF': {
                                'assignments': [0, 0, 1, 1, 0],
                                'top_words': {0: ['word1'], 1: ['word2']}
                            }
                        }
                        mock_topic_model_class.return_value = mock_model_instance
                        
                        from ArticleCrawler.library.models import TopicCluster
                        mock_clusters = [
                            TopicCluster(cluster_id=0, label="Topic 1", paper_ids=["W0", "W1", "W4"]),
                            TopicCluster(cluster_id=1, label="Topic 2", paper_ids=["W2", "W3"])
                        ]
                        mock_labeler_instance = Mock()
                        mock_labeler_instance.label_clusters.return_value = mock_clusters
                        mock_labeler_class.return_value = mock_labeler_instance
                        
                        orchestrator = TopicModelingOrchestrator(
                            library_manager=library_manager,
                            paper_reader=paper_reader,
                            logger=mock_logger
                        )
                        
                        with patch.object(orchestrator, '_organize_papers_by_topics'):
                            clusters = orchestrator.run_topic_modeling(
                                library_path=sample_library,
                                model_type='NMF'
                            )
                        
                        assert len(clusters) == 2