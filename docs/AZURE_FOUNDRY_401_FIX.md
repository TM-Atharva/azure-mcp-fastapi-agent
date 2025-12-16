# Azure Foundry 401 Unauthorized Error - Diagnostic Guide

## Error

```json
{
  "detail": "Failed to fetch agents: Failed to fetch agents from Azure Foundry: Client error '401 Unauthorized' for url 'https://poc-wdf-resource.services.ai.azure.com/api/projects/poc-wdf-azure-ai/agents'"
}
```

## Root Cause

The 401 Unauthorized error means **authentication with Azure Foundry is failing**. This is NOT the event loop blocking issue - it's a credential/configuration issue.

## Diagnostic Checklist

### 1. Check Backend Environment Variables

Run in `backend/` directory:

```bash
# On Windows PowerShell
type .env
```

You MUST have these variables set:

```env
AZURE_FOUNDRY_ENDPOINT=https://poc-wdf-resource.services.ai.azure.com
AZURE_FOUNDRY_API_KEY=<your-actual-api-key>
AZURE_FOUNDRY_PROJECT_ID=poc-wdf-azure-ai
```

**❓ Is your API Key valid?** The API key might have:

- Expired
- Wrong permissions
- Been regenerated
- Incorrect format

### 2. Verify API Key Access

Test the API directly from PowerShell:

```powershell
$apiKey = "your-actual-api-key"
$endpoint = "https://poc-wdf-resource.services.ai.azure.com"
$projectId = "poc-wdf-azure-ai"

$response = Invoke-WebRequest -Uri "$endpoint/api/projects/$projectId/agents" `
  -Headers @{"api-key" = $apiKey; "Content-Type" = "application/json"} `
  -ErrorAction SilentlyContinue

Write-Host "Status: $($response.StatusCode)"
Write-Host "Body: $($response.Content)"
```

**Expected**: Status 200 with agent list
**If 401**: API key is invalid or expired

### 3. Check Azure Credentials

If API key fails, the backend falls back to Azure credential authentication. Make sure you have one of:

**Option A: Azure CLI**

```bash
az login  # Interactive login
az account show  # Verify logged in
```

**Option B: Managed Identity** (Azure App Service)

- Only works when deployed to Azure
- Requires proper role assignment

**Option C: Service Principal**

```bash
# Set environment variables
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
AZURE_TENANT_ID=<your-tenant-id>
```

### 4. Check Azure Foundry Configuration

Verify in Azure Portal:

- [ ] Azure AI Foundry resource exists
- [ ] Project "poc-wdf-azure-ai" exists
- [ ] API key has appropriate permissions
- [ ] API key scope includes agent operations
- [ ] Resource region matches endpoint

### 5. Enable Debug Logging

Restart backend with DEBUG enabled:

```env
DEBUG=true
```

This will show:

- Headers being sent
- Token generation attempts
- Each authentication method tried
- Detailed error messages

Look in console output for:

```
Fetching agents from: https://poc-wdf-resource.services.ai.azure.com/api/projects/poc-wdf-azure-ai/agents
Request headers: {...}
Response status: 401
API key authentication failed (401), attempting Azure credential authentication...
Attempting to get bearer token for scope: https://ai.azure.com/.default
```

### 6. Common Issues & Solutions

#### Issue: API Key is empty

**Solution**:

1. Go to Azure Portal
2. Find your AI Foundry resource
3. Navigate to Keys and Endpoints
4. Copy the API key
5. Add to `backend/.env`:

```env
AZURE_FOUNDRY_API_KEY=<paste-key-here>
```

#### Issue: API Key expired

**Solution**: Regenerate in Azure Portal

- Keys and Endpoints → Regenerate

#### Issue: Wrong endpoint or project ID

**Solution**: Verify in Azure Portal

```
Resource: poc-wdf-resource
Project ID should be: poc-wdf-azure-ai
Endpoint: https://poc-wdf-resource.services.ai.azure.com
```

#### Issue: Missing Azure CLI or credentials

**Solution**: Install Azure CLI

```bash
# Windows - use Chocolatey or direct install
choco install azure-cli

# Or download from: https://aka.ms/installazurecliwindows

# Then login
az login
```

#### Issue: Credentials have no permissions

**Solution**: Ensure your account/principal has role:

- "AI Project Member" or "Contributor" role on the resource

### 7. Test the Fix

After fixing credentials:

1. **Restart backend**:

```bash
cd backend
python main.py
```

2. **Try `/api/agents` endpoint**:

```bash
# Get token first (if using Azure AD)
# Then call:
curl -H "Authorization: Bearer <your-token>" \
  http://localhost:8000/api/agents
```

3. **Check console logs** for:

```
Fetching agents from: https://...
Response status: 200
Agents synchronized successfully
```

## What This Fix Includes

Updated `backend/azure_foundry.py` to:

1. Log detailed authentication attempts
2. Try multiple Azure credential token scopes:
   - `https://ai.azure.com/.default` (for Azure AI)
   - `https://cognitiveservices.azure.com/.default` (for Cognitive Services)
   - `https://management.azure.com/.default` (fallback)
3. Continue trying other scopes if one fails
4. Better error logging for debugging

## Summary

The 401 error is almost always one of:

1. **Missing API Key** - Set `AZURE_FOUNDRY_API_KEY` env var
2. **Invalid API Key** - Regenerate in Azure Portal
3. **Wrong Endpoint/Project** - Verify configuration
4. **Missing Azure Credentials** - Run `az login` or set service principal vars

**Next Steps:**

1. Check your `backend/.env` file
2. Verify API key in Azure Portal
3. Run the PowerShell test above
4. Check debug logs
5. Verify Azure credentials are set

Once credentials are correct, `/api/agents` will respond successfully! 🎯
