from app.schemas.papers import (
    ColumnOptionsPage,
    PaginatedPaperSummaries,
    PaperDetail,
    PaperMarkResponse,
    PaperSummary,
)
from app.schemas.staging import ColumnFilterOption


def test_list_catalog_papers(
    app_client,
    mock_paper_catalog_service,
    mock_crawler_execution_service,
):
    sample = PaginatedPaperSummaries(
        page=1,
        page_size=25,
        total=2,
        papers=[
            PaperSummary(
                paper_id="W123",
                title="Transformer Advances",
                authors=["Alice"],
                venue="MLConf",
                year=2022,
                doi="10.1000/abc",
                url="https://example.org/W123",
                citation_count=20,
                centrality_in=0.3,
                centrality_out=0.6,
                is_seed=False,
                is_retracted=False,
                selected=False,
                mark="good",
                nmf_topic=1,
                lda_topic=None,
                topics=["nmf_topic:1"],
            )
        ],
        column_options={
            "title": [ColumnFilterOption(value="Transformer Advances", label="Transformer Advances", count=1)]
        },
    )
    mock_paper_catalog_service.list_papers.return_value = sample

    response = app_client.get("/api/v1/crawler/jobs/job_sample/papers")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["papers"][0]["paper_id"] == "W123"
    mock_paper_catalog_service.list_papers.assert_called_once()
    mock_crawler_execution_service.get_job_status.assert_called_with("job_sample")


def test_list_column_options(
    app_client,
    mock_paper_catalog_service,
):
    options_page = ColumnOptionsPage(
        column="title",
        page=1,
        page_size=50,
        total=1,
        options=[ColumnFilterOption(value="foo", label="Foo", count=2)],
    )
    mock_paper_catalog_service.list_column_options.return_value = options_page

    response = app_client.get(
        "/api/v1/crawler/jobs/job_sample/papers/column-options",
        params={"column": "title"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["options"][0]["label"] == "Foo"
    mock_paper_catalog_service.list_column_options.assert_called_once()


def test_export_catalog(
    app_client,
    mock_paper_catalog_service,
):
    mock_paper_catalog_service.export_catalog.return_value = b"excel"

    response = app_client.get("/api/v1/crawler/jobs/job_sample/papers/export")

    assert response.status_code == 200
    assert response.content == b"excel"
    assert "attachment; filename=\"job_sample_papers.xlsx\"" in response.headers["content-disposition"]
    mock_paper_catalog_service.export_catalog.assert_called_once_with("job_sample")


def test_update_paper_mark(
    app_client,
    mock_paper_catalog_service,
):
    mock_paper_catalog_service.update_mark.return_value = PaperMarkResponse(
        paper_id="W123",
        mark="neutral",
    )

    response = app_client.post(
        "/api/v1/crawler/jobs/job_sample/papers/W123/mark",
        json={"mark": "neutral"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["paper_id"] == "W123"
    assert payload["mark"] == "neutral"
    mock_paper_catalog_service.update_mark.assert_called_once_with("job_sample", "W123", "neutral")


def test_get_paper_metadata(
    app_client,
    mock_paper_metadata_service,
):
    detail = PaperDetail(
        paper_id="W789",
        title="Graph Research",
        abstract=None,
        authors=["Bob"],
        institutions=["Example Institute"],
        year=2023,
        venue="GraphConf",
        doi="10.2222/graph",
        url="https://example.org/W789",
        cited_by_count=3,
        references_count=12,
    )
    mock_paper_metadata_service.get_paper_details.return_value = detail

    response = app_client.get("/api/v1/papers/W789")

    assert response.status_code == 200
    payload = response.json()
    assert payload["paper_id"] == "W789"
    assert payload["title"] == "Graph Research"
    mock_paper_metadata_service.get_paper_details.assert_called_once_with("W789")
