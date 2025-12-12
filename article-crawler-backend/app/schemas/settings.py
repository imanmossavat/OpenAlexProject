from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class OpenAlexSettings(BaseModel):
    """Current OpenAlex integration status."""

    configured: bool = Field(False, description="Whether OpenAlex email is configured")
    email: Optional[EmailStr] = Field(None, description="Contact email for OpenAlex polite usage")


class ZoteroSettings(BaseModel):
    """Current Zotero integration status."""

    configured: bool = Field(False, description="Whether Zotero credentials are configured")
    library_id: Optional[str] = Field(None, description="Zotero library identifier")
    library_type: Optional[str] = Field(None, description="Zotero library type user|group")
    has_api_key: bool = Field(False, description="Whether an API key is stored")


class IntegrationSettingsResponse(BaseModel):
    """Aggregated integration settings response."""

    openalex: OpenAlexSettings
    zotero: ZoteroSettings


class LibraryRootSettings(BaseModel):
    """Configuration for the default library discovery path."""

    path: Optional[str] = Field(
        default=None,
        description="Absolute path used as the primary library discovery root. None = use built-in defaults.",
    )


class UpdateOpenAlexSettingsRequest(BaseModel):
    """Payload for updating OpenAlex polite email."""

    email: EmailStr


class UpdateZoteroSettingsRequest(BaseModel):
    """Payload for updating Zotero credentials."""

    library_id: str = Field(..., description="Zotero user or group library id")
    library_type: Literal["user", "group"] = Field(
        default="user", description="Zotero library type"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Optional API key. Omit to keep existing, empty string to clear.",
    )


class UpdateLibraryRootRequest(BaseModel):
    """Payload for updating the default library discovery root."""

    path: Optional[str] = Field(
        default=None,
        description="Absolute path to use for discovery. Empty/None resets to default search paths.",
    )
