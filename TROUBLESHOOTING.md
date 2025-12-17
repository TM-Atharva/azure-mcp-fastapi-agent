# Troubleshooting Guide

## Fixed Issues

### ✅ Azure Table Storage Error
**Problem:** Table names with underscores (`mcp_tokens`, `user_roles`, `agent_permissions`) are invalid.

**Solution:** Renamed to alphanumeric:
- `mcptokens`
- `userroles`
- `agentpermissions`

### ✅ Chat Click Error
**Problem:** Error when clicking on chat sessions.

**Solutions Applied:**
1. Added error handling in `fetchMessages()` to prevent crashes
2. Added null checks for `response.messages`
3. Fixed agent ID comparison with `String()` conversion
4. Removed unused variables causing lint warnings

## Current Status

✅ Backend running on http://localhost:8000
✅ Frontend running on http://localhost:5173
✅ Tables created successfully
✅ Chat UI loads without errors

## Testing the Application

### 1. Test Login
- Visit http://localhost:5173
- Click "Sign in with Microsoft"
- Complete Azure AD authentication

### 2. Test Chat
- You should see the ChatGPT-style UI with:
  - Sidebar on the left (chat history)
  - Agent dropdown in header
  - Chat area in center
  
### 3. Create New Chat
- Click "New Chat" button
- Select an agent from dropdown
- Type a message and send

### 4. Test Chat History
- Previous chats appear in sidebar
- Click on a chat to load it
- Hover over chat to see delete button

## Known TypeScript Warnings

These are **safe to ignore** - they're just IDE linting before compilation:

```
Cannot find module './Sidebar' or its corresponding type declarations.
Cannot find module './ChatArea' or its corresponding type declarations.
```

The files exist and Vite compiles them correctly at runtime.

## API Endpoints Available

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agents` | GET | List permitted agents (RBAC filtered) |
| `/api/sessions` | GET | Get user's chat sessions |
| `/api/sessions` | POST | Create new chat session |
| `/api/sessions/{id}` | GET | Get session history |
| `/api/sessions/{id}` | DELETE | Delete session |
| `/api/chat` | POST | Send message to agent |
| `/api/mcp/servers` | GET | List MCP servers |
| `/api/mcp/connections` | GET | Get user's MCP connections |

## Next Steps

1. **Test the UI** - Try creating chats and sending messages
2. **Add MCP Tool** - Configure GitHub MCP in Azure Portal for Agent813
3. **Test MCP Flow** - Once configured, test OAuth consent
4. **Add MCP UI** - Create connection status badges in agent dropdown

## Common Issues

### Issue: "Failed to fetch agents"
**Solution:** Check backend logs, verify Azure Foundry credentials in `.env`

### Issue: "Failed to create session"
**Solution:** Ensure agent exists and user has permission (RBAC)

### Issue: Messages not loading
**Solution:** Check browser console, verify session ID is valid

### Issue: Can't delete chat
**Solution:** Ensure you're the owner of the session

## Environment Variables

Make sure these are set in `backend/.env`:

```env
# Azure AD
AZURE_CLIENT_ID=your-client-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_SECRET=your-secret

# Azure Foundry
AZURE_FOUNDRY_ENDPOINT=https://your-endpoint
AZURE_FOUNDRY_API_KEY=your-key
AZURE_FOUNDRY_PROJECT_ID=your-project-id

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=your-connection-string

# MCP
MCP_ENABLED=true

# Fix this typo!
SHAREPOINT_ENABLED=false  # NOT "flase"
```

---

*Last Updated: December 17, 2025*
