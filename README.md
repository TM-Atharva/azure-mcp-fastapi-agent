# Azure MCP FastAPI Agent

Enterprise-grade conversational AI platform built on Azure AI Foundry with advanced identity management, role-based access control, and retrieval-augmented generation.

[![Azure AI Foundry](https://img.shields.io/badge/Azure%20AI%20Foundry-Enabled-blue)](https://azure.microsoft.com/en-us/products/ai-foundry/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5.3-3178C6.svg)](https://www.typescriptlang.org/)

---

## 🌟 Key Features

### 🔐 Enterprise Authentication & Security

- **Azure Entra ID OAuth 2.0** - Secure single sign-on with popup-based authentication
- **JWT Token Validation** - JWKS-based token verification with automatic refresh
- **OAuth Identity Passthrough (MCP)** - User context propagation to AI agents with consent flow
- **Azure Table Storage** - Secure data persistence with user-scoped access

### 🎯 Role-Based Access Control (RBAC)

- **Dynamic Agent Filtering** - Users see only authorized agents based on their roles
- **Azure AD App Roles Integration** - No code changes when adding users or roles
- **Configuration-Driven** - Manage permissions via JSON file without code deployment
- **Four Built-in Roles**: Admin (all agents), FinanceAnalyst, HRAnalyst, BasicUser
- **Hot-Reload Support** - Update permissions without server restart

### 🤖 Multi-Agent AI System

- **Azure AI Foundry Integration** - Dynamic agent discovery and management
- **Agent Selection UI** - User-friendly interface for choosing specialized agents
- **Streaming Responses** - Real-time message streaming for better UX
- **Session Management** - Persistent conversation history with context awareness
- **Agent Metadata** - Capabilities, models, and department tagging

### 📚 Retrieval-Augmented Generation (RAG)

- **Azure AI Search Integration** - Semantic search across enterprise knowledge base
- **SharePoint MCP Connector** - Real-time document access with OAuth consent
- **Permission-Aware Search** - Users see only documents they're authorized to access
- **Multi-Source Retrieval** - Combine indexed and real-time data sources
- **Configurable Connectors** - Easy addition of new knowledge sources

### 💬 Modern Chat Experience

- **Real-time Streaming** - Token-by-token response rendering
- **Markdown Support** - Rich text formatting with code syntax highlighting
- **Mobile Responsive** - Optimized for phones, tablets, and desktops
- **Message History** - Persistent sessions with search and filtering
- **Typing Indicators** - Visual feedback during agent processing
- **Error Handling** - Graceful fallbacks with retry mechanisms

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React + TS)                   │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  Login        │  │  Agent       │  │  Chat Interface    │   │
│  │  (MSAL)       │→ │  Selection   │→ │  (Streaming)       │   │
│  └───────────────┘  └──────────────┘  └────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS + JWT
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Auth        │  │  RBAC        │  │  RAG Service         │  │
│  │  Middleware  │→ │  Filter      │→ │  (AI Search)         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Azure AI Foundry (Agent API)                     │   │
│  │  • GPT-4o, GPT-4 Turbo                                   │   │
│  │  • Custom Agents with Tools                              │   │
│  │  • OAuth Identity Passthrough                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Azure Infrastructure                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Entra ID    │  │  Table       │  │  AI Search           │  │
│  │  (OAuth)     │  │  Storage     │  │  (RAG)               │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **Azure Subscription** with:
  - Azure AI Foundry project
  - Azure Entra ID App Registration
  - Azure Table Storage account
  - Azure AI Search (optional, for RAG)

### 1. Clone Repository

```bash
git clone <repository-url>
cd azure-mcp-fastapi-agent
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Create `.env` file:**

```bash
# Azure Entra ID
AZURE_CLIENT_ID=your-client-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_SECRET=your-client-secret

# Azure Foundry
AZURE_FOUNDRY_ENDPOINT=https://your-project.region.api.azureml.ms
AZURE_FOUNDRY_API_KEY=your-api-key
AZURE_FOUNDRY_PROJECT_ID=your-project-id

# Azure Table Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...

# Optional: Azure AI Search (for RAG)
AZURE_AI_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_AI_SEARCH_KEY=your-search-key
AZURE_AI_SEARCH_INDEX=your-index-name
```

**Run backend:**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend running at: http://localhost:8000

### 3. Frontend Setup

```bash
# In root directory
npm install
```

**Create `.env` file:**

```bash
VITE_AZURE_CLIENT_ID=your-client-id
VITE_AZURE_TENANT_ID=your-tenant-id
VITE_API_BASE_URL=http://localhost:8000
```

**Run frontend:**

```bash
npm run dev
```

Frontend running at: http://localhost:5173

---

## 📖 Documentation

Comprehensive guides available in the `docs/` directory:

### Setup & Configuration

- **[Azure Setup Index](docs/AZURE_SETUP_INDEX.md)** - Master guide for all Azure configuration
- **[Azure Foundry 401 Fix](docs/AZURE_FOUNDRY_401_FIX.md)** - Troubleshooting authentication issues
- **[Azure Storage Setup](docs/AZURE_STORAGE_SETUP.md)** - Table Storage configuration
- **[Blocking IO Fix](docs/BLOCKING_IO_FIX.md)** - Async/await best practices

### RBAC & Security

- **[Agent-Level RBAC Guide](docs/AGENT_LEVEL_RBAC_GUIDE.md)** - Complete RBAC implementation explanation
- **[Dynamic RBAC Solutions](docs/DYNAMIC_RBAC_SOLUTIONS.md)** - Three approaches comparison (App Roles, Groups, Database)
- **[RBAC Implementation Guide](docs/RBAC_IMPLEMENTATION_GUIDE.md)** - Step-by-step setup for Tejas/Rahul/Dixit scenario
- **[Azure AD App Roles Setup](docs/AZURE_AD_APP_ROLES_SETUP.md)** - Exact Azure Portal navigation steps
- **[RBAC Azure Setup Guide](docs/RBAC_AZURE_SETUP_GUIDE.md)** - Azure AD Security Groups configuration

### RAG Integration

- **[RAG Azure Setup Guide](docs/RAG_AZURE_SETUP_GUIDE.md)** - Azure AI Search and SharePoint connector setup
- **[README Table Storage](docs/README_TABLE_STORAGE.md)** - Data persistence patterns

### MCP (Model Context Protocol)

- **[MCP Complete Setup](docs/MCP_COMPLETE_SETUP.md)** - End-to-end MCP configuration
- **[MCP Testing Guide](docs/MCP_TESTING_COMPLETE.md)** - Complete testing procedures
- **[MCP Flow Diagram](docs/MCP_FLOW_DIAGRAM.md)** - Visual architecture guide
- **[MCP Verification Guide](docs/MCP_VERIFICATION_GUIDE.md)** - Validation checklist
- **[Official MCP Implementation Plan](docs/OFFICIAL_MCP_IMPLEMENTATION_PLAN.md)** - Migration to Microsoft's official pattern

### Additional Resources

- **[Setup Guides Summary](docs/SETUP_GUIDES_SUMMARY.md)** - Executive overview
- **[Migration to Table Storage](docs/MIGRATION_TO_TABLE_STORAGE.md)** - Database migration guide
- **[Frontend Requirements](FRONTEND_REQUIREMENTS.md)** - UI/UX specifications

---

## 🎯 Use Cases

### 1. Department-Specific AI Assistants

**Scenario:** Finance, HR, and Sales teams need specialized agents

**Implementation:**

- Create Azure AD App Roles: `FinanceAnalyst`, `HRAnalyst`, `SalesAnalyst`
- Configure `backend/rbac_config.json` with agent patterns
- Name agents: "Budget Planning Assistant", "Recruiting Assistant", "CRM Data Analyzer"
- Assign users to roles in Azure Portal

**Result:** Each department sees only their relevant agents

### 2. Enterprise Knowledge Base Chat

**Scenario:** Query company documents, policies, and SharePoint files

**Implementation:**

- Set up Azure AI Search with document indexing
- Configure SharePoint MCP connector
- Enable permission-aware search
- Users automatically see only authorized documents

**Result:** Secure, context-aware knowledge retrieval

### 3. Multi-Tenant Agent Platform

**Scenario:** Multiple clients sharing the same infrastructure

**Implementation:**

- Create separate Azure AD App Roles per tenant
- Use agent metadata for tenant isolation
- Configure per-tenant connection strings
- Enable audit logging for compliance

**Result:** Isolated, secure multi-tenant deployment

---

## 🛠️ Technology Stack

### Frontend

| Technology   | Version | Purpose                 |
| ------------ | ------- | ----------------------- |
| React        | 18.3.1  | UI framework            |
| TypeScript   | 5.5.3   | Type safety             |
| Vite         | 5.4.2   | Build tool & dev server |
| Tailwind CSS | 3.4.1   | Utility-first styling   |
| MSAL Browser | 3.x     | Azure AD authentication |
| Axios        | 1.7.x   | HTTP client             |
| Lucide React | 0.344.0 | Icon library            |

### Backend

| Technology        | Version | Purpose              |
| ----------------- | ------- | -------------------- |
| FastAPI           | 0.115.0 | Web framework        |
| Python            | 3.11+   | Runtime              |
| Pydantic          | 2.x     | Data validation      |
| HTTPX             | 0.27.x  | Async HTTP client    |
| PyJWT             | 2.x     | JWT token validation |
| Cryptography      | 43.x    | JWKS key validation  |
| Azure Data Tables | 12.x    | Table Storage SDK    |
| Azure AI Search   | 11.4.0  | RAG integration      |

### Infrastructure

| Service             | Purpose                        |
| ------------------- | ------------------------------ |
| Azure AI Foundry    | Agent hosting & orchestration  |
| Azure Entra ID      | Authentication & authorization |
| Azure Table Storage | Data persistence               |
| Azure AI Search     | Document retrieval (RAG)       |
| Azure App Service   | Production hosting (optional)  |

---

## 📁 Project Structure

```
azure-mcp-fastapi-agent/
├── backend/
│   ├── main.py                  # FastAPI application
│   ├── auth.py                  # JWT validation & MCP context
│   ├── azure_foundry.py         # Foundry client
│   ├── config.py                # Environment settings
│   ├── models.py                # Pydantic schemas
│   ├── rbac.py                  # Static RBAC (legacy)
│   ├── rbac_dynamic.py          # Dynamic RBAC (recommended)
│   ├── rbac_config.json         # Role permissions config
│   ├── rag_integration.py       # RAG service
│   ├── table_storage.py         # Azure Table Storage client
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # Environment variables
├── src/
│   ├── components/
│   │   ├── Login.tsx            # Authentication UI
│   │   ├── AgentSelection.tsx   # Agent picker
│   │   └── Chat.tsx             # Chat interface
│   ├── contexts/
│   │   └── AuthContext.tsx      # MSAL wrapper
│   ├── services/
│   │   └── api.ts               # Backend API client
│   ├── types/
│   │   └── index.ts             # TypeScript types
│   ├── config/
│   │   └── azureConfig.ts       # Azure configuration
│   ├── App.tsx                  # Main component
│   └── main.tsx                 # Entry point
├── docs/                        # Documentation (20+ guides)
├── package.json                 # Node dependencies
├── tsconfig.json                # TypeScript config
├── vite.config.ts               # Vite configuration
├── tailwind.config.js           # Tailwind CSS config
└── README.md                    # This file
```

---

## 🔧 Configuration

### RBAC Configuration

Edit `backend/rbac_config.json` to manage roles and agent permissions:

```json
{
  "role_permissions": {
    "Admin": {
      "description": "Full access to all agents",
      "agent_patterns": ["*"],
      "allow_all": true
    },
    "FinanceAnalyst": {
      "description": "Finance department agents",
      "agent_patterns": ["budget", "invoice", "expense", "financial"],
      "allow_all": false
    },
    "HRAnalyst": {
      "description": "HR department agents",
      "agent_patterns": ["recruiting", "hr", "employee", "hiring"],
      "allow_all": false
    }
  },
  "default_role": "BasicUser"
}
```

**Add new role:** Just edit JSON, no code changes needed!

### Azure AD App Roles

Create roles in Azure Portal:

1. **Azure Active Directory** → **App registrations** → [Your App] → **App roles**
2. Click **+ Create app role**
3. Fill in: Display name, Value (must match `rbac_config.json`), Description
4. Save

Assign users:

1. **Enterprise applications** → [Your App] → **Users and groups**
2. Click **+ Add user/group**
3. Select user and role
4. Assign

**See detailed guide:** [docs/AZURE_AD_APP_ROLES_SETUP.md](docs/AZURE_AD_APP_ROLES_SETUP.md)

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
npm run test
```

### Manual Testing

1. **Authentication Flow:**

   - Navigate to http://localhost:5173
   - Click "Sign In with Microsoft"
   - Verify token in browser DevTools

2. **Agent Filtering:**

   - Login as different users (Admin, FinanceAnalyst, HRAnalyst)
   - Verify each sees correct agents
   - Check `/api/agents` response

3. **Chat Functionality:**

   - Select an agent
   - Send messages
   - Verify streaming responses
   - Check session persistence

4. **RBAC Enforcement:**
   - Try accessing unauthorized agent via API
   - Verify 403 response
   - Check backend logs for access decisions

---

## 🚀 Deployment

### Backend Deployment (Azure App Service)

```bash
# Create App Service
az webapp create \
  --resource-group myResourceGroup \
  --plan myAppServicePlan \
  --name myapp-backend \
  --runtime "PYTHON:3.11"

# Configure environment variables
az webapp config appsettings set \
  --resource-group myResourceGroup \
  --name myapp-backend \
  --settings @backend/.env

# Deploy
cd backend
zip -r deploy.zip .
az webapp deployment source config-zip \
  --resource-group myResourceGroup \
  --name myapp-backend \
  --src deploy.zip
```

### Frontend Deployment (Azure Static Web Apps)

```bash
# Build
npm run build

# Deploy
az staticwebapp create \
  --name myapp-frontend \
  --resource-group myResourceGroup \
  --source ./dist \
  --location "East US 2"
```

**See complete deployment guide:** [docs/SETUP.md](docs/SETUP.md)

---

## 🔒 Security Best Practices

### Implemented

✅ JWT token validation with JWKS rotation
✅ HTTPS-only communication in production
✅ Environment variable separation (no secrets in code)
✅ Row-level security on data tables
✅ CORS configuration for known origins
✅ Rate limiting on API endpoints
✅ Input validation with Pydantic
✅ SQL injection prevention (parameterized queries)

### Recommended for Production

- [ ] Enable Azure AD Conditional Access policies
- [ ] Configure Application Insights for monitoring
- [ ] Set up Azure Key Vault for secret management
- [ ] Enable Azure DDoS Protection
- [ ] Implement request rate limiting (Azure API Management)
- [ ] Configure Content Security Policy (CSP) headers
- [ ] Enable audit logging to Azure Monitor

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Commit changes:** `git commit -m 'Add amazing feature'`
4. **Push to branch:** `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Workflow

1. Update documentation for any new features
2. Add tests for new functionality
3. Ensure all tests pass: `pytest` and `npm test`
4. Follow code style: `black` for Python, `prettier` for TypeScript
5. Update README if needed

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Support & Troubleshooting

### Common Issues

**Issue:** 401 Unauthorized when calling Foundry API

- **Solution:** Check API key and endpoint in `.env`, see [docs/AZURE_FOUNDRY_401_FIX.md](docs/AZURE_FOUNDRY_401_FIX.md)

**Issue:** Users see no agents after login

- **Solution:** Verify Azure AD role assignment and `rbac_config.json` patterns, see [docs/RBAC_IMPLEMENTATION_GUIDE.md](docs/RBAC_IMPLEMENTATION_GUIDE.md)

**Issue:** "No 'roles' claim in JWT token"

- **Solution:** Configure token claims in App Registration, see [docs/AZURE_AD_APP_ROLES_SETUP.md](docs/AZURE_AD_APP_ROLES_SETUP.md)

**Issue:** RAG search returns no results

- **Solution:** Verify Azure AI Search index and permissions, see [docs/RAG_AZURE_SETUP_GUIDE.md](docs/RAG_AZURE_SETUP_GUIDE.md)

**Issue:** Async/await errors in backend

- **Solution:** Check event loop usage, see [docs/BLOCKING_IO_FIX.md](docs/BLOCKING_IO_FIX.md)

### Get Help

- **Documentation:** Check the `docs/` directory (20+ guides)
- **Issues:** Open a GitHub issue with detailed description
- **Discussions:** Join repository discussions for Q&A

---

## 🗺️ Roadmap

### Phase 1 - Core Features ✅ (Completed)

- [x] Azure Entra ID authentication
- [x] Azure Foundry integration
- [x] Basic chat interface
- [x] Role-based agent filtering
- [x] RAG integration (Azure AI Search + SharePoint)
- [x] OAuth identity passthrough (MCP)

### Phase 2 - Enhanced Features 🚧 (In Progress)

- [ ] Admin UI for RBAC management
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] File upload for agents
- [ ] Agent marketplace

### Phase 3 - Enterprise Features 📅 (Planned)

- [ ] Multi-tenant isolation
- [ ] Custom agent builder UI
- [ ] Workflow automation
- [ ] Integration with Microsoft Teams
- [ ] Advanced audit logging
- [ ] Cost management dashboard

---

## 🙏 Acknowledgments

Built with:

- [Azure AI Foundry](https://azure.microsoft.com/en-us/products/ai-foundry/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Microsoft Authentication Library (MSAL)](https://github.com/AzureAD/microsoft-authentication-library-for-js)
- [Tailwind CSS](https://tailwindcss.com/)

Special thanks to the open-source community for their incredible tools and libraries.

---

## 📧 Contact

**Project Maintainer:** Tejas  
**Repository:** [Azure MCP FastAPI Agent](https://github.com/your-org/azure-mcp-fastapi-agent)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ for the Azure AI community

</div>
