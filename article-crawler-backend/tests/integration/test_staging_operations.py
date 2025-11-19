
import pytest
from unittest.mock import Mock

from app.schemas.staging import StagingListResponse


def _build_list_response(
    session_id: str,
    rows,
    *,
    total_rows: int | None = None,
    selected_count: int = 0,
    page: int = 1,
    page_size: int = 25,
):
    total_rows = total_rows if total_rows is not None else len(rows)
    filtered_rows = total_rows
    total_pages = max(1, (total_rows + page_size - 1) // max(1, page_size))
    return StagingListResponse(
        session_id=session_id,
        rows=rows,
        total_rows=total_rows,
        filtered_rows=filtered_rows,
        selected_count=selected_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


class TestStagingOperations:
    """Test staging table filtering, pagination, editing, and selection."""
    
    def test_staging_pagination_and_filtering(
        self,
        app_client,
        test_session_id,
        mock_staging_service,
        sample_staging_papers
    ):

        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            sample_staging_papers,
            total_rows=50,
            selected_count=0,
            page=1,
            page_size=25,
        )
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"page": 1, "page_size": 25}
        )
        assert response.status_code == 200
        page1_data = response.json()
        assert page1_data["page"] == 1
        assert page1_data["total_rows"] == 50
        
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            sample_staging_papers,
            total_rows=50,
            selected_count=0,
            page=2,
            page_size=25,
        )
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"page": 2, "page_size": 25}
        )
        assert response.status_code == 200
        page2_data = response.json()
        assert page2_data["page"] == 2
        
        filtered_papers = [p for p in sample_staging_papers if p.year and 2015 <= p.year <= 2020]
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            filtered_papers,
            total_rows=len(filtered_papers),
            selected_count=0,
            page=1,
            page_size=25,
        )
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"year_min": 2015, "year_max": 2020}
        )
        assert response.status_code == 200
        year_filtered = response.json()
        assert all(
            row["year"] is None or (2015 <= row["year"] <= 2020)
            for row in year_filtered["rows"]
        )
        
        papers_with_doi = [p for p in sample_staging_papers if p.doi]
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            papers_with_doi,
            total_rows=len(papers_with_doi),
            selected_count=0,
            page=1,
            page_size=25,
        )
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"doi_presence": "with"}
        )
        assert response.status_code == 200
        doi_filtered = response.json()
        assert all(row["doi"] is not None for row in doi_filtered["rows"])
        
        papers_without_doi = [p for p in sample_staging_papers if not p.doi]
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            papers_without_doi,
            total_rows=len(papers_without_doi),
            selected_count=0,
            page=1,
            page_size=25,
        )
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"doi_presence": "without"}
        )
        assert response.status_code == 200
        no_doi_filtered = response.json()
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"title": "Attention"}
        )
        assert response.status_code == 200
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"author": "Vaswani"}
        )
        assert response.status_code == 200
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"keyword": "transformer"}
        )
        assert response.status_code == 200
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"venue": "NeurIPS"}
        )
        assert response.status_code == 200
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={
                "year_min": 2017,
                "year_max": 2019,
                "doi_presence": "with",
                "keyword": "deep learning"
            }
        )
        assert response.status_code == 200
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"selected_only": True}
        )
        assert response.status_code == 200
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"sort_by": "year", "sort_dir": "desc"}
        )
        assert response.status_code == 200
    
    def test_staging_inline_editing(
        self,
        app_client,
        test_session_id,
        mock_staging_service,
        sample_staging_papers
    ):
        staging_id = 1
        original_paper = sample_staging_papers[0]
        
        edit_payload = {
            "title": "Updated Paper Title",
            "authors": "New Author, Another Author",
            "year": 2023,
            "venue": "Updated Conference",
            "doi": "10.1234/updated.doi"
        }
        
        updated_paper = original_paper.model_copy(update=edit_payload)
        mock_staging_service.update_row.return_value = updated_paper
        
        response = app_client.patch(
            f"/api/v1/seeds/session/{test_session_id}/staging/{staging_id}",
            json=edit_payload
        )
        assert response.status_code == 200
        updated_data = response.json()
        assert updated_data["title"] == edit_payload["title"]
        assert updated_data["authors"] == edit_payload["authors"]
        assert updated_data["year"] == edit_payload["year"]
        assert updated_data["doi"] == edit_payload["doi"]
        
        mock_staging_service.update_row.assert_called_once()
    
    def test_staging_selection_updates(
        self,
        app_client,
        test_session_id,
        mock_staging_service
    ):

        staging_ids = [1, 2, 3, 4, 5]
        mock_staging_service.set_selection.return_value = len(staging_ids)
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            [],
            total_rows=10,
            selected_count=5,
        )
        
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/staging/select",
            json={
                "staging_ids": staging_ids,
                "is_selected": True
            }
        )
        assert response.status_code == 200
        selection_response = response.json()
        assert selection_response["updated_count"] == 5
        assert selection_response["selected_count"] == 5
        
        deselect_ids = [1, 2]
        mock_staging_service.set_selection.return_value = len(deselect_ids)
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            [],
            total_rows=10,
            selected_count=3,
        )
        
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/staging/select",
            json={
                "staging_ids": deselect_ids,
                "is_selected": False
            }
        )
        assert response.status_code == 200
        deselection_response = response.json()
        assert deselection_response["updated_count"] == 2
        assert deselection_response["selected_count"] == 3
    
    def test_staging_bulk_removal(
        self,
        app_client,
        test_session_id,
        mock_staging_service
    ):

        initial_total = 10
        
        staging_ids_to_remove = [3, 5, 7]
        mock_staging_service.remove_rows.return_value = len(staging_ids_to_remove)
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            [],
            total_rows=initial_total - len(staging_ids_to_remove),
        )
        
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/staging/remove",
            json={"staging_ids": staging_ids_to_remove}
        )
        assert response.status_code == 200
        removal_response = response.json()
        assert removal_response["removed_count"] == 3
        assert removal_response["total_rows"] == 7
        
        staging_id_to_remove = 1
        mock_staging_service.remove_rows.return_value = 1
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            [],
            total_rows=6,
        )
        
        response = app_client.delete(
            f"/api/v1/seeds/session/{test_session_id}/staging/{staging_id_to_remove}"
        )
        assert response.status_code == 200
        single_removal = response.json()
        assert single_removal["removed_count"] == 1
        assert single_removal["total_rows"] == 6
        
        mock_staging_service.clear_session = Mock()
        
        response = app_client.delete(
            f"/api/v1/seeds/session/{test_session_id}/staging"
        )
        assert response.status_code == 200
        clear_response = response.json()
        assert "message" in clear_response
        mock_staging_service.clear_session.assert_called_once_with(test_session_id)
