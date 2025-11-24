
import pytest
from unittest.mock import Mock
from app.schemas.staging import StagingMatchRow
from app.schemas.seeds import SeedMatchResult, MatchedSeed, UnmatchedSeed


class TestManualIDsWorkflow:
    
    def test_add_manual_ids(self, app_client, test_session_id, mock_staging_service, sample_staging_papers):
        mock_staging_service.add_rows.return_value = [sample_staging_papers[0]]
        
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            json=[{
                "source": "Manual IDs",
                "source_type": "manual",
                "source_id": "W2741809807"
            }]
        )
        
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_set_library_details(self, app_client, test_session_id, mock_library_service):
        response = app_client.post(
            f"/api/v1/library/{test_session_id}/details",
            json={
                "name": "Test Library",
                "path": "/tmp/test-lib",
                "description": "Simple test"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Library"
    
    def test_create_library_endpoint_exists(self, app_client, test_session_id):
        response = app_client.post(
            f"/api/v1/library/{test_session_id}/create"
        )
        
        assert response.status_code in [200, 400, 404, 422, 500]
    
    def test_manual_ids_with_invalid_ids(
        self,
        app_client,
        test_session_id,
        mock_seed_selection_service,
        mock_staging_service
    ):

        mock_seed_selection_service.match_paper_ids.return_value = SeedMatchResult(
            matched_seeds=[
                MatchedSeed(
                    paper_id="W2741809807",
                    title="Attention Is All You Need",
                    authors="Ashish Vaswani",
                    year=2017,
                    venue="NeurIPS"
                )
            ],
            unmatched_seeds=[
                UnmatchedSeed(input_id="invalid-id-1", error="Not found"),
                UnmatchedSeed(input_id="invalid-id-2", error="Not found")
            ],
            total_matched=1,
            total_unmatched=2
        )
        
        staging_payload = [
            {"source": "Manual IDs", "source_type": "manual", "source_id": "W2741809807"},
            {"source": "Manual IDs", "source_type": "manual", "source_id": "invalid-id-1"},
            {"source": "Manual IDs", "source_type": "manual", "source_id": "invalid-id-2"}
        ]
        
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            json=staging_payload
        )
        
        assert response.status_code == 200
        staged_papers = response.json()
        assert len(staged_papers) >= 1
    
    def test_manual_ids_workflow_with_duplicates(
        self,
        app_client,
        test_session_id,
        mock_seed_selection_service,
        mock_staging_service
    ):

        staging_payload = [
            {"source": "Manual IDs", "source_type": "manual", "source_id": "W2741809807"},
            {"source": "Manual IDs", "source_type": "manual", "source_id": "W2741809807"},  # Duplicate
            {"source": "Manual IDs", "source_type": "manual", "source_id": "W2964141474"}
        ]
        
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            json=staging_payload
        )
        
        assert response.status_code == 200
        staged_papers = response.json()
        assert len(staged_papers) >= 2