# RBAC (Role-Based Access Control) - Azure Setup Guide

## Overview

This guide provides step-by-step instructions to configure **Role-Based Access Control (RBAC)** in Azure Active Directory to control which users can access which AI agents.

---

## Table of Contents

1. [Azure AD Groups Setup](#azure-ad-groups-setup)
2. [App Registration Configuration](#app-registration-configuration)
3. [Group-Based Role Mapping](#group-based-role-mapping)
4. [Testing RBAC](#testing-rbac)

---

## Azure AD Groups Setup

### Prerequisites

- Azure AD administrator access
- Azure AD Premium P1 or P2 license (for group claims)
- List of users and their intended roles

### Roles Overview

| Role        | Access Level | Agent Types                       |
| ----------- | ------------ | --------------------------------- |
| **Admin**   | Full access  | All agents                        |
| **Analyst** | Data-focused | Data, analytics, reporting agents |
| **User**    | Standard     | Chat, assistant, general agents   |
| **Guest**   | Limited      | Public agents only                |

### Step 1: Create Azure AD Security Groups

#### 1.1 Navigate to Azure AD

1. Go to [Azure Portal](https://portal.azure.com/)
2. Click **"Azure Active Directory"**
3. Click **"Groups"** (left menu)

#### 1.2 Create Admin Group

1. Click **"+ New group"**
2. Fill in details:
   ```
   Group type: Security
   Group name: AI-Admins
   Group description: Users with full access to all AI agents
   Membership type: Assigned
   ```
3. Click **"No members selected"**
4. Search and add admin users:
   - Search for users by name or email
   - Select admin users
   - Click **"Select"**
5. Click **"Create"**

#### 1.3 Create Analyst Group

1. Click **"+ New group"**
2. Fill in details:
   ```
   Group type: Security
   Group name: AI-Analysts
   Group description: Users with access to data and analytics agents
   Membership type: Assigned
   ```
3. Add analyst users
4. Click **"Create"**

#### 1.4 Create User Group

1. Click **"+ New group"**
2. Fill in details:
   ```
   Group type: Security
   Group name: AI-Users
   Group description: Standard users with access to basic agents
   Membership type: Assigned
   ```
3. Add regular users
4. Click **"Create"**

#### 1.5 Create Guest Group (Optional)

1. Click **"+ New group"**
2. Fill in details:
   ```
   Group type: Security
   Group name: AI-Guests
   Group description: Limited access to public agents only
   Membership type: Assigned
   ```
3. Add guest users
4. Click **"Create"**

#### 1.6 Note Group Object IDs

For each group:

1. Click on the group name
2. Click **"Properties"**
3. Copy the **"Object ID"** - you'll need this for configuration

Example:

```
AI-Admins: 12345678-1234-1234-1234-123456789012
AI-Analysts: 23456789-2345-2345-2345-234567890123
AI-Users: 34567890-3456-3456-3456-345678901234
AI-Guests: 45678901-4567-4567-4567-456789012345
```

---

## App Registration Configuration

### Step 1: Add Group Claims to Token

#### 1.1 Navigate to App Registration

1. In Azure Portal, click **"Azure Active Directory"**
2. Click **"App registrations"**
3. Click on your application (the one used for authentication)

#### 1.2 Configure Token Claims

1. Click **"Token configuration"** (left menu)
2. Click **"+ Add groups claim"**
3. Select:
   ```
   ✅ Security groups
   ✅ Groups assigned to the application (if using app roles)
   ```
4. For **ID token**, select:
   ```
   ✅ Group ID
   ```
5. For **Access token**, select:
   ```
   ✅ Group ID
   ```
6. Click **"Add"**

#### 1.3 Configure Optional Claims (Recommended)

1. Still in **"Token configuration"**
2. Click **"+ Add optional claim"**
3. Select **"Access"** token
4. Add these claims:
   ```
   ✅ email
   ✅ family_name
   ✅ given_name
   ✅ upn (User Principal Name)
   ```
5. Click **"Add"**

#### 1.4 Grant Admin Consent

1. Click **"API permissions"** (left menu)
2. You should see **"GroupMember.Read.All"** or similar
3. If not, click **"+ Add a permission"** → **"Microsoft Graph"** → **"Delegated permissions"** → Add **"GroupMember.Read.All"**
4. Click **"Grant admin consent for [Your Tenant]"**
5. Click **"Yes"** to confirm

### Step 2: Update App Manifest (For Advanced Scenarios)

#### 2.1 Configure Group Membership Claims

1. In your App Registration, click **"Manifest"** (left menu)
2. Find the `groupMembershipClaims` property
3. Change it to:
   ```json
   "groupMembershipClaims": "SecurityGroup"
   ```
4. Click **"Save"**

This ensures group membership is included in the token.

---

## Group-Based Role Mapping

### Step 1: Update Backend Configuration

#### 1.1 Add Group IDs to Environment Variables

Add to your `.env` file:

```env
# RBAC - Azure AD Group IDs
AZURE_AD_GROUP_ADMINS=12345678-1234-1234-1234-123456789012
AZURE_AD_GROUP_ANALYSTS=23456789-2345-2345-2345-234567890123
AZURE_AD_GROUP_USERS=34567890-3456-3456-3456-345678901234
AZURE_AD_GROUP_GUESTS=45678901-4567-4567-4567-456789012345
```

#### 1.2 Update Config Module

Update `backend/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # RBAC - Azure AD Groups
    AZURE_AD_GROUP_ADMINS: Optional[str] = None
    AZURE_AD_GROUP_ANALYSTS: Optional[str] = None
    AZURE_AD_GROUP_USERS: Optional[str] = None
    AZURE_AD_GROUP_GUESTS: Optional[str] = None

    class Config:
        env_file = ".env"
```

#### 1.3 Update RBAC Module

Update `backend/rbac.py` to use Azure AD groups:

```python
from config import settings

@staticmethod
def get_user_roles(user_email: str, azure_user_data: dict = None) -> Set[UserRole]:
    """
    Determine user roles based on Azure AD group membership.
    """
    roles = {UserRole.USER}  # Default role

    # Get user's group memberships from token
    user_groups = []
    if azure_user_data:
        user_groups = azure_user_data.get("groups", [])

    # Map Azure AD groups to roles
    if settings.AZURE_AD_GROUP_ADMINS in user_groups:
        roles.add(UserRole.ADMIN)
        logger.info(f"User {user_email} assigned ADMIN role (Azure AD group)")

    if settings.AZURE_AD_GROUP_ANALYSTS in user_groups:
        roles.add(UserRole.ANALYST)
        logger.info(f"User {user_email} assigned ANALYST role (Azure AD group)")

    if settings.AZURE_AD_GROUP_USERS in user_groups:
        roles.add(UserRole.USER)
        logger.info(f"User {user_email} assigned USER role (Azure AD group)")

    if settings.AZURE_AD_GROUP_GUESTS in user_groups:
        roles.add(UserRole.GUEST)
        logger.info(f"User {user_email} assigned GUEST role (Azure AD group)")

    # Fallback to email-based detection if no groups found
    if len(roles) == 1 and UserRole.USER in roles:
        # Use existing email-based logic as fallback
        admin_domains = ["admin.com", "leadership.com"]
        admin_emails = []

        email_domain = user_email.split("@")[-1] if "@" in user_email else ""

        if email_domain in admin_domains or user_email in admin_emails:
            roles.add(UserRole.ADMIN)
            logger.info(f"User {user_email} assigned ADMIN role (email domain)")

        analyst_keywords = ["analyst", "data", "bi", "analytics"]
        if any(keyword in user_email.lower() for keyword in analyst_keywords):
            roles.add(UserRole.ANALYST)
            logger.info(f"User {user_email} assigned ANALYST role (email keyword)")

    logger.info(f"Final roles for {user_email}: {[r.value for r in roles]}")
    return roles
```

### Step 2: Update Authentication Module

Update `backend/auth.py` to extract group claims:

```python
async def validate_token(self, token: str) -> Dict[str, Any]:
    """
    Validate Azure Entra ID access token and extract claims.
    """
    try:
        # ... existing validation code ...

        # Decode and verify token
        signing_key = self.jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.client_id,
            issuer=issuer,
            options={"verify_exp": True}
        )

        # Extract group memberships
        groups = payload.get("groups", [])

        logger.info(f"Token validated for user: {payload.get('email', 'unknown')}")
        logger.info(f"User groups: {groups}")

        # Add groups to payload for RBAC
        payload["groups"] = groups

        return payload

    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
```

Update the `get_current_user` function to pass groups:

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> UserProfile:
    """Get current user from token with group membership."""
    token = credentials.credentials
    claims = await auth_handler.validate_token(token)

    # Get or create user
    user = await asyncio.to_thread(
        table_storage.get_or_create_user,
        azure_id=claims.get("oid") or claims.get("sub"),
        email=claims.get("email") or claims.get("upn"),
        name=claims.get("name", "Unknown User")
    )

    # Add groups to user profile for RBAC
    user_profile = UserProfile(**user)
    user_profile.azure_data = {"groups": claims.get("groups", [])}

    return user_profile
```

Update `models.py` to include azure_data:

```python
class UserProfile(BaseModel):
    """User profile information from Azure Entra ID"""
    id: UUID
    azure_id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: datetime
    azure_data: Optional[Dict[str, Any]] = {}  # Add this field
```

---

## Testing RBAC

### Step 1: Verify Group Membership

#### 1.1 Check User's Groups in Azure AD

1. Go to Azure Portal → Azure Active Directory
2. Click **"Users"**
3. Click on a test user
4. Click **"Groups"** (left menu)
5. Verify user is in correct groups

#### 1.2 Test Token Contains Groups

Run this test script:

```python
# test_token_groups.py
import os
import requests
from msal import PublicClientApplication

# Your app configuration
client_id = os.getenv("AZURE_CLIENT_ID")
tenant_id = os.getenv("AZURE_TENANT_ID")
authority = f"https://login.microsoftonline.com/{tenant_id}"

# Create MSAL app
app = PublicClientApplication(
    client_id=client_id,
    authority=authority
)

# Get token interactively
scopes = ["User.Read"]
result = app.acquire_token_interactive(scopes=scopes)

if "access_token" in result:
    # Decode token to see claims
    import jwt
    token = result["access_token"]
    decoded = jwt.decode(token, options={"verify_signature": False})

    print("User:", decoded.get("email") or decoded.get("upn"))
    print("Groups:", decoded.get("groups", []))

    if "groups" not in decoded:
        print("\n⚠️  WARNING: No groups in token!")
        print("Make sure 'Group claims' are configured in App Registration")
else:
    print("Error:", result.get("error_description"))
```

### Step 2: Test API Endpoints

#### 2.1 Test User Roles Endpoint

```bash
# Get user roles
curl http://localhost:8000/api/user-roles \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected response:

```json
{
  "success": true,
  "user_email": "admin@company.com",
  "roles": ["admin", "user"],
  "description": {
    "admin": "Full access to all agents",
    "analyst": "Access to data analysis agents",
    "user": "Access to basic chat agents",
    "guest": "Limited access"
  }
}
```

#### 2.2 Test Agent Filtering

Test with different users:

**Admin user:**

```bash
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Should return ALL agents
```

**Analyst user:**

```bash
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer ANALYST_TOKEN"

# Should return data/analytics/chat agents (not admin agents)
```

**Regular user:**

```bash
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer USER_TOKEN"

# Should return only chat/assistant agents
```

### Step 3: End-to-End Testing

#### 3.1 Create Test Users

Create test accounts in Azure AD:

```
admin-test@yourdomain.com    → Add to AI-Admins group
analyst-test@yourdomain.com  → Add to AI-Analysts group
user-test@yourdomain.com     → Add to AI-Users group
guest-test@yourdomain.com    → Add to AI-Guests group
```

#### 3.2 Test Login Flow

For each test user:

1. Log in to your application
2. Check what agents they see
3. Verify they can't access restricted agents
4. Check logs for role assignment

#### 3.3 Test Role Changes

1. Add a user to a new group in Azure AD
2. User logs out and logs back in
3. Verify they see additional agents
4. Check role assignment in logs

---

## Advanced Configuration

### Option 1: Use App Roles (Instead of Groups)

App Roles are an alternative to Security Groups.

#### Create App Roles

1. In App Registration, click **"App roles"**
2. Click **"+ Create app role"**
3. Create roles:

```
Display name: Admin
Value: admin
Description: Full access to all agents
Allowed member types: Users/Groups
Enable this app role: Yes
```

Repeat for: analyst, user, guest

#### Assign Users to App Roles

1. Go to **"Enterprise applications"**
2. Find your app
3. Click **"Users and groups"**
4. Click **"+ Add user/group"**
5. Select user and assign role

### Option 2: Dynamic Groups (Requires Azure AD Premium P1)

Create groups that auto-assign based on user attributes:

```
Rule syntax:
user.department -eq "IT"          → AI-Admins
user.jobTitle -contains "Analyst" → AI-Analysts
user.userType -eq "Member"        → AI-Users
user.userType -eq "Guest"         → AI-Guests
```

### Option 3: Nested Groups

Create hierarchical group structure:

```
AI-All-Users (parent)
├── AI-Admins (inherits all + admin access)
├── AI-Analysts (inherits all + analyst access)
└── AI-Users (basic access)
```

---

## Monitoring and Auditing

### Step 1: Enable Azure AD Sign-in Logs

1. In Azure Portal → Azure Active Directory
2. Click **"Monitoring"** → **"Sign-in logs"**
3. Filter by your application
4. View user sign-ins and group claims

### Step 2: Check Application Logs

Monitor your backend logs for:

```
✓ User roles assigned from Azure AD groups
✓ Agent filtering applied
✓ Access denied attempts
```

### Step 3: Create Alerts (Optional)

Set up alerts for:

- Failed authorization attempts
- Users with no group membership
- Unexpected role assignments

---

## Troubleshooting

### Issue: Groups not in token

**Solutions:**

1. Verify token configuration includes group claims
2. Check admin consent was granted for GroupMember.Read.All
3. Ensure groupMembershipClaims is set to "SecurityGroup" in manifest
4. User must log out and log back in after group changes

### Issue: Too many groups (token size limit)

If user is in >200 groups, Azure AD returns a `groups:src1` claim instead.

**Solution:**
Use the Microsoft Graph API to fetch groups:

```python
# Instead of reading groups from token
groups_url = "https://graph.microsoft.com/v1.0/me/memberOf"
response = requests.get(groups_url, headers={"Authorization": f"Bearer {token}"})
groups = [g["id"] for g in response.json()["value"]]
```

### Issue: User sees wrong agents

**Solutions:**

1. Check user's group membership in Azure AD
2. Verify group IDs match in .env file
3. Check logs for role assignment
4. User must log out and log back in after group changes

### Issue: Guest users can't access

**Solutions:**

1. Verify guest users are in AI-Guests group
2. Check guest user settings in Azure AD
3. Ensure app allows guest users
4. Verify guest users accepted invitation

---

## Security Best Practices

### Access Control

✅ **Use Security Groups** (not distribution lists)  
✅ **Implement least privilege** (start with minimal access)  
✅ **Regular access reviews** (quarterly audit group membership)  
✅ **Remove ex-employees** from groups immediately  
✅ **Document group purposes** in descriptions

### Token Security

✅ **Short token lifetimes** (1 hour max)  
✅ **Validate tokens on every request**  
✅ **Don't trust client-side role claims**  
✅ **Log all authorization decisions**  
✅ **Implement rate limiting per user**

### Audit and Compliance

✅ **Enable Azure AD audit logs**  
✅ **Monitor group membership changes**  
✅ **Track agent access patterns**  
✅ **Generate access reports regularly**  
✅ **Keep security group documentation updated**

---

## Success Checklist

✅ Azure AD Security Groups created (Admins, Analysts, Users, Guests)  
✅ Users assigned to appropriate groups  
✅ Group Object IDs documented  
✅ App Registration configured for group claims  
✅ Token configuration includes groups  
✅ Admin consent granted for GroupMember.Read.All  
✅ Backend config updated with group IDs  
✅ RBAC module uses Azure AD groups  
✅ Auth module extracts group claims  
✅ Test users created for each role  
✅ API endpoints return correct roles  
✅ Agent filtering works per role  
✅ Logs show role assignments  
✅ Users see only authorized agents

---

## Maintenance

### Weekly Tasks

- Review new user additions
- Check for users in wrong groups
- Monitor failed authorization attempts

### Monthly Tasks

- Audit group membership
- Review and update agent access patterns
- Check for orphaned accounts

### Quarterly Tasks

- Complete access review
- Update RBAC documentation
- Test with new agents
- Review and optimize group structure

---

## Next Steps

1. **Test with Real Users**

   - Deploy to test environment
   - Get feedback from different roles
   - Refine group assignments

2. **Add More Granular Controls**

   - Agent-level permissions (beyond visibility)
   - Time-based access
   - Location-based restrictions

3. **Integrate with Compliance Tools**

   - Export access logs
   - Generate compliance reports
   - Implement approval workflows

4. **Enhance UI**
   - Show user's roles in profile
   - Display why agent is/isn't accessible
   - Add role request workflow

---

**Estimated Setup Time:** 1-2 hours  
**Complexity:** Medium  
**Prerequisites:** Azure AD admin access, Premium P1 license (for group claims)
