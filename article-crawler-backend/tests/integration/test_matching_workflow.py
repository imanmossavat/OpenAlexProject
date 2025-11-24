
import pytest
from app.schemas.staging import StagingMatchRow
from unittest.mock import Mock
from app.schemas.seeds import SeedMatchResult, UnmatchedSeed


class TestMatchingWorkflow:
    
    def test_matching_needs_selection(self, app_client, test_session_id, mock_staging_service):
        mock_staging_service.get_selected_rows.return_value = []
        
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/staging/match",
            json={"api_provider": "openalex"}
        )
        
        assert response.status_code == 400
        assert "no selected" in response.json()["detail"].lower()
    
    def test_selection_works(self, app_client, test_session_id, mock_staging_service):
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/staging/select",
            json={"staging_ids": [1, 2, 3], "is_selected": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "updated_count" in data
    
    def test_edit_staged_paper(self, app_client, test_session_id, mock_staging_service, sample_staging_papers):
        mock_staging_service.get_row.return_value = sample_staging_papers[0]
        mock_staging_service.update_row.return_value = sample_staging_papers[0]
        
        response = app_client.patch(
            f"/api/v1/seeds/session/{test_session_id}/staging/1",
            json={"title": "Updated Title", "year": 2023}
        )
        
        assert response.status_code == 200
    
    def test_match_with_no_selection_error(
        self,
        app_client,
        test_session_id,
        mock_staging_service
    ):

        mock_staging_service.get_selected_rows.return_value = []
        
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/staging/match",
            json={"api_provider": "openalex"}
        )
        
        assert response.status_code == 400
        error_response = response.json()
        assert "detail" in error_response
        assert "no selected" in error_response["detail"].lower()
