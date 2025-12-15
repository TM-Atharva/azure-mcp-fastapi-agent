# Azure Chatbot Backend API

FastAPI backend with Azure Entra ID authentication, Azure Foundry integration, and OAuth Identity Passthrough (MCP).

## Quick Start

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### Run Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or:

```bash
python main.py
```

## Architecture

### File Structure

```
backend/
├── main.py              # FastAPI application and routes
├── auth.py              # Authentication middleware and MCP
├── azure_foundry.py     # Azure Foundry client integration
├── models.py            # Pydantic models for validation
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── README.md           # This file
```

### Key Components

#### 1. Authentication (`auth.py`)

Implements Azure Entra ID OAuth 2.0 token validation:

```python
from auth import get_current_user, get_mcp_context

@app.get("/protected")
async def protected_route(user: UserProfile = Depends(get_current_user)):
    return {"user_id": user.id}
```

**Features**:

- JWT token validation with JWKS
- User profile management in Supabase
- OAuth Identity Passthrough (MCP) context creation
- Automatic user creation/update on login

#### 2. Azure Foundry Integration (`azure_foundry.py`)

Manages communication with Azure Foundry:

```python
from azure_foundry import foundry_client

# List agents
agents = await foundry_client.list_agents()

# Send message with MCP context
response = await foundry_client.send_message(
    agent_id="agent-123",
    message="Hello",
    conversation_history=[],
    mcp_context=mcp_ctx
)
```

**Features**:

- Agent discovery and synchronization
- Message sending with user context
- Streaming support (prepared for future use)
- Automatic agent database sync

#### 3. OAuth Identity Passthrough (MCP)

The MCP implementation ensures user context is maintained throughout:

**Flow**:

1. Frontend sends request with user's Azure AD access token
2. Backend validates token and extracts user claims
3. Backend creates MCP context:
   ```python
   {
       "oauth_token": "original_user_token",
       "user_identity": {
           "azure_id": "user_oid",
           "email": "user@example.com",
           "name": "User Name"
       },
       "mcp_enabled": true,
       "timestamp": "2024-01-01T00:00:00Z"
   }
   ```
4. MCP context is passed to Azure Foundry with each agent call
5. Agent can use user's token to access resources on their behalf

**Security**:

- Original token is preserved and validated
- User identity is verified at every step
- Audit trail maintained with actual user information
- Token permissions scope agent capabilities

#### 4. Configuration (`config.py`)

Centralized configuration with Pydantic validation:

```python
from config import settings

# Access configuration
client_id = settings.AZURE_CLIENT_ID
authority = settings.authority_url
```

**Features**:

- Environment variable validation
- Type checking with Pydantic
- Default values and computed properties
- Secure credential management

#### 5. Data Models (`models.py`)

Pydantic models for request/response validation:

```python
from models import SendMessageRequest, MessageResponse

@app.post("/chat", response_model=MessageResponse)
async def chat(request: SendMessageRequest):
    # Request is automatically validated
    pass
```

**Benefits**:

- Automatic request validation
- OpenAPI documentation generation
- Type safety throughout application
- Clear API contracts

## API Documentation

### Interactive Documentation

Once the server is running, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Authentication

All protected endpoints require Bearer token authentication:

```
Authorization: Bearer <azure_ad_access_token>
```

### Endpoints

#### Health Check

```
GET /
GET /api/health
```

#### Authentication

```
GET /api/auth/me
```

Returns current user profile.

#### Agents

```
GET /api/agents
GET /api/agents/{agent_id}
```

#### Sessions

```
POST /api/sessions
GET /api/sessions
GET /api/sessions/{session_id}
DELETE /api/sessions/{session_id}
```

#### Chat

```
POST /api/chat
```

Sends message with OAuth Identity Passthrough.

## OAuth Identity Passthrough (MCP) Deep Dive

### What is MCP?

OAuth Identity Passthrough (MCP - Managed Context Propagation) is a security pattern that maintains user identity and authorization context throughout a multi-service architecture.

### Why MCP?

Without MCP, AI agents would operate under a service account identity, making it impossible to:

- Access user-specific resources
- Implement proper authorization
- Maintain audit trails with actual user identity
- Comply with security and compliance requirements

### MCP Implementation Details

#### Step 1: Token Reception

```python
@app.post("/chat")
async def chat(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    # Token is user's original Azure AD token
```

#### Step 2: Token Validation

```python
# Validate token signature, expiration, audience
decoded = jwt.decode(
    token,
    signing_key.key,
    algorithms=["RS256"],
    audience=settings.AZURE_CLIENT_ID,
    issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0"
)
```

#### Step 3: MCP Context Creation

```python
def create_mcp_context(token: str, user_info: Dict) -> Dict:
    return {
        "oauth_token": token,
        "user_identity": {
            "azure_id": user_info["oid"],
            "email": user_info["email"],
            "name": user_info["name"]
        },
        "mcp_enabled": True,
        "timestamp": datetime.utcnow().isoformat()
    }
```

#### Step 4: Agent Call with MCP

```python
payload = {
    "message": "Hello",
    "mcp_context": {
        "authorization": f"Bearer {mcp_context['oauth_token']}",
        "user_identity": mcp_context["user_identity"],
        "timestamp": mcp_context["timestamp"]
    }
}

response = await http_client.post(agent_endpoint, json=payload)
```

### MCP Security Considerations

1. **Token Validation**: Always validate tokens before creating MCP context
2. **Token Expiration**: Handle expired tokens gracefully
3. **Scope Verification**: Ensure token has required scopes
4. **Secure Transport**: Always use HTTPS
5. **Token Storage**: Never log or store tokens
6. **Audit Logging**: Log all MCP context usage

## Error Handling

The API uses standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (validation error)
- `401`: Unauthorized (invalid or missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `500`: Internal Server Error

Error responses follow this format:

```json
{
  "detail": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Database Operations

### Supabase Client

The backend uses Supabase service role key for database operations:

```python
from supabase import create_client

supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY
)
```

### Row Level Security

Even with service role key, the application implements RLS-like logic:

```python
# Only fetch user's own data
result = supabase.table("chat_sessions").select("*").eq(
    "user_id", current_user.id
).execute()
```

## Testing

### Manual Testing

Use the interactive API docs at `/api/docs` to test endpoints.

### Example cURL Requests

```bash
# Get current user
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"

# List agents
curl -X GET "http://localhost:8000/api/agents" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create session
curl -X POST "http://localhost:8000/api/sessions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "AGENT_UUID"}'

# Send message
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_UUID",
    "content": "Hello, how are you?"
  }'
```

## Deployment

### Development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or use the built-in server:

```bash
DEBUG=false python main.py
```

### Environment Variables

Ensure all required environment variables are set in production:

- Azure credentials
- Azure Foundry credentials
- Supabase credentials
- CORS origins for your frontend domain

### Docker (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t azure-chatbot-backend .
docker run -p 8000:8000 --env-file .env azure-chatbot-backend
```

## Monitoring and Logging

### Logging

The application uses Python's built-in logging:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("User authenticated: {email}")
logger.error("Failed to fetch agents: {error}")
```

### Health Monitoring

Monitor the health endpoint:

```bash
curl http://localhost:8000/api/health
```

Response includes status of all services:

```json
{
  "status": "healthy",
  "services": {
    "api": "operational",
    "azure_ad": "operational",
    "azure_foundry": "operational",
    "supabase": "operational"
  },
  "mcp_enabled": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Common Issues

### Token Validation Fails

**Symptom**: 401 errors with "Invalid token"

**Solutions**:

- Verify Azure AD tenant ID is correct
- Check that client ID matches
- Ensure token is not expired
- Verify JWKS endpoint is accessible

### Azure Foundry Connection Fails

**Symptom**: 500 errors when listing agents

**Solutions**:

- Verify Azure Foundry endpoint URL
- Check API key is valid
- Ensure project ID is correct
- Verify network connectivity

### Database Access Issues

**Symptom**: 500 errors on session operations

**Solutions**:

- Verify Supabase URL and key
- Check RLS policies are configured
- Ensure tables exist
- Verify service role key has correct permissions

## Contributing

When adding new features:

1. Add Pydantic models to `models.py`
2. Implement business logic in appropriate module
3. Add endpoints to `main.py`
4. Update this documentation
5. Test with interactive docs

## Security Checklist

Before deploying to production:

- [ ] All environment variables configured
- [ ] Debug mode disabled (`DEBUG=false`)
- [ ] CORS origins restricted to production domains
- [ ] HTTPS enforced
- [ ] Client secrets rotated
- [ ] Logging configured for production
- [ ] Error messages don't leak sensitive info
- [ ] Rate limiting configured
- [ ] Health monitoring set up

## License

MIT License
