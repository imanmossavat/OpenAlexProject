"""Helpers for features that depend on optional, heavy packages.

The recommender / title-similarity features need ``torch`` and
``sentence-transformers`` (several GB). Nothing else in the project does, so
they live behind the ``ml`` extra and are imported only when actually used:

    pip install -e "fakenewscitationnetwork[ml]"
"""

from __future__ import annotations

import importlib
from types import ModuleType

ML_EXTRA_HINT = 'pip install -e "fakenewscitationnetwork[ml]"   (or: pip install -r requirements-ml.txt)'


def import_ml_dependency(module_name: str, feature: str) -> ModuleType:
    """Import an optional ML module, raising a helpful error if it is missing."""
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:  # pragma: no cover - message formatting only
        raise ImportError(
            f"{feature} requires the optional package '{module_name}', which is not installed.\n"
            f"Install the ML extras with:\n    {ML_EXTRA_HINT}"
        ) from exc
