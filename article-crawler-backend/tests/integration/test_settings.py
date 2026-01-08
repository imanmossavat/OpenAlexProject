
import pytest


class TestIntegrationSettings:
    """Test configuration of integration settings (OpenAlex, Zotero)."""
    
    def test_configure_openalex_settings(
        self,
        app_client,
        mock_integration_settings_service
    ):

        response = app_client.get("/api/v1/settings/integrations")
        assert response.status_code == 200
        initial_settings = response.json()
        assert "openalex" in initial_settings
        assert initial_settings["openalex"]["configured"] is False
        
        new_email = "test@example.com"
        response = app_client.put(
            "/api/v1/settings/openalex",
            json={"email": new_email}
        )
        assert response.status_code == 200
        updated_settings = response.json()
        assert updated_settings["openalex"]["email"] == new_email
        assert updated_settings["openalex"]["configured"] is True
        
        response = app_client.get("/api/v1/settings/integrations")
        assert response.status_code == 200
        persisted_settings = response.json()
        assert persisted_settings["openalex"]["email"] == new_email
        assert persisted_settings["openalex"]["configured"] is True
        
        response = app_client.put(
            "/api/v1/settings/openalex",
            json={"email": ""}
        )

        assert response.status_code != 200 or response.json()["openalex"]["email"] == ""
    
    def test_configure_zotero_settings(
        self,
        app_client,
        mock_integration_settings_service
    ):

        response = app_client.get("/api/v1/settings/integrations")
        assert response.status_code == 200
        initial_settings = response.json()
        assert "zotero" in initial_settings
        assert initial_settings["zotero"]["configured"] is False
        
        new_api_key = "test-zotero-api-key-12345"
        new_library_id = "67890"
        response = app_client.put(
            "/api/v1/settings/zotero",
            json={
                "library_id": new_library_id,
                "library_type": "user",
                "api_key": new_api_key
            }
        )
        assert response.status_code == 200
        updated_settings = response.json()
        assert updated_settings["zotero"]["library_id"] == new_library_id
        assert updated_settings["zotero"]["library_type"] == "user"
        assert updated_settings["zotero"]["has_api_key"] is True
        assert updated_settings["zotero"]["configured"] is True
        
        response = app_client.get("/api/v1/settings/integrations")
        assert response.status_code == 200
        persisted_settings = response.json()
        assert persisted_settings["zotero"]["library_id"] == new_library_id
        assert persisted_settings["zotero"]["has_api_key"] is True
        assert persisted_settings["zotero"]["configured"] is True
        
        response = app_client.put(
            "/api/v1/settings/zotero",
            json={"library_type": "user"}
        )
        assert response.status_code >= 400
    
    def test_get_all_integration_settings(
        self,
        app_client,
        mock_integration_settings_service
    ):

        app_client.put("/api/v1/settings/openalex", json={"email": "configured@example.com"})
        app_client.put(
            "/api/v1/settings/zotero",
            json={
                "library_id": "12345",
                "library_type": "user",
                "api_key": "configured-key"
            }
        )
        
        response = app_client.get("/api/v1/settings/integrations")
        assert response.status_code == 200
        all_settings = response.json()
        
        assert "openalex" in all_settings
        assert "zotero" in all_settings
        
        assert all_settings["openalex"]["email"] == "configured@example.com"
        assert all_settings["openalex"]["configured"] is True
        
        assert all_settings["zotero"]["library_id"] == "12345"
        assert all_settings["zotero"]["has_api_key"] is True
        assert all_settings["zotero"]["configured"] is True
