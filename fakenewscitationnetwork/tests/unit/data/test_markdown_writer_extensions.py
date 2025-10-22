# tests/unit/data/test_markdown_writer_extensions.py (COMPLETE FIX)

import pytest
from pathlib import Path
from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
from ArticleCrawler.library.models import PaperData


@pytest.mark.unit
class TestMarkdownWriterExtensions:
    
    @pytest.fixture
    def storage_config(self, temp_dir):
        class SimpleConfig:
            def __init__(self):
                self.experiment_file_name = 'library'
                self.vault_folder = temp_dir
                self.abstracts_folder = temp_dir / "abstracts"
                self.figure_folder = temp_dir / "figures"
                self.metadata_folder = temp_dir / "metadata"
                self.summary_folder = temp_dir / "summary"
                self.open_vault_folder = False
        return SimpleConfig()
    
    @pytest.fixture
    def markdown_writer(self, storage_config):
        return MarkdownFileGenerator(
            storage_and_logging_options=storage_config,
            api_provider_type='openalex'
        )
    
    @pytest.fixture
    def sample_paper_data(self):
        return PaperData(
            paper_id="W123456",
            title="Test Paper Title",
            authors=[
                {'authorId': 'A123', 'name': 'John Doe'},
                {'authorId': 'A456', 'name': 'Jane Smith'}
            ],
            year=2024,
            venue="Test Conference",
            doi="10.1234/test.2024",
            abstract="This is a test abstract for the paper.",
            url="https://openalex.org/W123456",
            concepts=[
                {'id': 'C123', 'display_name': 'Machine Learning', 'level': 2, 'score': 0.95}
            ],
            topics=[
                {'id': 'T123', 'display_name': 'Deep Learning', 'score': 0.9}
            ],
            fields=[
                {'id': 'F123', 'display_name': 'Computer Science'}
            ]
        )
    
    def test_create_paper_markdown_with_openalex_metadata(self, markdown_writer, sample_paper_data, temp_dir):
        output_path = temp_dir / "test_paper.md"
        
        result_path = markdown_writer.create_paper_markdown_with_openalex_metadata(
            paper_data=sample_paper_data,
            output_path=output_path
        )
        
        assert result_path.exists()
        content = result_path.read_text(encoding='utf-8')
        assert "paper_id: W123456" in content
        assert "Test Paper Title" in content
        assert "John Doe" in content
    
    def test_create_openalex_frontmatter(self, markdown_writer, sample_paper_data):
        frontmatter = markdown_writer._create_openalex_frontmatter(sample_paper_data)
        
        assert "paper_id: W123456" in frontmatter
        assert "title: Test Paper Title" in frontmatter
        assert "year: 2024" in frontmatter
        assert "John Doe" in frontmatter
        assert "concepts:" in frontmatter
        assert "Machine Learning" in frontmatter
    
    def test_create_openalex_frontmatter_minimal(self, markdown_writer):
        minimal_paper = PaperData(
            paper_id="W999",
            title="Minimal Paper",
            authors=[]
        )
        
        frontmatter = markdown_writer._create_openalex_frontmatter(minimal_paper)
        
        assert "paper_id: W999" in frontmatter
        assert "title: Minimal Paper" in frontmatter
    
    def test_create_paper_body_with_openalex(self, markdown_writer, sample_paper_data):
        body = markdown_writer._create_paper_body_with_openalex(sample_paper_data)
        
        assert "# [Test Paper Title]" in body
        assert "**Authors**: John Doe, Jane Smith" in body
        assert "**Year**: 2024" in body
        assert "**Venue**: Test Conference" in body
        assert "## Abstract" in body
        assert "This is a test abstract" in body
        assert "## Concepts" in body
        assert "Machine Learning" in body
    
    def test_create_paper_body_no_abstract(self, markdown_writer):
        paper = PaperData(
            paper_id="W111",
            title="No Abstract Paper",
            authors=[]
        )
        
        body = markdown_writer._create_paper_body_with_openalex(paper)
        
        assert "## Abstract" in body
        assert "*No abstract available*" in body
    
    def test_create_paper_body_with_topics(self, markdown_writer, sample_paper_data):
        body = markdown_writer._create_paper_body_with_openalex(sample_paper_data)
        
        assert "## Topics" in body
        assert "Deep Learning" in body
    
    def test_create_paper_body_with_fields(self, markdown_writer, sample_paper_data):
        body = markdown_writer._create_paper_body_with_openalex(sample_paper_data)
        
        assert "## Fields" in body
        assert "Computer Science" in body