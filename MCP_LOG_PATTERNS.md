# MCP Log Pattern Visual Guide

## When You Send a Message - What You'll See in Logs

### Complete Message Flow with MCP

Here's exactly what appears in the backend console/logs when you send a message:

---

## 📍 Log Pattern #1: Message Processing Starts

```
Processing message for session 550e8400-e29b-41d4-a716-446655440000
```

**What it means:** System received your message  
**Status:** ✅ Normal

---

## 📍 Log Pattern #2: MCP Context Verification

```
═══ MCP CONTEXT AT ENDPOINT ═══
MCP Context Available: True
MCP Enabled: True
User Identity - Email: john.doe@company.com, ID: 12345678-1234-1234-1234-123456789012
Current User - Email: john.doe@company.com, ID: 12345678-1234-1234-1234-123456789012
══════════════════════════════
```

**What it means:**

- Your user info was extracted from Azure AD token
- MCP context is available
- Email and ID match between auth and MCP

**Status:** ✅ **CRITICAL - MCP context received!**

---

## 📍 Log Pattern #3: Agent Call Preparation

```
Calling agent gpt-4-agent-uuid with MCP context
MCP Context being passed: True
  └─ MCP will include user: john.doe@company.com
```

**What it means:** About to call the AI agent WITH your user info  
**Status:** ✅ MCP context is being passed to agent

---

## 📍 Log Pattern #4: MCP Headers Configuration

```
✓ MCP ENABLED AND CONFIGURED
  ├─ User Email: john.doe@company.com
  ├─ User ID: 12345678-1234-1234-1234-123456789012
  ├─ X-User-Id Header: 12345678-1234-1234-1234-123456789012
  ├─ X-User-Email Header: john.doe@company.com
  └─ MCP Enabled Setting: True
```

**What it means:**

- MCP is enabled ✓
- Headers are being created with your info
- These headers will be sent to Azure Foundry

**Status:** ✅ **CRITICAL - Headers configured!**

---

## 📍 Log Pattern #5: Request Headers Being Sent

```
Calling endpoint: https://api.foundry.azure.com/api/projects/my-project/models/chat/completions
Request headers being sent: {'Content-Type': 'application/json', 'Authorization': 'Bearer eyJhbGc...', 'X-User-Id': '12345678-1234-1234-1234-123456789012', 'X-User-Email': 'john.doe@company.com'}
Request payload: {
  "model": "gpt-4-deployment",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 2048
}
```

**What it means:**

- Actual HTTP request with MCP headers
- `X-User-Id` and `X-User-Email` are in the request
- Azure Foundry will receive your user context

**Status:** ✅ **CRITICAL - Headers in the actual request!**

---

## 📍 Log Pattern #6: Response from Azure

```
Response status: 200
```

**What it means:** Azure Foundry processed request successfully  
**Status:** ✅ Success

---

## Complete Sequence Summary

```
✅ Step 1: Message processing started
       ↓
✅ Step 2: MCP context extracted from token
       ↓
✅ Step 3: Agent called with MCP context
       ↓
✅ Step 4: MCP headers configured
       ├─ X-User-Id set
       ├─ X-User-Email set
       └─ Headers verified
       ↓
✅ Step 5: Headers sent in HTTP request to Azure
       ├─ X-User-Id: 12345678-...
       ├─ X-User-Email: john.doe@company.com
       └─ Other headers present
       ↓
✅ Step 6: Azure responds with 200 (success)
       ↓
✅ RESULT: MCP IS WORKING! 🎉
```

---

## What If Something Is Wrong?

### ❌ Error Pattern: MCP NOT ENABLED

```
⚠ MCP NOT ENABLED - mcp_context: True, MCP_ENABLED: False
```

**Problem:** MCP_ENABLED setting is False  
**Solution:**

1. Open `.env` file
2. Set `MCP_ENABLED=True`
3. Restart backend
4. Try again

---

### ❌ Error Pattern: No MCP Context

```
⚠ MCP NOT ENABLED - mcp_context: False, MCP_ENABLED: True
```

**Problem:** MCP context wasn't created  
**Solution:**

1. Make sure you're logged in
2. Verify Authorization header is being sent
3. Check Azure AD token is valid
4. Try again

---

### ❌ Error Pattern: Missing Headers

```
Calling endpoint: https://...
Request headers being sent: {'Content-Type': 'application/json', 'Authorization': 'Bearer ...'}
```

**Problem:** X-User-\* headers not in the request  
**Solution:**

- This indicates MCP context was empty
- Check patterns #2 and #4 for details
- Restart backend with MCP_ENABLED=True

---

## Verification Checklist

When you send a message, you should see:

- [ ] Log Pattern #1: Message processing
- [ ] Log Pattern #2: MCP context received
- [ ] Log Pattern #3: Agent call preparation
- [ ] Log Pattern #4: **✓ MCP ENABLED** message
- [ ] Log Pattern #5: X-User-\* headers in request
- [ ] Log Pattern #6: Response status 200

**All checked?** ✅ **MCP is working perfectly!**

---

## Quick Grep Commands

Find patterns in logs:

```bash
# Look for MCP context received
grep "═══ MCP CONTEXT" backend.log

# Look for MCP headers confirmed
grep "✓ MCP ENABLED" backend.log

# Look for headers in request
grep "X-User-Email" backend.log

# Look for errors
grep "⚠ MCP NOT ENABLED" backend.log
```

---

## Real-World Example

### Successful MCP Flow

```
User "john.doe@company.com" sends message:

1. Backend receives message
2. Extracts user from JWT token
3. Creates MCP context with john.doe@company.com
4. Sets headers: X-User-Email: john.doe@company.com
5. Sends to Azure with those headers
6. Azure Foundry agent receives request as john.doe
7. Agent can access john.doe's resources
8. All audit trails show john.doe made the request
```

### Failed MCP Flow

```
Same user sends message BUT MCP_ENABLED=False:

1. Backend receives message
2. Tries to create MCP context
3. MCP_ENABLED is False - skips header creation
4. Sends to Azure WITHOUT user headers
5. Azure Foundry agent doesn't know who sent the request
6. Agent might deny access or run with default permissions
7. No user audit trail
```

---

## Tips for Monitoring

1. **Keep logs visible:**

   - Run backend in terminal or console
   - Don't hide the output
   - Watch it in real-time

2. **Copy exact patterns:**

   - `✓ MCP ENABLED` ← Look for this exactly
   - `X-User-Email` ← Look for this
   - `Request headers` ← Watch this section

3. **Check timestamps:**

   - Should match when you sent message
   - Helps confirm you're looking at right message

4. **Send multiple messages:**
   - Pattern should repeat
   - Consistency confirms it's working

---

## Advanced: Decode JWT Token

If you want to see what's in your token:

```bash
# Copy the Authorization header value (without "Bearer ")
# Paste into: https://jwt.io

# You'll see:
{
  "oid": "12345678-1234-1234-1234-123456789012",  # This becomes X-User-Id
  "email": "john.doe@company.com",                # This becomes X-User-Email
  "name": "John Doe",
  ...
}
```

This confirms the data being passed to the agent.

---

**Summary:** If you see patterns #2, #4, and #5 with your email → ✅ MCP is working!
