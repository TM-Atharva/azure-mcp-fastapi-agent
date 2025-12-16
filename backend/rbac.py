"""
Role-Based Access Control (RBAC) for Agent Visibility

This module implements RBAC to control which users can see and interact
with specific agents based on their assigned roles.

Roles:
- admin: Full access to all agents
- analyst: Access to data analysis and reporting agents
- user: Access to basic chat agents
- guest: Limited access to public agents
"""

from typing import List, Set, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """Enumeration of user roles in the system"""
    ADMIN = "admin"
    ANALYST = "analyst"
    USER = "user"
    GUEST = "guest"


class AgentAccessControl:
    """
    Manages agent access control based on user roles.
    
    This class determines which agents are visible and accessible
    to users based on their assigned roles.
    """
    
    # Default role assignments for agents
    # Key: agent_name_pattern, Value: set of allowed roles
    DEFAULT_AGENT_PERMISSIONS = {
        "admin": {UserRole.ADMIN},
        "data": {UserRole.ADMIN, UserRole.ANALYST},
        "analytics": {UserRole.ADMIN, UserRole.ANALYST},
        "reporting": {UserRole.ADMIN, UserRole.ANALYST},
        "chat": {UserRole.ADMIN, UserRole.ANALYST, UserRole.USER},
        "assistant": {UserRole.ADMIN, UserRole.ANALYST, UserRole.USER},
        "general": {UserRole.ADMIN, UserRole.ANALYST, UserRole.USER},
        "public": {UserRole.ADMIN, UserRole.ANALYST, UserRole.USER, UserRole.GUEST},
    }
    
    @staticmethod
    def get_user_roles(user_email: str, azure_user_data: dict = None) -> Set[UserRole]:
        """
        Determine user roles based on email domain, Azure AD groups, or other criteria.
        
        Args:
            user_email: User's email address
            azure_user_data: Additional Azure AD user data (groups, claims, etc.)
        
        Returns:
            Set of UserRole values assigned to the user
        """
        roles = {UserRole.USER}  # Default role for all authenticated users
        
        # Check for admin role (customize based on your requirements)
        admin_domains = ["admin.com", "leadership.com"]
        admin_emails = []  # Add specific admin emails here
        
        email_domain = user_email.split("@")[-1] if "@" in user_email else ""
        
        if email_domain in admin_domains or user_email in admin_emails:
            roles.add(UserRole.ADMIN)
            logger.info(f"User {user_email} assigned ADMIN role")
        
        # Check for analyst role
        analyst_keywords = ["analyst", "data", "bi", "analytics"]
        if any(keyword in user_email.lower() for keyword in analyst_keywords):
            roles.add(UserRole.ANALYST)
            logger.info(f"User {user_email} assigned ANALYST role")
        
        # Check Azure AD groups if available
        if azure_user_data and "groups" in azure_user_data:
            groups = azure_user_data.get("groups", [])
            
            # Map Azure AD group IDs/names to roles
            group_role_mapping = {
                "Admins": UserRole.ADMIN,
                "DataAnalysts": UserRole.ANALYST,
                "Analysts": UserRole.ANALYST,
                # Add your Azure AD group mappings here
            }
            
            for group in groups:
                group_name = group if isinstance(group, str) else group.get("displayName", "")
                if group_name in group_role_mapping:
                    roles.add(group_role_mapping[group_name])
                    logger.info(f"User {user_email} assigned {group_role_mapping[group_name]} from group {group_name}")
        
        logger.info(f"Final roles for {user_email}: {[r.value for r in roles]}")
        return roles
    
    @staticmethod
    def get_agent_required_roles(agent_name: str, agent_description: str = "") -> Set[UserRole]:
        """
        Determine which roles are required to access an agent based on its name/description.
        
        Args:
            agent_name: Name of the agent
            agent_description: Description of the agent
        
        Returns:
            Set of UserRole values that are allowed to access this agent
        """
        agent_text = f"{agent_name} {agent_description}".lower()
        
        # Check for specific keywords in agent name/description
        for keyword, allowed_roles in AgentAccessControl.DEFAULT_AGENT_PERMISSIONS.items():
            if keyword in agent_text:
                logger.debug(f"Agent '{agent_name}' matched keyword '{keyword}', allowed roles: {allowed_roles}")
                return allowed_roles
        
        # Default: allow all authenticated users
        default_roles = {UserRole.ADMIN, UserRole.ANALYST, UserRole.USER}
        logger.debug(f"Agent '{agent_name}' using default roles: {default_roles}")
        return default_roles
    
    @staticmethod
    def can_access_agent(user_roles: Set[UserRole], agent_required_roles: Set[UserRole]) -> bool:
        """
        Check if user has permission to access an agent.
        
        Args:
            user_roles: Set of roles assigned to the user
            agent_required_roles: Set of roles required to access the agent
        
        Returns:
            True if user has at least one of the required roles
        """
        has_access = bool(user_roles & agent_required_roles)
        logger.debug(f"Access check: user_roles={user_roles}, required={agent_required_roles}, granted={has_access}")
        return has_access
    
    @staticmethod
    def filter_agents_by_access(agents: List[dict], user_roles: Set[UserRole]) -> List[dict]:
        """
        Filter a list of agents to only include those the user can access.
        
        Args:
            agents: List of agent dictionaries
            user_roles: Set of roles assigned to the user
        
        Returns:
            Filtered list of agents the user can access
        """
        # Admins always see all agents
        if UserRole.ADMIN in user_roles:
            logger.info("Admin user - returning all agents")
            return agents
        
        filtered_agents = []
        for agent in agents:
            agent_name = agent.get("name", "")
            agent_description = agent.get("description", "")
            
            required_roles = AgentAccessControl.get_agent_required_roles(
                agent_name, agent_description
            )
            
            if AgentAccessControl.can_access_agent(user_roles, required_roles):
                filtered_agents.append(agent)
                logger.debug(f"Agent '{agent_name}' accessible to user")
            else:
                logger.debug(f"Agent '{agent_name}' NOT accessible to user")
        
        logger.info(f"Filtered {len(agents)} agents to {len(filtered_agents)} based on user roles")
        return filtered_agents


# Convenience functions for use in endpoints
def get_user_roles_from_profile(user_profile: dict) -> Set[UserRole]:
    """Extract user roles from user profile"""
    return AgentAccessControl.get_user_roles(
        user_email=user_profile.get("email", ""),
        azure_user_data=user_profile.get("azure_data", {})
    )


def filter_agents_for_user(agents: List[dict], user_profile: dict) -> List[dict]:
    """Filter agents based on user's roles"""
    user_roles = get_user_roles_from_profile(user_profile)
    return AgentAccessControl.filter_agents_by_access(agents, user_roles)
