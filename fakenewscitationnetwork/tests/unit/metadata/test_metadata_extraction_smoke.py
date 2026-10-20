"""Smoke tests for the non-PDF metadata extractors.

The sample documents are generated into a temp directory at test time, so the
tests do not depend on binary fixtures being committed to the repository.
"""

import sys
from pathlib import Path

import pytest

THIS_FILE = Path(__file__).resolve()

REPO_ROOT = THIS_FILE.parents[4]
sys.path.insert(0, str(REPO_ROOT))

from fakenewscitationnetwork.ArticleCrawler.metadata_extraction.extractors import (
    DocxExtractor,
    HtmlExtractor,
    XmlExtractor,
    LatexExtractor,
)

TITLE = "Spread of Misinformation on Social Networks"
DOI = "10.1234/example.2024.001"


@pytest.fixture(scope="module")
def samples(tmp_path_factory):
    """Create one tiny sample document per supported format."""
    d = tmp_path_factory.mktemp("metadata_samples")

    (d / "test.html").write_text(
        f"""<html><head>
<title>ignored fallback</title>
<meta name="citation_title" content="{TITLE}">
<meta name="citation_author" content="Ada Lovelace">
<meta name="citation_doi" content="{DOI}">
<meta name="citation_journal_title" content="Journal of Tests">
</head><body><div id="abstract">A short abstract about testing.</div></body></html>""",
        encoding="utf-8",
    )

    (d / "test.xml").write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<article>
  <front>
    <journal-meta><journal-title-group><journal-title>Journal of Tests</journal-title></journal-title-group></journal-meta>
    <article-meta>
      <article-id pub-id-type="doi">{DOI}</article-id>
      <title-group><article-title>{TITLE}</article-title></title-group>
      <contrib-group><contrib contrib-type="author"><name><surname>Lovelace</surname><given-names>Ada</given-names></name></contrib></contrib-group>
      <pub-date><year>2024</year></pub-date>
      <abstract><p>A short abstract about testing.</p></abstract>
    </article-meta>
  </front>
</article>""",
        encoding="utf-8",
    )

    (d / "test.tex").write_text(
        "\\documentclass{article}\n"
        f"\\title{{{TITLE}}}\n"
        "\\author{Ada Lovelace}\n"
        "\\date{2024}\n"
        "\\begin{document}\n\\maketitle\n"
        "\\begin{abstract}A short abstract about testing.\\end{abstract}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )

    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_paragraph(TITLE)
    document.add_paragraph("Ada Lovelace")
    document.add_paragraph("A short abstract about testing.")
    document.save(str(d / "test.docx"))

    return d


def test_docx_extractor_smoke(samples):
    metadata = DocxExtractor().extract(str(samples / "test.docx"))
    assert metadata.title == TITLE


def test_html_extractor_smoke(samples):
    pytest.importorskip("bs4")
    metadata = HtmlExtractor().extract(str(samples / "test.html"))
    assert metadata.title == TITLE
    assert metadata.doi == DOI


def test_xml_extractor_smoke(samples):
    metadata = XmlExtractor().extract(str(samples / "test.xml"))
    assert metadata.title == TITLE
    assert metadata.doi == DOI
    assert metadata.authors == ["Ada Lovelace"]


def test_latex_extractor_smoke(samples):
    pytest.importorskip("pylatexenc")
    metadata = LatexExtractor().extract(str(samples / "test.tex"))
    assert metadata.title == TITLE


def test_missing_file_returns_empty_metadata(tmp_path):
    """Extractors should degrade gracefully (not raise) on a missing file."""
    metadata = XmlExtractor().extract(str(tmp_path / "does-not-exist.xml"))
    assert metadata.title is None
