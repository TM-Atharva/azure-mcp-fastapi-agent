# Official Microsoft MCP OAuth Identity Passthrough - Implementation Plan

## Overview

This guide provides step-by-step instructions to implement **official Microsoft MCP (Model Context Protocol) OAuth Identity Passthrough** for Azure Foundry Agents, following the [official Microsoft documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/mcp-authentication).

---

## Current State vs Target State

### What You Have Now
- ✅ User authentication with Azure Entra ID
- ✅ JWT token validation
- ✅ User context passed via headers
- ✅ Using `/models/chat/completions` API (Chat Completions)
- ⚠️ Custom SharePoint RAG implementation

### What You Need (Official MCP)
- ✅ User authentication with Azure Entra ID (keep)
- 🔄 Use **Azure Agent SDK** instead of Chat Completions
- ➕ Configure **MCP tools** in agents
- ➕ Set up **OAuth connections** in Azure Foundry
- ➕ Handle **Foundry-managed consent flow**
- ➕ Let Foundry store/manage OAuth tokens

---

## Phase 1: Azure Portal Configuration

### Step 1: Access Azure AI Foundry Portal

1. Navigate to [https://ai.azure.com/](https://ai.azure.com/)
2. Sign in with your Azure credentials
3. Select your **Azure AI Foundry Project**
   - Or create a new project if needed

### Step 2: Create OAuth Connection for MCP Server

#### 2.1 Navigate to Connections

1. In Azure AI Foundry Portal, click on **"Settings"** (left sidebar)
2. Click on **"Connections"**
3. Click **"+ New connection"**

#### 2.2 Configure OAuth Connection

**For SharePoint/Microsoft Graph:**

1. **Connection Type:** Select **"Custom OAuth"**
2. **Connection Name:** `sharepoint-oauth`
3. **Display Name:** `SharePoint OAuth Connection`

4. **OAuth Configuration:**
   ```
   Client ID: [Your Azure AD App Client ID]
   Client Secret: [Your Azure AD App Client Secret]
   
   Authorization URL: 
   https://login.microsoftonline.com/{YOUR_TENANT_ID}/oauth2/v2.0/authorize
   
   Token URL:
   https://login.microsoftonline.com/{YOUR_TENANT_ID}/oauth2/v2.0/token
   
   Refresh URL:
   https://login.microsoftonline.com/{YOUR_TENANT_ID}/oauth2/v2.0/token
   
   Scopes:
   Sites.Read.All Files.Read.All User.Read offline_access
   ```

5. Click **"Create"**
6. Note the **Connection ID** - you'll need this for MCP tool configuration

**For GitHub (Optional):**

1. **Connection Type:** Select **"Custom OAuth"**
2. **Connection Name:** `github-oauth`
3. **OAuth Configuration:**
   ```
   Client ID: [Your GitHub OAuth App Client ID]
   Client Secret: [Your GitHub OAuth App Client Secret]
   
   Authorization URL: https://github.com/login/oauth/authorize
   Token URL: https://github.com/login/oauth/access_token
   Refresh URL: https://github.com/login/oauth/access_token
   
   Scopes: repo read:org read:user
   ```

### Step 3: Configure MCP Server

#### 3.1 Deploy MCP Server (if custom)

If using custom MCP server:
1. Deploy your MCP server to Azure (App Service, Container Apps, etc.)
2. Note the **Server URL** (e.g., `https://your-mcp-server.azurewebsites.net/mcp`)

For Microsoft services (SharePoint, Graph):
- Use Microsoft Graph MCP server: `https://graph.microsoft.com/mcp/`
- Or use Microsoft's official MCP servers when available

#### 3.2 Test MCP Server Endpoint

Verify your MCP server is accessible:
```bash
curl https://your-mcp-server.azurewebsites.net/mcp/health
```

### Step 4: Configure Agent with MCP Tools

#### 4.1 Navigate to Agents

1. In Azure AI Foundry Portal, click **"Agents"** (left sidebar)
2. Select your existing agent or create a new one
3. Click **"Edit agent"**

#### 4.2 Add MCP Tool to Agent

1. Scroll to **"Tools"** section
2. Click **"+ Add tool"**
3. Select **"MCP (Model Context Protocol)"**

4. **MCP Tool Configuration:**
   ```
   Tool Name: sharepoint_search
   Tool Label: SharePoint Search
   
   Server URL: https://graph.microsoft.com/mcp/
   Server Label: microsoft-graph
   
   Connection: sharepoint-oauth (select from dropdown)
   
   Require Approval: Never
   (or "Always" if you want user confirmation)
   
   Description: 
   Searches SharePoint sites and documents using the user's permissions.
   Returns only documents the user has access to.
   ```

5. Click **"Save tool"**

#### 4.3 Configure Multiple MCP Tools (Optional)

Repeat for other MCP servers:
- GitHub: `https://github.com/mcp/` (if available)
- Custom MCP servers you've deployed

### Step 5: Update Agent Instructions

Update your agent's system instructions to use MCP tools:

```
You are an AI assistant with access to the user's SharePoint documents.

When the user asks about documents, reports, or files:
1. Use the sharepoint_search tool to find relevant documents
2. Only show results the user has permission to access
3. Provide summaries and links to documents

Important:
- User's permissions are automatically enforced
- If you need access to SharePoint, you will prompt for OAuth consent
- Always respect user privacy and data access policies

Available tools:
- sharepoint_search: Search SharePoint sites and documents
```

Save the agent configuration.

---

## Phase 2: Backend Code Changes

### Step 1: Update Dependencies

Add Azure Agent SDK to `requirements.txt`:

```txt
azure-ai-projects==1.0.0b3  # Already installed
azure-identity==1.19.0      # Already installed
```

### Step 2: Create New Azure Foundry Client Module

Create `backend/azure_foundry_mcp.py`:

```python
"""
Azure Foundry MCP Client - Official Implementation

This module implements the official Microsoft MCP OAuth Identity Passthrough
pattern using Azure Agent SDK.
"""

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentThread,
    AgentThreadCreationOptions,
    AgentMessage,
    AgentMessageRole
)
from azure.identity import DefaultAzureCredential
from typing import Dict, Any, AsyncGenerator, Optional
import logging
import asyncio

from config import settings

logger = logging.getLogger(__name__)


class AzureFoundryMCPClient:
    """
    Official MCP client using Azure Agent SDK.
    
    This replaces direct Chat Completions API calls with
    proper Agent SDK usage including MCP tool support.
    """
    
    def __init__(self):
        self.project_endpoint = settings.AZURE_FOUNDRY_ENDPOINT
        self.credential = DefaultAzureCredential()
        
        # Initialize AI Project Client
        self.project_client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=self.credential
        )
        
        logger.info("✓ Azure Foundry MCP Client initialized")
        logger.info(f"  Endpoint: {self.project_endpoint}")
    
    async def create_thread_for_user(
        self,
        user_azure_id: str,
        user_email: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create an agent thread for a user.
        
        Args:
            user_azure_id: User's Azure AD object ID
            user_email: User's email
            metadata: Optional thread metadata
        
        Returns:
            Thread ID
        """
        try:
            thread_metadata = metadata or {}
            thread_metadata.update({
                "user_azure_id": user_azure_id,
                "user_email": user_email
            })
            
            # Create thread using asyncio.to_thread for sync SDK
            thread = await asyncio.to_thread(
                self.project_client.agents.create_thread,
                metadata=thread_metadata
            )
            
            logger.info(f"Created thread {thread.id} for user {user_email}")
            return thread.id
            
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise
    
    async def send_message_to_agent(
        self,
        agent_id: str,
        thread_id: str,
        message: str,
        user_azure_id: str,
        user_email: str,
        user_oauth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to an agent with MCP support.
        
        This method:
        1. Adds user message to thread
        2. Runs the agent with user context
        3. Handles OAuth consent requests if needed
        4. Returns agent response
        
        Args:
            agent_id: Agent ID
            thread_id: Thread ID
            message: User's message
            user_azure_id: User's Azure AD ID
            user_email: User's email
            user_oauth_token: Optional OAuth token for MCP servers
        
        Returns:
            Dict with response and consent info if needed
        """
        try:
            # Step 1: Add user message to thread
            await asyncio.to_thread(
                self.project_client.agents.create_message,
                thread_id=thread_id,
                role=AgentMessageRole.USER,
                content=message
            )
            
            logger.info(f"Added message to thread {thread_id}")
            
            # Step 2: Create and run agent with user context
            run_options = {
                "agent_id": agent_id,
                "thread_id": thread_id,
                "metadata": {
                    "user_azure_id": user_azure_id,
                    "user_email": user_email
                }
            }
            
            # If user has OAuth token, include it
            if user_oauth_token:
                run_options["additional_instructions"] = (
                    f"User context: {user_email}\n"
                    f"OAuth token available for MCP tools."
                )
            
            run = await asyncio.to_thread(
                self.project_client.agents.create_and_process_run,
                **run_options
            )
            
            logger.info(f"Run {run.id} status: {run.status}")
            
            # Step 3: Check for OAuth consent request
            if run.status == "requires_action":
                required_action = run.required_action
                
                if required_action.type == "oauth_consent":
                    # Foundry needs OAuth consent from user
                    consent_request = required_action.oauth_consent_request
                    
                    logger.warning(f"OAuth consent required for {consent_request.provider}")
                    
                    return {
                        "type": "oauth_consent_required",
                        "provider": consent_request.provider,
                        "consent_url": consent_request.consent_url,
                        "scopes": consent_request.scopes,
                        "message": f"Please authorize access to {consent_request.provider}",
                        "run_id": run.id,
                        "thread_id": thread_id
                    }
            
            # Step 4: Get agent response messages
            messages = await asyncio.to_thread(
                self.project_client.agents.list_messages,
                thread_id=thread_id
            )
            
            # Get the latest assistant message
            assistant_messages = [
                msg for msg in messages.data 
                if msg.role == AgentMessageRole.ASSISTANT
            ]
            
            if not assistant_messages:
                raise Exception("No assistant response found")
            
            latest_message = assistant_messages[0]
            
            return {
                "type": "message",
                "content": latest_message.content[0].text.value,
                "message_id": latest_message.id,
                "run_id": run.id,
                "thread_id": thread_id
            }
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    async def continue_after_consent(
        self,
        run_id: str,
        thread_id: str
    ) -> Dict[str, Any]:
        """
        Continue agent run after user has provided OAuth consent.
        
        Args:
            run_id: The run ID that required consent
            thread_id: Thread ID
        
        Returns:
            Agent response
        """
        try:
            # Resume the run - Foundry now has user's OAuth token
            run = await asyncio.to_thread(
                self.project_client.agents.submit_tool_outputs_to_run,
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=[]  # Empty, consent was provided
            )
            
            # Wait for completion
            while run.status in ["in_progress", "queued"]:
                await asyncio.sleep(1)
                run = await asyncio.to_thread(
                    self.project_client.agents.get_run,
                    thread_id=thread_id,
                    run_id=run_id
                )
            
            # Get response
            messages = await asyncio.to_thread(
                self.project_client.agents.list_messages,
                thread_id=thread_id
            )
            
            assistant_messages = [
                msg for msg in messages.data 
                if msg.role == AgentMessageRole.ASSISTANT
            ]
            
            latest_message = assistant_messages[0]
            
            return {
                "type": "message",
                "content": latest_message.content[0].text.value,
                "message_id": latest_message.id,
                "run_id": run.id
            }
            
        except Exception as e:
            logger.error(f"Failed to continue after consent: {e}")
            raise


# Global instance
mcp_client = AzureFoundryMCPClient()
```

### Step 3: Update Main API Endpoints

Update `backend/main.py` to support MCP consent flow:

```python
# Add to imports
from azure_foundry_mcp import mcp_client

# New model for consent callback
class OAuthConsentCallback(BaseModel):
    run_id: str
    thread_id: str
    consented: bool

# Update chat endpoint
@app.post("/api/chat/mcp")
async def send_message_mcp(
    request: SendMessageRequest,
    current_user: UserProfile = Depends(get_current_user),
    mcp_context: Dict[str, Any] = Depends(get_mcp_context)
):
    """
    Send message using official MCP with OAuth consent support.
    """
    try:
        # Get or create thread
        thread_id = request.metadata.get("thread_id")
        if not thread_id:
            thread_id = await mcp_client.create_thread_for_user(
                user_azure_id=current_user.azure_id,
                user_email=current_user.email
            )
        
        # Get agent ID from session
        session = await table_storage.get_session_by_id(
            user_azure_id=current_user.azure_id,
            session_id=str(request.session_id)
        )
        agent_id = session.get("agent_azure_id")
        
        # Send message
        response = await mcp_client.send_message_to_agent(
            agent_id=agent_id,
            thread_id=thread_id,
            message=request.content,
            user_azure_id=current_user.azure_id,
            user_email=current_user.email,
            user_oauth_token=mcp_context.get("oauth_token")
        )
        
        # Check if consent is required
        if response["type"] == "oauth_consent_required":
            # Return consent request to frontend
            return {
                "status": "consent_required",
                "consent_url": response["consent_url"],
                "provider": response["provider"],
                "scopes": response["scopes"],
                "run_id": response["run_id"],
                "thread_id": response["thread_id"],
                "message": response["message"]
            }
        
        # Normal response
        return {
            "status": "success",
            "content": response["content"],
            "message_id": response["message_id"],
            "thread_id": response["thread_id"]
        }
        
    except Exception as e:
        logger.error(f"MCP chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/mcp/consent-callback")
async def handle_consent_callback(
    callback: OAuthConsentCallback,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Handle OAuth consent callback from frontend.
    
    After user consents in popup, frontend calls this endpoint
    to continue the agent run.
    """
    try:
        if not callback.consented:
            return {"status": "consent_denied"}
        
        # Continue agent run with consent
        response = await mcp_client.continue_after_consent(
            run_id=callback.run_id,
            thread_id=callback.thread_id
        )
        
        return {
            "status": "success",
            "content": response["content"],
            "message_id": response["message_id"]
        }
        
    except Exception as e:
        logger.error(f"Consent callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Phase 3: Frontend Changes

### Step 1: Update API Client

Add to `src/services/api.ts`:

```typescript
interface MCPChatResponse {
  status: 'success' | 'consent_required';
  content?: string;
  consent_url?: string;
  provider?: string;
  scopes?: string[];
  run_id?: string;
  thread_id?: string;
  message?: string;
}

async sendMessageMCP(
  sessionId: string,
  content: string,
  threadId?: string
): Promise<MCPChatResponse> {
  const response = await this.client.post<MCPChatResponse>('/chat/mcp', {
    session_id: sessionId,
    content,
    metadata: { thread_id: threadId }
  });
  return response.data;
}

async handleConsentCallback(
  runId: string,
  threadId: string,
  consented: boolean
): Promise<any> {
  const response = await this.client.post('/chat/mcp/consent-callback', {
    run_id: runId,
    thread_id: threadId,
    consented
  });
  return response.data;
}
```

### Step 2: Update Chat Component

Add consent handling to `src/components/Chat.tsx`:

```typescript
const [consentInfo, setConsentInfo] = useState<any>(null);

const handleSendMessage = async () => {
  try {
    const response = await apiClient.sendMessageMCP(
      currentSession.id,
      message,
      threadId
    );
    
    if (response.status === 'consent_required') {
      // Show consent dialog
      setConsentInfo(response);
      
      // Open consent URL in popup
      const popup = window.open(
        response.consent_url,
        'oauth-consent',
        'width=500,height=600'
      );
      
      // Wait for popup to close
      const checkPopup = setInterval(() => {
        if (popup?.closed) {
          clearInterval(checkPopup);
          handleConsentComplete(response.run_id, response.thread_id);
        }
      }, 1000);
    } else {
      // Normal message response
      addMessage({
        role: 'assistant',
        content: response.content
      });
    }
  } catch (error) {
    // Handle error
  }
};

const handleConsentComplete = async (runId: string, threadId: string) => {
  try {
    const response = await apiClient.handleConsentCallback(
      runId,
      threadId,
      true
    );
    
    if (response.status === 'success') {
      addMessage({
        role: 'assistant',
        content: response.content
      });
    }
  } catch (error) {
    console.error('Consent callback failed:', error);
  }
};
```

---

## Phase 4: Testing

### Step 1: Test OAuth Connection

1. In Azure Foundry Portal, go to Connections
2. Find your `sharepoint-oauth` connection
3. Click **"Test connection"**
4. Verify it shows "Connected"

### Step 2: Test Agent with MCP Tool

1. In Azure Foundry Portal, go to Agents
2. Open your agent with MCP tool
3. Click **"Test agent"**
4. Send a message: "Search for quarterly reports in SharePoint"
5. Verify:
   - Agent prompts for OAuth consent
   - Consent link appears
   - After consent, search works

### Step 3: Test End-to-End Flow

1. Start your backend: `python main.py`
2. Start your frontend: `npm run dev`
3. Log in as a user
4. Send a message that requires SharePoint access
5. Verify:
   - Consent popup appears
   - User can grant access
   - Agent continues with search results
   - Results respect user permissions

### Step 4: Verify MCP Logs

Check backend logs for:
```
✓ Azure Foundry MCP Client initialized
✓ OAuth consent required for microsoft-graph
✓ Run continued after consent
✓ MCP tool invoked successfully
```

---

## Phase 5: Migration Strategy

### Option A: Gradual Migration (Recommended)

1. **Keep existing chat endpoint** (`/api/chat`) working
2. **Add new MCP endpoint** (`/api/chat/mcp`) alongside
3. **Add feature flag** to switch between implementations
4. **Test MCP endpoint** thoroughly
5. **Migrate users** gradually
6. **Deprecate old endpoint** once stable

### Option B: Direct Migration

1. Replace Chat Completions API with Agent SDK
2. Update all endpoints at once
3. Test thoroughly before deploying
4. Have rollback plan ready

---

## Configuration Reference

### Environment Variables

Add to `.env`:

```env
# Azure Foundry MCP
AZURE_FOUNDRY_ENDPOINT=https://your-project.inference.ai.azure.com
AZURE_FOUNDRY_MCP_ENABLED=true

# OAuth Connections (from Foundry Portal)
SHAREPOINT_CONNECTION_ID=your-connection-id-from-portal
GITHUB_CONNECTION_ID=your-github-connection-id

# Feature Flags
USE_OFFICIAL_MCP=true  # Toggle between implementations
```

### Agent Configuration JSON

Example of agent with MCP tools (for reference):

```json
{
  "name": "SharePoint Assistant",
  "instructions": "You help users search SharePoint...",
  "model": "gpt-4",
  "tools": [
    {
      "type": "mcp",
      "mcp": {
        "server_url": "https://graph.microsoft.com/mcp/",
        "server_label": "microsoft-graph",
        "project_connection_id": "sharepoint-oauth",
        "require_approval": "never"
      }
    }
  ]
}
```

---

## Troubleshooting

### Issue: "Connection not found"

**Solution:**
1. Verify connection exists in Azure Foundry Portal
2. Check connection ID matches agent configuration
3. Ensure connection status is "Connected"

### Issue: "OAuth consent loop"

**Solution:**
1. Check redirect URI in Azure AD app registration
2. Verify scopes match what's configured in connection
3. Clear browser cookies and retry

### Issue: "MCP tool not invoked"

**Solution:**
1. Check agent instructions mention the tool
2. Verify tool is added to agent configuration
3. Test user query is relevant to tool's purpose

### Issue: "Permission denied after consent"

**Solution:**
1. Check OAuth scopes include required permissions
2. Verify user has permissions in SharePoint
3. Check token refresh is working in Foundry

---

## Success Criteria

✅ **Implementation is successful when:**

1. Agent uses MCP tools defined in Foundry Portal
2. OAuth consent flow is handled by Foundry (not custom code)
3. User sees consent popup for external services
4. Foundry manages and refreshes OAuth tokens
5. Agent can access user's SharePoint/GitHub/etc. with proper permissions
6. Logs show "MCP tool invoked" messages
7. Gap analysis requirements are fully met

---

## Next Steps After Implementation

1. **Monitor MCP usage** - Check Foundry logs for MCP invocations
2. **Add more MCP servers** - Connect GitHub, Jira, etc.
3. **Customize tool approvals** - Configure when users need to approve tool usage
4. **Enhance agent instructions** - Train agents to use MCP tools effectively
5. **Add audit logging** - Track which users access which MCP tools

---

## References

- [MCP Authentication - Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/mcp-authentication)
- [Azure Agent SDK Documentation](https://learn.microsoft.com/en-us/python/api/azure-ai-projects/)
- [Model Context Protocol Spec](https://spec.modelcontextprotocol.io/)
- [Azure AI Foundry Portal](https://ai.azure.com/)

---

**Estimated Implementation Time:** 4-6 hours  
**Complexity:** Medium  
**Impact:** Enables true Microsoft MCP OAuth Identity Passthrough
