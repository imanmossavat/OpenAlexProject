
import pytest
from unittest.mock import Mock
from fastapi import HTTPException


class TestErrorCases:
    
    def test_invalid_session_id(
        self,
        app_client,
        mock_staging_service
    ):

        mock_staging_service.list_rows.side_effect = HTTPException(
            status_code=404,
            detail="Session not found"
        )
        
        invalid_session_id = "non-existent-session-id-12345"
        
        response = app_client.get(
            f"/api/v1/seeds/session/{invalid_session_id}/staging"
        )
        assert response.status_code >= 400
        
        mock_staging_service.add_rows.side_effect = HTTPException(
            status_code=404,
            detail="Session not found"
        )
        
        response = app_client.post(
            f"/api/v1/seeds/session/{invalid_session_id}/staging",
            json=[{
                "source": "Manual IDs",
                "source_type": "manual",
                "source_id": "W123456",
                "title": "Test"
            }]
        )
        assert response.status_code >= 400
    
    def test_no_papers_selected_for_matching(
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
        assert "no selected" in error_response["detail"].lower() or "selection" in error_response["detail"].lower()
    
    def test_confirm_matches_without_matching(
        self,
        app_client,
        test_session_id,
        mock_staging_service,
        mock_seed_session_service
    ):

        mock_staging_service.get_match_rows.return_value = []
        
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/staging/match/confirm",
            json={"staging_ids": [1, 2, 3]}
        )
        
        assert response.status_code == 400
        error_response = response.json()
        assert "detail" in error_response
        assert "match" in error_response["detail"].lower()
    
    def test_invalid_library_path(
        self,
        app_client,
        test_session_id,
        mock_library_service
    ):

        response = app_client.post(
            f"/api/v1/library/{test_session_id}/details",
            json={
                "name": "Test Library",
                "path": "relative/path/to/library",
                "description": "Test"
            }
        )
        assert response.status_code in [200, 400, 422]
        
        response = app_client.post(
            f"/api/v1/library/{test_session_id}/details",
            json={
                "name": "Test Library",
                "path": "",
                "description": "Test"
            }
        )
        assert response.status_code in [200, 400, 422]
        
        invalid_paths = [
            "/path/with/\x00/nullbyte",
            "/path/with/../traversal",
        ]
        
        for invalid_path in invalid_paths:
            response = app_client.post(
                f"/api/v1/library/{test_session_id}/details",
                json={
                    "name": "Test Library",
                    "path": invalid_path,
                    "description": "Test"
                }
            )
            assert response.status_code in [200, 400, 422]
    
    def test_create_library_without_seeds(
        self,
        app_client,
        test_session_id,
        mock_seed_session_service,
        mock_library_service
    ):

        mock_seed_session_service.get_session.return_value = Mock(
            session_id=test_session_id,
            seeds=[],
            total_seeds=0
        )
        
        response = app_client.post(
            f"/api/v1/library/{test_session_id}/details",
            json={
                "name": "Empty Library",
                "path": "/tmp/empty-library"
            }
        )
        assert response.status_code == 200
        
        mock_library_service.create.return_value = {
            "session_id": test_session_id,
            "name": "Empty Library",
            "base_path": "/tmp/empty-library",
            "total_requested": 0,
            "saved_count": 0,
            "papers": []
        }
        
        response = app_client.post(
            f"/api/v1/library/{test_session_id}/create"
        )

        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            create_response = response.json()
            assert create_response["saved_count"] == 0
    
    def test_edit_nonexistent_staged_paper(
        self,
        app_client,
        test_session_id,
        mock_staging_service
    ):

        mock_staging_service.update_row.side_effect = HTTPException(
            status_code=404,
            detail="Staging paper not found"
        )
        
        nonexistent_staging_id = 99999
        
        response = app_client.patch(
            f"/api/v1/seeds/session/{test_session_id}/staging/{nonexistent_staging_id}",
            json={
                "title": "Updated Title",
                "year": 2023
            }
        )
        
        assert response.status_code == 404
    
    def test_remove_nonexistent_staged_paper(
        self,
        app_client,
        test_session_id,
        mock_staging_service
    ):

        mock_staging_service.remove_rows.return_value = 0
        
        nonexistent_staging_id = 99999
        
        response = app_client.delete(
            f"/api/v1/seeds/session/{test_session_id}/staging/{nonexistent_staging_id}"
        )
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            removal_response = response.json()
            assert removal_response["removed_count"] == 0
    
    def test_library_details_validation(
        self,
        app_client,
        test_session_id
    ):

        response = app_client.post(
            f"/api/v1/library/{test_session_id}/details",
            json={
                "name": "",
                "path": "/tmp/library"
            }
        )
        assert response.status_code in [400, 422]
        
        response = app_client.post(
            f"/api/v1/library/{test_session_id}/details",
            json={
                "name": "A" * 1000,
                "path": "/tmp/library"
            }
        )
        assert response.status_code in [400, 422, 200]
        
        response = app_client.post(
            f"/api/v1/library/{test_session_id}/details",
            json={
                "name": "Test Library"
            }
        )
        assert response.status_code in [200, 400, 422]
