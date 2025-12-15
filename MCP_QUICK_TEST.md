# MCP Testing - Quick Start

## What is MCP?

**MCP** = OAuth Identity Passthrough = User's authentication context passed to AI agents

When you send a message, your user identity is included so:

- Agents know who you are
- Agents can access your resources
- All actions are audited with your identity

## ✅ Quick Verification (2 minutes)

### Step 1: Check Configuration

```bash
# From project root, test the MCP config endpoint
curl http://localhost:8000/api/mcp-config
```

You should see:

```json
{
  "mcp_enabled": true,
  "status": "enabled"
}
```

✅ If you see `"mcp_enabled": true` → **MCP is configured!**

### Step 2: Run Verification Script

```bash
# Navigate to backend folder
cd backend

# Run the verification script
python verify_mcp.py
```

You should see:

```
✓ MCP is ENABLED in configuration
✓ MCP is ENABLED in health check
✓ MCP is properly configured!
```

✅ If you see green checkmarks → **MCP is ready!**

### Step 3: Send a Test Message & Check Logs

**What to do:**

1. Open the UI (localhost:5173)
2. Login with your credentials
3. Select an AI agent
4. Send a chat message (e.g., "Hello")
5. Watch the **backend console/logs**

**What to look for in backend logs:**

Search for these messages in order:

**Message 1 (near top of logs):**

```
═══ MCP CONTEXT AT ENDPOINT ═══
MCP Context Available: True
MCP Enabled: True
User Identity - Email: your.email@example.com
```

✅ This shows MCP context is received

**Message 2 (middle of logs):**

```
✓ MCP ENABLED AND CONFIGURED
  ├─ User Email: your.email@example.com
  ├─ User ID: some-uuid-here
  ├─ X-User-Id Header: some-uuid-here
  ├─ X-User-Email Header: your.email@example.com
  └─ MCP Enabled Setting: True
```

✅ This shows MCP headers are being set

**Message 3 (further down):**

```
Request headers being sent: {...'X-User-Id': 'some-uuid-here', 'X-User-Email': 'your.email@example.com'...}
```

✅ This shows headers are in the actual request

## 🎯 Success Criteria

All three? **✅ MCP is working perfectly!**

Missing any? See **Troubleshooting** section below.

## 🔍 Full Log Check

When you send a message, you should see this sequence:

```
1. Processing message for session {session-id}

2. ═══ MCP CONTEXT AT ENDPOINT ═══
   MCP Context Available: True
   ...
   ══════════════════════════════

3. Calling agent {agent-id} with MCP context
   MCP Context being passed: True
     └─ MCP will include user: your.email@example.com

4. ✓ MCP ENABLED AND CONFIGURED
     ├─ User Email: your.email@example.com
     ├─ User ID: {uuid}
     ...

5. Calling endpoint: https://...{endpoint}/models/chat/completions
   Request headers being sent: {...'X-User-Id': '{uuid}', 'X-User-Email': '...'...}

6. Response status: 200
```

Each step = ✅ MCP is working

## ❌ Troubleshooting

### Issue: "MCP NOT ENABLED" message appears

```
⚠ MCP NOT ENABLED - mcp_context: True, MCP_ENABLED: False
```

**Solution:**

1. Open `.env` file in project root
2. Find the line: `MCP_ENABLED=`
3. Change it to: `MCP_ENABLED=True`
4. Restart backend
5. Try again

### Issue: No X-User-Id/X-User-Email headers visible

**Check 1:** Are you authenticated?

- Must be logged in with valid Azure AD token
- Should see "Authorization: Bearer {token}" in headers

**Check 2:** Is backend running?

- Terminal should show: `INFO:     Application startup complete`

**Check 3:** Check .env file

```
MCP_ENABLED=True          # Should be True
AZURE_CLIENT_ID=...       # Should not be empty
AZURE_TENANT_ID=...       # Should not be empty
```

### Issue: Cannot connect to backend

```
Cannot connect to backend at http://localhost:8000/api
```

**Solution:**

1. Make sure backend is running: `python -m uvicorn main:app --reload`
2. Should see: `Uvicorn running on http://127.0.0.1:8000`
3. Try curl again

### Issue: /api/mcp-config returns 404

```
curl: (7) Failed to connect to localhost port 8000
```

**Solution:**

1. Backend not running
2. Or backend code not updated

Start backend:

```bash
cd backend
python -m uvicorn main:app --reload
```

## 📊 Expected Behavior

### ✅ MCP Working

- Logs show all three patterns above
- User email appears in X-User-Email header
- No warning messages about MCP disabled

### ❌ MCP Not Working

- Only see "Request headers being sent: {}" (empty headers)
- See "⚠ MCP NOT ENABLED" warning
- No X-User-Id or X-User-Email in headers
- Error messages in logs

## 🚀 Next Steps

1. **Verify MCP is working** (this guide)
2. Once confirmed → **Proceed to UI changes** to display model name
3. Then test end-to-end with model name visible

## 📝 Log File Reference

| Pattern                      | Means                       |
| ---------------------------- | --------------------------- |
| `✓ MCP ENABLED`              | Headers being set ✅        |
| `⚠ MCP NOT ENABLED`          | Headers NOT being set ❌    |
| `═══ MCP CONTEXT`            | MCP context received ✅     |
| `X-User-Email`               | User passed to agent ✅     |
| `Request headers being sent` | Final check before Azure ✅ |

## 💡 Pro Tips

1. **Grep for specific patterns:**

   ```bash
   # In backend logs window, Ctrl+F search for:
   "✓ MCP ENABLED"        # Find MCP confirmation
   "X-User-Email"         # Find user headers
   "Request headers"      # Find final headers
   ```

2. **Check multiple messages:**

   - Send several messages
   - See the pattern repeated each time
   - Consistency = reliability

3. **Compare timestamps:**
   - Look at timestamps in logs
   - Should align with when you sent message in UI

## Questions?

If MCP isn't working:

1. Check `.env` file has `MCP_ENABLED=True`
2. Restart backend
3. Look for "⚠ MCP NOT ENABLED" messages
4. Verify Authorization header is sent
5. Check Azure AD token is valid

All fixed? Move to next section: **UI Changes to Display Model Name** 🎉
