
import pytest


class TestZoteroWorkflow:
    
    
    
    def test_zotero_workflow_with_filtering(
        self,
        app_client,
        test_session_id,
        mock_zotero_service,
        mock_staging_service
    ):

        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/zotero/collections/ABC123/stage",
            json={"action": "stage_all"}
        )
        assert response.status_code == 200
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={
                "year_min": 2015,
                "year_max": 2020,
                "sources": ["zotero"]
            }
        )
        assert response.status_code == 200
        filtered_response = response.json()
        assert "rows" in filtered_response
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={
                "keyword": "machine learning",
                "sources": ["zotero"]
            }
        )
        assert response.status_code == 200
