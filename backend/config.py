"""
Configuration management for Azure Chatbot Backend

This module handles all configuration settings including Azure Entra ID,
Azure Foundry, and Azure Table Storage credentials.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Azure Entra ID Configuration:
    - AZURE_CLIENT_ID: Application (client) ID from Azure App Registration
    - AZURE_TENANT_ID: Directory (tenant) ID from Azure Portal
    - AZURE_CLIENT_SECRET: Client secret for backend authentication

    Azure Foundry Configuration:
    - AZURE_FOUNDRY_ENDPOINT: Azure Foundry project endpoint URL
    - AZURE_FOUNDRY_API_KEY: API key for Azure Foundry access
    - AZURE_FOUNDRY_PROJECT_ID: Your Azure Foundry project identifier

    Azure Table Storage Configuration:
    - AZURE_STORAGE_CONNECTION_STRING: Connection string for Azure Storage Account
    - AZURE_STORAGE_ACCOUNT_NAME: Storage account name (alternative to connection string)
    - AZURE_STORAGE_ACCOUNT_KEY: Storage account key (alternative to connection string)

    OAuth Identity Passthrough (MCP):
    - MCP_ENABLED: Enable OAuth Identity Passthrough for agent calls
    """

    # Azure Entra ID Settings
    AZURE_CLIENT_ID: str
    AZURE_TENANT_ID: str
    AZURE_CLIENT_SECRET: str
    AZURE_AUTHORITY: Optional[str] = None

    # Azure Foundry Settings
    AZURE_FOUNDRY_ENDPOINT: str
    AZURE_FOUNDRY_API_KEY: str
    AZURE_FOUNDRY_PROJECT_ID: str

    # Azure Table Storage Settings
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_ACCOUNT_NAME: Optional[str] = None
    AZURE_STORAGE_ACCOUNT_KEY: Optional[str] = None

    # OAuth Identity Passthrough (MCP) Settings
    MCP_ENABLED: bool = True

    # RAG Integration Settings
    AZURE_AI_SEARCH_ENDPOINT: Optional[str] = None
    AZURE_AI_SEARCH_KEY: Optional[str] = None
    AZURE_AI_SEARCH_INDEX: str = "documents"
    
    # SharePoint RAG Settings
    SHAREPOINT_SITE_URL: Optional[str] = None
    SHAREPOINT_ENABLED: bool = False

    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # API Settings
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def authority_url(self) -> str:
        """Generate Azure AD authority URL"""
        if self.AZURE_AUTHORITY:
            return self.AZURE_AUTHORITY
        return f"https://login.microsoftonline.com/{self.AZURE_TENANT_ID}"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
