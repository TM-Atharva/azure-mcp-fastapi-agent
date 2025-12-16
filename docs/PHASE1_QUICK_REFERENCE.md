# Phase 1 Quick Reference

## What Was Implemented?

### ✅ 1. RBAC + Agent Visibility

Users now see only agents they have permission to access based on their role.

**Roles:**

- `admin` - See all agents
- `analyst` - See data/analytics/reporting agents
- `user` - See basic chat agents
- `guest` - See only public agents

**Auto-assigned based on:**

- Email domain (admin.com → admin)
- Email keywords (analyst@ → analyst)
- Azure AD groups (optional)

**Customize in:** `backend/rbac.py`

### ✅ 2. RAG Integration

Agents can now access documents from Azure AI Search and SharePoint.

**Sources:**

- **Azure AI Search** - Indexed documents with semantic search
- **SharePoint** - Live documents via Microsoft Graph API

**Permission-aware:** Users only see documents they can access

### ✅ 3. OAuth Consent Flow

Additional consent flow for SharePoint/OneDrive access.

---

## New API Endpoints

### RBAC Endpoints

```bash
# Get current user's roles
GET /api/user-roles
Authorization: Bearer YOUR_TOKEN

# List agents (auto-filtered by role)
GET /api/agents
Authorization: Bearer YOUR_TOKEN
```

### RAG Endpoints

```bash
# Search knowledge base
POST /api/rag/search?query=test&top=5
Authorization: Bearer YOUR_TOKEN

# Get RAG configuration
GET /api/rag/config

# Request OAuth consent for SharePoint
POST /api/rag/consent?source=sharepoint
Authorization: Bearer YOUR_TOKEN
```

---

## Configuration

### Required (Already Set Up)

```env
AZURE_CLIENT_ID=...
AZURE_TENANT_ID=...
AZURE_CLIENT_SECRET=...
AZURE_FOUNDRY_ENDPOINT=...
AZURE_FOUNDRY_API_KEY=...
AZURE_STORAGE_CONNECTION_STRING=...
MCP_ENABLED=true
```

### Optional - Azure AI Search

```env
AZURE_AI_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_AI_SEARCH_KEY=your_api_key
AZURE_AI_SEARCH_INDEX=documents
```

### Optional - SharePoint

```env
SHAREPOINT_ENABLED=true
SHAREPOINT_SITE_URL=https://company.sharepoint.com/sites/knowledge
```

**SharePoint requires additional Azure AD permissions:**

- Sites.Read.All
- Files.Read.All
- User.Read

---

## Quick Test Commands

### Test RBAC

```bash
# Check your roles
curl http://localhost:8000/api/user-roles \
  -H "Authorization: Bearer YOUR_TOKEN"

# See filtered agents
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test RAG

```bash
# Check RAG status
curl http://localhost:8000/api/rag/config

# Search (if RAG configured)
curl -X POST "http://localhost:8000/api/rag/search?query=test" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get SharePoint consent URL
curl -X POST "http://localhost:8000/api/rag/consent?source=sharepoint" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Frontend Usage

```typescript
import { apiClient } from "./services/api";

// Check user roles
const roles = await apiClient.getUserRoles();
console.log("My roles:", roles.roles);

// Agents automatically filtered by role
const agents = await apiClient.getAgents();

// Check RAG configuration
const ragConfig = await apiClient.getRagConfig();

// Search knowledge base
const results = await apiClient.searchKnowledgeBase(
  "quarterly reports",
  ["ai_search", "sharepoint"],
  5
);

// Request SharePoint consent
const consent = await apiClient.requestRagConsent("sharepoint");
window.location.href = consent.consent_url;
```

---

## Customization

### Change Role Assignment Logic

Edit `backend/rbac.py`:

```python
# Add admin domains
admin_domains = ["admin.com", "leadership.com", "yourdomain.com"]

# Add specific admin emails
admin_emails = ["admin@company.com", "ceo@company.com"]

# Map Azure AD groups
group_role_mapping = {
    "Global Admins": UserRole.ADMIN,
    "Data Team": UserRole.ANALYST,
}
```

### Change Agent Access Patterns

Edit `backend/rbac.py`:

```python
DEFAULT_AGENT_PERMISSIONS = {
    "keyword": {UserRole.ADMIN, UserRole.ANALYST},
    "your-agent-name": {UserRole.USER},
}
```

---

## Files Modified/Created

### New Files

- ✅ `backend/rbac.py` - RBAC implementation
- ✅ `backend/rag_integration.py` - RAG service
- ✅ `backend/.env.template` - Updated environment template
- ✅ `docs/PHASE1_IMPLEMENTATION.md` - Full documentation
- ✅ `docs/PHASE1_QUICK_REFERENCE.md` - This file

### Modified Files

- ✅ `backend/main.py` - Added RBAC filtering & RAG endpoints
- ✅ `backend/config.py` - Added RAG configuration
- ✅ `backend/requirements.txt` - Added azure-search-documents
- ✅ `src/services/api.ts` - Added RAG API methods

---

## Troubleshooting

### RBAC: Users see wrong agents

- Check role assignment logic in `backend/rbac.py`
- Verify user email patterns match your organization
- Add logging to see assigned roles

### RAG: Azure AI Search not working

- Verify `AZURE_AI_SEARCH_ENDPOINT` is correct
- Check API key has permissions
- Ensure index name matches configuration
- Check documents have `permissions` field

### RAG: SharePoint returns 401/403

- User needs additional OAuth consent
- Call `/api/rag/consent?source=sharepoint`
- Verify Azure AD app has required permissions
- Check permissions granted admin consent

---

## What's Different?

### Before Phase 1

```
User → Login → See ALL agents → Chat with any agent
```

### After Phase 1

```
User → Login → Assigned roles → See FILTERED agents → Chat with permitted agents
                     ↓
                RAG enabled
                     ↓
         Agents can search Azure AI Search + SharePoint
                     ↓
         Only returns documents user can access
```

---

## Next Steps

1. **Test locally:**

   ```bash
   cd backend
   python main.py
   ```

2. **Customize RBAC:**

   - Edit `backend/rbac.py`
   - Add your admin emails/domains
   - Test with different user accounts

3. **Configure RAG (optional):**

   - Set up Azure AI Search service
   - Add RAG environment variables
   - Test search endpoints

4. **Deploy:**
   - Update environment variables
   - Grant Azure AD permissions for SharePoint
   - Test with real users

---

## Support

**Documentation:**

- Full guide: `docs/PHASE1_IMPLEMENTATION.md`
- This quick reference: `docs/PHASE1_QUICK_REFERENCE.md`
- MCP docs: `docs/MCP_INDEX.md`

**Testing:**

- FastAPI docs: http://localhost:8000/api/docs
- Health check: http://localhost:8000/api/health
- MCP config: http://localhost:8000/api/mcp-config
- RAG config: http://localhost:8000/api/rag/config

**Logs:**

- Backend: Console output or `backend/logs/`
- Check for "✓ RBAC enabled" and "✓ RAG enabled" on startup
