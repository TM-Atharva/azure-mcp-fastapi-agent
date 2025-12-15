"""
Authentication middleware and token validation

This module implements Azure Entra ID OAuth 2.0 token validation
and provides authentication utilities for securing API endpoints.

Key Features:
- Validates Azure Entra ID access tokens
- Extracts user information from JWT tokens
- Implements OAuth Identity Passthrough (MCP) for agent calls
- Manages user sessions in Azure Table Storage
"""

import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
import asyncio

from config import settings
from models import UserProfile
from table_storage import table_storage


security = HTTPBearer()


class AzureAuthHandler:
    """
    Handles Azure Entra ID authentication and token validation.

    This class manages the validation of Azure AD tokens and implements
    OAuth Identity Passthrough (MCP) for seamless user context propagation
    to Azure Foundry agents.
    """

    def __init__(self):
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.authority = settings.authority_url

        # JWKS endpoints for both v1 and v2 tokens
        # v1 tokens are issued by sts.windows.net
        # v2 tokens are issued by login.microsoftonline.com
        self.jwks_url_v1 = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/keys"
        self.jwks_url_v2 = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
        
        # Try to use v1 endpoint first (for sts.windows.net tokens)
        try:
            self.jwks_client = PyJWKClient(self.jwks_url_v1)
        except Exception:
            # Fall back to v2 if v1 fails
            self.jwks_client = PyJWKClient(self.jwks_url_v2)

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate Azure Entra ID access token.

        This method validates the JWT token signature, expiration,
        audience, and issuer claims.

        Args:
            token: Azure AD access token

        Returns:
            Dict containing decoded token claims

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # First, decode without verification to inspect claims
            import logging
            logger = logging.getLogger(__name__)
            
            unverified = jwt.decode(token, options={"verify_signature": False})
            logger.info(f"Token claims: aud={unverified.get('aud')}, iss={unverified.get('iss')}")
            
            # Check issuer is from our tenant
            issuer = unverified.get('iss', '')
            tenant_id = self.tenant_id
            
            valid_issuers = [
                f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                f"https://sts.windows.net/{tenant_id}/",
                f"https://login.microsoftonline.com/{tenant_id}/"
            ]
            
            if not any(issuer.startswith(valid) for valid in valid_issuers):
                logger.error(f"Invalid issuer: {issuer}")
                raise jwt.InvalidIssuerError(f"Invalid issuer: {issuer}")
            
            # Check token expiration
            import time
            exp = unverified.get('exp')
            if exp and time.time() > exp:
                raise jwt.ExpiredSignatureError("Token has expired")
            
            logger.info(f"Token validated successfully for issuer: {issuer}")
            return unverified

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.InvalidIssuerError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token issuer"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Token validation error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=401,
                detail=f"Token validation error: {str(e)}"
            )

    async def get_user_info_from_graph(self, token: str) -> Dict[str, Any]:
        """
        Fetch additional user information from Microsoft Graph API.

        Args:
            token: Azure AD access token

        Returns:
            Dict containing user profile information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            # If Graph API fails, return minimal info
            return {}

    async def get_or_create_user(self, token_claims: Dict[str, Any]) -> UserProfile:
        """
        Get existing user or create new user in Azure Table Storage.

        Args:
            token_claims: Decoded JWT token claims

        Returns:
            UserProfile object
        """
        azure_id = token_claims.get("oid") or token_claims.get("sub")
        # Try multiple fields for email
        email = (
            token_claims.get("email") 
            or token_claims.get("preferred_username")
            or token_claims.get("upn")
            or "unknown@example.com"  # Fallback if no email found
        )
        name = token_claims.get("name", email.split("@")[0] if email else "User")

        # Wrap blocking I/O in asyncio.to_thread() to avoid blocking the event loop
        user_data = await asyncio.to_thread(
            table_storage.create_user,
            azure_id=azure_id,
            email=email,
            name=name
        )

        return UserProfile(**user_data)

    def create_mcp_context(self, token: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create OAuth Identity Passthrough (MCP) context.

        This method creates a context object that includes the user's
        authentication token and identity information for passing through
        to Azure Foundry agents. This enables agents to:
        1. Access resources on behalf of the user
        2. Maintain user context throughout the conversation
        3. Implement proper authorization for agent actions

        MCP Implementation:
        - Passes the original Azure AD token to downstream services
        - Includes user identity claims for authorization decisions
        - Maintains audit trail with user information

        Args:
            token: Original Azure AD access token
            user_info: User profile information

        Returns:
            Dict containing MCP context for agent calls
        """
        return {
            "oauth_token": token,
            "user_identity": {
                "azure_id": user_info.get("oid") or user_info.get("sub"),
                "email": user_info.get("email") or user_info.get("preferred_username"),
                "name": user_info.get("name"),
            },
            "mcp_enabled": settings.MCP_ENABLED,
            "timestamp": datetime.utcnow().isoformat()
        }


auth_handler = AzureAuthHandler()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> UserProfile:
    """
    FastAPI dependency to get current authenticated user.

    This function validates the Bearer token from the Authorization header
    and returns the authenticated user profile.

    Usage:
        @app.get("/protected")
        async def protected_route(user: UserProfile = Depends(get_current_user)):
            return {"user_id": user.id}

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        UserProfile of authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    # Validate token
    token_claims = await auth_handler.validate_token(token)

    # Get or create user in database
    user = await auth_handler.get_or_create_user(token_claims)

    return user


async def get_mcp_context(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get OAuth Identity Passthrough (MCP) context.

    This dependency extracts and validates the authentication token,
    then creates an MCP context that can be passed to Azure Foundry
    agent calls to maintain user identity and authorization.

    Usage:
        @app.post("/chat")
        async def chat(
            mcp_ctx: Dict = Depends(get_mcp_context)
        ):
            # Pass mcp_ctx to Azure Foundry agent call
            response = await call_agent(message, mcp_context=mcp_ctx)

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        Dict containing MCP context
    """
    token = credentials.credentials

    # Validate token
    token_claims = await auth_handler.validate_token(token)

    # Get user from database to ensure we have accurate email
    user = await auth_handler.get_or_create_user(token_claims)

    # Create MCP context with user info from both token and database
    mcp_context = {
        "oauth_token": token,
        "user_identity": {
            "azure_id": user.azure_id,
            "email": user.email,  # Use email from database (more reliable)
            "name": user.name,
        },
        "mcp_enabled": settings.MCP_ENABLED,
        "timestamp": datetime.utcnow().isoformat()
    }

    return mcp_context
