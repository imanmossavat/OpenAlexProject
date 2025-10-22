import pytest
import pandas as pd
from unittest.mock import Mock
from ArticleCrawler.data.metadata_parser import MetadataParser, paper2dict
from ArticleCrawler.data.data_frame_store import DataFrameStore
from ArticleCrawler.data.frame_manager import AcademicFeatureComputer


@pytest.mark.unit
class TestMetadataParser:
    
    @pytest.fixture
    def parser(self, empty_data_frame_store, mock_logger):
        feature_computer = AcademicFeatureComputer()
        return MetadataParser(empty_data_frame_store, feature_computer, mock_logger)
    
    def test_parse_metadata_adds_new_papers(self, parser, sample_paper_object):
        initial_count = len(parser.store.df_paper_metadata)
        parser.parse_metadata([sample_paper_object], processed=True)
        assert len(parser.store.df_paper_metadata) == initial_count + 1
    
    def test_parse_metadata_does_not_duplicate_existing_papers(self, parser, sample_paper_object):
        parser.parse_metadata([sample_paper_object], processed=True)
        initial_count = len(parser.store.df_paper_metadata)
        parser.parse_metadata([sample_paper_object], processed=True)
        assert len(parser.store.df_paper_metadata) == initial_count
    
    def test_parse_metadata_sets_processed_flag(self, parser, sample_paper_object):
        parser.parse_metadata([sample_paper_object], processed=True)
        paper_row = parser.store.df_paper_metadata[
            parser.store.df_paper_metadata['paperId'] == sample_paper_object.paperId
        ]
        assert paper_row['processed'].iloc[0] == True
    
    def test_parse_author_extracts_authors_from_paper(self, parser, sample_paper_object):
        parser.parse_author([sample_paper_object])
        assert len(parser.store.df_author) > 0
        assert len(parser.store.df_paper_author) > 0
    
    def test_parse_author_removes_duplicates(self, parser, sample_paper_object):
        parser.parse_author([sample_paper_object])
        initial_count = len(parser.store.df_author)
        parser.parse_author([sample_paper_object])
        assert len(parser.store.df_author) == initial_count
    
    def test_parse_citations_adds_citations(self, parser, sample_paper_object, paper_validator):
        citation = Mock()
        citation.paperId = 'W999'
        citation.title = 'Citing Paper'
        citation.authors = []
        citation.citations = []
        citation.references = []
        sample_paper_object.citations = [citation]
        
        parser.parse_citations([sample_paper_object], paper_validator)
        assert len(parser.store.df_paper_citations) > 0
    
    def test_parse_references_adds_references(self, parser, sample_paper_object, paper_validator):
        reference = Mock()
        reference.paperId = 'W888'
        reference.title = 'Referenced Paper'
        reference.authors = []
        reference.citations = []
        reference.references = []
        sample_paper_object.references = [reference]
        
        parser.parse_references([sample_paper_object], paper_validator)
        assert len(parser.store.df_paper_references) > 0
    
    def test_parse_abstracts_adds_non_empty_abstracts(self, parser, sample_paper_object):
        parser.parse_abstracts([sample_paper_object])
        assert len(parser.store.df_abstract) > 0
        assert sample_paper_object.paperId in parser.store.df_abstract['paperId'].values
    
    def test_parse_abstracts_skips_none_abstracts(self, parser, sample_paper_without_abstract):
        parser.parse_abstracts([sample_paper_without_abstract])
        assert sample_paper_without_abstract.paperId not in parser.store.df_abstract['paperId'].values
    
    def test_compute_features_creates_citations_df(self, parser, sample_paper_metadata_df):
        parser.store.df_paper_metadata = sample_paper_metadata_df
        parser.compute_features()
        assert 'df_citations' in dir(parser.store)


@pytest.mark.unit
class TestPaper2Dict:
    
    def test_paper2dict_converts_paper_to_dict(self, sample_paper_object):
        columns = ['paperId', 'title', 'venue', 'year', 'processed']
        result = paper2dict(sample_paper_object, processed=True, columns=columns)
        assert isinstance(result, dict)
        assert result['paperId'] == sample_paper_object.paperId
        assert result['processed'] == True
    
    def test_paper2dict_handles_missing_columns(self, sample_paper_object):
        columns = ['paperId', 'title', 'nonexistent_field']
        result = paper2dict(sample_paper_object, processed=False, columns=columns)
        assert result['nonexistent_field'] == '' 
