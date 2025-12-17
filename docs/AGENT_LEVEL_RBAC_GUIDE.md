# Agent-Level RBAC Implementation Guide

## Executive Summary

**Can Azure AI Foundry provide native agent-level RBAC?** ❌ **NO**

Azure Foundry's built-in RBAC roles (`Azure AI User`, `Azure AI Project Manager`, `Azure AI Account Owner`) only control **project-level** access, not individual agent access.

**Solution:** ✅ **Application-level RBAC** (already implemented in `backend/rbac.py`)

Your application implements a two-layer security model:

1. **Azure Foundry RBAC** → Controls who can access the project
2. **Application RBAC** → Controls which agents each user can see/use

---

## Example Scenario: Finance vs HR Department

### Users & Requirements

| User      | Department | Required Agent Access | Azure Role               | Application Role          |
| --------- | ---------- | --------------------- | ------------------------ | ------------------------- |
| **Tejas** | Admin      | All agents            | `Azure AI Account Owner` | `ADMIN`                   |
| **Rahul** | Finance    | Finance agents only   | `Azure AI User`          | Custom: `FINANCE_ANALYST` |
| **Dixit** | HR         | HR agents only        | `Azure AI User`          | Custom: `HR_ANALYST`      |

---

## Architecture: Two-Layer RBAC

```
┌──────────────────────────────────────────────────────────────┐
│                     User Authenticates                       │
│                   (Azure Entra ID OAuth)                     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│              LAYER 1: Azure Foundry RBAC                     │
│         (Project-level access control)                       │
│                                                              │
│  ✅ Tejas → Azure AI Account Owner (manage project)         │
│  ✅ Rahul → Azure AI User (build agents, run traces)        │
│  ✅ Dixit → Azure AI User (build agents, run traces)        │
│                                                              │
│  Decision: Can this user access Foundry project?            │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│          LAYER 2: Application RBAC (backend/rbac.py)         │
│            (Agent-level filtering)                           │
│                                                              │
│  Tejas (ADMIN)         → Sees all agents                     │
│  Rahul (FINANCE_ANALYST) → Sees: Budget Agent, Invoice Bot  │
│  Dixit (HR_ANALYST)     → Sees: Recruiting Agent, HR Helper │
│                                                              │
│  Decision: Which agents should this user see?               │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                  Frontend UI (filtered)                      │
│                                                              │
│  Rahul sees:        Dixit sees:        Tejas sees:          │
│  ├─ Budget Agent    ├─ Recruiting      ├─ Budget Agent      │
│  └─ Invoice Bot     └─ HR Helper       ├─ Invoice Bot       │
│                                         ├─ Recruiting Agent  │
│                                         ├─ HR Helper         │
│                                         └─ All others...     │
└──────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Implementation

### Phase 1: Azure Foundry RBAC Setup (Project-Level)

#### Step 1.1: Assign Azure Foundry Roles

**In Azure Portal:**

1. Navigate to **Azure AI Foundry** project
2. Go to **Access Control (IAM)** → **Add role assignment**

**Tejas (Admin/Owner):**

```
Role: Azure AI Account Owner
Scope: Foundry Account/Project
User: tejas@yourcompany.com
```

- Can manage project, deploy models, assign roles
- Full administrative access

**Rahul (Finance Department):**

```
Role: Azure AI User
Scope: Foundry Project
User: rahul@yourcompany.com
```

- Can build agents, run traces, use deployed models
- **Cannot** see which specific agents (Layer 2 controls this)

**Dixit (HR Department):**

```
Role: Azure AI User
Scope: Foundry Project
User: dixit@yourcompany.com
```

- Can build agents, run traces, use deployed models
- **Cannot** see which specific agents (Layer 2 controls this)

**Result:** All three users can access the Foundry project, but Azure doesn't know about Finance vs HR distinction.

---

### Phase 2: Application-Level Agent Filtering (Existing Implementation)

Your `backend/rbac.py` already implements this! You just need to configure it.

#### Step 2.1: Define Custom Roles

**Edit `backend/rbac.py`:**

```python
from enum import Enum
from typing import List, Set

class UserRole(Enum):
    """User roles with hierarchical permissions"""
    ADMIN = "admin"              # Tejas - sees all agents
    FINANCE_ANALYST = "finance_analyst"  # Rahul - finance agents only
    HR_ANALYST = "hr_analyst"     # Dixit - HR agents only
    ANALYST = "analyst"           # Legacy role
    USER = "user"
    GUEST = "guest"

# Agent permission mapping
DEFAULT_AGENT_PERMISSIONS = {
    # Finance agents
    "budget": [UserRole.ADMIN, UserRole.FINANCE_ANALYST],
    "invoice": [UserRole.ADMIN, UserRole.FINANCE_ANALYST],
    "expense": [UserRole.ADMIN, UserRole.FINANCE_ANALYST],
    "financial": [UserRole.ADMIN, UserRole.FINANCE_ANALYST],

    # HR agents
    "recruiting": [UserRole.ADMIN, UserRole.HR_ANALYST],
    "hr": [UserRole.ADMIN, UserRole.HR_ANALYST],
    "employee": [UserRole.ADMIN, UserRole.HR_ANALYST],
    "hiring": [UserRole.ADMIN, UserRole.HR_ANALYST],
    "onboarding": [UserRole.ADMIN, UserRole.HR_ANALYST],

    # General agents
    "general": [UserRole.ADMIN, UserRole.ANALYST, UserRole.USER],
}
```

#### Step 2.2: Map Users to Roles

**Option A: Email-based mapping (backend/rbac.py)**

```python
class AgentAccessControl:
    def get_user_roles(self, user_email: str) -> Set[UserRole]:
        """Determine user roles based on email or Azure AD groups"""
        email_lower = user_email.lower()
        roles = set()

        # Admin
        if email_lower == "tejas@yourcompany.com":
            roles.add(UserRole.ADMIN)

        # Finance Department
        elif email_lower == "rahul@yourcompany.com":
            roles.add(UserRole.FINANCE_ANALYST)

        # HR Department
        elif email_lower == "dixit@yourcompany.com":
            roles.add(UserRole.HR_ANALYST)

        # Department-based mapping
        elif email_lower.startswith("finance."):
            roles.add(UserRole.FINANCE_ANALYST)
        elif email_lower.startswith("hr."):
            roles.add(UserRole.HR_ANALYST)

        # Default role if no match
        if not roles:
            roles.add(UserRole.USER)

        return roles
```

**Option B: Azure AD Security Groups (Recommended for production)**

```python
import os
from typing import Dict, Set

# Azure AD Group ID mapping (from environment variables)
AD_GROUP_TO_ROLE = {
    os.getenv("AZURE_AD_ADMIN_GROUP_ID"): UserRole.ADMIN,
    os.getenv("AZURE_AD_FINANCE_GROUP_ID"): UserRole.FINANCE_ANALYST,
    os.getenv("AZURE_AD_HR_GROUP_ID"): UserRole.HR_ANALYST,
}

class AgentAccessControl:
    def get_user_roles_from_token(self, token_payload: Dict) -> Set[UserRole]:
        """Extract roles from Azure AD group claims in JWT token"""
        roles = set()

        # Get groups claim from token
        user_groups = token_payload.get("groups", [])

        for group_id in user_groups:
            if group_id in AD_GROUP_TO_ROLE:
                roles.add(AD_GROUP_TO_ROLE[group_id])

        # Fallback to email-based mapping
        if not roles:
            user_email = token_payload.get("preferred_username", "")
            roles = self.get_user_roles(user_email)

        return roles
```

**Environment variables (.env):**

```bash
# Azure AD Security Group IDs (get from Azure Portal → Entra ID → Groups)
AZURE_AD_ADMIN_GROUP_ID=12345678-1234-1234-1234-123456789abc
AZURE_AD_FINANCE_GROUP_ID=22345678-1234-1234-1234-123456789def
AZURE_AD_HR_GROUP_ID=32345678-1234-1234-1234-123456789ghi
```

#### Step 2.3: Backend API Already Filters Agents

Your **`backend/main.py`** already has this implemented:

```python
@app.get("/api/agents")
async def list_agents(current_user: dict = Depends(get_current_user)):
    """List all agents with RBAC filtering"""
    user_email = current_user.get("preferred_username", "")

    # Get all agents from Azure Foundry
    all_agents = await azure_foundry_client.list_agents()

    # Filter based on user's roles
    filtered_agents = filter_agents_for_user(all_agents, user_email)

    return {"agents": filtered_agents}
```

**The filtering happens automatically!** Rahul will only see finance agents, Dixit only HR agents.

---

## Agent Naming Convention

To make filtering work, **name your agents with keywords** that match `DEFAULT_AGENT_PERMISSIONS`:

### Finance Agents (Rahul sees these)

- ✅ "Budget Planning Assistant"
- ✅ "Invoice Processing Bot"
- ✅ "Expense Report Analyzer"
- ✅ "Financial Data Assistant"

### HR Agents (Dixit sees these)

- ✅ "Recruiting Assistant"
- ✅ "HR Policy Helper"
- ✅ "Employee Onboarding Bot"
- ✅ "Hiring Coordinator"

### Admin Only (Tejas sees all)

- ✅ All agents above
- ✅ "System Configuration Agent"
- ✅ "Data Migration Tool"

**Filtering logic** (already in `backend/rbac.py`):

```python
def get_agent_required_roles(self, agent_name: str) -> Set[UserRole]:
    """Determine which roles can access this agent"""
    agent_name_lower = agent_name.lower()

    for keyword, required_roles in DEFAULT_AGENT_PERMISSIONS.items():
        if keyword in agent_name_lower:
            return set(required_roles)

    # Default: only ADMIN can access unknown agents
    return {UserRole.ADMIN}
```

---

## Testing the Implementation

### Test Case 1: Tejas (Admin)

**Login as:** `tejas@yourcompany.com`

**Expected behavior:**

```json
GET /api/agents
Response:
{
  "agents": [
    {"id": "1", "name": "Budget Planning Assistant", ...},
    {"id": "2", "name": "Invoice Processing Bot", ...},
    {"id": "3", "name": "Recruiting Assistant", ...},
    {"id": "4", "name": "HR Policy Helper", ...},
    {"id": "5", "name": "System Configuration Agent", ...}
  ]
}
```

✅ **Sees all 5 agents**

---

### Test Case 2: Rahul (Finance)

**Login as:** `rahul@yourcompany.com`

**Expected behavior:**

```json
GET /api/agents
Response:
{
  "agents": [
    {"id": "1", "name": "Budget Planning Assistant", ...},
    {"id": "2", "name": "Invoice Processing Bot", ...}
  ]
}
```

✅ **Sees only 2 finance agents**
❌ Cannot see HR or admin agents

**Chat attempt with hidden agent:**

```json
POST /api/chat
{
  "agent_id": "3",  // Recruiting Assistant (HR agent)
  "message": "Hello"
}

Response: 403 Forbidden
{
  "detail": "Access denied: You do not have permission to use this agent"
}
```

---

### Test Case 3: Dixit (HR)

**Login as:** `dixit@yourcompany.com`

**Expected behavior:**

```json
GET /api/agents
Response:
{
  "agents": [
    {"id": "3", "name": "Recruiting Assistant", ...},
    {"id": "4", "name": "HR Policy Helper", ...}
  ]
}
```

✅ **Sees only 2 HR agents**
❌ Cannot see finance or admin agents

---

## Azure Portal Configuration for Azure AD Groups (Production)

### Step 1: Create Security Groups

**In Azure Portal:**

1. Go to **Azure Active Directory** → **Groups** → **New group**

**Create 3 groups:**

| Group Name   | Type     | Members               | Purpose                   |
| ------------ | -------- | --------------------- | ------------------------- |
| `AI-Admins`  | Security | tejas@yourcompany.com | Full access to all agents |
| `AI-Finance` | Security | rahul@yourcompany.com | Finance agents only       |
| `AI-HR`      | Security | dixit@yourcompany.com | HR agents only            |

2. Copy each group's **Object ID** (found in group overview)

---

### Step 2: Configure App Registration for Group Claims

**In Azure Portal:**

1. Go to **Azure Active Directory** → **App registrations** → Your app
2. Click **Token configuration** → **Add groups claim**
3. Select **Security groups**
4. Check **Group ID** for access tokens
5. Save

**Result:** JWT tokens will now include `groups` claim with group IDs

---

### Step 3: Update Backend Configuration

**Add to `backend/.env`:**

```bash
# Copy Object IDs from Azure Portal → Entra ID → Groups
AZURE_AD_ADMIN_GROUP_ID=12345678-1234-1234-1234-123456789abc
AZURE_AD_FINANCE_GROUP_ID=22345678-1234-1234-1234-123456789def
AZURE_AD_HR_GROUP_ID=32345678-1234-1234-1234-123456789ghi
```

**Update `backend/rbac.py`** to use group claims (code provided in Step 2.2 Option B above)

---

## Why Azure Foundry RBAC Can't Do This

### Azure Foundry's Built-in Roles Limitations

| Role                       | What It Controls                               | What It CAN'T Control     |
| -------------------------- | ---------------------------------------------- | ------------------------- |
| `Azure AI User`            | Can build agents, run traces, use models       | ❌ Which specific agents  |
| `Azure AI Project Manager` | Can create projects, assign Azure AI User role | ❌ Agent-level filtering  |
| `Azure AI Account Owner`   | Can manage account, deploy models              | ❌ Agent visibility rules |

**From Microsoft docs:**

```json
"dataActions": [
  "Microsoft.CognitiveServices/accounts/AIServices/agents/read",
  "Microsoft.CognitiveServices/accounts/AIServices/agents/write",
  "Microsoft.CognitiveServices/accounts/AIServices/agents/delete"
]
```

☝️ These permissions apply to **ALL agents**, not individual agents.

**No support for:**

- ❌ Agent-specific RBAC conditions
- ❌ Agent tags or labels for access control
- ❌ Per-agent permission assignments
- ❌ Department-based agent filtering

---

## Alternative Approach: Multiple Foundry Projects

If you **really** want native Azure RBAC separation, create separate projects:

```
Subscription
├── Finance-Project
│   ├── Budget Agent
│   ├── Invoice Bot
│   └── RBAC: Tejas (Owner), Rahul (Azure AI User)
│
├── HR-Project
│   ├── Recruiting Agent
│   ├── HR Helper
│   └── RBAC: Tejas (Owner), Dixit (Azure AI User)
│
└── Admin-Project
    └── RBAC: Tejas only
```

**Pros:**

- ✅ Native Azure RBAC enforcement
- ✅ Complete project isolation
- ✅ Separate billing/cost tracking

**Cons:**

- ❌ Requires multiple Foundry projects (additional cost)
- ❌ Tejas must switch projects to see all agents
- ❌ More complex deployment and management
- ❌ No unified agent catalog

**Recommendation:** Use application-level RBAC (existing implementation) unless you have strict compliance requirements.

---

## Security Considerations

### Backend Enforcement (Critical)

✅ **Already implemented:**

```python
@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    user_email = current_user.get("preferred_username", "")

    # CHECK: Can this user access this agent?
    if not can_user_access_agent(user_email, request.agent_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Proceed with chat...
```

### Frontend Hiding (UI/UX only)

⚠️ **Frontend filtering is NOT security** - it's UI/UX:

```typescript
// src/services/api.ts
export const getAgents = async (): Promise<Agent[]> => {
  // Backend already filtered agents based on user's roles
  const response = await apiClient.get("/api/agents");
  return response.data.agents; // Only shows permitted agents
};
```

**Never filter agents client-side only!** Malicious users can bypass frontend code.

---

## Troubleshooting

### Issue: User sees no agents

**Possible causes:**

1. User has no role assigned → Check `get_user_roles()` logic
2. No agents match user's roles → Check `DEFAULT_AGENT_PERMISSIONS`
3. Agent names don't contain keywords → Rename agents or update keywords

**Debug:**

```python
# Add logging to backend/rbac.py
def get_user_roles(self, user_email: str) -> Set[UserRole]:
    roles = # ... your logic
    logger.info(f"User {user_email} has roles: {roles}")
    return roles
```

---

### Issue: User sees wrong agents

**Possible causes:**

1. Role mapping incorrect → Check email/group ID matching
2. Agent keywords overlap → Make keywords more specific
3. Caching issue → Clear browser cache, restart backend

**Debug:**

```python
# Add logging to filter_agents_by_access()
def can_access_agent(self, user_roles: Set[UserRole], agent_name: str) -> bool:
    required_roles = self.get_agent_required_roles(agent_name)
    can_access = bool(user_roles & required_roles)
    logger.info(f"Agent '{agent_name}' requires {required_roles}, user has {user_roles}, access={can_access}")
    return can_access
```

---

## Summary

| Question                                   | Answer                                                                               |
| ------------------------------------------ | ------------------------------------------------------------------------------------ |
| **Can Azure Foundry do agent-level RBAC?** | ❌ No, only project-level                                                            |
| **Do we need to rewrite everything?**      | ❌ No, already implemented!                                                          |
| **What do we configure?**                  | 1. Azure Foundry roles for project access<br>2. Application RBAC for agent filtering |
| **Is it secure?**                          | ✅ Yes, if backend enforces permissions                                              |
| **Can we use Azure AD groups?**            | ✅ Yes, recommended for production                                                   |

---

## Next Steps

### For Development (Quick Start)

1. ✅ Update `backend/rbac.py` with user-to-role mapping

   - Add Tejas → ADMIN
   - Add Rahul → FINANCE_ANALYST
   - Add Dixit → HR_ANALYST

2. ✅ Update agent names to include keywords

   - Finance agents: "Budget", "Invoice", "Expense"
   - HR agents: "Recruiting", "HR", "Employee"

3. ✅ Test with each user account
   - Verify filtered agent lists
   - Try unauthorized chat requests

### For Production (Enterprise)

1. Create Azure AD Security Groups (AI-Admins, AI-Finance, AI-HR)
2. Configure App Registration for group claims
3. Update `backend/rbac.py` to use group claims from JWT
4. Deploy and test with real users

---

**Created:** December 17, 2025  
**Status:** ✅ Backend implementation already exists, just needs configuration
