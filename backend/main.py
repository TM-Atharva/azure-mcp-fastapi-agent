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
from rbac import filter_agents_for_user, get_user_roles_from_profile
from rag_integration import RAGService


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
    
    # Initialize RAG service if configured
    global rag_service
    rag_service = RAGService(
        ai_search_endpoint=settings.AZURE_AI_SEARCH_ENDPOINT,
        ai_search_key=settings.AZURE_AI_SEARCH_KEY,
        sharepoint_tenant_id=settings.AZURE_TENANT_ID if settings.SHAREPOINT_ENABLED else None,
        sharepoint_site_url=settings.SHAREPOINT_SITE_URL
    )
    
    if settings.AZURE_AI_SEARCH_ENDPOINT:
        logger.info("✓ RAG: Azure AI Search enabled")
    if settings.SHAREPOINT_ENABLED:
        logger.info("✓ RAG: SharePoint enabled")


# Global RAG service instance
rag_service: RAGService = None


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


@app.get("/api/mcp-config")
async def get_mcp_config():
    """
    Get MCP configuration status.
    
    This endpoint returns information about MCP (OAuth Identity Passthrough)
    configuration, useful for debugging and verification.
    
    Returns:
        Dict with MCP configuration details
    """
    logger.info("MCP config check requested")
    return {
        "mcp_enabled": settings.MCP_ENABLED,
        "description": "OAuth Identity Passthrough (MCP) for Azure Foundry agents",
        "status": "enabled" if settings.MCP_ENABLED else "disabled",
        "implementation": {
            "headers_used": ["X-User-Id", "X-User-Email"],
            "context_includes": [
                "oauth_token",
                "user_identity (azure_id, email, name)",
                "mcp_enabled flag",
                "timestamp"
            ]
        },
        "how_to_verify": {
            "step_1": "Send a chat message with authentication",
            "step_2": "Check backend logs for '✓ MCP ENABLED' message",
            "step_3": "Verify X-User-Id and X-User-Email headers in logs",
            "step_4": "Check 'Request headers being sent' in logs"
        }
    }


@app.get("/api/user-context")
async def get_user_context(current_user: UserProfile = Depends(get_current_user)):
    """
    Get current user context information.
    
    This endpoint can be called by Azure Foundry agents (as a tool) to retrieve
    the authenticated user's information. Agents can use this to personalize
    responses with the user's email and name.
    
    Returns:
        Dict with user identity information
    """
    logger.info(f"User context requested for: {current_user.email}")
    return {
        "success": True,
        "user": {
            "azure_id": current_user.azure_id,
            "email": current_user.email,
            "name": current_user.name,
            "display_name": current_user.display_name
        },
        "message": f"User {current_user.name} is logged in as {current_user.email}",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/user-roles")
async def get_user_roles(current_user: UserProfile = Depends(get_current_user)):
    """
    Get current user's assigned roles for RBAC.
    
    This endpoint returns the roles assigned to the authenticated user,
    which determine which agents they can access.
    
    Returns:
        Dict with user roles and permissions
    """
    logger.info(f"User roles requested for: {current_user.email}")
    
    user_profile = {
        "email": current_user.email,
        "azure_data": {}  # Can be enhanced with Azure AD groups
    }
    
    roles = get_user_roles_from_profile(user_profile)
    roles_list = [role.value for role in roles]
    
    return {
        "success": True,
        "user_email": current_user.email,
        "roles": roles_list,
        "description": {
            "admin": "Full access to all agents",
            "analyst": "Access to data analysis and reporting agents",
            "user": "Access to basic chat agents",
            "guest": "Limited access to public agents"
        },
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
    Get list of available Azure Foundry agents filtered by user's role.

    This endpoint retrieves all available agents from Azure Foundry,
    synchronizes them with the local database, and filters them based
    on the user's assigned roles (RBAC).

    Headers:
        Authorization: Bearer <azure_ad_access_token>

    Returns:
        AgentResponse: List of agents accessible to the user
    """
    try:
        logger.info(f"Fetching agents for user: {current_user.email}")
        
        # Get all agents from Azure Foundry
        all_agents = await foundry_client.list_agents()
        
        # Convert Agent models to dicts for filtering
        agents_dicts = [agent.model_dump() if hasattr(agent, 'model_dump') else agent.__dict__ for agent in all_agents]
        
        # Filter agents based on user's roles (RBAC)
        user_profile = {
            "email": current_user.email,
            "azure_data": {}  # Can be enhanced with Azure AD groups
        }
        filtered_agents_dicts = filter_agents_for_user(agents_dicts, user_profile)
        
        # Convert back to Agent models
        from models import Agent as AgentModel
        filtered_agents = [AgentModel(**agent_dict) if isinstance(agent_dict, dict) else agent_dict 
                          for agent_dict in filtered_agents_dicts]
        
        logger.info(f"Filtered {len(all_agents)} agents to {len(filtered_agents)} for user {current_user.email}")

        return AgentResponse(
            agents=filtered_agents,
            count=len(filtered_agents)
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
        
        # Log MCP context at entry point
        logger.info("═══ MCP CONTEXT AT ENDPOINT ═══")
        logger.info(f"MCP Context Available: {mcp_context is not None}")
        if mcp_context:
            logger.info(f"MCP Enabled: {mcp_context.get('mcp_enabled')}")
            user_id = mcp_context.get('user_identity', {}).get('azure_id', 'unknown')
            user_email = mcp_context.get('user_identity', {}).get('email', 'unknown')
            logger.info(f"User Identity - Email: {user_email}, ID: {user_id}")
            logger.info(f"Current User - Email: {current_user.email}, ID: {current_user.id}")
        logger.info("══════════════════════════════")

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
        logger.info(f"MCP Context being passed: {bool(mcp_context)}")
        if mcp_context:
            logger.info(f"  └─ MCP will include user: {mcp_context.get('user_identity', {}).get('email')}")
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

@app.post("/api/chat/stream")
async def send_chat_message_stream(
    request: SendMessageRequest,
    current_user: UserProfile = Depends(get_current_user),
    mcp_context: Dict[str, Any] = Depends(get_mcp_context)
):
    """
    Send a message to an agent and stream the response in real-time.

    This endpoint uses a FastAPI StreamingResponse to deliver the agent's
    response chunks instantly as they are received from Azure Foundry.

    Headers:
        Authorization: Bearer <azure_ad_access_token>

    Body:
        SendMessageRequest: session_id, content

    Returns:
        StreamingResponse (text/event-stream): Stream of response content
    """
    try:
        logger.info(f"Streaming message request for session {request.session_id}")

        # 1. Verify session (same logic as send_chat_message)
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

        # 2. Store user message (You will need to create a placeholder/incomplete message
        #    in the database if you want to store the stream, but for simplicity,
        #    we'll skip user message storage here for a cleaner demo)

        # 3. Get conversation history (same logic)
        message_entities = await asyncio.to_thread(
            table_storage.get_session_messages,
            str(request.session_id),
            limit=20
        )

        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in message_entities
        ]

        # 4. Get agent info (same logic)
        agent = await foundry_client.get_agent_by_id(session_entity["agent_id"])
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )

        # 5. Define the asynchronous generator for streaming
        async def stream_generator():
            full_response_content = ""
            
            # Start the stream from the Foundry Client
            async for chunk in foundry_client.send_message_stream(
                agent_id=agent.azure_agent_id,
                message=request.content,
                conversation_history=conversation_history,
                mcp_context=mcp_context
            ):
                # Accumulate content for eventual storage
                full_response_content += chunk
                
                # Yield the chunk immediately to the client
                yield chunk

            # --- Post-Stream Storage (Crucial Step for History) ---
            logger.info(f"Stream complete. Storing response for session {request.session_id}")
            
            # Store the final agent response
            if full_response_content:
                await asyncio.to_thread(
                    table_storage.create_message,
                    session_id=str(request.session_id),
                    role="assistant",
                    content=full_response_content,
                    metadata={"stream_complete": True}
                )
            
            # Update session timestamp
            await asyncio.to_thread(
                table_storage.update_session_timestamp,
                user_azure_id=current_user.azure_id,
                session_id=str(request.session_id)
            )
            # --- End Post-Stream Storage ---

        # 6. Return StreamingResponse
        # Note: We use 'text/plain' or 'text/event-stream' here depending on the client expectation.
        # Since the generator yields raw content chunks (not full SSE packets), 'text/plain' is often simpler for a client to consume.
        # If the client expects formal SSE, you'd wrap the chunks in "data: ..." format.
        return StreamingResponse(
            stream_generator(),
            media_type="text/plain" 
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming message: {str(e)}")
        # If the streaming fails before the response starts, raise an HTTP error.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream message: {str(e)}"
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


# RAG (Retrieval-Augmented Generation) Endpoints
@app.post("/api/rag/search")
async def search_knowledge_base(
    query: str,
    sources: List[str] = ["ai_search", "sharepoint"],
    top: int = 5,
    current_user: UserProfile = Depends(get_current_user),
    mcp_context: Dict[str, Any] = Depends(get_mcp_context)
):
    """
    Search knowledge base (Azure AI Search and/or SharePoint) with user context.
    
    This endpoint implements RAG by searching across configured knowledge sources
    using the user's authentication context for permission-aware retrieval.
    
    Args:
        query: Search query text
        sources: List of sources to search (ai_search, sharepoint)
        top: Number of results per source
    
    Headers:
        Authorization: Bearer <azure_ad_access_token>
    
    Returns:
        Combined search results from all sources
    """
    try:
        if not rag_service:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="RAG service not configured. Please set AZURE_AI_SEARCH_ENDPOINT or enable SharePoint."
            )
        
        logger.info(f"RAG search for user {current_user.email}: {query}")
        
        # Get user's OAuth token for SharePoint access
        user_token = mcp_context.get("oauth_token")
        
        results = await rag_service.search_knowledge_base(
            query=query,
            user_email=current_user.email,
            user_token=user_token,
            sources=sources,
            top=top
        )
        
        return results
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge base search failed: {str(e)}"
        )


@app.get("/api/rag/config")
async def get_rag_config():
    """
    Get RAG configuration status.
    
    Returns:
        Dict with RAG configuration details and enabled sources
    """
    return {
        "rag_enabled": rag_service is not None,
        "sources": {
            "azure_ai_search": {
                "enabled": settings.AZURE_AI_SEARCH_ENDPOINT is not None,
                "endpoint": settings.AZURE_AI_SEARCH_ENDPOINT,
                "index": settings.AZURE_AI_SEARCH_INDEX if settings.AZURE_AI_SEARCH_ENDPOINT else None
            },
            "sharepoint": {
                "enabled": settings.SHAREPOINT_ENABLED,
                "site_url": settings.SHAREPOINT_SITE_URL if settings.SHAREPOINT_ENABLED else None
            }
        },
        "oauth_passthrough": settings.MCP_ENABLED,
        "description": "RAG integration with Azure AI Search and SharePoint using OAuth Identity Passthrough"
    }


@app.post("/api/rag/consent")
async def request_rag_consent(
    source: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Request additional OAuth consent for RAG sources.
    
    This endpoint returns the OAuth consent URL for accessing
    specific RAG sources like SharePoint that require additional permissions.
    
    Args:
        source: RAG source (sharepoint, onedrive, etc.)
    
    Returns:
        Dict with consent URL and required scopes
    """
    consent_configs = {
        "sharepoint": {
            "scopes": [
                "Sites.Read.All",
                "Files.Read.All",
                "User.Read"
            ],
            "resource": "Microsoft SharePoint"
        },
        "onedrive": {
            "scopes": [
                "Files.Read.All",
                "User.Read"
            ],
            "resource": "Microsoft OneDrive"
        }
    }
    
    if source not in consent_configs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown RAG source: {source}. Available: {list(consent_configs.keys())}"
        )
    
    config = consent_configs[source]
    scopes_str = " ".join(config["scopes"])
    
    # Build OAuth consent URL
    consent_url = (
        f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={settings.AZURE_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri=http://localhost:5173"  # Update for production
        f"&response_mode=query"
        f"&scope={scopes_str}"
        f"&state={source}"
    )
    
    return {
        "source": source,
        "resource": config["resource"],
        "scopes": config["scopes"],
        "consent_url": consent_url,
        "instructions": (
            f"To access {config['resource']}, you need to grant additional permissions. "
            f"Please visit the consent_url to authorize access."
        )
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
