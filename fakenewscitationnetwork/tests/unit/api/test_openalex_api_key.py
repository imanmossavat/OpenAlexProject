import pyalex
import pytest
from unittest.mock import MagicMock, patch

from ArticleCrawler.api.openalex_api import OpenAlexAPIProvider


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.setattr("ArticleCrawler.api.openalex_api.load_dotenv", lambda *a, **k: None)
    for name in ("OPENALEX_EMAIL", "OPENALEX_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    old = (pyalex.config.email, pyalex.config.api_key)
    yield
    pyalex.config.email, pyalex.config.api_key = old


@pytest.mark.unit
def test_requires_key_or_email():
    with pytest.raises(ValueError, match="OPENALEX_API_KEY"):
        OpenAlexAPIProvider()


@pytest.mark.unit
def test_key_alone_is_enough_and_configures_pyalex(monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", "k123")
    OpenAlexAPIProvider()
    assert pyalex.config.api_key == "k123"


@pytest.mark.unit
def test_email_only_still_works(monkeypatch):
    monkeypatch.setenv("OPENALEX_EMAIL", "a@b.c")
    provider = OpenAlexAPIProvider()
    assert provider._api_key is None


@pytest.mark.unit
def test_direct_requests_send_bearer_key(monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", "k123")
    provider = OpenAlexAPIProvider()
    provider._rate_limit = lambda: None
    response = MagicMock()
    response.json.return_value = {"results": [], "meta": {"count": 0}}
    with patch("ArticleCrawler.api.openalex_api.requests.get", return_value=response) as get:
        provider._fetch_paginated_works("doi:10.1/x", 1, 25)
    assert get.call_args.kwargs["headers"] == {"Authorization": "Bearer k123"}
