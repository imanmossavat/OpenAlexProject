import sys
from pathlib import Path
import pytest

THIS_FILE = Path(__file__).resolve()

REPO_ROOT = THIS_FILE.parents[4]
sys.path.insert(0, str(REPO_ROOT))

SAMPLES_DIR = REPO_ROOT / "testfilesDifferentfiletypes"

from fakenewscitationnetwork.ArticleCrawler.metadata_extraction.extractors import (
    DocxExtractor,
    HtmlExtractor,
    XmlExtractor,
    LatexExtractor,
)


def test_docx_extractor_smoke():
    pytest.importorskip("docx")
    sample = SAMPLES_DIR / "test.docx"
    extractor = DocxExtractor()
    metadata = extractor.extract(str(sample))
    assert metadata.title


def test_html_extractor_smoke():
    pytest.importorskip("bs4")
    sample = SAMPLES_DIR / "test.html"
    extractor = HtmlExtractor()
    metadata = extractor.extract(str(sample))
    assert metadata.title


def test_xml_extractor_smoke():
    sample = SAMPLES_DIR / "test.xml"
    extractor = XmlExtractor()
    metadata = extractor.extract(str(sample))
    assert metadata.title


def test_latex_extractor_smoke():
    pytest.importorskip("pylatexenc")
    sample = SAMPLES_DIR / "test.tex"
    extractor = LatexExtractor()
    metadata = extractor.extract(str(sample))
    assert metadata.title
