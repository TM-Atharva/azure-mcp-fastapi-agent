# MCP Flow Diagram

## Message Flow with MCP

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                              │
│                                                                       │
│  1. Open UI → Login → Select Agent → Send Message                  │
│                                                                       │
│        "Hello, how are you?"                                         │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │  REQUEST WITH AUTHORIZATION       │
         │  Headers:                          │
         │  - Authorization: Bearer {JWT}    │
         │  - Content-Type: application/json │
         └───────────────┬───────────────────┘
                         │
                         ▼
     ┌─────────────────────────────────────────────┐
     │          BACKEND: /api/chat ENDPOINT        │
     │                                              │
     │  1. Parse request                           │
     │  2. Log: "Processing message..."            │
     └──────────────────┬──────────────────────────┘
                        │
                        ▼
    ┌──────────────────────────────────────────────┐
    │   DEPENDENCY: get_current_user()             │
    │   - Validate JWT token                       │
    │   - Extract user from token                  │
    │   - Get user profile from DB                 │
    │                                               │
    │   Result: UserProfile(email, id, name)      │
    └──────────────┬───────────────────────────────┘
                   │
                   ▼
   ┌────────────────────────────────────────────────┐
   │  DEPENDENCY: get_mcp_context()                │
   │  - Validate JWT token                         │
   │  - Extract user info from token:              │
   │    • azure_id (oid or sub)                   │
   │    • email (email or preferred_username)     │
   │    • name                                     │
   │  - Create MCP context dict                    │
   │                                                │
   │  Log: "═══ MCP CONTEXT AT ENDPOINT ═══"      │
   │        "MCP Context Available: True"          │
   │        "User Identity - Email: user@..."      │
   │        "══════════════════════════════"       │
   │                                                │
   │  Result: Dict with user_identity + token     │
   └──────────────┬───────────────────────────────┘
                  │
                  ▼
  ┌───────────────────────────────────────────────┐
  │     ENDPOINT LOGIC: send_chat_message()       │
  │                                                │
  │  1. Get conversation history                  │
  │  2. Get agent info                            │
  │                                                │
  │  Log: "Calling agent {agent_id} with MCP"    │
  │        "MCP Context being passed: True"       │
  │        "└─ MCP will include user: ..."        │
  └──────────────┬────────────────────────────────┘
                 │
                 ▼
 ┌────────────────────────────────────────────────┐
 │  CALL: foundry_client.send_message()           │
 │                                                 │
 │  Parameters:                                    │
 │  - agent_id                                    │
 │  - message content                             │
 │  - conversation_history                        │
 │  - mcp_context ← PASSED HERE!                 │
 │                                                 │
 └──────────────┬─────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────┐
│  AZURE_FOUNDRY: send_message() Method            │
│                                                   │
│  1. Get auth headers (Bearer token)              │
│  2. Check if mcp_context provided                │
│                                                   │
│  IF MCP_ENABLED and mcp_context:                │
│    Log: "✓ MCP ENABLED AND CONFIGURED"          │
│          "├─ User Email: user@..."              │
│          "├─ User ID: {uuid}"                   │
│          "├─ X-User-Id Header: {uuid}"         │
│          "├─ X-User-Email Header: user@..."    │
│          "└─ MCP Enabled Setting: True"         │
│                                                   │
│    Extract user from mcp_context:               │
│    - user_email = mcp_context['user_identity']['email']
│    - user_id = mcp_context['user_identity']['azure_id']
│                                                   │
│    Add to headers:                              │
│    - headers['X-User-Id'] = user_id             │
│    - headers['X-User-Email'] = user_email       │
│                                                   │
│  ELSE:                                           │
│    Log: "⚠ MCP NOT ENABLED"                    │
│    (Headers NOT added)                           │
│                                                   │
└──────────────┬────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  PREPARE HTTP REQUEST                            │
│                                                  │
│  Headers being built:                            │
│  {                                               │
│    'Content-Type': 'application/json',           │
│    'Authorization': 'Bearer {JWT}',              │
│    'X-User-Id': 'user-uuid',        ← MCP       │
│    'X-User-Email': 'user@...'       ← MCP       │
│  }                                               │
│                                                  │
│  Log: "Request headers being sent: {...}"      │
│        (shows all headers including X-User-*)   │
│                                                  │
└──────────────┬───────────────────────────────────┘
               │
               ▼
 ┌──────────────────────────────────────────────┐
 │  POST to Azure Foundry                       │
 │  https://.../models/chat/completions        │
 │                                              │
 │  Headers include:                            │
 │  - X-User-Id: {user-uuid}                   │
 │  - X-User-Email: {user-email}               │
 │  - Authorization: Bearer {token}             │
 │                                              │
 │  Log: "Calling endpoint: https://..."       │
 │        "Response status: 200"                │
 └──────────────┬───────────────────────────────┘
                │
                ▼
  ┌────────────────────────────────────────────┐
  │    AZURE FOUNDRY AGENT                     │
  │                                            │
  │  Receives request with headers:            │
  │  X-User-Email: user@company.com           │
  │                                            │
  │  Agent can now:                            │
  │  ✓ Know who is making the request         │
  │  ✓ Access user-specific resources         │
  │  ✓ Enforce user-level authorization       │
  │  ✓ Maintain audit trail                   │
  └──────────────┬─────────────────────────────┘
                 │
                 ▼
   ┌──────────────────────────────────────────┐
   │  AGENT RESPONSE                          │
   │                                          │
   │  Returns:                                │
   │  - Response message                      │
   │  - Metadata (usage, tokens, etc.)        │
   │  - Processed as authenticated request   │
   └──────────────┬───────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────────────┐
    │  BACKEND: Store Response & Reply        │
    │                                         │
    │  1. Store message in database           │
    │  2. Return to frontend                  │
    └──────────────┬────────────────────────────┘
                   │
                   ▼
    ┌────────────────────────────────────────┐
    │  FRONTEND: Display Response            │
    │                                        │
    │  User sees message in chat window      │
    └────────────────────────────────────────┘
```

---

## Log Output Timeline

```
Timeline of logs when you send a message:

00:00 → Message arrives at /api/chat endpoint
        "Processing message for session ..."

00:01 → MCP context dependency executes
        "═══ MCP CONTEXT AT ENDPOINT ═══"
        "MCP Context Available: True"
        "MCP Enabled: True"
        "User Identity - Email: user@company.com, ID: uuid"
        "══════════════════════════════"

00:02 → Endpoint logic prepares agent call
        "Calling agent {agent-id} with MCP context"
        "MCP Context being passed: True"
        "└─ MCP will include user: user@company.com"

00:03 → send_message() executes in azure_foundry
        "✓ MCP ENABLED AND CONFIGURED"
        "├─ User Email: user@company.com"
        "├─ User ID: uuid"
        "├─ X-User-Id Header: uuid"
        "├─ X-User-Email Header: user@company.com"
        "└─ MCP Enabled Setting: True"

00:04 → HTTP request being prepared
        "Calling endpoint: https://.../models/chat/completions"
        "Request headers being sent: {...'X-User-Id': 'uuid', 'X-User-Email': 'user@company.com'...}"

00:05 → Request sent, awaiting response
        (network delay, processing by Azure)

00:06 → Response received
        "Response status: 200"

00:07 → Message stored and returned to frontend
        (User sees response in UI)

SUCCESS: All steps completed with MCP headers! ✅
```

---

## MCP Context Structure

```
mcp_context = {
    "oauth_token": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMzQ1Njc4In0.eyJzcWIiOjEyMzQ1Njc4OTB9.sig",

    "user_identity": {
        "azure_id": "12345678-1234-1234-1234-123456789012",  ← Becomes X-User-Id header
        "email": "john.doe@company.com",                     ← Becomes X-User-Email header
        "name": "John Doe"
    },

    "mcp_enabled": True,

    "timestamp": "2024-12-15T10:30:00.000000"
}

                    ↓
            (Extracted in send_message)
                    ↓

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer {JWT_token}",
    "X-User-Id": "12345678-1234-1234-1234-123456789012",  ← From mcp_context
    "X-User-Email": "john.doe@company.com"               ← From mcp_context
}

                    ↓
            (Sent in HTTP request)
                    ↓

Azure Foundry Agent receives:
    Headers: {X-User-Id, X-User-Email}
    → Now knows it's John Doe making the request
    → Can access John Doe's resources
    → Maintains audit trail with John's ID
```

---

## Success vs Failure

### ✅ SUCCESS: MCP Headers Present

```
Request to Azure:
POST /models/chat/completions

Headers:
  Content-Type: application/json
  Authorization: Bearer eyJ...
  X-User-Id: 12345678-1234-1234-1234-123456789012  ← MCP HEADER
  X-User-Email: john.doe@company.com               ← MCP HEADER

Body:
  {messages: [...], model: "gpt-4", ...}

Agent receives request as: john.doe@company.com
Status: ✅ MCP is working!
```

### ❌ FAILURE: MCP Headers Missing

```
Request to Azure:
POST /models/chat/completions

Headers:
  Content-Type: application/json
  Authorization: Bearer eyJ...
  (NO X-User-Id header)
  (NO X-User-Email header)

Body:
  {messages: [...], model: "gpt-4", ...}

Agent receives request with NO user context
Status: ❌ MCP is NOT working!

Possible causes:
- MCP_ENABLED = False
- mcp_context = None
- Token validation failed
```

---

## Key Decision Points

```
Is MCP Enabled?
└─ Yes → Create MCP Context?
         └─ Yes → Has user_identity?
                  └─ Yes → Add X-User-Id header
                  └─ Yes → Add X-User-Email header
                  └─ Yes → Send to Azure WITH headers ✅

         └─ No  → Send to Azure WITHOUT headers ❌
                  (MCP_ENABLED=False in .env)

└─ No  → Send to Azure WITHOUT headers ❌
         (MCP_ENABLED=False in .env)
```

---

## Verification Checkpoints

```
┌─ Start: Send message from UI
│
├─ Checkpoint 1: Message received at endpoint
│   Log: "Processing message for session..."
│   Status: ✅
│
├─ Checkpoint 2: MCP context extracted
│   Log: "═══ MCP CONTEXT AT ENDPOINT ═══"
│   Status: ✅
│
├─ Checkpoint 3: User identity available
│   Log: "User Identity - Email: user@..."
│   Status: ✅
│
├─ Checkpoint 4: MCP headers configured
│   Log: "✓ MCP ENABLED AND CONFIGURED"
│   Status: ✅
│
├─ Checkpoint 5: Headers in request
│   Log: "Request headers being sent: {...X-User-Email...}"
│   Status: ✅
│
├─ Checkpoint 6: Azure responds
│   Log: "Response status: 200"
│   Status: ✅
│
└─ End: User sees response in UI ✅

All checkpoints present = MCP WORKING! 🎉
```

---

**Visual Guide Created:** December 15, 2025
