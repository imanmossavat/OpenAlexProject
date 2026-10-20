"""Guard against heavy / desktop-only dependencies creeping back into import time.

`import ArticleCrawler` must work on a headless server without the optional ML
stack (torch, sentence-transformers) or a desktop GUI library (tkinter). The
checks run in a fresh subprocess so modules already imported by other tests
cannot hide a regression.
"""

import subprocess
import sys
import textwrap

import pytest

from ArticleCrawler.utils.optional_dependencies import import_ml_dependency


def _run(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.unit
def test_package_import_does_not_load_ml_stack():
    result = _run(
        """
        import sys
        import ArticleCrawler
        loaded = [m for m in ("torch", "sentence_transformers", "transformers") if m in sys.modules]
        assert not loaded, f"ML modules imported at package import time: {loaded}"
        """
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.unit
def test_cli_import_does_not_load_tkinter():
    result = _run(
        """
        import sys
        import ArticleCrawler.cli.ui.pdf_ui_helpers
        assert "tkinter" not in sys.modules, "tkinter imported at module import time"
        """
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.unit
def test_lazy_ml_exports_are_still_resolvable_by_name():
    import ArticleCrawler

    for name in ("TitleSimilarityEngine", "PaperRecommender", "RecommenderEmbeddingModel"):
        assert name in ArticleCrawler._LAZY_ML_EXPORTS


@pytest.mark.unit
def test_unknown_package_attribute_still_raises_attribute_error():
    import ArticleCrawler

    with pytest.raises(AttributeError):
        ArticleCrawler.this_does_not_exist


@pytest.mark.unit
def test_missing_ml_dependency_gives_actionable_error():
    with pytest.raises(ImportError, match=r"\[ml\]"):
        import_ml_dependency("definitely_not_an_installed_module_xyz", "SomeFeature")
