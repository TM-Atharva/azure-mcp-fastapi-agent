"""
Azure Table Storage Operations

This module handles all interactions with Azure Table Storage for
persisting chat data including users, agents, sessions, and messages.

Tables:
- users: User profiles from Azure Entra ID
- agents: AI agents from Azure Foundry
- sessions: Chat sessions between users and agents
- messages: Individual chat messages
"""

from azure.data.tables import TableServiceClient, TableClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import json
import ast # Added explicit import for ast module for literal_eval
from config import settings


class TableStorageClient:
    """
    Client for managing Azure Table Storage operations.

    This client provides CRUD operations for all application tables
    and handles entity serialization/deserialization.
    """

    def __init__(self):
        """Initialize Table Storage client with connection string or account credentials"""
        if settings.AZURE_STORAGE_CONNECTION_STRING:
            self.service_client = TableServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
        elif settings.AZURE_STORAGE_ACCOUNT_NAME and settings.AZURE_STORAGE_ACCOUNT_KEY:
            endpoint = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.table.core.windows.net"
            self.service_client = TableServiceClient(
                endpoint=endpoint,
                credential={"account_name": settings.AZURE_STORAGE_ACCOUNT_NAME,
                           "account_key": settings.AZURE_STORAGE_ACCOUNT_KEY}
            )
        else:
            raise ValueError("Azure Storage credentials not configured")

        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Create tables if they don't exist"""
        tables = [
            "users", 
            "agents", 
            "sessions", 
            "messages",
            "mcptokens",        # MCP OAuth tokens per user-server
            "userroles",        # RBAC user role assignments
            "agentpermissions"  # RBAC agent visibility rules
        ]
        for table_name in tables:
            try:
                self.service_client.create_table(table_name)
            except ResourceExistsError:
                pass

    def _get_table_client(self, table_name: str) -> TableClient:
        """Get table client for specific table"""
        return self.service_client.get_table_client(table_name)

    def _to_iso_string(self, dt: Optional[datetime] = None) -> str:
        """Convert datetime to ISO string"""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.isoformat()

    def create_user(self, azure_id: str, email: str, name: str, avatar_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create or update user in Table Storage.

        PartitionKey: azure_id
        RowKey: azure_id (for simple lookups)
        """
        table_client = self._get_table_client("users")

        entity = {
            "PartitionKey": azure_id,
            "RowKey": azure_id,
            "id": str(uuid.uuid4()),
            "azure_id": azure_id,
            "email": email,
            "name": name,
            "avatar_url": avatar_url or "",
            "created_at": self._to_iso_string(),
            "last_login": self._to_iso_string()
        }

        try:
            existing = table_client.get_entity(partition_key=azure_id, row_key=azure_id)
            entity["id"] = existing["id"]
            entity["created_at"] = existing["created_at"]
            entity["last_login"] = self._to_iso_string()
            table_client.update_entity(entity, mode="replace")
        except ResourceNotFoundError:
            table_client.create_entity(entity)

        return entity

    def get_user_by_azure_id(self, azure_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Azure ID"""
        table_client = self._get_table_client("users")
        try:
            return dict(table_client.get_entity(partition_key=azure_id, row_key=azure_id))
        except ResourceNotFoundError:
            return None

    def update_user_last_login(self, azure_id: str) -> None:
        """Update user's last login timestamp"""
        table_client = self._get_table_client("users")
        try:
            entity = table_client.get_entity(partition_key=azure_id, row_key=azure_id)
            entity["last_login"] = self._to_iso_string()
            table_client.update_entity(entity, mode="replace")
        except ResourceNotFoundError:
            pass

    def create_or_update_agent(
        self,
        azure_agent_id: str,
        name: str,
        description: Optional[str] = None,
        capabilities: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update agent in Table Storage.

        PartitionKey: "agents" (all agents in same partition for efficient queries)
        RowKey: azure_agent_id
        """
        table_client = self._get_table_client("agents")

        entity = {
            "PartitionKey": "agents",
            "RowKey": azure_agent_id,
            "azure_agent_id": azure_agent_id,
            "name": name,
            "description": description or "",
            "capabilities": json.dumps(capabilities or {}),
            "is_active": True,
            "updated_at": self._to_iso_string()
        }

        try:
            existing = table_client.get_entity(partition_key="agents", row_key=azure_agent_id)
            entity["id"] = existing["id"]
            entity["created_at"] = existing["created_at"]
            table_client.update_entity(entity, mode="replace")
        except ResourceNotFoundError:
            entity["id"] = str(uuid.uuid4())
            entity["created_at"] = self._to_iso_string()
            table_client.create_entity(entity)

        # Parse JSON capabilities back to dict before returning
        if "capabilities" in entity and isinstance(entity["capabilities"], str):
            caps_str = entity["capabilities"].strip()
            if caps_str:
                try:
                    # Try to parse as JSON first
                    entity["capabilities"] = json.loads(caps_str)
                except (json.JSONDecodeError, TypeError):
                    try:
                        # Fall back to evaluating as Python literal for old data
                        entity["capabilities"] = ast.literal_eval(caps_str)
                    except (ValueError, SyntaxError):
                        entity["capabilities"] = {}
            else:
                entity["capabilities"] = {}
        
        return entity

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all active agents"""
        table_client = self._get_table_client("agents")
        query_filter = "PartitionKey eq 'agents' and is_active eq true"
        entities = table_client.query_entities(query_filter)
        agents = []
        for entity in entities:
            entity_dict = dict(entity)
            # Parse JSON/Python literal capabilities back to dict
            if "capabilities" in entity_dict and isinstance(entity_dict["capabilities"], str):
                caps_str = entity_dict["capabilities"].strip()
                if caps_str:
                    try:
                        entity_dict["capabilities"] = json.loads(caps_str)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            entity_dict["capabilities"] = ast.literal_eval(caps_str)
                        except (ValueError, SyntaxError):
                            entity_dict["capabilities"] = {}
                else:
                    entity_dict["capabilities"] = {}
            agents.append(entity_dict)
        return agents

    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        table_client = self._get_table_client("agents")
        query_filter = f"PartitionKey eq 'agents' and id eq '{agent_id}'"
        entities = list(table_client.query_entities(query_filter))
        if entities:
            entity = dict(entities[0])
            # Parse JSON/Python literal capabilities back to dict
            if "capabilities" in entity and isinstance(entity["capabilities"], str):
                caps_str = entity["capabilities"].strip()
                if caps_str:
                    try:
                        entity["capabilities"] = json.loads(caps_str)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            entity["capabilities"] = ast.literal_eval(caps_str)
                        except (ValueError, SyntaxError):
                            entity["capabilities"] = {}
                else:
                    entity["capabilities"] = {}
            return entity
        return None

    def get_agent_by_azure_id(self, azure_agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by Azure agent ID"""
        table_client = self._get_table_client("agents")
        # Ensure the RowKey is clean
        clean_agent_id = azure_agent_id.strip() 
        try:
            entity = dict(table_client.get_entity(partition_key="agents", row_key=clean_agent_id))
            # Parse JSON/Python literal capabilities back to dict
            if "capabilities" in entity and isinstance(entity["capabilities"], str):
                caps_str = entity["capabilities"].strip()
                if caps_str:
                    try:
                        entity["capabilities"] = json.loads(caps_str)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            entity["capabilities"] = ast.literal_eval(caps_str)
                        except (ValueError, SyntaxError):
                            entity["capabilities"] = {}
                else:
                    entity["capabilities"] = {}
            return entity
        except ResourceNotFoundError:
            return None

    def create_session(
        self,
        user_azure_id: str,
        agent_id: str,
        title: str = "New Chat"
    ) -> Dict[str, Any]:
        """
        Create new chat session.

        PartitionKey: user_azure_id (for efficient user-scoped queries)
        RowKey: session_id (UUID)
        """
        table_client = self._get_table_client("sessions")

        session_id = str(uuid.uuid4())
        entity = {
            "PartitionKey": user_azure_id,
            "RowKey": session_id,
            "id": session_id,
            "user_azure_id": user_azure_id,
            "agent_id": agent_id,
            "title": title,
            "created_at": self._to_iso_string(),
            "updated_at": self._to_iso_string(),
            "is_active": True
        }

        table_client.create_entity(entity)
        return entity

    def get_user_sessions(self, user_azure_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        table_client = self._get_table_client("sessions")
        query_filter = f"PartitionKey eq '{user_azure_id}'"
        entities = table_client.query_entities(query_filter)
        sessions = [dict(entity) for entity in entities]
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions

    def get_session_by_id(self, user_azure_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get specific session"""
        table_client = self._get_table_client("sessions")
        try:
            return dict(table_client.get_entity(partition_key=user_azure_id, row_key=session_id))
        except ResourceNotFoundError:
            return None

    def update_session_timestamp(self, user_azure_id: str, session_id: str) -> None:
        """Update session's last activity timestamp"""
        table_client = self._get_table_client("sessions")
        try:
            entity = table_client.get_entity(partition_key=user_azure_id, row_key=session_id)
            entity["updated_at"] = self._to_iso_string()
            table_client.update_entity(entity, mode="replace")
        except ResourceNotFoundError:
            pass

    def delete_session(self, user_azure_id: str, session_id: str) -> None:
        """Delete session and all its messages"""
        sessions_table = self._get_table_client("sessions")
        messages_table = self._get_table_client("messages")

        try:
            sessions_table.delete_entity(partition_key=user_azure_id, row_key=session_id)
        except ResourceNotFoundError:
            pass

        query_filter = f"PartitionKey eq '{session_id}'"
        messages = messages_table.query_entities(query_filter)
        for message in messages:
            messages_table.delete_entity(
                partition_key=message["PartitionKey"],
                row_key=message["RowKey"]
            )

    def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create new chat message.

        PartitionKey: session_id (for efficient session-scoped queries)
        RowKey: timestamp + UUID (for ordering)
        """
        table_client = self._get_table_client("messages")

        message_id = str(uuid.uuid4())
        timestamp = self._to_iso_string()

        row_key = f"{timestamp}_{message_id}"

        entity = {
            "PartitionKey": session_id,
            "RowKey": row_key,
            "id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": json.dumps(metadata or {}), # Ensure metadata is stored as JSON string
            "created_at": timestamp
        }

        table_client.create_entity(entity)
        return entity

    def get_session_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all messages for a session, ordered by creation time.

        Args:
            session_id: Session ID
            limit: Maximum number of messages to return (most recent if limited)

        Returns:
            List of message entities ordered by creation time
        """
        table_client = self._get_table_client("messages")
        query_filter = f"PartitionKey eq '{session_id}'"
        entities = table_client.query_entities(query_filter)

        messages = [dict(entity) for entity in entities]
        messages.sort(key=lambda x: x.get("RowKey", ""))

        # Parse metadata back to dict
        for msg in messages:
            if "metadata" in msg and isinstance(msg["metadata"], str):
                try:
                    msg["metadata"] = json.loads(msg["metadata"])
                except (json.JSONDecodeError, TypeError):
                    msg["metadata"] = {} # Default to empty dict on parse failure
        
        if limit:
            messages = messages[-limit:]

        return messages

    # ============================================================
    # MCP Token Storage Methods
    # ============================================================

    def store_mcp_token(
        self,
        user_id: str,
        server_label: str,
        access_token: str,
        refresh_token: str = "",
        expires_at: Optional[datetime] = None
    ) -> None:
        """
        Store MCP OAuth tokens for a user-server pair.

        PartitionKey: user_id
        RowKey: server_label

        Note: In production, encrypt tokens before storage!
        """
        table_client = self._get_table_client("mcptokens")
        entity = {
            "PartitionKey": user_id,
            "RowKey": server_label,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at.isoformat() if expires_at else "",
            "connected_at": self._to_iso_string()
        }
        table_client.upsert_entity(entity)

    def get_user_mcp_tokens(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all MCP tokens for a user.

        Returns:
            Dict mapping server_label to token info
        """
        table_client = self._get_table_client("mcptokens")
        query_filter = f"PartitionKey eq '{user_id}'"
        entities = table_client.query_entities(query_filter)
        
        tokens = {}
        for entity in entities:
            server_label = entity["RowKey"]
            tokens[server_label] = {
                "access_token": entity.get("access_token", ""),
                "refresh_token": entity.get("refresh_token", ""),
                "expires_at": entity.get("expires_at", ""),
                "connected_at": entity.get("connected_at", "")
            }
        return tokens

    def delete_mcp_token(self, user_id: str, server_label: str) -> None:
        """Delete MCP token (disconnect user from service)"""
        table_client = self._get_table_client("mcptokens")
        try:
            table_client.delete_entity(partition_key=user_id, row_key=server_label)
        except ResourceNotFoundError:
            pass

    # ============================================================
    # RBAC Methods - User Roles
    # ============================================================

    def assign_user_role(
        self,
        user_id: str,
        role: str,
        assigned_by: str
    ) -> None:
        """
        Assign a role to a user.

        PartitionKey: user_id
        RowKey: role
        """
        table_client = self._get_table_client("userroles")
        entity = {
            "PartitionKey": user_id,
            "RowKey": role,
            "assigned_by": assigned_by,
            "assigned_at": self._to_iso_string()
        }
        table_client.upsert_entity(entity)

    def get_user_roles(self, user_id: str) -> List[str]:
        """Get all roles assigned to a user"""
        table_client = self._get_table_client("userroles")
        query_filter = f"PartitionKey eq '{user_id}'"
        entities = table_client.query_entities(query_filter)
        return [entity["RowKey"] for entity in entities]

    def remove_user_role(self, user_id: str, role: str) -> None:
        """Remove a role from a user"""
        table_client = self._get_table_client("userroles")
        try:
            table_client.delete_entity(partition_key=user_id, row_key=role)
        except ResourceNotFoundError:
            pass

    # ============================================================
    # RBAC Methods - Agent Permissions
    # ============================================================

    def set_agent_permissions(
        self,
        agent_id: str,
        allowed_roles: List[str],
        allowed_users: Optional[List[str]] = None
    ) -> None:
        """
        Set which roles/users can access an agent.

        PartitionKey: "permissions"
        RowKey: agent_id
        """
        table_client = self._get_table_client("agentpermissions")
        entity = {
            "PartitionKey": "permissions",
            "RowKey": agent_id,
            "allowed_roles": json.dumps(allowed_roles),
            "allowed_users": json.dumps(allowed_users or []),
            "updated_at": self._to_iso_string()
        }
        table_client.upsert_entity(entity)

    def get_agent_permissions(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get permissions for a specific agent"""
        table_client = self._get_table_client("agentpermissions")
        try:
            entity = table_client.get_entity(partition_key="permissions", row_key=agent_id)
            return {
                "allowed_roles": json.loads(entity.get("allowed_roles", "[]")),
                "allowed_users": json.loads(entity.get("allowed_users", "[]"))
            }
        except ResourceNotFoundError:
            return None

    def get_user_accessible_agents(self, user_id: str) -> List[str]:
        """
        Get list of agent IDs that a user can access based on RBAC.

        Returns all agent IDs if no permissions are set (default allow).
        """
        # Get user's roles
        user_roles = self.get_user_roles(user_id)
        
        # If no roles assigned, give default "user" role
        if not user_roles:
            user_roles = ["user"]
        
        # Query all agent permissions
        table_client = self._get_table_client("agentpermissions")
        try:
            permissions = list(table_client.query_entities("PartitionKey eq 'permissions'"))
        except Exception:
            return []  # On error, return empty (deny access)
        
        # If no permissions defined, all agents are accessible
        if not permissions:
            return []  # Empty means "no restrictions"
        
        accessible = []
        for perm in permissions:
            agent_id = perm["RowKey"]
            allowed_roles = json.loads(perm.get("allowed_roles", "[]"))
            allowed_users = json.loads(perm.get("allowed_users", "[]"))
            
            # Check if user has access
            if user_id in allowed_users:
                accessible.append(agent_id)
            elif any(role in allowed_roles for role in user_roles):
                accessible.append(agent_id)
        
        return accessible


table_storage = TableStorageClient()