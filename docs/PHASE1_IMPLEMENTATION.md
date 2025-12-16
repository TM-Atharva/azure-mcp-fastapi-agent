# Phase 1 Implementation Guide

## Overview

This document describes the Phase 1 features implemented in the Azure MCP FastAPI Agent application:

1. **OAuth Identity Passthrough (MCP)** ✅ Already Implemented
2. **RAG Integration (Azure AI Search / SharePoint)** ✅ **NEW**
3. **RBAC + Agent Visibility** ✅ **NEW**

---

## Feature 1: OAuth Identity Passthrough (MCP)

### Status: ✅ Already Implemented

OAuth Identity Passthrough was already fully implemented in your application. The system passes user authentication context to Azure Foundry agents using MCP (Model Context Protocol).

**Key Files:**

- [backend/auth.py](../backend/auth.py) - Token validation and user context
- [backend/azure_foundry.py](../backend/azure_foundry.py) - MCP implementation for agent calls
- [backend/main.py](../backend/main.py) - MCP context injection

**How It Works:**

1. User authenticates with Azure Entra ID
2. Frontend sends access token with each request
3. Backend validates token and extracts user info
4. User context passed to agents via headers (X-User-Id, X-User-Email)
5. Agents can access user-specific resources with proper permissions

**Verification:**

```bash
# Check MCP status
curl http://localhost:8000/api/mcp-config

# Test user context
curl http://localhost:8000/api/user-context \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Feature 2: RBAC + Agent Visibility

### Status: ✅ **NEWLY IMPLEMENTED**

Role-Based Access Control (RBAC) now controls which users can see and interact with specific agents.

### User Roles

| Role        | Access Level | Visible Agents                          |
| ----------- | ------------ | --------------------------------------- |
| **admin**   | Full access  | All agents                              |
| **analyst** | Data-focused | Data, analytics, reporting, chat agents |
| **user**    | Standard     | Chat, assistant, general agents         |
| **guest**   | Limited      | Public agents only                      |

### Implementation Files

**Backend:**

- [backend/rbac.py](../backend/rbac.py) - **NEW** - Core RBAC logic
- [backend/main.py](../backend/main.py) - Updated `/api/agents` endpoint with filtering

**Key Components:**

1. **AgentAccessControl Class** - Manages role-based access
2. **Role Assignment** - Auto-assigns roles based on:
   - Email domain
   - Email keywords (analyst, data, etc.)
   - Azure AD groups (when available)
3. **Agent Filtering** - Filters agents by name/description patterns

### Agent Access Patterns

Agents are matched against keywords to determine required roles:

```python
"admin" -> {ADMIN}
"data" -> {ADMIN, ANALYST}
"analytics" -> {ADMIN, ANALYST}
"reporting" -> {ADMIN, ANALYST}
"chat" -> {ADMIN, ANALYST, USER}
"assistant" -> {ADMIN, ANALYST, USER}
"general" -> {ADMIN, ANALYST, USER}
"public" -> {ADMIN, ANALYST, USER, GUEST}
```

### Customization

**To customize role assignment**, edit [backend/rbac.py](../backend/rbac.py):

```python
# Add admin domains
admin_domains = ["admin.com", "leadership.com"]

# Add specific admin emails
admin_emails = ["admin@company.com"]

# Map Azure AD groups to roles
group_role_mapping = {
    "Admins": UserRole.ADMIN,
    "DataAnalysts": UserRole.ANALYST,
    # Add your groups here
}
```

**To customize agent permissions**, edit the patterns in [backend/rbac.py](../backend/rbac.py):

```python
DEFAULT_AGENT_PERMISSIONS = {
    "keyword": {UserRole.ADMIN, UserRole.ANALYST},
    # Add more patterns
}
```

### API Endpoints

#### Get User Roles

```bash
GET /api/user-roles
Authorization: Bearer YOUR_TOKEN

Response:
{
  "success": true,
  "user_email": "user@company.com",
  "roles": ["user", "analyst"],
  "description": {
    "admin": "Full access to all agents",
    "analyst": "Access to data analysis agents",
    "user": "Access to basic chat agents",
    "guest": "Limited access"
  }
}
```

#### List Agents (Filtered by Role)

```bash
GET /api/agents
Authorization: Bearer YOUR_TOKEN

# Returns only agents accessible to the user based on their roles
```

### Frontend Integration

The frontend automatically receives filtered agents. No changes needed to display logic - agents are filtered server-side.

To show user roles in UI (optional):

```typescript
import { apiClient } from "./services/api";

// Get current user's roles
const rolesResponse = await apiClient.getUserRoles();
console.log("User roles:", rolesResponse.roles);
```

---

## Feature 3: RAG Integration (Azure AI Search / SharePoint)

### Status: ✅ **NEWLY IMPLEMENTED**

RAG (Retrieval-Augmented Generation) integration enables agents to access knowledge from Azure AI Search and SharePoint.

### Architecture

```
User Request
    ↓
Frontend (OAuth Token)
    ↓
Backend (Token Validation + MCP)
    ↓
RAG Service
    ├─→ Azure AI Search (API Key or Azure Identity)
    └─→ SharePoint (User's OAuth Token - Identity Passthrough)
    ↓
Filtered Results (User Permissions)
    ↓
Agent Response
```

### Implementation Files

**Backend:**

- [backend/rag_integration.py](../backend/rag_integration.py) - **NEW** - RAG service implementation
- [backend/config.py](../backend/config.py) - Updated with RAG settings
- [backend/main.py](../backend/main.py) - New RAG endpoints

**Frontend:**

- [src/services/api.ts](../src/services/api.ts) - New RAG API methods

### Components

#### 1. Azure AI Search Integration

**Features:**

- Semantic search with captions and answers
- User-based permission filtering
- Configurable index and endpoint

**Configuration** (add to `.env`):

```env
# Azure AI Search
AZURE_AI_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_AI_SEARCH_KEY=your_api_key  # Optional - can use Azure Identity
AZURE_AI_SEARCH_INDEX=documents
```

**Permission Filtering:**
Documents in AI Search should have a `permissions` field:

```json
{
  "id": "doc1",
  "content": "...",
  "permissions": ["user@company.com", "everyone"]
}
```

The search automatically filters to show only documents the user can access.

#### 2. SharePoint MCP Connector

**Features:**

- Microsoft Graph API integration
- OAuth Identity Passthrough (uses user's token)
- Permission-aware search (user sees only what they have access to)

**Configuration** (add to `.env`):

```env
# SharePoint RAG
SHAREPOINT_ENABLED=true
SHAREPOINT_SITE_URL=https://company.sharepoint.com/sites/knowledge
```

**OAuth Scopes Required:**

- `Sites.Read.All`
- `Files.Read.All`
- `User.Read`

### API Endpoints

#### 1. Search Knowledge Base

```bash
POST /api/rag/search
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

Params:
  query: "search query"
  sources: ["ai_search", "sharepoint"]
  top: 5

Response:
{
  "query": "your search",
  "timestamp": "2025-12-16T...",
  "sources": {
    "ai_search": {
      "count": 3,
      "documents": [...]
    },
    "sharepoint": {
      "count": 2,
      "documents": [...]
    }
  }
}
```

#### 2. Get RAG Configuration

```bash
GET /api/rag/config

Response:
{
  "rag_enabled": true,
  "sources": {
    "azure_ai_search": {
      "enabled": true,
      "endpoint": "https://...",
      "index": "documents"
    },
    "sharepoint": {
      "enabled": true,
      "site_url": "https://..."
    }
  },
  "oauth_passthrough": true
}
```

#### 3. Request OAuth Consent (SharePoint)

```bash
POST /api/rag/consent
Params:
  source: "sharepoint"

Response:
{
  "source": "sharepoint",
  "resource": "Microsoft SharePoint",
  "scopes": ["Sites.Read.All", "Files.Read.All", "User.Read"],
  "consent_url": "https://login.microsoftonline.com/...",
  "instructions": "To access SharePoint, visit the consent_url..."
}
```

### Frontend Usage

```typescript
// Check RAG configuration
const ragConfig = await apiClient.getRagConfig();
console.log("RAG sources:", ragConfig.sources);

// Search knowledge base
const results = await apiClient.searchKnowledgeBase(
  "quarterly reports",
  ["ai_search", "sharepoint"],
  5
);

// Request SharePoint consent (if needed)
const consent = await apiClient.requestRagConsent("sharepoint");
window.location.href = consent.consent_url;
```

### OAuth Consent Flow

For SharePoint access, additional OAuth consent is required:

1. **Check if consent is needed:**

   - Try to search SharePoint
   - If 401 error with insufficient permissions

2. **Request consent:**

   ```typescript
   const consent = await apiClient.requestRagConsent("sharepoint");
   ```

3. **Redirect user:**

   ```typescript
   window.location.href = consent.consent_url;
   ```

4. **Handle redirect:**

   - User grants permissions
   - Returns to your app with auth code
   - Exchange code for token (handled by MSAL)

5. **Retry search:**
   - Now has required permissions
   - Can access SharePoint documents

### Permission-Aware RAG

**Azure AI Search:**

- Filter by document `permissions` field
- Only shows docs user can access
- Query: `permissions/any(p: p eq 'user@company.com' or p eq 'everyone')`

**SharePoint:**

- Uses user's OAuth token
- Microsoft Graph enforces SharePoint permissions
- User sees only files they have access to
- No additional filtering needed

### Integration with Agents

Agents can use RAG via tools/functions:

**Option 1: Direct Tool Call**

```python
# Agent calls /api/rag/search as a tool
{
  "tool": "search_knowledge_base",
  "parameters": {
    "query": "Q4 financial report"
  }
}
```

**Option 2: Context Injection**

```python
# Backend searches before sending to agent
knowledge = await rag_service.search_knowledge_base(user_query)
context = "Relevant documents: " + format_results(knowledge)
agent_prompt = f"{context}\n\nUser question: {user_query}"
```

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:

- `azure-search-documents==11.4.0`

### 2. Configure Environment Variables

Add to your `.env` file:

```env
# Existing variables...
AZURE_CLIENT_ID=...
AZURE_TENANT_ID=...
AZURE_CLIENT_SECRET=...
AZURE_FOUNDRY_ENDPOINT=...
AZURE_FOUNDRY_API_KEY=...

# RBAC (no config needed - uses email-based logic)

# RAG - Azure AI Search (Optional)
AZURE_AI_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_AI_SEARCH_KEY=your_api_key
AZURE_AI_SEARCH_INDEX=documents

# RAG - SharePoint (Optional)
SHAREPOINT_ENABLED=true
SHAREPOINT_SITE_URL=https://company.sharepoint.com/sites/knowledge
```

### 3. Azure AD App Registration Updates

For SharePoint RAG, add scopes to your Azure AD app:

1. Go to Azure Portal → App Registrations → Your App
2. Navigate to **API Permissions**
3. Click **Add a permission** → Microsoft Graph
4. Add **Delegated Permissions:**
   - `Sites.Read.All`
   - `Files.Read.All`
   - `User.Read`
5. Click **Grant admin consent**

### 4. Azure AI Search Setup (Optional)

If using Azure AI Search:

1. Create Azure AI Search service in Azure Portal
2. Create a search index named `documents` (or configure custom name)
3. Add fields:
   - `id` (string, key)
   - `content` (string, searchable)
   - `title` (string, searchable)
   - `url` (string)
   - `permissions` (collection of strings, filterable)
4. Index your documents with permission metadata

### 5. Test the Implementation

#### Test RBAC

```bash
# Get your roles
curl http://localhost:8000/api/user-roles \
  -H "Authorization: Bearer YOUR_TOKEN"

# List agents (will be filtered by role)
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Test RAG

```bash
# Check RAG config
curl http://localhost:8000/api/rag/config

# Search knowledge base
curl -X POST "http://localhost:8000/api/rag/search?query=test&top=5" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Request SharePoint consent
curl -X POST "http://localhost:8000/api/rag/consent?source=sharepoint" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Testing Checklist

### RBAC Testing

- [ ] Different users see different agents based on email
- [ ] Admin users see all agents
- [ ] Analyst users see data/analytics agents
- [ ] Regular users see basic chat agents
- [ ] `/api/user-roles` returns correct roles
- [ ] `/api/agents` filters correctly

### RAG Testing

- [ ] `/api/rag/config` shows correct configuration
- [ ] Azure AI Search returns results (if configured)
- [ ] SharePoint search returns results (if configured)
- [ ] Permission filtering works (users see only authorized docs)
- [ ] OAuth consent flow works for SharePoint
- [ ] User token is passed correctly (MCP)

### Integration Testing

- [ ] Agents can access RAG search results
- [ ] User identity is maintained throughout RAG calls
- [ ] Permission errors are handled gracefully
- [ ] Multiple RAG sources work together

---

## Troubleshooting

### RBAC Issues

**Problem:** All users see all agents

- **Solution:** Check [backend/rbac.py](../backend/rbac.py) role assignment logic
- Verify `get_user_roles()` returns correct roles for your users

**Problem:** Admin users not recognized

- **Solution:** Add admin emails/domains to [backend/rbac.py](../backend/rbac.py):
  ```python
  admin_domains = ["admin.com", "yourdomain.com"]
  admin_emails = ["admin@company.com"]
  ```

### RAG Issues

**Problem:** Azure AI Search not working

- Check `AZURE_AI_SEARCH_ENDPOINT` is correct
- Verify API key or Azure Identity has permissions
- Check index name matches `AZURE_AI_SEARCH_INDEX`
- Ensure documents have `permissions` field

**Problem:** SharePoint returns 401/403

- User needs to consent to additional permissions
- Call `/api/rag/consent?source=sharepoint`
- Redirect user to consent URL
- Verify scopes in Azure AD app registration

**Problem:** Users can see documents they shouldn't

- **Azure AI Search:** Check `permissions` field in documents
- **SharePoint:** Microsoft Graph enforces permissions automatically
- Verify user's token is being passed correctly (MCP)

### OAuth Consent Issues

**Problem:** Consent loop (keeps asking for consent)

- Check redirect URI matches Azure AD app registration
- Verify token is stored after consent
- Check token expiration and refresh logic

---

## Architecture Diagrams

### RBAC Flow

```
User Login
    ↓
Extract Email & Azure AD Data
    ↓
Assign Roles (admin, analyst, user, guest)
    ↓
User Requests Agents (/api/agents)
    ↓
Filter Agents by Required Roles
    ↓
Return Only Accessible Agents
```

### RAG Search Flow

```
User Query
    ↓
Validate Token & Extract User Context
    ↓
RAG Service
    ├─→ Azure AI Search
    │   ├─→ Add permission filter (user email)
    │   └─→ Return filtered results
    └─→ SharePoint MCP
        ├─→ Use user's OAuth token
        ├─→ Microsoft Graph enforces permissions
        └─→ Return accessible files
    ↓
Combine Results
    ↓
Return to User/Agent
```

---

## Next Steps

### Phase 2 Considerations

1. **Enhanced RBAC:**

   - Dynamic role assignment from Azure AD groups
   - Custom role definitions
   - Agent-level permissions (not just visibility)

2. **Advanced RAG:**

   - Azure AI Foundry RAG capabilities
   - Vector embeddings for semantic search
   - Multi-turn conversations with RAG context
   - Document summarization

3. **Additional MCP Features:**

   - Tool calling with user permissions
   - Resource-specific tokens
   - Audit logging and compliance

4. **UI Enhancements:**
   - Show user roles in UI
   - RAG source indicators
   - Permission request flows in UI
   - Agent capability badges

---

## Support

For questions or issues:

1. Check logs: `backend/logs` or console output
2. Review documentation: `docs/` folder
3. Test endpoints with `/api/docs` (FastAPI Swagger UI)
4. Check Azure AD app permissions
5. Verify environment variables

---

## Summary

✅ **Phase 1 Complete:**

| Feature                          | Status          | Files                       |
| -------------------------------- | --------------- | --------------------------- |
| OAuth Identity Passthrough (MCP) | ✅ Pre-existing | auth.py, azure_foundry.py   |
| RBAC + Agent Visibility          | ✅ Implemented  | rbac.py, main.py            |
| RAG Integration                  | ✅ Implemented  | rag_integration.py, main.py |

**Key Capabilities:**

- Users only see agents they have permission to use
- Agents can access Azure AI Search and SharePoint
- All data access respects user permissions (MCP + RAG)
- OAuth consent flow for additional permissions
- Fully integrated with existing MCP implementation
