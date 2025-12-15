# Quick Setup Guide

This guide will help you get the Azure AI Chatbot application up and running quickly.

## Prerequisites Checklist

- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] Azure subscription with access to create App Registrations
- [ ] Access to Azure AI Foundry
- [ ] Supabase project (already configured)

## Step-by-Step Setup

### 1. Azure Entra ID Setup (15 minutes)

#### Create App Registration

1. Visit [Azure Portal](https://portal.azure.com)
2. Go to **Azure Active Directory** → **App registrations** → **New registration**
3. Fill in:
   - Name: `Azure AI Chatbot`
   - Supported account types: `Single tenant`
   - Redirect URI:
     - Type: `Single-page application (SPA)`
     - URI: `http://localhost:5173`
4. Click **Register**

#### Configure App

1. Go to **Authentication**
2. Enable:
   - ✅ Access tokens
   - ✅ ID tokens
3. Click **Save**

#### Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Description: `Backend API Secret`
4. Expiration: `24 months`
5. Click **Add**
6. **IMPORTANT**: Copy the secret value immediately

#### Copy Configuration Values

From the **Overview** page, copy:
- Application (client) ID
- Directory (tenant) ID

### 2. Azure AI Foundry Setup (10 minutes)

1. Visit [Azure AI Foundry](https://ai.azure.com)
2. Create or select a project
3. Go to **Settings** → **Keys and endpoints**
4. Copy:
   - Project endpoint URL
   - API key
   - Project ID

### 3. Configure Environment Variables (5 minutes)

#### Frontend Configuration

Edit `.env` file in the project root:

```env
VITE_AZURE_CLIENT_ID=<paste_client_id_here>
VITE_AZURE_TENANT_ID=<paste_tenant_id_here>
VITE_AZURE_REDIRECT_URI=http://localhost:5173
VITE_API_URL=http://localhost:8000/api
```

#### Backend Configuration

Create `backend/.env` file:

```env
# Azure Entra ID
AZURE_CLIENT_ID=<paste_client_id_here>
AZURE_TENANT_ID=<paste_tenant_id_here>
AZURE_CLIENT_SECRET=<paste_client_secret_here>

# Azure Foundry
AZURE_FOUNDRY_ENDPOINT=<paste_foundry_endpoint_here>
AZURE_FOUNDRY_API_KEY=<paste_foundry_api_key_here>
AZURE_FOUNDRY_PROJECT_ID=<paste_project_id_here>

# Supabase (get service role key from Supabase dashboard)
SUPABASE_URL=https://ifxjccehmmukumnftbbl.supabase.co
SUPABASE_SERVICE_KEY=<get_from_supabase_dashboard>

# Settings
MCP_ENABLED=true
CORS_ORIGINS=http://localhost:5173
DEBUG=false
```

**To get Supabase Service Role Key**:
1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **API**
4. Copy the `service_role` key (NOT the anon key)

### 4. Install Dependencies (5 minutes)

#### Frontend

```bash
npm install
```

#### Backend

```bash
cd backend
pip install -r requirements.txt
```

### 5. Start the Application (2 minutes)

#### Start Backend (Terminal 1)

```bash
cd backend
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Start Frontend (Terminal 2)

```bash
npm run dev
```

You should see:
```
VITE v5.4.8  ready in XXX ms

➜  Local:   http://localhost:5173/
```

### 6. Test the Application

1. Open browser to `http://localhost:5173`
2. You should see the login page
3. Click "Sign in with Microsoft"
4. Complete Azure AD authentication
5. You should see the agent selection page

If agents don't appear, make sure:
- Azure Foundry credentials are correct
- You have agents published in Azure Foundry
- Backend is running without errors

## Verification Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Can access login page
- [ ] Azure login popup appears
- [ ] After login, redirects to agent selection
- [ ] Agents load from Azure Foundry
- [ ] Can create chat session
- [ ] Can send and receive messages

## Common Issues

### "Invalid redirect URI"
**Fix**: Make sure `http://localhost:5173` is exactly configured in Azure AD App Registration

### "Failed to load agents"
**Fix**: Check Azure Foundry credentials in `backend/.env`

### "Token validation failed"
**Fix**: Verify Client ID and Tenant ID match between frontend and backend

### Backend won't start
**Fix**: Ensure Python dependencies are installed: `pip install -r requirements.txt`

### Frontend shows blank page
**Fix**: Check browser console for errors. Ensure `.env` variables are set correctly

## Next Steps

1. Read the full [README.md](./README.md) for detailed documentation
2. Check [backend/README.md](./backend/README.md) for API documentation
3. Configure additional agents in Azure Foundry
4. Customize the UI to match your branding
5. Set up production deployment

## Getting Help

If you encounter issues:

1. Check the console output for error messages
2. Verify all environment variables are set correctly
3. Ensure all prerequisites are installed
4. Review the detailed documentation in README.md
5. Check that Supabase database tables are created (they should be)

## Quick Reference

### Important URLs

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/api/health

### Environment Files

- Frontend: `.env` (in project root)
- Backend: `backend/.env`

### Commands

```bash
# Frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run typecheck    # Check TypeScript

# Backend
cd backend
python main.py       # Start server
```

## Success!

If you can log in and see the agent selection page, you're all set!

Enjoy building with Azure AI!
