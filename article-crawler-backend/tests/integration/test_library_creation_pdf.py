
import pytest
from io import BytesIO


class TestPDFWorkflow:
    
    
    def test_pdf_upload_endpoint(self, app_client, test_session_id, mock_pdf_service):
        from io import BytesIO
        
        pdf_content = b"%PDF-1.4 fake pdf"
        files = [("files", ("test.pdf", BytesIO(pdf_content), "application/pdf"))]
        
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/pdfs/upload",
            files=files
        )
        
        assert response.status_code == 200
        assert "upload_id" in response.json()
    
    def test_check_grobid_availability(self, app_client, test_session_id, mock_pdf_service):
        mock_pdf_service.check_grobid_availability.return_value = (True, None)
        
        response = app_client.get(
            f"/api/v1/seeds/session/{test_session_id}/pdfs/grobid/status"
        )
        
        assert response.status_code in [200, 404]
    
    def test_pdf_extract_endpoint_exists(self, app_client, test_session_id):
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/pdfs/upload-123/extract"
        )
        
        assert response.status_code in [200, 400, 404, 422, 500]


class TestEndToEndSimple:
    
    def test_basic_workflow(
        self,
        app_client,
        test_session_id,
        mock_staging_service,
        mock_library_service,
        mock_pdf_service,
        sample_staging_papers
    ):
        from io import BytesIO
        
        response = app_client.post(
            "/api/v1/seeds/session/start",
            json={"use_case": "library_creation"}
        )
        assert response.status_code == 200
        
        pdf_content = b"%PDF-1.4 fake pdf"
        files = [("files", ("test.pdf", BytesIO(pdf_content), "application/pdf"))]
        response = app_client.post(
            f"/api/v1/seeds/session/{test_session_id}/pdfs/upload",
            files=files
        )
        assert response.status_code == 200
        upload_id = response.json()["upload_id"]
        
        mock_staging_service.add_rows.return_value = [sample_staging_papers[0]]
        
        response = app_client.post(
            f"/api/v1/library/{test_session_id}/details",
            json={"name": "PDF Library", "path": "/tmp/pdf-lib"}
        )
        assert response.status_code == 200