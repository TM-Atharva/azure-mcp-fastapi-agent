# Azure AI Chatbot Application

A comprehensive, production-ready chatbot application with Azure Entra ID authentication, Azure Foundry integration, and OAuth Identity Passthrough (MCP). Features a mobile-responsive React frontend and FastAPI backend.

## ⭐ Phase 1 Features (NEW)

**Just Added:**

- **RBAC + Agent Visibility**: Users see only agents they have permission to access
- **RAG Integration**: Azure AI Search and SharePoint knowledge base
- **OAuth Consent Flow**: Enhanced permissions for SharePoint access

📖 **[Read Phase 1 Documentation →](PHASE1_README.md)**

---

## Features

### Authentication & Security

- **Azure Entra ID OAuth 2.0**: Enterprise-grade authentication
- **OAuth Identity Passthrough (MCP)**: Seamless user context propagation to AI agents
- **RBAC (Role-Based Access Control)**: ⭐ NEW - Filter agents by user role
- **Secure Token Validation**: JWT validation with JWKS
- **Row Level Security**: Database-level security with Azure Table Storage

### AI Integration

- **Azure Foundry Integration**: Dynamic agent discovery and management
- **RAG (Retrieval-Augmented Generation)**: ⭐ NEW - Azure AI Search + SharePoint
- **Multi-Agent Support**: Chat with multiple specialized AI agents
- **Context-Aware Conversations**: Full conversation history maintained
- **Real-Time Responses**: Responsive chat interface with typing indicators

### User Experience

- **Mobile-Responsive Design**: Optimized for mobile, tablet, and desktop
- **Modern UI**: Clean, professional interface with Tailwind CSS
- **Session Management**: Create, view, and delete chat sessions
- **Error Handling**: Comprehensive error states and user feedback

## Technology Stack

### Frontend

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **MSAL Browser** for Azure authentication
- **Axios** for API communication
- **Lucide React** for icons

### Backend

- **FastAPI** for REST API
- **Python 3.11+**
- **MSAL** for token validation
- **Azure AI Projects SDK** for Foundry integration
- **Supabase** for database and storage

### Infrastructure

- **Supabase**: PostgreSQL database with RLS
- **Azure Entra ID**: Identity and access management
- **Azure Foundry**: AI agent platform

## Architecture

### OAuth Identity Passthrough (MCP)

The application implements OAuth Identity Passthrough, ensuring that:

1. **User Context Preservation**: User identity is maintained throughout the conversation
2. **Secure Authorization**: Agents can make authorized API calls on behalf of users
3. **Audit Trails**: All actions are logged with actual user information
4. **Resource Access**: Agents can access user-specific resources securely

#### MCP Flow

```
User → Azure AD Login → Access Token
  ↓
Access Token → Frontend → Backend API
  ↓
Backend validates token → Creates MCP Context
  ↓
MCP Context + Message → Azure Foundry Agent
  ↓
Agent uses user's token → Accesses resources
  ↓
Agent response → Backend → Frontend → User
```

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Azure subscription
- Supabase account (already configured in this project)

### 1. Azure Entra ID Configuration

#### Create App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations** > **New registration**
3. Configure:
   - **Name**: Azure AI Chatbot
   - **Supported account types**: Single tenant or multi-tenant
   - **Redirect URI**:
     - Platform: Single-page application (SPA)
     - URI: `http://localhost:5173`
4. Click **Register**

#### Configure Authentication

1. In your app registration, go to **Authentication**
2. Under **Implicit grant and hybrid flows**, enable:
   - Access tokens
   - ID tokens
3. Add additional redirect URIs as needed for production
4. Save changes

#### Create Client Secret (for backend)

1. Go to **Certificates & secrets** > **New client secret**
2. Add description: "Backend API Secret"
3. Set expiration (recommend 24 months)
4. Copy the secret value immediately (you won't be able to see it again)

#### Note Required Values

Copy these values for configuration:

- **Application (client) ID**: Found on Overview page
- **Directory (tenant) ID**: Found on Overview page
- **Client secret**: Copied from previous step

### 2. Azure Foundry Configuration

#### Create Azure AI Foundry Project

1. Go to [Azure AI Foundry Portal](https://ai.azure.com)
2. Create a new project or use an existing one
3. Note the following values:
   - **Project Endpoint**: Found in project settings
   - **API Key**: Generate in project settings > Keys and endpoints
   - **Project ID**: Found in project settings

#### Configure Agents

1. In Azure AI Foundry, create or configure AI agents
2. Ensure agents are published and active
3. Note agent capabilities and descriptions

### 3. Environment Configuration

#### Frontend Configuration

Update `/tmp/cc-agent/61459630/project/.env`:

```env
VITE_SUPABASE_URL=https://ifxjccehmmukumnftbbl.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmeGpjY2VobW11a3VtbmZ0YmJsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU2NDY3ODQsImV4cCI6MjA4MTIyMjc4NH0.ljZRZ7Mv4HWB9CP7AeTaaXgM3GzBgkSkEro70XCiFeo

VITE_AZURE_CLIENT_ID=<your_azure_client_id>
VITE_AZURE_TENANT_ID=<your_azure_tenant_id>
VITE_AZURE_REDIRECT_URI=http://localhost:5173

VITE_API_URL=http://localhost:8000/api
```

#### Backend Configuration

Create `backend/.env` file (use `backend/.env.example` as template):

```env
# Azure Entra ID
AZURE_CLIENT_ID=<your_azure_client_id>
AZURE_TENANT_ID=<your_azure_tenant_id>
AZURE_CLIENT_SECRET=<your_client_secret>

# Azure Foundry
AZURE_FOUNDRY_ENDPOINT=<your_foundry_endpoint>
AZURE_FOUNDRY_API_KEY=<your_foundry_api_key>
AZURE_FOUNDRY_PROJECT_ID=<your_project_id>

# Supabase (Service Role Key for backend)
SUPABASE_URL=https://ifxjccehmmukumnftbbl.supabase.co
SUPABASE_SERVICE_KEY=<your_supabase_service_role_key>

# Settings
MCP_ENABLED=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DEBUG=false
```

### 4. Installation

#### Install Frontend Dependencies

```bash
npm install
```

#### Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 5. Database Setup

The database schema is already created in Supabase. To verify:

1. Go to your Supabase project dashboard
2. Navigate to **Table Editor**
3. Verify these tables exist:
   - `users`
   - `agents`
   - `chat_sessions`
   - `chat_messages`

### 6. Running the Application

#### Start Backend Server

```bash
cd backend
python main.py
```

The backend will run on `http://localhost:8000`

API documentation available at:

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

#### Start Frontend Development Server

```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

### 7. Testing the Application

1. Open `http://localhost:5173` in your browser
2. Click "Sign in with Microsoft"
3. Complete Azure AD authentication
4. Select an AI agent from the list
5. Start chatting!

## API Endpoints

### Authentication

- `GET /api/auth/me` - Get current user profile

### Agents

- `GET /api/agents` - List all available agents
- `GET /api/agents/{agent_id}` - Get specific agent

### Chat Sessions

- `POST /api/sessions` - Create new chat session
- `GET /api/sessions` - List user's sessions
- `GET /api/sessions/{session_id}` - Get session with message history
- `DELETE /api/sessions/{session_id}` - Delete session

### Messages

- `POST /api/chat` - Send message and get response

### Health

- `GET /` - Basic health check
- `GET /api/health` - Detailed health check

## OAuth Identity Passthrough (MCP) Implementation

### How It Works

1. **User Authentication**: User logs in with Azure Entra ID and receives an access token
2. **Token Propagation**: Frontend includes token in Authorization header for all API calls
3. **Token Validation**: Backend validates token using Azure AD JWKS endpoint
4. **MCP Context Creation**: Backend creates MCP context with user identity and token
5. **Agent Communication**: MCP context is passed to Azure Foundry with each message
6. **Agent Authorization**: Agent uses user's token to access resources on their behalf

### Security Considerations

- **Token Security**: Tokens are transmitted over HTTPS only
- **Token Validation**: Strict JWT validation with signature, expiration, and audience checks
- **Least Privilege**: Agents only have access to what user's token permits
- **Audit Logging**: All actions logged with user identity for compliance

## Database Schema

### Users Table

Stores authenticated user information from Azure Entra ID

### Agents Table

Stores AI agents synced from Azure Foundry

### Chat Sessions Table

Tracks conversations between users and agents

### Chat Messages Table

Stores all messages with role (user/assistant/system)

All tables have Row Level Security (RLS) enabled with policies ensuring users can only access their own data.

## Development

### Frontend Development

```bash
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run typecheck    # Run TypeScript type checking
```

### Backend Development

```bash
cd backend
uvicorn main:app --reload    # Development server with auto-reload
python main.py               # Production server
```

### Code Structure

```
project/
├── src/
│   ├── components/          # React components
│   │   ├── Login.tsx        # Login page
│   │   ├── AgentSelection.tsx  # Agent selection UI
│   │   └── Chat.tsx         # Chat interface
│   ├── contexts/            # React contexts
│   │   └── AuthContext.tsx  # Authentication context
│   ├── config/              # Configuration
│   │   └── azureConfig.ts   # Azure MSAL config
│   ├── services/            # API services
│   │   └── api.ts           # API client
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   ├── App.tsx              # Main app component
│   └── main.tsx             # Entry point
├── backend/
│   ├── main.py              # FastAPI application
│   ├── auth.py              # Authentication & MCP
│   ├── azure_foundry.py     # Azure Foundry integration
│   ├── models.py            # Pydantic models
│   ├── config.py            # Configuration
│   └── requirements.txt     # Python dependencies
└── README.md                # This file
```

## Troubleshooting

### Authentication Issues

**Problem**: "Invalid token" or "Token has expired"

- **Solution**: Ensure Azure AD app registration is configured correctly
- Check that redirect URI matches exactly
- Verify client ID and tenant ID are correct

**Problem**: "Failed to fetch user profile"

- **Solution**: Ensure `User.Read` scope is granted in Azure AD
- Check that access token has required permissions

### Agent Loading Issues

**Problem**: "Failed to load agents"

- **Solution**: Verify Azure Foundry credentials are correct
- Check that agents are published in Azure Foundry
- Ensure API endpoint is accessible

### Database Issues

**Problem**: "Failed to create session" or "Access denied"

- **Solution**: Verify Supabase URL and service key are correct
- Check that RLS policies are properly configured
- Ensure user exists in users table

### Backend Connection Issues

**Problem**: Frontend can't connect to backend

- **Solution**: Ensure backend is running on port 8000
- Check CORS settings in backend config
- Verify `VITE_API_URL` is set correctly in frontend .env

## Production Deployment

### Frontend Deployment

1. Build the frontend:

   ```bash
   npm run build
   ```

2. Deploy the `dist/` folder to your hosting service (Vercel, Netlify, etc.)

3. Update environment variables for production:
   - Set production Azure redirect URI
   - Update API URL to production backend

### Backend Deployment

1. Choose a hosting service (Azure App Service, AWS, etc.)

2. Set environment variables on hosting platform

3. Deploy backend code

4. Update CORS_ORIGINS to include production frontend URL

### Azure AD Production Configuration

1. Add production redirect URI to Azure AD app registration
2. Update any production-specific scopes or permissions
3. Consider using separate app registrations for dev/prod

## Security Best Practices

1. **Never commit secrets**: Use environment variables
2. **Use HTTPS**: Always in production
3. **Rotate keys**: Regularly rotate client secrets and API keys
4. **Monitor logs**: Watch for suspicious authentication attempts
5. **Update dependencies**: Keep all packages up to date
6. **RLS policies**: Never bypass Row Level Security
7. **Input validation**: Backend validates all inputs
8. **Rate limiting**: Consider adding rate limiting in production

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:

1. Check this documentation
2. Review Azure AD and Azure Foundry documentation
3. Check application logs for error details
4. Review Supabase logs for database issues
