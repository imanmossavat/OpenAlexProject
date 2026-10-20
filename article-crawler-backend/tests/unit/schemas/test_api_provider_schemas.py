"""Semantic Scholar was retired (see docs/decisions/semantic-scholar-to-openalex.md).

The API must reject it explicitly instead of accepting it and failing later.
"""

import pytest
from pydantic import ValidationError

from app.schemas.seeds import PaperIDsRequest
from app.schemas.staging import MatchSelectedRequest
from app.schemas.zotero_seeds import ZoteroMatchRequest


@pytest.mark.unit
@pytest.mark.parametrize(
    "factory",
    [
        lambda p: PaperIDsRequest(paper_ids=["W123"], api_provider=p),
        lambda p: ZoteroMatchRequest(api_provider=p),
        lambda p: MatchSelectedRequest(api_provider=p),
    ],
)
def test_openalex_is_accepted(factory):
    assert factory("openalex").api_provider == "openalex"


@pytest.mark.unit
@pytest.mark.parametrize(
    "factory",
    [
        lambda p: PaperIDsRequest(paper_ids=["W123"], api_provider=p),
        lambda p: ZoteroMatchRequest(api_provider=p),
        lambda p: MatchSelectedRequest(api_provider=p),
    ],
)
def test_semantic_scholar_is_rejected(factory):
    with pytest.raises(ValidationError):
        factory("semantic_scholar")


@pytest.mark.unit
def test_default_provider_is_openalex():
    assert PaperIDsRequest(paper_ids=["W123"]).api_provider == "openalex"
    assert ZoteroMatchRequest().api_provider == "openalex"
