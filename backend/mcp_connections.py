"""
MCP Connection Management

Manages connections to external MCP servers configured in Azure Foundry.
Handles OAuth token storage and retrieval for each user-server pair.

This module works with MCP tools that are configured in Azure Foundry Portal
with OAuth Identity Passthrough authentication.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server from Azure Foundry catalog"""
    server_label: str
    server_url: str
    display_name: str
    description: str = ""
    requires_oauth: bool = True
    oauth_scopes: List[str] = field(default_factory=list)
    icon: str = "🔗"


# Pre-configured MCP servers from Azure Foundry catalog
# These are examples - actual URLs may vary based on Azure configuration
MCP_SERVERS: Dict[str, MCPServerConfig] = {
    "github": MCPServerConfig(
        server_label="github",
        server_url="https://api.githubcopilot.com/mcp/",
        display_name="GitHub",
        description="Access repositories, commits, pull requests, and issues",
        requires_oauth=True,
        oauth_scopes=["repo", "user", "read:org"],
        icon="🐙"
    ),
    "outlook": MCPServerConfig(
        server_label="outlook",
        server_url="https://outlook.office.com/mcp/",
        display_name="Outlook Mail",
        description="Read and send emails, manage calendar",
        requires_oauth=True,
        oauth_scopes=["Mail.Read", "Mail.Send", "Calendars.Read"],
        icon="📧"
    ),
    "sharepoint": MCPServerConfig(
        server_label="sharepoint",
        server_url="https://graph.microsoft.com/mcp/sharepoint/",
        display_name="SharePoint",
        description="Access SharePoint files and documents",
        requires_oauth=True,
        oauth_scopes=["Files.Read.All", "Sites.Read.All"],
        icon="📁"
    ),
    "teams": MCPServerConfig(
        server_label="teams",
        server_url="https://graph.microsoft.com/mcp/teams/",
        display_name="Microsoft Teams",
        description="Access Teams messages and channels",
        requires_oauth=True,
        oauth_scopes=["Chat.Read", "Channel.ReadBasic.All"],
        icon="💬"
    ),
    "fetch": MCPServerConfig(
        server_label="fetch",
        server_url="https://fetch-mcp.azure.com/",
        display_name="Fetch (HTTP)",
        description="Make HTTP requests to external APIs",
        requires_oauth=False,
        oauth_scopes=[],
        icon="🌐"
    )
}


class MCPConnectionManager:
    """
    Manages MCP connections and user OAuth tokens.
    
    Works with Azure Table Storage to persist user MCP tokens
    and provides methods to build tool_resources for Agent API calls.
    """
    
    def __init__(self, table_storage_client=None):
        """
        Initialize MCP Connection Manager.
        
        Args:
            table_storage_client: TableStorageClient instance (lazy loaded if None)
        """
        self._table_storage = table_storage_client
    
    @property
    def table_storage(self):
        """Lazy load table storage client"""
        if self._table_storage is None:
            from table_storage import table_storage
            self._table_storage = table_storage
        return self._table_storage
    
    def get_available_servers(self) -> List[Dict[str, Any]]:
        """
        Get list of available MCP servers from catalog.
        
        Returns:
            List of server configurations
        """
        return [
            {
                "label": config.server_label,
                "display_name": config.display_name,
                "description": config.description,
                "url": config.server_url,
                "requires_oauth": config.requires_oauth,
                "scopes": config.oauth_scopes,
                "icon": config.icon
            }
            for config in MCP_SERVERS.values()
        ]
    
    def get_user_mcp_connections(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all MCP connections for a user.
        
        Args:
            user_id: Azure user ID
            
        Returns:
            Dict mapping server_label to connection info
        """
        try:
            tokens = self.table_storage.get_user_mcp_tokens(user_id)
            return tokens
        except Exception as e:
            logger.error(f"Error getting MCP connections for user {user_id}: {e}")
            return {}
    
    def get_servers_with_status(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get available servers with user's connection status.
        
        Args:
            user_id: Azure user ID
            
        Returns:
            List of servers with connected status
        """
        servers = self.get_available_servers()
        connections = self.get_user_mcp_connections(user_id)
        
        for server in servers:
            label = server["label"]
            if label in connections:
                server["connected"] = True
                server["connected_at"] = connections[label].get("connected_at")
            else:
                server["connected"] = False
                server["connected_at"] = None
        
        return servers
    
    def store_user_consent(
        self,
        user_id: str,
        server_label: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """
        Store OAuth tokens after user consent.
        
        Note: In production, tokens should be encrypted before storage.
        Azure Foundry typically manages tokens internally, but we track
        connection status for UI purposes.
        
        Args:
            user_id: Azure user ID
            server_label: MCP server label (e.g., "github")
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional)
            expires_at: Token expiration time (optional)
            
        Returns:
            True if stored successfully
        """
        try:
            self.table_storage.store_mcp_token(
                user_id=user_id,
                server_label=server_label,
                access_token=access_token,
                refresh_token=refresh_token or "",
                expires_at=expires_at
            )
            logger.info(f"✓ Stored MCP consent for user {user_id}, server {server_label}")
            return True
        except Exception as e:
            logger.error(f"Failed to store MCP consent: {e}")
            return False
    
    def remove_user_connection(self, user_id: str, server_label: str) -> bool:
        """
        Remove user's MCP connection (disconnect from service).
        
        Args:
            user_id: Azure user ID
            server_label: MCP server label
            
        Returns:
            True if removed successfully
        """
        try:
            self.table_storage.delete_mcp_token(user_id, server_label)
            logger.info(f"✓ Removed MCP connection for user {user_id}, server {server_label}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove MCP connection: {e}")
            return False
    
    def build_tool_resources(
        self,
        user_id: str,
        requested_servers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build tool_resources dict for Agent API run.
        
        This creates the structure expected by Azure Agent Service
        when calling agents with MCP tools configured.
        
        Args:
            user_id: Azure user ID
            requested_servers: List of server labels to include (None = all connected)
            
        Returns:
            Dict with mcp tool_resources structure
        """
        connections = self.get_user_mcp_connections(user_id)
        
        if not connections:
            logger.debug(f"No MCP connections found for user {user_id}")
            return {}
        
        mcp_resources = {}
        
        for server_label, connection in connections.items():
            # Filter to requested servers if specified
            if requested_servers and server_label not in requested_servers:
                continue
            
            access_token = connection.get("access_token")
            if access_token:
                mcp_resources[server_label] = {
                    "headers": {
                        "Authorization": f"Bearer {access_token}"
                    },
                    "require_approval": "never"
                }
        
        if mcp_resources:
            logger.info(f"✓ Built tool_resources for {list(mcp_resources.keys())}")
            return {"mcp": mcp_resources}
        
        return {}
    
    def get_agent_mcp_servers(self, agent_capabilities: Dict[str, Any]) -> List[str]:
        """
        Get list of MCP server labels an agent is configured to use.
        
        This reads from agent capabilities to determine which MCP
        servers the agent has access to.
        
        Args:
            agent_capabilities: Agent's capabilities dict from database
            
        Returns:
            List of MCP server labels
        """
        return agent_capabilities.get("mcp_servers", [])


# Singleton instance
mcp_manager = MCPConnectionManager()
