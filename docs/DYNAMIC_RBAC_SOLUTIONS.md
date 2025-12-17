# Dynamic Agent-Level RBAC Solutions

## Problem Statement

**Current Issue:** Hard-coded user-to-role mappings require code changes every time:

- New users are added
- Users change departments
- New roles are created
- New agents need role assignments

```python
# ❌ BAD: Hard-coded, not scalable
if email == "rahul@yourcompany.com":
    roles.add(UserRole.FINANCE_ANALYST)
```

**Requirements:**

1. ✅ No code changes when adding users
2. ✅ No code changes when creating new roles
3. ✅ No code changes when adding new agents
4. ✅ Centralized management in Azure Portal or configuration
5. ✅ Dynamic role-to-agent permission mapping

---

## Recommended Solution Comparison

| Solution                           | Scalability | Ease of Setup | No Code Changes | Admin UI     | Azure Native | Cost |
| ---------------------------------- | ----------- | ------------- | --------------- | ------------ | ------------ | ---- |
| **🥇 Azure AD App Roles + Config** | ⭐⭐⭐⭐⭐  | ⭐⭐⭐⭐      | ✅ Yes          | Azure Portal | ✅ Yes       | Free |
| **🥈 Azure AD Groups + Config**    | ⭐⭐⭐⭐⭐  | ⭐⭐⭐⭐⭐    | ✅ Yes          | Azure Portal | ✅ Yes       | Free |
| **🥉 Database-driven RBAC**        | ⭐⭐⭐⭐⭐  | ⭐⭐⭐        | ✅ Yes          | Custom Build | ⚠️ Partial   | $    |
| ❌ Hard-coded emails               | ⭐          | ⭐⭐⭐⭐⭐    | ❌ No           | None         | ❌ No        | Free |

---

## 🥇 Solution 1: Azure AD App Roles + Configuration File (RECOMMENDED)

**Best for:** Medium-to-large enterprises, requires minimal setup, fully Azure-native

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         Azure AD App Registration                           │
│                                                             │
│  App Roles (defined once):                                 │
│  ├─ Admin              (all agents)                        │
│  ├─ FinanceAnalyst     (finance agents)                    │
│  ├─ HRAnalyst          (HR agents)                         │
│  └─ BasicUser          (public agents)                     │
│                                                             │
│  Users assigned to roles:                                  │
│  ├─ Tejas  → Admin                                         │
│  ├─ Rahul  → FinanceAnalyst                                │
│  └─ Dixit  → HRAnalyst                                     │
└─────────────────────────────────────────────────────────────┘
                         ↓
                    JWT Token
        { "roles": ["FinanceAnalyst"] }
                         ↓
┌─────────────────────────────────────────────────────────────┐
│         Backend: rbac_config.json                           │
│                                                             │
│  {                                                          │
│    "role_permissions": {                                   │
│      "FinanceAnalyst": {                                   │
│        "agent_patterns": ["budget", "invoice", "finance"]  │
│      }                                                      │
│    }                                                        │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                         ↓
              Backend filters agents
                         ↓
        Rahul sees: Budget Agent, Invoice Bot
```

### Implementation Steps

#### Step 1: Define App Roles in Azure AD

**In Azure Portal:**

1. Navigate to **Azure Active Directory** → **App registrations** → Your app
2. Go to **App roles** → **Create app role**

**Create these roles:**

```json
Role 1: Admin
{
  "displayName": "Administrator",
  "description": "Full access to all agents and system configuration",
  "value": "Admin",
  "allowedMemberTypes": ["User"],
  "isEnabled": true
}

Role 2: FinanceAnalyst
{
  "displayName": "Finance Analyst",
  "description": "Access to finance and budget-related agents",
  "value": "FinanceAnalyst",
  "allowedMemberTypes": ["User"],
  "isEnabled": true
}

Role 3: HRAnalyst
{
  "displayName": "HR Analyst",
  "description": "Access to HR and recruiting agents",
  "value": "HRAnalyst",
  "allowedMemberTypes": ["User"],
  "isEnabled": true
}

Role 4: BasicUser
{
  "displayName": "Basic User",
  "description": "Access to general-purpose agents",
  "value": "BasicUser",
  "allowedMemberTypes": ["User"],
  "isEnabled": true
}
```

#### Step 2: Assign Users to App Roles

**In Azure Portal:**

1. Navigate to **Azure Active Directory** → **Enterprise applications** → Your app
2. Go to **Users and groups** → **Add user/group**

**Assign:**

- Tejas → Admin
- Rahul → FinanceAnalyst
- Dixit → HRAnalyst

**Result:** JWT tokens will include `roles` claim:

```json
{
  "preferred_username": "rahul@company.com",
  "roles": ["FinanceAnalyst"]
}
```

#### Step 3: Create Configuration File

**Create: `backend/rbac_config.json`**

```json
{
  "version": "1.0",
  "description": "Agent access control configuration",

  "role_permissions": {
    "Admin": {
      "description": "Full access to all agents",
      "agent_patterns": ["*"],
      "allow_all": true
    },

    "FinanceAnalyst": {
      "description": "Finance department agents",
      "agent_patterns": [
        "budget",
        "invoice",
        "expense",
        "financial",
        "accounting",
        "payroll"
      ],
      "allow_all": false
    },

    "HRAnalyst": {
      "description": "HR department agents",
      "agent_patterns": [
        "recruiting",
        "hr",
        "employee",
        "hiring",
        "onboarding",
        "benefits"
      ],
      "allow_all": false
    },

    "BasicUser": {
      "description": "General purpose agents",
      "agent_patterns": ["general", "assistant", "chat", "public"],
      "allow_all": false
    }
  },

  "default_role": "BasicUser",

  "agent_metadata": {
    "description": "Optional: Define specific agent permissions",
    "agents": {
      "Budget Planning Assistant": {
        "required_roles": ["Admin", "FinanceAnalyst"],
        "department": "Finance"
      },
      "Invoice Processing Bot": {
        "required_roles": ["Admin", "FinanceAnalyst"],
        "department": "Finance"
      },
      "Recruiting Assistant": {
        "required_roles": ["Admin", "HRAnalyst"],
        "department": "HR"
      }
    }
  }
}
```

**Key Benefits:**

- ✅ Add new roles: just update JSON, no code changes
- ✅ Add new agents: update agent_patterns in JSON
- ✅ Change permissions: edit JSON and restart backend
- ✅ Version controlled: track changes in Git

#### Step 4: Update Backend Code

**Update: `backend/rbac.py`**

```python
"""
Dynamic Role-Based Access Control using Azure AD App Roles + Configuration
"""

import json
import os
from typing import List, Set, Dict, Any
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AgentAccessControl:
    """
    Dynamic agent access control using Azure AD App Roles and configuration file.
    """

    def __init__(self, config_path: str = "backend/rbac_config.json"):
        """Initialize with configuration file"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        logger.info(f"Loaded RBAC configuration from {config_path}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return self._get_default_config()

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded {len(config.get('role_permissions', {}))} role configurations")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Fallback default configuration"""
        return {
            "role_permissions": {
                "Admin": {"agent_patterns": ["*"], "allow_all": True},
                "BasicUser": {"agent_patterns": ["general", "chat"], "allow_all": False}
            },
            "default_role": "BasicUser"
        }

    def reload_config(self):
        """Reload configuration file (useful for hot-reloading)"""
        self.config = self._load_config()
        logger.info("Configuration reloaded")

    def get_user_roles_from_token(self, token_payload: Dict[str, Any]) -> List[str]:
        """
        Extract roles from Azure AD token.

        Args:
            token_payload: Decoded JWT token from Azure AD

        Returns:
            List of role names from token's 'roles' claim
        """
        roles = token_payload.get("roles", [])

        if not roles:
            # Fallback to default role
            default_role = self.config.get("default_role", "BasicUser")
            logger.info(f"No roles in token, assigning default: {default_role}")
            roles = [default_role]
        else:
            logger.info(f"User has roles: {roles}")

        return roles

    def can_access_agent(self, user_roles: List[str], agent_name: str) -> bool:
        """
        Check if user with given roles can access the agent.

        Args:
            user_roles: List of role names from user's token
            agent_name: Name of the agent to check access for

        Returns:
            True if user can access the agent, False otherwise
        """
        agent_name_lower = agent_name.lower()
        role_permissions = self.config.get("role_permissions", {})

        for role in user_roles:
            if role not in role_permissions:
                logger.warning(f"Unknown role: {role}")
                continue

            role_config = role_permissions[role]

            # Check if role has full access
            if role_config.get("allow_all", False):
                logger.debug(f"Role '{role}' has full access")
                return True

            # Check agent patterns
            agent_patterns = role_config.get("agent_patterns", [])
            for pattern in agent_patterns:
                if pattern == "*" or pattern.lower() in agent_name_lower:
                    logger.debug(f"Agent '{agent_name}' matches pattern '{pattern}' for role '{role}'")
                    return True

        # Check agent-specific metadata (optional)
        agent_metadata = self.config.get("agent_metadata", {}).get("agents", {})
        if agent_name in agent_metadata:
            required_roles = agent_metadata[agent_name].get("required_roles", [])
            if any(role in required_roles for role in user_roles):
                logger.debug(f"Agent '{agent_name}' explicitly allows roles: {user_roles}")
                return True

        logger.debug(f"Access denied: Agent '{agent_name}' not accessible for roles {user_roles}")
        return False

    def filter_agents_by_access(self, user_roles: List[str], agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter list of agents based on user's roles.

        Args:
            user_roles: List of role names from user's token
            agents: List of agent dictionaries (must have 'name' or 'id' field)

        Returns:
            Filtered list of agents the user can access
        """
        filtered = []

        for agent in agents:
            agent_name = agent.get("name", agent.get("id", "Unknown"))
            if self.can_access_agent(user_roles, agent_name):
                filtered.append(agent)

        logger.info(f"Filtered {len(agents)} agents to {len(filtered)} for roles {user_roles}")
        return filtered
```

#### Step 5: Update Main API

**Update: `backend/main.py`**

```python
from fastapi import FastAPI, Depends, HTTPException
from backend.rbac import AgentAccessControl
from backend.auth import get_current_user

app = FastAPI()

# Initialize RBAC controller
rbac = AgentAccessControl(config_path="backend/rbac_config.json")

@app.get("/api/agents")
async def list_agents(current_user: dict = Depends(get_current_user)):
    """List agents filtered by user's roles"""

    # Get all agents from Azure Foundry
    all_agents = await azure_foundry_client.list_agents()

    # Extract roles from JWT token
    user_roles = rbac.get_user_roles_from_token(current_user)

    # Filter agents based on roles
    filtered_agents = rbac.filter_agents_by_access(user_roles, all_agents)

    return {"agents": filtered_agents, "user_roles": user_roles}


@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send message to agent (with RBAC check)"""

    # Get user roles
    user_roles = rbac.get_user_roles_from_token(current_user)

    # Get agent details
    agent = await azure_foundry_client.get_agent(request.agent_id)

    # Check access
    if not rbac.can_access_agent(user_roles, agent["name"]):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: You do not have permission to use agent '{agent['name']}'"
        )

    # Proceed with chat...
    response = await azure_foundry_client.chat(request.agent_id, request.message)
    return response


@app.post("/api/rbac/reload")
async def reload_rbac_config(current_user: dict = Depends(get_current_user)):
    """Reload RBAC configuration (admin only)"""

    user_roles = rbac.get_user_roles_from_token(current_user)

    if "Admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Admin role required")

    rbac.reload_config()
    return {"message": "RBAC configuration reloaded successfully"}
```

### Adding New Roles (No Code Changes!)

**Scenario:** New "SalesAnalyst" role needed for CRM agents

**Step 1: Azure Portal**

1. Go to App registrations → App roles → Create app role
2. Add role: `SalesAnalyst`

**Step 2: Update `rbac_config.json`**

```json
{
  "role_permissions": {
    "SalesAnalyst": {
      "description": "Sales and CRM agents",
      "agent_patterns": ["crm", "sales", "customer", "pipeline"],
      "allow_all": false
    }
  }
}
```

**Step 3: Restart backend (or call `/api/rbac/reload` endpoint)**

**Done!** No code changes required. Just assign users to the new role in Azure Portal.

---

## 🥈 Solution 2: Azure AD Security Groups + Configuration File

**Best for:** Enterprises already using Azure AD groups for access management

### Differences from App Roles

| Aspect         | App Roles        | Security Groups                 |
| -------------- | ---------------- | ------------------------------- |
| Setup location | App Registration | Azure Active Directory → Groups |
| Token claim    | `roles`          | `groups` (Group Object IDs)     |
| Visibility     | App-specific     | Organization-wide               |
| Use case       | App-level roles  | Department/team structure       |

### Implementation

#### Step 1: Create Security Groups

**In Azure Portal:**

1. Navigate to **Azure Active Directory** → **Groups** → **New group**

**Create groups:**

- `AI-Admins` (Object ID: `11111111-1111-1111-1111-111111111111`)
- `AI-Finance` (Object ID: `22222222-2222-2222-2222-222222222222`)
- `AI-HR` (Object ID: `33333333-3333-3333-3333-333333333333`)

2. Add members:
   - Tejas → AI-Admins
   - Rahul → AI-Finance
   - Dixit → AI-HR

#### Step 2: Configure Token Claims

**In Azure Portal:**

1. Go to **App registrations** → Your app → **Token configuration**
2. Click **Add groups claim** → Select **Security groups**
3. Check **Group ID** for access tokens

#### Step 3: Update Configuration File

**Create: `backend/rbac_config.json`**

```json
{
  "version": "1.0",
  "description": "RBAC using Azure AD Security Groups",

  "group_to_role_mapping": {
    "11111111-1111-1111-1111-111111111111": "Admin",
    "22222222-2222-2222-2222-222222222222": "FinanceAnalyst",
    "33333333-3333-3333-3333-333333333333": "HRAnalyst"
  },

  "role_permissions": {
    "Admin": {
      "agent_patterns": ["*"],
      "allow_all": true
    },
    "FinanceAnalyst": {
      "agent_patterns": ["budget", "invoice", "finance"]
    },
    "HRAnalyst": {
      "agent_patterns": ["recruiting", "hr", "employee"]
    }
  }
}
```

#### Step 4: Update Backend Code

```python
def get_user_roles_from_token(self, token_payload: Dict[str, Any]) -> List[str]:
    """
    Extract roles from Azure AD groups in token.
    """
    group_ids = token_payload.get("groups", [])
    group_to_role = self.config.get("group_to_role_mapping", {})

    roles = []
    for group_id in group_ids:
        if group_id in group_to_role:
            role = group_to_role[group_id]
            roles.append(role)
            logger.info(f"Mapped group {group_id} to role {role}")

    if not roles:
        roles = [self.config.get("default_role", "BasicUser")]

    return roles
```

### Adding New Groups (No Code Changes!)

**Scenario:** Add Sales team

1. Azure Portal → Create group `AI-Sales`
2. Copy group Object ID: `44444444-4444-4444-4444-444444444444`
3. Update `rbac_config.json`:
   ```json
   {
     "group_to_role_mapping": {
       "44444444-4444-4444-4444-444444444444": "SalesAnalyst"
     },
     "role_permissions": {
       "SalesAnalyst": {
         "agent_patterns": ["crm", "sales"]
       }
     }
   }
   ```
4. Restart backend

---

## 🥉 Solution 3: Database-Driven RBAC (Advanced)

**Best for:** Large enterprises requiring audit trails, admin UI, complex hierarchies

### Architecture

```
┌───────────────────────────────────────────┐
│     Azure Table Storage / SQL Database    │
│                                           │
│  Tables:                                  │
│  ├─ Users (email, department, roles)     │
│  ├─ Roles (role_id, name, description)   │
│  ├─ Agents (agent_id, name, department)  │
│  └─ RoleAgentPermissions                 │
│     (role_id, agent_id, access_level)    │
└───────────────────────────────────────────┘
                    ↑
                    │ Query on each request
                    ↓
┌───────────────────────────────────────────┐
│           Backend API                     │
│  - Fetch user's roles from database       │
│  - Query agent permissions                │
│  - Filter agents dynamically              │
└───────────────────────────────────────────┘
                    ↑
                    │
┌───────────────────────────────────────────┐
│      Admin UI (Optional)                  │
│  - Manage users and roles                 │
│  - Assign permissions                     │
│  - Audit logs                             │
└───────────────────────────────────────────┘
```

### Implementation (Azure Table Storage)

**Create Tables:**

**1. Roles Table:**
| PartitionKey | RowKey | RoleName | Description |
|--------------|--------|----------|-------------|
| roles | admin | Admin | Full access |
| roles | finance | FinanceAnalyst | Finance agents |
| roles | hr | HRAnalyst | HR agents |

**2. UserRoles Table:**
| PartitionKey | RowKey | Email | Roles |
|--------------|--------|-------|-------|
| users | tejas@company.com | tejas@company.com | ["admin"] |
| users | rahul@company.com | rahul@company.com | ["finance"] |
| users | dixit@company.com | dixit@company.com | ["hr"] |

**3. RolePermissions Table:**
| PartitionKey | RowKey | AgentPattern | AllowedRoles |
|--------------|--------|--------------|--------------|
| permissions | budget | budget* | ["admin", "finance"] |
| permissions | invoice | invoice* | ["admin", "finance"] |
| permissions | recruiting | recruit\* | ["admin", "hr"] |

**Backend Code:**

```python
from azure.data.tables import TableServiceClient

class DatabaseRBAC:
    def __init__(self, connection_string: str):
        self.table_client = TableServiceClient.from_connection_string(connection_string)
        self.user_roles_table = self.table_client.get_table_client("UserRoles")
        self.role_permissions_table = self.table_client.get_table_client("RolePermissions")

    def get_user_roles(self, email: str) -> List[str]:
        """Query user roles from database"""
        try:
            entity = self.user_roles_table.get_entity(
                partition_key="users",
                row_key=email
            )
            return entity.get("Roles", [])
        except Exception as e:
            logger.warning(f"User {email} not found in database: {e}")
            return []

    def can_access_agent(self, user_roles: List[str], agent_name: str) -> bool:
        """Query agent permissions from database"""
        query_filter = f"PartitionKey eq 'permissions'"
        entities = self.role_permissions_table.query_entities(query_filter)

        for entity in entities:
            pattern = entity.get("AgentPattern", "")
            allowed_roles = entity.get("AllowedRoles", [])

            if pattern in agent_name.lower():
                if any(role in allowed_roles for role in user_roles):
                    return True

        return False
```

### Adding New Users (Admin UI)

**REST API Endpoints:**

```python
@app.post("/api/admin/users")
async def create_user_role(
    email: str,
    roles: List[str],
    current_user: dict = Depends(require_admin)
):
    """Add user with roles to database"""
    entity = {
        "PartitionKey": "users",
        "RowKey": email,
        "Email": email,
        "Roles": roles
    }
    table_client.upsert_entity(entity)
    return {"message": f"User {email} assigned roles {roles}"}

@app.post("/api/admin/permissions")
async def create_permission(
    agent_pattern: str,
    allowed_roles: List[str],
    current_user: dict = Depends(require_admin)
):
    """Add agent permission rule"""
    entity = {
        "PartitionKey": "permissions",
        "RowKey": agent_pattern,
        "AgentPattern": agent_pattern,
        "AllowedRoles": allowed_roles
    }
    table_client.upsert_entity(entity)
    return {"message": f"Permission created for {agent_pattern}"}
```

**Benefits:**

- ✅ Fully dynamic, no file edits
- ✅ Admin UI for self-service management
- ✅ Audit trail (Table Storage timestamps)
- ✅ Supports complex permission hierarchies

**Drawbacks:**

- ❌ More complex setup
- ❌ Requires database schema design
- ❌ Slower than in-memory config (needs caching)

---

## Recommendation Summary

### For Tejas, Rahul, Dixit Scenario:

**🥇 Choose: Azure AD App Roles + Configuration File**

**Why:**

1. ✅ **No code changes:** Add users in Azure Portal, update JSON for agents
2. ✅ **Azure-native:** Uses App Roles feature built into Azure AD
3. ✅ **Easy to manage:** IT admin assigns roles in Enterprise Application
4. ✅ **Version controlled:** JSON file tracked in Git
5. ✅ **Fast:** No database queries, config loaded in memory
6. ✅ **Secure:** Roles come from trusted Azure AD token

**When to upgrade to Database-driven:**

- \> 10 custom roles
- Need admin UI for business users
- Require complex permission hierarchies
- Need detailed audit logs

---

## Implementation Checklist

### Phase 1: Azure AD Setup (1-2 hours)

- [ ] Create App Roles in App Registration (Admin, FinanceAnalyst, HRAnalyst)
- [ ] Assign Tejas → Admin
- [ ] Assign Rahul → FinanceAnalyst
- [ ] Assign Dixit → HRAnalyst
- [ ] Verify roles appear in JWT token (test with jwt.io)

### Phase 2: Backend Configuration (1 hour)

- [ ] Create `backend/rbac_config.json` with role permissions
- [ ] Update `backend/rbac.py` with dynamic role loading
- [ ] Update `backend/main.py` to use token roles
- [ ] Test locally with mock tokens

### Phase 3: Agent Naming (30 minutes)

- [ ] Rename agents to match patterns in config:
  - Finance: "Budget Planning", "Invoice Bot"
  - HR: "Recruiting Assistant", "HR Helper"
- [ ] Deploy agents to Azure Foundry

### Phase 4: Testing (1 hour)

- [ ] Test Tejas sees all agents
- [ ] Test Rahul sees only finance agents
- [ ] Test Dixit sees only HR agents
- [ ] Test unauthorized access returns 403

### Phase 5: Future Scalability (ongoing)

- [ ] Add new role: Just update Azure AD + JSON file
- [ ] Add new user: Just assign role in Azure Portal
- [ ] Add new agent: Include keyword in name, or update JSON

---

## FAQ

**Q: What if someone creates a new agent called "Budget" but it's actually for HR?**

**A:** Two options:

1. Use strict naming conventions (enforce "Finance: Budget" prefix)
2. Use agent-specific metadata in config:
   ```json
   "agent_metadata": {
     "agents": {
       "Budget Planner": {
         "required_roles": ["Admin", "FinanceAnalyst"]
       }
     }
   }
   ```

**Q: Can users have multiple roles?**

**A:** Yes! Azure AD supports multiple role assignments. User will see agents allowed by **any** of their roles (OR logic).

**Q: How do I test without Azure AD?**

**A:** Mock the token in development:

```python
if os.getenv("ENV") == "development":
    # Mock token for testing
    return {
        "preferred_username": "test@company.com",
        "roles": ["FinanceAnalyst"]
    }
```

**Q: Performance impact of loading JSON on every request?**

**A:** Load once at startup, cache in memory. Only reload when config changes:

```python
# Load once
rbac = AgentAccessControl("rbac_config.json")

# Reload endpoint (admin only)
@app.post("/api/rbac/reload")
async def reload_config():
    rbac.reload_config()
```

---

**Created:** December 17, 2025  
**Recommended:** Azure AD App Roles + Configuration File  
**Status:** Ready for implementation
