# Azure AD App Roles Setup Guide - Exact Steps

## What Are App Roles vs. Azure RBAC Roles?

| Feature           | Azure AD App Roles                      | Azure RBAC Custom Roles                    |
| ----------------- | --------------------------------------- | ------------------------------------------ |
| **Location**      | App registrations → App roles           | Subscriptions → IAM → Roles                |
| **Purpose**       | Application authorization               | Azure resource management                  |
| **Controls**      | What users can do **in your app**       | What users can do **with Azure resources** |
| **Example**       | "FinanceAnalyst can see finance agents" | "Can create Virtual Machines"              |
| **Shows in**      | JWT token `roles` claim                 | Azure portal permissions                   |
| **Use for RBAC?** | ✅ **YES - Use this!**                  | ❌ **NO - Wrong feature**                  |

---

## Step-by-Step: Create App Roles (Exact Clicks)

### Step 1: Navigate to App Registrations

**Click path:**

```
1. Open Azure Portal (portal.azure.com)
2. Search bar → Type "App registrations" → Press Enter
3. Click on your application (the one you created for this chatbot)
   - Example name: "azure-mcp-fastapi-agent" or "ChatbotApp"
```

**What you see:**

```
┌─────────────────────────────────────────────────────┐
│ azure-mcp-fastapi-agent                             │
├─────────────────────────────────────────────────────┤
│ Overview                                            │
│ Quickstart                                          │
│ Branding & properties                               │
│ Authentication                                      │
│ Certificates & secrets                              │
│ Token configuration                                 │
│ API permissions                                     │
│ Expose an API                                       │
│ App roles                          ← CLICK HERE     │
│ Owners                                              │
│ Manifest                                            │
└─────────────────────────────────────────────────────┘
```

---

### Step 2: Click "App roles"

**Location:** Left sidebar menu

**What you see:**

```
┌──────────────────────────────────────────────────────────────┐
│ azure-mcp-fastapi-agent | App roles                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Define app roles for your application                       │
│                                                              │
│  App roles appear in the roles claim of security tokens.    │
│                                                              │
│  [+ Create app role]                    ← CLICK HERE        │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Display name     │ Description        │ Value    │ ... │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │ (No roles yet)                                        │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

### Step 3: Create "Admin" Role

**Click:** `+ Create app role` button

**Fill in the form:**

```
┌─────────────────────────────────────────────────────────┐
│ Create app role                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Display name *                                          │
│ ┌─────────────────────────────────────────────────┐     │
│ │ Administrator                                   │     │
│ └─────────────────────────────────────────────────┘     │
│                                                         │
│ Value *                                                 │
│ ┌─────────────────────────────────────────────────┐     │
│ │ Admin                                           │ ← IMPORTANT: Use this exact value
│ └─────────────────────────────────────────────────┘     │
│                                                         │
│ Description *                                           │
│ ┌─────────────────────────────────────────────────┐     │
│ │ Full access to all agents and system           │     │
│ │ configuration                                   │     │
│ └─────────────────────────────────────────────────┘     │
│                                                         │
│ Allowed member types *                                  │
│ ☑ Users/Groups                                          │
│ ☐ Applications                                          │
│                                                         │
│ Do you want to enable this app role? *                 │
│ ☑ Yes    ☐ No                                          │
│                                                         │
│             [Cancel]  [Apply]  ← CLICK APPLY           │
└─────────────────────────────────────────────────────────┘
```

**⚠️ CRITICAL:** The **Value** field must match your `rbac_config.json`:

```json
{
  "role_permissions": {
    "Admin": {  ← Must match the "Value" field exactly
      ...
    }
  }
}
```

---

### Step 4: Create "FinanceAnalyst" Role

**Click:** `+ Create app role` again

**Fill in:**

| Field                    | Value                                              |
| ------------------------ | -------------------------------------------------- |
| **Display name**         | Finance Analyst                                    |
| **Value**                | `FinanceAnalyst` ← **Must match rbac_config.json** |
| **Description**          | Access to finance and budget-related agents        |
| **Allowed member types** | ☑ Users/Groups                                     |
| **Enable**               | ☑ Yes                                              |

**Click:** `Apply`

---

### Step 5: Create "HRAnalyst" Role

**Click:** `+ Create app role` again

**Fill in:**

| Field                    | Value                                         |
| ------------------------ | --------------------------------------------- |
| **Display name**         | HR Analyst                                    |
| **Value**                | `HRAnalyst` ← **Must match rbac_config.json** |
| **Description**          | Access to HR and recruiting agents            |
| **Allowed member types** | ☑ Users/Groups                                |
| **Enable**               | ☑ Yes                                         |

**Click:** `Apply`

---

### Step 6: Verify Roles Created

**You should now see:**

```
┌──────────────────────────────────────────────────────────────┐
│ azure-mcp-fastapi-agent | App roles                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [+ Create app role]                                         │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Display name    │ Description           │ Value         ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ Administrator   │ Full access...        │ Admin         ││
│  │ Finance Analyst │ Access to finance...  │ FinanceAnalyst││
│  │ HR Analyst      │ Access to HR...       │ HRAnalyst     ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

✅ **Roles created successfully!**

---

## Step 7: Assign Users to Roles

**⚠️ IMPORTANT:** Creating roles doesn't assign them to users. You must do this separately!

### Navigate to Enterprise Applications

**Click path:**

```
1. Azure Portal → Search "Enterprise applications"
2. Find and click your application
   - Same name as App registration: "azure-mcp-fastapi-agent"
3. Click "Users and groups" in left menu
```

**What you see:**

```
┌──────────────────────────────────────────────────────────────┐
│ azure-mcp-fastapi-agent | Users and groups                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [+ Add user/group]                      ← CLICK HERE       │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Name            │ Type    │ Assignment              │...││
│  ├─────────────────────────────────────────────────────────┤│
│  │ (No users yet)                                          ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

### Assign Tejas (Admin)

**Click:** `+ Add user/group`

**Fill in:**

```
┌─────────────────────────────────────────────────────────┐
│ Add Assignment                                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Users and groups                                        │
│ ┌─────────────────────────────────────────────────┐     │
│ │ None Selected                                   │     │
│ └─────────────────────────────────────────────────┘     │
│ [Select users and groups]   ← CLICK HERE               │
│                                                         │
│ Select a role                                           │
│ ┌─────────────────────────────────────────────────┐     │
│ │ None Selected                                   │     │
│ └─────────────────────────────────────────────────┘     │
│ [Select a role]             ← CLICK HERE               │
│                                                         │
│                              [Assign]                   │
└─────────────────────────────────────────────────────────┘
```

**Step 7a:** Click `Select users and groups`

- Search for: `tejas@yourcompany.com`
- Check the box next to Tejas
- Click `Select`

**Step 7b:** Click `Select a role`

- Choose: `Administrator`
- Click `Select`

**Step 7c:** Click `Assign`

✅ **Tejas assigned to Admin role!**

---

### Assign Rahul (Finance)

**Repeat same process:**

1. Click `+ Add user/group`
2. Select user: `rahul@yourcompany.com`
3. Select role: `Finance Analyst`
4. Click `Assign`

✅ **Rahul assigned to FinanceAnalyst role!**

---

### Assign Dixit (HR)

**Repeat same process:**

1. Click `+ Add user/group`
2. Select user: `dixit@yourcompany.com`
3. Select role: `HR Analyst`
4. Click `Assign`

✅ **Dixit assigned to HRAnalyst role!**

---

### Verify Assignments

**You should now see:**

```
┌──────────────────────────────────────────────────────────────┐
│ azure-mcp-fastapi-agent | Users and groups                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [+ Add user/group]  [Refresh]  [Remove]                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │☐ Name                 │ Type    │ Assignment           ││
│  ├─────────────────────────────────────────────────────────┤│
│  │☐ Tejas Kumar          │ User    │ Administrator        ││
│  │☐ Rahul Sharma          │ User    │ Finance Analyst      ││
│  │☐ Dixit Patel           │ User    │ HR Analyst           ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

✅ **All users assigned!**

---

## Step 8: Configure Token to Include Roles

**This ensures roles appear in the JWT token**

### Navigate Back to App Registration

**Click path:**

```
Azure Portal → App registrations → [Your app] → Token configuration
```

**Click:** `+ Add optional claim`

**Select:**

- Token type: `Access`
- Claim: `roles`
- Check the box
- Click `Add`

**Alternative (if above doesn't work):**

The roles should appear automatically in tokens when:

1. App roles are defined (✅ Done in Step 3-5)
2. Users are assigned to roles (✅ Done in Step 7)
3. User logs in with scope that requests the app

**Test by decoding a JWT token at:** https://jwt.ms

---

## Step 9: Test the Configuration

### Test 1: Get a Token

**Have Rahul log in to your application**

**The JWT token should contain:**

```json
{
  "aud": "your-app-client-id",
  "iss": "https://login.microsoftonline.com/...",
  "preferred_username": "rahul@yourcompany.com",
  "roles": ["FinanceAnalyst"],
  "...": "..."
}
```

**Copy the access token and paste it into:** https://jwt.ms

**Verify:** `roles` claim shows `["FinanceAnalyst"]`

---

### Test 2: Backend Extracts Roles

**Your backend code (`backend/main.py`):**

```python
from backend.rbac_dynamic import AgentAccessControl

rbac = AgentAccessControl(config_path="backend/rbac_config.json")

@app.get("/api/agents")
async def list_agents(current_user: dict = Depends(get_current_user)):
    # current_user is the decoded JWT token
    print("Token payload:", current_user)

    # Extract roles from token
    user_roles = rbac.get_user_roles_from_token(current_user)
    print("User roles:", user_roles)

    # Should print: User roles: ['FinanceAnalyst']
```

---

### Test 3: Agent Filtering Works

**When Rahul calls `/api/agents`:**

**Backend logic:**

1. Extract roles from token: `["FinanceAnalyst"]`
2. Load `rbac_config.json`
3. Check `FinanceAnalyst` patterns: `["budget", "invoice", "expense", "financial"]`
4. Filter agents: Only return agents with those keywords
5. Response: Rahul sees only finance agents

---

## Common Issues & Solutions

### Issue 1: "No 'roles' claim in token"

**Symptoms:** Token doesn't contain `roles` field

**Causes:**

1. User not assigned to any role
2. Token requested with wrong scope
3. App roles not properly configured

**Solutions:**

**A. Check user assignment:**

```
Enterprise applications → [Your app] → Users and groups
→ Verify user is listed with a role
```

**B. Check token configuration:**

```
App registrations → [Your app] → Token configuration
→ Ensure "roles" claim is included
```

**C. Request token with correct scope:**

```typescript
// Frontend: src/services/api.ts
const msalConfig = {
  auth: {
    clientId: "your-client-id",
    authority: "https://login.microsoftonline.com/your-tenant-id",
  },
  scopes: [
    "api://your-api-client-id/user_impersonation", // Include API scope
    "openid",
    "profile",
    "email",
  ],
};
```

---

### Issue 2: "Unknown role" warning in backend

**Symptoms:**

```
WARNING: Unknown role 'FinanceAnalyst' for user user@company.com, ignoring
```

**Cause:** Role value in Azure AD doesn't match `rbac_config.json`

**Solution:**

**Check Azure AD App Role "Value" field:**

```
App registrations → App roles → Finance Analyst → Value: "FinanceAnalyst"
```

**Check rbac_config.json:**

```json
{
  "role_permissions": {
    "FinanceAnalyst": {  ← Must match exactly (case-sensitive!)
      ...
    }
  }
}
```

**Fix:** Make them match exactly, then reload config:

```bash
POST /api/rbac/reload
```

---

### Issue 3: User sees all agents (not filtered)

**Symptoms:** Admin patterns apply to everyone

**Cause:** Default role has `"allow_all": true`

**Solution:**

**Check `rbac_config.json`:**

```json
{
  "default_role": "BasicUser",  ← Used when no roles in token
  "role_permissions": {
    "BasicUser": {
      "agent_patterns": ["general", "chat"],  ← NOT ["*"]
      "allow_all": false  ← NOT true
    }
  }
}
```

---

## Difference: App Roles vs. Azure RBAC Roles

### When Someone Says "Create Custom Roles"

**They might mean:**

**Option 1: Azure AD App Roles** (What we're doing)

- **Purpose:** Application authorization (in your app)
- **Example:** "Finance users can see finance agents"
- **Created in:** App registrations → App roles
- **Assigned in:** Enterprise applications → Users and groups
- **Result:** `roles` claim in JWT token

**Option 2: Azure RBAC Custom Roles** (NOT what we want)

- **Purpose:** Azure resource management
- **Example:** "Finance team can create Storage Accounts"
- **Created in:** Subscriptions → IAM → Roles
- **Assigned in:** Resource → Access Control (IAM)
- **Result:** Azure portal permissions (no JWT claim)

---

## Quick Reference

### Navigation Cheat Sheet

| Task                  | Location                                                        |
| --------------------- | --------------------------------------------------------------- |
| **Create roles**      | App registrations → [Your app] → App roles → + Create           |
| **Assign users**      | Enterprise applications → [Your app] → Users and groups → + Add |
| **View token**        | https://jwt.ms (paste access token)                             |
| **Configure backend** | Edit `backend/rbac_config.json`                                 |
| **Reload config**     | `POST /api/rbac/reload` or restart backend                      |

---

### Role Value Mapping

**Azure AD App Role (Value field) → rbac_config.json (key)**

| Azure AD         | rbac_config.json          | User Sees      |
| ---------------- | ------------------------- | -------------- |
| `Admin`          | `"Admin": {...}`          | All agents     |
| `FinanceAnalyst` | `"FinanceAnalyst": {...}` | Finance agents |
| `HRAnalyst`      | `"HRAnalyst": {...}`      | HR agents      |

**MUST MATCH EXACTLY** (case-sensitive!)

---

## Summary

✅ **Create App Roles here:**

- Azure Portal → App registrations → [Your app] → **App roles**

✅ **Assign users here:**

- Azure Portal → Enterprise applications → [Your app] → **Users and groups**

❌ **Don't use:**

- Subscriptions → IAM → Roles (that's for Azure resources, not your app)

✅ **Result:**

- JWT tokens contain `roles` claim
- Backend extracts roles from token
- Agents filtered based on `rbac_config.json`

---

**Created:** December 17, 2025  
**Purpose:** Clear guide for creating Azure AD App Roles for agent-level RBAC
