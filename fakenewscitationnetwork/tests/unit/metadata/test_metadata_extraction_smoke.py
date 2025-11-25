import importlib.util
import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = PROJECT_ROOT / "fakenewscitationnetwork" / "ArticleCrawler"
SAMPLES_DIR = PROJECT_ROOT / "testfilesDifferentfiletypes"


def load_module(relative_path: str, module_name: str):
    """Load module without triggering ArticleCrawler __init__ side effects."""
    module_path = PACKAGE_ROOT / relative_path
    pkg_name = "metadata_extraction"
    subpkg_name = f"{pkg_name}.extractors"

    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(PACKAGE_ROOT / "metadata_extraction")]
        sys.modules[pkg_name] = pkg
    if subpkg_name not in sys.modules:
        subpkg = types.ModuleType(subpkg_name)
        subpkg.__path__ = [str(PACKAGE_ROOT / "metadata_extraction" / "extractors")]
        sys.modules[subpkg_name] = subpkg

    qualified_name = f"{subpkg_name}.{module_name}"
    spec = importlib.util.spec_from_file_location(qualified_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_docx_extractor_smoke():
    pytest.importorskip("docx")
    module = load_module(
        "metadata_extraction/extractors/docx_extractor.py", "docx_extractor"
    )
    extractor = module.DocxExtractor()
    sample = SAMPLES_DIR / "test.docx"
    metadata = extractor.extract(str(sample))
    assert metadata.title


def test_html_extractor_smoke():
    pytest.importorskip("bs4")
    module = load_module(
        "metadata_extraction/extractors/html_extractor.py", "html_extractor"
    )
    extractor = module.HtmlExtractor()
    sample = SAMPLES_DIR / "test.html"
    metadata = extractor.extract(str(sample))
    assert metadata.title


def test_xml_extractor_smoke():
    module = load_module(
        "metadata_extraction/extractors/xml_extractor.py", "xml_extractor"
    )
    extractor = module.XmlExtractor()
    sample = SAMPLES_DIR / "test.xml"
    metadata = extractor.extract(str(sample))
    assert metadata.title


def test_latex_extractor_smoke():
    pytest.importorskip("pylatexenc")
    module = load_module(
        "metadata_extraction/extractors/latex_extractor.py", "latex_extractor"
    )
    extractor = module.LatexExtractor()
    sample = SAMPLES_DIR / "test.tex"
    metadata = extractor.extract(str(sample))
    assert metadata.title
