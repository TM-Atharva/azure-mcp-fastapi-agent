"""
FastAPI Backend for Azure Chatbot Application

This is the main entry point for the FastAPI backend. It provides:
- Azure Entra ID authentication endpoints
- Agent discovery and management endpoints
- Chat session and message handling endpoints
- OAuth Identity Passthrough (MCP) implementation for agent calls

Key Features:
- Secure token validation for all protected endpoints
- Real-time chat with Azure Foundry agents
- Session management with Azure Table Storage
- Comprehensive error handling and logging
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging
import json
import asyncio

from config import settings
from models import (
    UserProfile,
    Agent,
    AgentResponse,
    ChatSession,
    ChatMessage,
    CreateSessionRequest,
    SendMessageRequest,
    MessageResponse,
    SessionResponse,
    ChatHistoryResponse,
    ErrorResponse
)
from auth import get_current_user, get_mcp_context, auth_handler
from azure_foundry import foundry_client
from table_storage import table_storage


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize FastAPI application
app = FastAPI(
    title="Azure Chatbot API",
    description="Backend API for Azure-integrated chatbot with OAuth Identity Passthrough",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Azure Chatbot API...")
    logger.info(f"CORS Origins: {settings.cors_origins_list}")
    logger.info(f"MCP Enabled: {settings.MCP_ENABLED}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Azure Chatbot API...")
    await foundry_client.close()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Azure Chatbot API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "azure_ad": "operational",
            "azure_foundry": "operational",
            "azure_table_storage": "operational"
        },
        "mcp_enabled": settings.MCP_ENABLED,
        "timestamp": datetime.utcnow().isoformat()
    }


# Authentication Endpoints
@app.get("/api/auth/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get current authenticated user profile.

    This endpoint validates the Azure AD token and returns the user's profile
    information from the database.

    Headers:
        Authorization: Bearer <azure_ad_access_token>

    Returns:
        UserProfile: Current user's profile information
    """
    logger.info(f"User profile requested for: {current_user.email}")
    return current_user


# Agent Endpoints
@app.get("/api/agents", response_model=AgentResponse)
async def list_agents(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get list of available Azure Foundry agents.

    This endpoint retrieves all available agents from Azure Foundry,
    synchronizes them with the local database, and returns them to the client.

    Headers:
        Authorization: Bearer <azure_ad_access_token>

    Returns:
        AgentResponse: List of available agents
    """
    try:
        logger.info(f"Fetching agents for user: {current_user.email}")
        agents = await foundry_client.list_agents()

        return AgentResponse(
            agents=agents,
            count=len(agents)
        )

    except Exception as e:
        logger.error(f"Error fetching agents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agents: {str(e)}"
        )


@app.get("/api/agents/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: UUID,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get specific agent by ID.

    Args:
        agent_id: UUID of the agent

    Headers:
        Authorization: Bearer <azure_ad_access_token>

    Returns:
        Agent: Agent information
    """
    agent = await foundry_client.get_agent_by_id(agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    return agent


# Chat Session Endpoints
@app.post("/api/sessions", response_model=SessionResponse)
async def create_chat_session(
    request: CreateSessionRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Create a new chat session with a selected agent.

    This endpoint creates a new chat session in the database, linking
    the current user with the selected agent.

    Headers:
        Authorization: Bearer <azure_ad_access_token>

    Body:
        CreateSessionRequest: agent_id and optional title

    Returns:
        SessionResponse: Created session information
    """
    try:
        logger.info(f"Creating session for user {current_user.email} with agent {request.agent_id}")

        # Verify agent exists
        agent = await foundry_client.get_agent_by_id(request.agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )

        # Create session - wrap blocking I/O in asyncio.to_thread()
        session_entity = await asyncio.to_thread(
            table_storage.create_session,
            user_azure_id=current_user.azure_id,
            agent_id=str(request.agent_id),
            title=request.title or "New Chat"
        )

        session = ChatSession(
            id=session_entity["id"],
            user_id=current_user.id,
            agent_id=session_entity["agent_id"],
            title=session_entity["title"],
            created_at=session_entity["created_at"],
            updated_at=session_entity["updated_at"],
            is_active=session_entity["is_active"]
        )
        logger.info(f"Created session: {session.id}")

        return SessionResponse(session=session)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@app.get("/api/sessions", response_model=List[ChatSession])
async def list_user_sessions(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get all chat sessions for current user.

    Headers:
        Authorization: Bearer <azure_ad_access_token>

    Returns:
        List[ChatSession]: User's chat sessions
    """
    try:
        # Wrap blocking I/O in asyncio.to_thread()
        session_entities = await asyncio.to_thread(
            table_storage.get_user_sessions,
            current_user.azure_id
        )

        sessions = []
        for entity in session_entities:
            session = ChatSession(
                id=entity["id"],
                user_id=current_user.id,
                agent_id=entity["agent_id"],
                title=entity["title"],
                created_at=entity["created_at"],
                updated_at=entity["updated_at"],
                is_active=entity["is_active"]
            )
            sessions.append(session)

        return sessions

    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sessions: {str(e)}"
        )


@app.get("/api/sessions/{session_id}", response_model=ChatHistoryResponse)
async def get_session_history(
    session_id: UUID,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get chat history for a specific session.

    Args:
        session_id: UUID of the chat session

    Headers:
        Authorization: Bearer <azure_ad_access_token>

    Returns:
        ChatHistoryResponse: Session and message history
    """
    try:
        # Get session - wrap blocking I/O in asyncio.to_thread()
        session_entity = await asyncio.to_thread(
            table_storage.get_session_by_id,
            user_azure_id=current_user.azure_id,
            session_id=str(session_id)
        )

        if not session_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = ChatSession(
            id=session_entity["id"],
            user_id=current_user.id,
            agent_id=session_entity["agent_id"],
            title=session_entity["title"],
            created_at=session_entity["created_at"],
            updated_at=session_entity["updated_at"],
            is_active=session_entity["is_active"]
        )

        # Get messages - wrap blocking I/O in asyncio.to_thread()
        message_entities = await asyncio.to_thread(
            table_storage.get_session_messages,
            str(session_id)
        )

        messages = []
        for entity in message_entities:
            message = ChatMessage(
                id=entity["id"],
                session_id=entity["session_id"],
                role=entity["role"],
                content=entity["content"],
                metadata=json.loads(entity.get("metadata", "{}")),
                created_at=entity["created_at"]
            )
            messages.append(message)

        return ChatHistoryResponse(
            session=session,
            messages=messages
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session history: {str(e)}"
        )


# Chat Message Endpoints
@app.post("/api/chat", response_model=MessageResponse)
async def send_chat_message(
    request: SendMessageRequest,
    current_user: UserProfile = Depends(get_current_user),
    mcp_context: Dict[str, Any] = Depends(get_mcp_context)
):
    """
    Send a message to an agent and get response.

    This endpoint implements OAuth Identity Passthrough (MCP) by:
    1. Validating the user's Azure AD token
    2. Creating an MCP context with user identity
    3. Passing the context to Azure Foundry with the message
    4. Storing both user message and agent response

    The MCP context ensures that:
    - Agent knows the user's identity
    - Agent can access user-specific resources
    - All actions are audited with user information
    - Proper authorization is maintained throughout

    Headers:
        Authorization: Bearer <azure_ad_access_token>

    Body:
        SendMessageRequest: session_id, content, optional metadata

    Returns:
        MessageResponse: Agent's response message
    """
    try:
        logger.info(f"Processing message for session {request.session_id}")

        # Verify session exists and belongs to user - wrap blocking I/O in asyncio.to_thread()
        session_entity = await asyncio.to_thread(
            table_storage.get_session_by_id,
            user_azure_id=current_user.azure_id,
            session_id=str(request.session_id)
        )

        if not session_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = ChatSession(
            id=session_entity["id"],
            user_id=current_user.id,
            agent_id=session_entity["agent_id"],
            title=session_entity["title"],
            created_at=session_entity["created_at"],
            updated_at=session_entity["updated_at"],
            is_active=session_entity["is_active"]
        )

        # Store user message - wrap blocking I/O in asyncio.to_thread()
        user_message_entity = await asyncio.to_thread(
            table_storage.create_message,
            session_id=str(request.session_id),
            role="user",
            content=request.content,
            metadata=request.metadata or {}
        )

        user_message = ChatMessage(
            id=user_message_entity["id"],
            session_id=user_message_entity["session_id"],
            role=user_message_entity["role"],
            content=user_message_entity["content"],
            metadata=json.loads(user_message_entity.get("metadata", "{}")),
            created_at=user_message_entity["created_at"]
        )

        # Get conversation history - wrap blocking I/O in asyncio.to_thread()
        message_entities = await asyncio.to_thread(
            table_storage.get_session_messages,
            str(request.session_id),
            limit=20
        )

        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in message_entities
        ]

        # Get agent info
        agent = await foundry_client.get_agent_by_id(session.agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )

        # Send message to agent with MCP context
        logger.info(f"Calling agent {agent.azure_agent_id} with MCP context")
        agent_response = await foundry_client.send_message(
            agent_id=agent.azure_agent_id,
            message=request.content,
            conversation_history=conversation_history,
            mcp_context=mcp_context,
            stream=False
        )

        # Store agent response - wrap blocking I/O in asyncio.to_thread()
        assistant_message_entity = await asyncio.to_thread(
            table_storage.create_message,
            session_id=str(request.session_id),
            role="assistant",
            content=agent_response.get("content", ""),
            metadata=agent_response.get("metadata", {})
        )

        assistant_message = ChatMessage(
            id=assistant_message_entity["id"],
            session_id=assistant_message_entity["session_id"],
            role=assistant_message_entity["role"],
            content=assistant_message_entity["content"],
            metadata=json.loads(assistant_message_entity.get("metadata", "{}")),
            created_at=assistant_message_entity["created_at"]
        )

        # Update session timestamp - wrap blocking I/O in asyncio.to_thread()
        await asyncio.to_thread(
            table_storage.update_session_timestamp,
            user_azure_id=current_user.azure_id,
            session_id=str(request.session_id)
        )

        logger.info(f"Message processed successfully for session {request.session_id}")

        return MessageResponse(message=assistant_message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Delete a chat session and all its messages.

    Args:
        session_id: UUID of the chat session

    Headers:
        Authorization: Bearer <azure_ad_access_token>

    Returns:
        Dict with success status
    """
    try:
        # Verify session exists and belongs to user - wrap blocking I/O in asyncio.to_thread()
        session_entity = await asyncio.to_thread(
            table_storage.get_session_by_id,
            user_azure_id=current_user.azure_id,
            session_id=str(session_id)
        )

        if not session_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Delete session and all its messages - wrap blocking I/O in asyncio.to_thread()
        await asyncio.to_thread(
            table_storage.delete_session,
            user_azure_id=current_user.azure_id,
            session_id=str(session_id)
        )

        logger.info(f"Deleted session: {session_id}")

        return {"success": True, "message": "Session deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
