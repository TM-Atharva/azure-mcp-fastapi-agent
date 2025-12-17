"""
Pydantic models for request/response validation

These models define the data structures used throughout the API
for type validation, serialization, and documentation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class UserProfile(BaseModel):
    """User profile information from Azure Entra ID"""
    id: UUID
    azure_id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: datetime


class AgentCapabilities(BaseModel):
    """Agent capabilities and metadata"""
    models: Optional[List[str]] = []
    max_tokens: Optional[int] = None
    supports_streaming: bool = False
    supports_functions: bool = False


class Agent(BaseModel):
    """AI Agent from Azure Foundry"""
    id: UUID
    azure_agent_id: str
    name: str
    description: Optional[str] = None
    capabilities: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class AgentResponse(BaseModel):
    """Response containing list of available agents"""
    agents: List[Agent]
    count: int


class ChatSession(BaseModel):
    """Chat session between user and agent"""
    id: UUID
    user_id: UUID
    agent_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool


class ChatMessage(BaseModel):
    """Individual chat message"""
    id: UUID
    session_id: UUID
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    metadata: Dict[str, Any] = {}
    created_at: datetime


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session"""
    agent_id: UUID
    title: Optional[str] = "New Chat"


class SendMessageRequest(BaseModel):
    """Request to send a message in a chat session"""
    session_id: UUID
    content: str
    metadata: Optional[Dict[str, Any]] = {}


class MessageResponse(BaseModel):
    """Response containing a chat message"""
    message: ChatMessage


class SessionResponse(BaseModel):
    """Response containing a chat session"""
    session: ChatSession


class ChatHistoryResponse(BaseModel):
    """Response containing chat history"""
    messages: List[ChatMessage]
    session: ChatSession


class TokenValidationRequest(BaseModel):
    """Request to validate Azure Entra ID token"""
    access_token: str


class TokenValidationResponse(BaseModel):
    """Response from token validation"""
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# MCP Models
# ============================================================

class MCPServer(BaseModel):
    """MCP server information"""
    label: str
    display_name: str
    description: str = ""
    url: str
    requires_oauth: bool = True
    scopes: List[str] = []
    icon: str = "🔗"
    connected: bool = False
    connected_at: Optional[str] = None


class MCPServersResponse(BaseModel):
    """Response containing list of MCP servers"""
    servers: List[MCPServer]


class MCPConsentCallbackRequest(BaseModel):
    """Request to store OAuth consent result"""
    server_label: str
    access_token: str
    refresh_token: Optional[str] = None


class MCPConsentRequiredResponse(BaseModel):
    """Response when OAuth consent is required"""
    type: str = "oauth_consent_required"
    consent_url: str
    server_label: str
    server_display_name: str


class MCPToolCallInfo(BaseModel):
    """Information about an MCP tool call in progress"""
    tool_name: str
    server_label: str
    status: str = "running"  # running, completed, failed
    arguments: Optional[Dict[str, Any]] = None

