"""
Dynamic Role-Based Access Control using Azure AD App Roles + Configuration File

This module implements a fully dynamic RBAC system that requires NO code changes
when adding new users, roles, or agents. Configuration is loaded from rbac_config.json.

Features:
- Azure AD App Roles integration (roles from JWT token)
- JSON-based configuration (version controlled, no code changes)
- Pattern-based agent matching (e.g., "budget" matches "Budget Planning Assistant")
- Agent-specific metadata (override pattern matching)
- Hot-reload support (update config without restarting)
- Comprehensive logging and audit trail

Usage:
    rbac = AgentAccessControl()
    user_roles = rbac.get_user_roles_from_token(jwt_payload)
    filtered_agents = rbac.filter_agents_by_access(user_roles, all_agents)
"""

import json
import os
from typing import List, Set, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentAccessControl:
    """
    Dynamic agent access control using Azure AD App Roles and configuration file.
    
    This implementation eliminates hard-coded user-to-role mappings and provides
    a scalable, enterprise-ready RBAC solution.
    """
    
    def __init__(self, config_path: str = "backend/rbac_config.json"):
        """
        Initialize access control with configuration file.
        
        Args:
            config_path: Path to JSON configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.last_loaded = datetime.now()
        logger.info(f"AgentAccessControl initialized with config from {config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Dictionary containing role permissions and settings
        """
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            role_count = len(config.get('role_permissions', {}))
            agent_count = len(config.get('agent_metadata', {}).get('agents', {}))
            logger.info(f"Loaded config: {role_count} roles, {agent_count} agent overrides")
            
            return config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}, using defaults")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Fallback default configuration if file cannot be loaded.
        
        Returns:
            Minimal default configuration
        """
        return {
            "version": "1.0",
            "role_permissions": {
                "Admin": {
                    "description": "Full access",
                    "agent_patterns": ["*"],
                    "allow_all": True
                },
                "BasicUser": {
                    "description": "Basic access",
                    "agent_patterns": ["general", "chat", "assistant"],
                    "allow_all": False
                }
            },
            "default_role": "BasicUser",
            "agent_metadata": {"agents": {}},
            "settings": {
                "enable_pattern_matching": True,
                "enable_agent_metadata": True,
                "case_sensitive_patterns": False,
                "log_access_attempts": True
            }
        }
    
    def reload_config(self) -> bool:
        """
        Reload configuration file (hot-reload support).
        
        Returns:
            True if reload successful, False otherwise
        """
        try:
            self.config = self._load_config()
            self.last_loaded = datetime.now()
            logger.info(f"Configuration reloaded successfully at {self.last_loaded}")
            return True
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False
    
    def get_user_roles_from_token(self, token_payload: Dict[str, Any]) -> List[str]:
        """
        Extract roles from Azure AD JWT token.
        
        The token should contain a 'roles' claim with app role values
        assigned to the user in Azure AD Enterprise Application.
        
        Example token payload:
        {
            "preferred_username": "user@company.com",
            "roles": ["FinanceAnalyst", "BasicUser"]
        }
        
        Args:
            token_payload: Decoded JWT token from Azure AD
        
        Returns:
            List of role names (e.g., ["FinanceAnalyst"])
        """
        roles = token_payload.get("roles", [])
        user_email = token_payload.get("preferred_username", "unknown")
        
        if not roles:
            # Fallback to default role if no roles in token
            default_role = self.config.get("default_role", "BasicUser")
            logger.info(f"No roles in token for {user_email}, assigning default: {default_role}")
            roles = [default_role]
        else:
            logger.info(f"User {user_email} has roles: {roles}")
        
        # Validate roles exist in configuration
        valid_roles = []
        role_permissions = self.config.get("role_permissions", {})
        
        for role in roles:
            if role in role_permissions:
                valid_roles.append(role)
            else:
                logger.warning(f"Unknown role '{role}' for user {user_email}, ignoring")
        
        if not valid_roles:
            # All roles were invalid, use default
            default_role = self.config.get("default_role", "BasicUser")
            logger.warning(f"No valid roles for {user_email}, falling back to {default_role}")
            valid_roles = [default_role]
        
        return valid_roles
    
    def can_access_agent(
        self,
        user_roles: List[str],
        agent_name: str,
        agent_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user with given roles can access the specified agent.
        
        Access determination logic:
        1. Check agent-specific metadata (if enabled and provided)
        2. Check pattern matching against agent name (if enabled)
        3. Deny access if no match found
        
        Args:
            user_roles: List of role names from user's token
            agent_name: Name of the agent to check access for
            agent_metadata: Optional agent metadata (overrides config lookup)
        
        Returns:
            True if user can access the agent, False otherwise
        """
        settings = self.config.get("settings", {})
        log_access = settings.get("log_access_attempts", True)
        
        # Prepare agent name for comparison
        agent_name_compare = agent_name
        if not settings.get("case_sensitive_patterns", False):
            agent_name_compare = agent_name.lower()
        
        role_permissions = self.config.get("role_permissions", {})
        
        # Check each role for access
        for role in user_roles:
            if role not in role_permissions:
                continue
            
            role_config = role_permissions[role]
            
            # Check if role has full access
            if role_config.get("allow_all", False):
                if log_access:
                    logger.debug(f"✅ Access granted: Role '{role}' has full access")
                return True
            
            # Check agent-specific metadata
            if settings.get("enable_agent_metadata", True):
                metadata = agent_metadata or self._get_agent_metadata(agent_name)
                if metadata:
                    required_roles = metadata.get("required_roles", [])
                    if role in required_roles:
                        if log_access:
                            logger.debug(f"✅ Access granted: Agent metadata allows role '{role}'")
                        return True
            
            # Check pattern matching
            if settings.get("enable_pattern_matching", True):
                agent_patterns = role_config.get("agent_patterns", [])
                for pattern in agent_patterns:
                    pattern_compare = pattern if settings.get("case_sensitive_patterns", False) else pattern.lower()
                    
                    if pattern_compare == "*" or pattern_compare in agent_name_compare:
                        if log_access:
                            logger.debug(f"✅ Access granted: Agent '{agent_name}' matches pattern '{pattern}' for role '{role}'")
                        return True
        
        # Access denied
        if log_access:
            logger.debug(f"❌ Access denied: Agent '{agent_name}' not accessible for roles {user_roles}")
        
        return False
    
    def _get_agent_metadata(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve agent-specific metadata from configuration.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Agent metadata dictionary or None if not found
        """
        agent_metadata_config = self.config.get("agent_metadata", {}).get("agents", {})
        return agent_metadata_config.get(agent_name)
    
    def filter_agents_by_access(
        self,
        user_roles: List[str],
        agents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter list of agents based on user's roles.
        
        Args:
            user_roles: List of role names from user's token
            agents: List of agent dictionaries (must have 'name' or 'id' field)
        
        Returns:
            Filtered list of agents the user can access
        """
        filtered = []
        
        for agent in agents:
            agent_name = agent.get("name", agent.get("id", "Unknown Agent"))
            agent_metadata = agent.get("metadata")  # Optional metadata from API
            
            if self.can_access_agent(user_roles, agent_name, agent_metadata):
                filtered.append(agent)
        
        logger.info(
            f"Filtered {len(agents)} agents to {len(filtered)} for roles {user_roles}"
        )
        
        return filtered
    
    def get_role_info(self, role_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific role.
        
        Args:
            role_name: Name of the role
        
        Returns:
            Role configuration dictionary or None if not found
        """
        role_permissions = self.config.get("role_permissions", {})
        return role_permissions.get(role_name)
    
    def get_all_roles(self) -> List[str]:
        """
        Get list of all configured roles.
        
        Returns:
            List of role names
        """
        return list(self.config.get("role_permissions", {}).keys())
    
    def get_config_version(self) -> str:
        """
        Get configuration version.
        
        Returns:
            Version string
        """
        return self.config.get("version", "unknown")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get RBAC statistics and configuration info.
        
        Returns:
            Dictionary with statistics
        """
        role_permissions = self.config.get("role_permissions", {})
        agent_metadata = self.config.get("agent_metadata", {}).get("agents", {})
        
        return {
            "config_version": self.get_config_version(),
            "last_loaded": self.last_loaded.isoformat(),
            "total_roles": len(role_permissions),
            "total_agent_overrides": len(agent_metadata),
            "roles": list(role_permissions.keys()),
            "default_role": self.config.get("default_role", "BasicUser"),
            "settings": self.config.get("settings", {})
        }


def filter_agents_for_user(
    agents: List[Dict[str, Any]],
    user_token: Dict[str, Any],
    config_path: str = "backend/rbac_config.json"
) -> List[Dict[str, Any]]:
    """
    Convenience function to filter agents for a user.
    
    This is a simpler interface for basic filtering without creating
    an AgentAccessControl instance manually.
    
    Args:
        agents: List of agent dictionaries
        user_token: Decoded JWT token payload
        config_path: Path to RBAC configuration file
    
    Returns:
        Filtered list of agents
    """
    rbac = AgentAccessControl(config_path)
    user_roles = rbac.get_user_roles_from_token(user_token)
    return rbac.filter_agents_by_access(user_roles, agents)
