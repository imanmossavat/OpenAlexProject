
import pytest
from io import BytesIO

from app.schemas.staging import StagingListResponse


def _build_list_response(session_id: str, rows):
    total_rows = len(rows)
    return StagingListResponse(
        session_id=session_id,
        rows=rows,
        total_rows=total_rows,
        filtered_rows=total_rows,
        selected_count=0,
        page=1,
        page_size=25,
        total_pages=1,
    )


class TestMixedSourcesWorkflow:
    
    
    def test_mixed_sources_with_source_filtering(
        self,
        app_client,
        test_session_id,
        mock_staging_service,
        sample_staging_papers
    ):

        manual_papers = [p for p in sample_staging_papers if p.source == "manual"]
        pdf_papers = [p for p in sample_staging_papers if p.source == "pdf"]
        zotero_papers = [p for p in sample_staging_papers if p.source == "zotero"]
        
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            manual_papers,
        )
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"sources": ["manual"]}
        )
        assert response.status_code == 200
        manual_results = response.json()
        assert all(row["source"] == "manual" for row in manual_results["rows"])
        
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            pdf_papers,
        )
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"sources": ["pdf"]}
        )
        assert response.status_code == 200
        pdf_results = response.json()
        assert all(row["source"] == "pdf" for row in pdf_results["rows"])
        
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            zotero_papers,
        )
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"sources": ["zotero"]}
        )
        assert response.status_code == 200
        zotero_results = response.json()
        assert all(row["source"] == "zotero" for row in zotero_results["rows"])
        
        combined = manual_papers + pdf_papers
        mock_staging_service.list_rows.return_value = _build_list_response(
            test_session_id,
            combined,
        )
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/staging",
            params={"sources": ["manual", "pdf"]}
        )
        assert response.status_code == 200
        mixed_results = response.json()
        assert all(
            row["source"] in ["manual", "pdf"]
            for row in mixed_results["rows"]
        )
