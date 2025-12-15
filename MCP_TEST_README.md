# MCP Feature - Test & Verify

## TL;DR - Start Here

**Goal:** Verify MCP (OAuth Identity Passthrough) is working correctly

**Time Required:** 5 minutes

**Steps:**

1. **Check if enabled:**

   ```bash
   curl http://localhost:8000/api/mcp-config
   ```

   Look for: `"mcp_enabled": true`

2. **Run test script:**

   ```bash
   cd backend && python verify_mcp.py
   ```

   Look for: ✓ Green checkmarks

3. **Send a message & check logs:**

   - Open UI, send a chat message
   - Look for: `✓ MCP ENABLED AND CONFIGURED`
   - Look for: `X-User-Email Header:` in logs

4. **Done!** If you see all three → MCP is working ✅

---

## Documentation

Start with these in order:

### 1. Quick Test (2 min)

📄 **MCP_QUICK_TEST.md**

- Fastest way to verify
- What logs to look for
- Troubleshooting tips

### 2. Full Guide (10 min)

📄 **MCP_VERIFICATION_GUIDE.md**

- Comprehensive step-by-step
- All expected behaviors
- Advanced testing

### 3. Technical Details

📄 **MCP_CHANGES_SUMMARY.md**

- What was changed
- Code references
- Implementation details

---

## What is MCP?

**MCP** = Your user ID/email is passed to AI agents so they know who you are.

**Flow:**

```
You → UI → Backend (gets your user info)
  → Azure Foundry Agent (receives X-User-Email header)
  → Agent knows it's YOU making the request
```

---

## Test Result Indicators

### ✅ MCP is Working

- `curl .../api/mcp-config` returns `"mcp_enabled": true`
- `python verify_mcp.py` shows green checks ✓
- Logs show `✓ MCP ENABLED AND CONFIGURED`
- Logs show `X-User-Email:` header
- Logs show `Request headers being sent: {...'X-User-Email'...}`

### ❌ MCP is NOT Working

- Config returns `"mcp_enabled": false`
- Verify script shows red X ✗
- Logs show `⚠ MCP NOT ENABLED`
- No X-User-Email in headers
- Request headers empty or missing

---

## Files Added/Updated

### New Files

- `backend/verify_mcp.py` - Test script
- `MCP_QUICK_TEST.md` - Quick guide
- `MCP_VERIFICATION_GUIDE.md` - Full guide
- `MCP_CHANGES_SUMMARY.md` - What changed
- `MCP_TESTING_COMPLETE.md` - Overview

### Modified Files

- `backend/main.py` - Added logging + `/api/mcp-config` endpoint
- `backend/azure_foundry.py` - Enhanced header logging
- `src/services/api.ts` - Added `getMcpConfig()` method

---

## Quick Commands

```bash
# Check configuration
curl http://localhost:8000/api/mcp-config

# Run verification
cd backend && python verify_mcp.py

# Check health with MCP status
curl http://localhost:8000/api/health | jq '.mcp_enabled'

# Watch backend logs
# (On Windows, using uvicorn: logs appear in terminal)
```

---

## Next Phase

Once MCP is verified ✅:

- Proceed to **UI Changes** to display deployed model name
- Complete end-to-end testing

---

## Need Help?

| Issue                 | Read                                |
| --------------------- | ----------------------------------- |
| Quick check           | MCP_QUICK_TEST.md                   |
| Detailed steps        | MCP_VERIFICATION_GUIDE.md           |
| Technical questions   | MCP_CHANGES_SUMMARY.md              |
| Something not working | MCP_QUICK_TEST.md → Troubleshooting |

---

**Created:** December 15, 2025  
**For:** MCP (OAuth Identity Passthrough) Verification
