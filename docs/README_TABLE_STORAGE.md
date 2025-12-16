# Azure AI Chatbot with Table Storage

A production-ready chatbot application featuring Azure Entra ID authentication, Azure Foundry AI integration, and OAuth Identity Passthrough (MCP). Data is persisted in Azure Table Storage.

## Key Features

### Authentication & Security
- **Azure Entra ID OAuth 2.0**: Enterprise-grade authentication
- **OAuth Identity Passthrough (MCP)**: User context propagation to AI agents
- **Secure Token Validation**: JWT validation with JWKS

### Data Persistence
- **Azure Table Storage**: Scalable NoSQL storage for chat data
- **Auto-provisioning**: Tables created automatically on first run
- **Chat History**: Full conversation history maintained

### AI Integration
- **Azure Foundry**: Dynamic agent discovery and communication
- **Multi-Agent Support**: Chat with multiple specialized AI agents
- **Context-Aware**: Full conversation history in agent calls

### User Experience
- **Mobile-Responsive**: Optimized for all screen sizes
- **Real-Time Chat**: Responsive interface with typing indicators
- **Session Management**: Create, view, and delete chat sessions

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Azure subscription
- Azure Entra ID App Registration
- Azure AI Foundry project
- Azure Storage Account

### 1. Clone and Install

```bash
# Install frontend dependencies
npm install

# Install backend dependencies
cd backend
pip install -r requirements.txt
```

### 2. Azure Setup

#### A. Azure Entra ID (5 min)
See [SETUP.md](./SETUP.md) for detailed instructions.

Quick version:
1. Create App Registration in Azure Portal
2. Note Client ID and Tenant ID
3. Create Client Secret
4. Configure redirect URI: `http://localhost:5173`

#### B. Azure Table Storage (2 min)
See [AZURE_STORAGE_SETUP.md](./AZURE_STORAGE_SETUP.md) for detailed instructions.

Quick version:
1. Create Storage Account in Azure Portal
2. Copy connection string from Access Keys
3. Add to `backend/.env`

#### C. Azure Foundry (5 min)
1. Create or open project in Azure AI Foundry
2. Note endpoint, API key, and project ID
3. Add agents to your project

### 3. Configure Environment

#### Frontend (.env)
```env
VITE_AZURE_CLIENT_ID=your_client_id
VITE_AZURE_TENANT_ID=your_tenant_id
VITE_AZURE_REDIRECT_URI=http://localhost:5173
VITE_API_URL=http://localhost:8000/api
```

#### Backend (backend/.env)
```env
# Azure Entra ID
AZURE_CLIENT_ID=your_client_id
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_SECRET=your_client_secret

# Azure Foundry
AZURE_FOUNDRY_ENDPOINT=your_foundry_endpoint
AZURE_FOUNDRY_API_KEY=your_foundry_api_key
AZURE_FOUNDRY_PROJECT_ID=your_project_id

# Azure Table Storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string

# Settings
MCP_ENABLED=true
CORS_ORIGINS=http://localhost:5173
DEBUG=false
```

### 4. Run Application

#### Start Backend (Terminal 1)
```bash
cd backend
python main.py
```

Server starts on: http://localhost:8000
API docs: http://localhost:8000/api/docs

#### Start Frontend (Terminal 2)
```bash
npm run dev
```

App opens on: http://localhost:5173

### 5. Use the Application

1. Open http://localhost:5173
2. Click "Sign in with Microsoft"
3. Complete Azure AD authentication
4. Select an AI agent
5. Start chatting!

## OAuth Identity Passthrough (MCP)

This application implements MCP to maintain user identity throughout conversations:

**Flow:**
1. User authenticates with Azure AD → receives access token
2. Frontend sends token with each API request
3. Backend validates token and creates MCP context
4. MCP context (token + user identity) passed to Azure Foundry
5. Agent uses user's token for authorized operations
6. Complete audit trail maintained

**Benefits:**
- Agents access user-specific resources securely
- Proper authorization at every level
- Full audit trail with user information
- Compliance with security requirements

## Architecture

### Frontend
- React 18 with TypeScript
- MSAL for Azure authentication
- Axios for API calls
- Tailwind CSS for styling

### Backend
- FastAPI for REST API
- Azure SDK for authentication
- Azure Foundry client for AI
- Azure Table Storage for data

### Data Storage
- **Azure Table Storage** (NoSQL)
  - users: User profiles
  - agents: AI agents
  - sessions: Chat sessions
  - messages: Chat messages

## API Endpoints

### Authentication
- `GET /api/auth/me` - Current user

### Agents
- `GET /api/agents` - List agents
- `GET /api/agents/{id}` - Get agent

### Sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions` - List user sessions
- `GET /api/sessions/{id}` - Get session with history
- `DELETE /api/sessions/{id}` - Delete session

### Chat
- `POST /api/chat` - Send message (with MCP)

## Development

### Frontend
```bash
npm run dev          # Dev server
npm run build        # Production build
npm run typecheck    # Type checking
```

### Backend
```bash
cd backend
python main.py       # Start server
```

## Deployment

### Frontend
1. Build: `npm run build`
2. Deploy `dist/` to your hosting service

### Backend
1. Deploy to Azure App Service, AWS, or similar
2. Set environment variables
3. Update CORS origins

### Azure Table Storage
- Already hosted and managed
- Automatic scaling
- Built-in redundancy

## Troubleshooting

### Backend won't start
- Check all environment variables are set
- Verify Azure Storage connection string is correct
- Ensure Python dependencies are installed

### Frontend can't connect
- Check backend is running on port 8000
- Verify CORS settings
- Check browser console for errors

### Authentication fails
- Verify Client ID and Tenant ID match
- Check redirect URI is configured in Azure AD
- Ensure App Registration is set up correctly

### Tables not created
- Tables are created automatically on first use
- Check backend logs for errors
- Verify storage account connection string

## Security Best Practices

1. **Never commit secrets** - Use environment variables
2. **Use HTTPS in production**
3. **Rotate keys regularly**
4. **Monitor logs** for suspicious activity
5. **Keep dependencies updated**
6. **Restrict CORS** to known domains
7. **Enable storage firewall** in production

## Documentation

- [SETUP.md](./SETUP.md) - Detailed setup guide
- [AZURE_STORAGE_SETUP.md](./AZURE_STORAGE_SETUP.md) - Storage setup
- [backend/README.md](./backend/README.md) - Backend API docs

## Cost Estimation

**Azure Services (Monthly):**
- Azure Table Storage: $0.50 - $2 (very low traffic)
- Azure Foundry: Based on usage
- Azure Entra ID: Free tier sufficient

**Total for Development: < $5/month**

## Support

For issues:
1. Check documentation
2. Review Azure Portal logs
3. Check application logs (backend console)
4. Verify all environment variables

## License

MIT License

---

Built with Azure Entra ID, Azure Foundry, and Azure Table Storage
