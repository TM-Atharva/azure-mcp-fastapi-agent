# MCP (OAuth Identity Passthrough) Verification Guide

## Overview

MCP (OAuth Identity Passthrough) is a security feature that passes the user's original authentication context to Azure Foundry agents. This guide helps you verify that MCP is properly configured and working.

## Current Implementation Status

✅ **MCP is Implemented** in your backend:

- Enabled in `config.py`: `MCP_ENABLED: bool = True`
- Configured in `auth.py`: `get_mcp_context()` dependency
- Used in `main.py`: `/api/chat` endpoint passes context to agents
- Headers sent to Azure Foundry: `X-User-Id`, `X-User-Email`

## Quick Verification Steps

### Step 1: Check MCP Configuration Endpoint

**What it does:** Verifies MCP is enabled in the system

```bash
curl http://localhost:8000/api/mcp-config
```

**Expected Response:**

```json
{
  "mcp_enabled": true,
  "status": "enabled",
  "implementation": {
    "headers_used": ["X-User-Id", "X-User-Email"],
    "context_includes": [...]
  }
}
```

### Step 2: Check Health Endpoint

**What it does:** Shows overall system health including MCP status

```bash
curl http://localhost:8000/api/health
```

**Look for:** `"mcp_enabled": true`

### Step 3: Send a Test Message and Check Logs

This is the **most important verification step**.

**Steps:**

1. Make sure backend is running with logs visible
2. Login to the UI
3. Select an agent
4. Send a message

**What to look for in backend logs:**

#### Log Pattern 1: MCP Context at Endpoint

```
═══ MCP CONTEXT AT ENDPOINT ═══
MCP Context Available: True
MCP Enabled: True
User Identity - Email: user@example.com, ID: {user-id}
Current User - Email: user@example.com, ID: {user-id}
══════════════════════════════
```

✅ **This confirms:** MCP context is being received at the endpoint

#### Log Pattern 2: Headers Being Set

```
✓ MCP ENABLED AND CONFIGURED
  ├─ User Email: user@example.com
  ├─ User ID: {user-id}
  ├─ X-User-Id Header: {user-id}
  ├─ X-User-Email Header: user@example.com
  └─ MCP Enabled Setting: True
```

✅ **This confirms:** MCP headers are being set correctly

#### Log Pattern 3: Headers Being Sent to Azure

```
Request headers being sent: {'Content-Type': 'application/json', 'Authorization': 'Bearer {token}', 'X-User-Id': '{user-id}', 'X-User-Email': 'user@example.com'}
```

✅ **This confirms:** MCP headers are in the HTTP request to Azure Foundry

### Step 4: Full Message Flow in Logs

When you send a message, look for this sequence:

1. **Message received:**

   ```
   Processing message for session {session-id}
   ```

2. **MCP context checked:**

   ```
   ═══ MCP CONTEXT AT ENDPOINT ═══
   MCP Context Available: True
   ...
   ```

3. **Agent called with MCP:**

   ```
   Calling agent {agent-id} with MCP context
   MCP Context being passed: True
     └─ MCP will include user: user@example.com
   ```

4. **Headers prepared:**

   ```
   ✓ MCP ENABLED AND CONFIGURED
   ```

5. **Request sent to Azure:**
   ```
   Calling endpoint: https://...{endpoint}/models/chat/completions
   Request headers being sent: {...'X-User-Id': '...', 'X-User-Email': '...'}
   ```

## MCP Context Structure

When passed to the agent, the MCP context includes:

```python
{
    "oauth_token": "Bearer {JWT-token}",
    "user_identity": {
        "azure_id": "{user-azure-id}",
        "email": "user@example.com",
        "name": "User Name"
    },
    "mcp_enabled": True,
    "timestamp": "2024-12-15T10:30:00.000000"
}
```

## Troubleshooting

### Issue: "MCP NOT ENABLED" message in logs

```
⚠ MCP NOT ENABLED - mcp_context: False, MCP_ENABLED: True
```

**Cause:** MCP context dependency is not being injected  
**Fix:** Check that your request includes proper Authorization header

### Issue: Missing X-User headers

```
Request headers being sent: {'Content-Type': 'application/json', 'Authorization': 'Bearer ...'}
```

**Cause:** MCP context is None or MCP_ENABLED is False  
**Fix:**

- Check `.env` file has `MCP_ENABLED=True`
- Ensure Authorization header is present in request
- Check auth token is valid

### Issue: "MCP_ENABLED: False" in MCP config endpoint

```json
{
  "mcp_enabled": false,
  "status": "disabled"
}
```

**Fix:** Set `MCP_ENABLED=True` in `.env` file and restart backend

## How MCP Works in Your System

```
User Login
    ↓
Get Azure AD Token (JWT)
    ↓
Send Message with Authorization Header
    ↓
Endpoint: POST /api/chat
    ↓
Extract User from JWT Token (get_current_user)
    ↓
Create MCP Context (get_mcp_context)
    - Extract user ID (oid/sub)
    - Extract email (email/preferred_username)
    - Include original JWT token
    ↓
Pass MCP Context to foundry_client.send_message()
    ↓
Add Headers to Azure Foundry Request:
    - X-User-Id: {user-id}
    - X-User-Email: {user-email}
    ↓
Call Azure Foundry Model Inference API
    ↓
Agent receives request WITH user context
    - Can access resources as that user
    - Maintains audit trail
    - Proper authorization enforced
```

## Key Files for MCP Implementation

| File                       | Purpose                                            |
| -------------------------- | -------------------------------------------------- |
| `backend/config.py`        | Contains `MCP_ENABLED` setting                     |
| `backend/auth.py`          | `get_mcp_context()` creates MCP context            |
| `backend/main.py`          | `/api/chat` endpoint receives & passes MCP context |
| `backend/azure_foundry.py` | `send_message()` adds MCP headers to request       |

## Expected MCP Behavior

✅ **When MCP is working correctly:**

- Every authenticated request includes user identity
- Azure Foundry agents receive X-User-Id and X-User-Email headers
- Logs show "✓ MCP ENABLED AND CONFIGURED"
- User's email matches between logs

❌ **When MCP is NOT working:**

- No X-User-Id/X-User-Email headers in logs
- "⚠ MCP NOT ENABLED" warning message
- Headers missing from "Request headers being sent"

## Testing with CURL (Advanced)

### Get MCP Config

```bash
curl -X GET http://localhost:8000/api/mcp-config
```

### Check Health with MCP Status

```bash
curl -X GET http://localhost:8000/api/health | jq '.mcp_enabled'
```

### Send a Message (requires valid token)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer {your-azure-ad-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "{session-uuid}",
    "content": "Hello"
  }'
```

Then check the backend logs for MCP confirmation messages.

## Summary Checklist

- [ ] Backend is running with visible logs
- [ ] MCP config endpoint returns `"mcp_enabled": true`
- [ ] Health endpoint shows `"mcp_enabled": true`
- [ ] Sent a test message from the UI
- [ ] Backend logs show "═══ MCP CONTEXT AT ENDPOINT ═══" message
- [ ] Backend logs show "✓ MCP ENABLED AND CONFIGURED"
- [ ] Backend logs show X-User-Id and X-User-Email in headers
- [ ] "Request headers being sent" includes X-User-\* headers
- [ ] User email matches across logs

**If all checks pass: ✅ MCP is working correctly!**
