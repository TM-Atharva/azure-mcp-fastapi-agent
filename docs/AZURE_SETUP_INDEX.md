# Azure Setup Guides - Complete Index

## Overview

This directory contains comprehensive step-by-step guides for setting up all Azure components required for the application.

---

## 📚 Setup Guides

### 1. Official MCP Implementation

**File:** [OFFICIAL_MCP_IMPLEMENTATION_PLAN.md](OFFICIAL_MCP_IMPLEMENTATION_PLAN.md)

Implement official Microsoft MCP (Model Context Protocol) OAuth Identity Passthrough using Azure Agent SDK.

**What you'll learn:**

- Configure MCP tools in Azure Foundry Portal
- Set up OAuth connections for external services
- Use Agent SDK instead of Chat Completions API
- Handle Foundry-managed OAuth consent flow

**Estimated Time:** 4-6 hours  
**Complexity:** High  
**Prerequisites:** Azure Foundry project, understanding of OAuth

---

### 2. RAG (Retrieval-Augmented Generation) Setup

**File:** [RAG_AZURE_SETUP_GUIDE.md](RAG_AZURE_SETUP_GUIDE.md)

Set up Azure AI Search and SharePoint for knowledge base retrieval.

**What you'll learn:**

- Create and configure Azure AI Search service
- Define search indexes with schemas
- Enable semantic search
- Index documents from Azure Blob Storage
- Configure SharePoint access via Microsoft Graph
- Set up permission-based filtering

**Estimated Time:** 2-3 hours  
**Complexity:** Medium  
**Prerequisites:** Azure subscription, SharePoint access

---

### 3. RBAC (Role-Based Access Control) Setup

**File:** [RBAC_AZURE_SETUP_GUIDE.md](RBAC_AZURE_SETUP_GUIDE.md)

Configure Azure AD groups and permissions for role-based agent access.

**What you'll learn:**

- Create Azure AD Security Groups
- Configure App Registration for group claims
- Map groups to application roles
- Test role-based filtering
- Implement dynamic groups
- Monitor and audit access

**Estimated Time:** 1-2 hours  
**Complexity:** Medium  
**Prerequisites:** Azure AD admin access, Premium P1 license

---

## 🎯 Quick Start Paths

### Path 1: Essential Setup (Start Here)

For basic functionality:

1. ✅ **Already Done:** Basic Azure setup (App Registration, Foundry)
2. ➡️ **[RBAC Setup](RBAC_AZURE_SETUP_GUIDE.md)** - Configure user roles
3. ➡️ Test with different users

**Time:** 2 hours  
**Result:** Users see only agents they should access

---

### Path 2: Add Knowledge Base (RAG)

For document search capabilities:

1. ✅ Complete Path 1
2. ➡️ **[RAG Setup](RAG_AZURE_SETUP_GUIDE.md)** - Configure Azure AI Search
3. ➡️ Index your documents
4. ➡️ Test search functionality

**Time:** 4 hours total  
**Result:** Agents can search company documents

---

### Path 3: Full Official MCP (Advanced)

For official Microsoft MCP pattern:

1. ✅ Complete Path 1 and 2
2. ➡️ **[Official MCP](OFFICIAL_MCP_IMPLEMENTATION_PLAN.md)** - Migrate to Agent SDK
3. ➡️ Configure MCP tools in Foundry
4. ➡️ Test OAuth consent flow

**Time:** 8 hours total  
**Result:** Full Microsoft MCP implementation with external service access

---

## 📋 Setup Checklist

### Prerequisites

- [ ] Azure subscription with appropriate permissions
- [ ] Azure AD administrator access
- [ ] Azure Foundry project created
- [ ] App Registration configured
- [ ] Backend and frontend code deployed

### RBAC Setup

- [ ] Azure AD Security Groups created
- [ ] Users assigned to groups
- [ ] Group claims configured in token
- [ ] Backend code updated for group mapping
- [ ] Testing completed with different roles

### RAG Setup

- [ ] Azure AI Search service created
- [ ] Search index defined and populated
- [ ] Semantic search enabled
- [ ] SharePoint permissions configured
- [ ] Document indexing working
- [ ] Permission filtering tested

### Official MCP Setup (Optional)

- [ ] OAuth connections created in Foundry
- [ ] MCP tools added to agents
- [ ] Backend migrated to Agent SDK
- [ ] Frontend handles consent flow
- [ ] End-to-end testing passed

---

## 🆘 Common Issues & Solutions

### Issue: Can't find Azure AI Search in Portal

**Solution:** Search is now called "Azure AI Search" (formerly Cognitive Search). Use the search bar and type "AI Search".

### Issue: Groups not showing in token

**Solution:**

1. Configure group claims in App Registration → Token configuration
2. Grant admin consent for GroupMember.Read.All
3. User must log out and log back in

### Issue: SharePoint 401/403 errors

**Solution:**

1. Verify Microsoft Graph API permissions granted
2. Check user has SharePoint access
3. Test with Graph Explorer first

### Issue: Azure AI Search returns no results

**Solution:**

1. Check index has documents (view in portal)
2. Test with simple query: `{"search": "*"}`
3. Verify API key is correct

### Issue: MCP tools not appearing

**Solution:**

1. Verify tool is added in Foundry Portal
2. Check agent configuration includes tool
3. Ensure OAuth connection is active

---

## 🔍 Testing Strategy

### 1. Component Testing

Test each component independently:

**RBAC:**

```bash
curl http://localhost:8000/api/user-roles -H "Authorization: Bearer TOKEN"
```

**RAG:**

```bash
curl -X POST "http://localhost:8000/api/rag/search?query=test" -H "Authorization: Bearer TOKEN"
```

**MCP:**

```bash
# Test agent with MCP tool
curl -X POST "http://localhost:8000/api/chat/mcp" -H "Authorization: Bearer TOKEN" -d '{"session_id": "...", "content": "Search SharePoint for reports"}'
```

### 2. Integration Testing

Test components working together:

- User with specific role searches for documents
- Results filtered by both role and permissions
- Agent uses MCP tool with user's identity

### 3. User Acceptance Testing

- Have real users test with their accounts
- Verify they see expected agents
- Check permission filtering works
- Gather feedback on usability

---

## 📊 Architecture Overview

```
User Authentication (Azure AD)
    ↓
RBAC Check (Azure AD Groups)
    ↓
Agent Selection (Filtered by Role)
    ↓
User Request
    ↓
┌─────────────────┬──────────────────┐
│ Option A:       │ Option B:        │
│ Current (RAG)   │ Official MCP     │
├─────────────────┼──────────────────┤
│ Direct API      │ Agent SDK        │
│ Custom Search   │ MCP Tools        │
│ Manual OAuth    │ Foundry OAuth    │
└─────────────────┴──────────────────┘
    ↓
RAG Search (AI Search + SharePoint)
    ↓
Permission Filtering (User Context)
    ↓
Agent Response
```

---

## 📖 Related Documentation

### Phase 1 Documentation

- [PHASE1_IMPLEMENTATION.md](PHASE1_IMPLEMENTATION.md) - Phase 1 feature overview
- [PHASE1_QUICK_REFERENCE.md](PHASE1_QUICK_REFERENCE.md) - Quick reference guide
- [PHASE1_SUMMARY.md](PHASE1_SUMMARY.md) - Executive summary

### MCP Documentation

- [MCP_INDEX.md](MCP_INDEX.md) - MCP documentation index
- [MCP_VERIFICATION_GUIDE.md](MCP_VERIFICATION_GUIDE.md) - MCP testing guide
- [MCP_FLOW_DIAGRAM.md](MCP_FLOW_DIAGRAM.md) - Visual flow diagrams

### General Documentation

- [README.md](README.md) - Main documentation
- [SETUP.md](SETUP.md) - Initial setup guide
- [PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md) - Project overview

---

## 🎓 Learning Resources

### Microsoft Documentation

- [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- [MCP Authentication](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/mcp-authentication)
- [Azure AI Search](https://learn.microsoft.com/en-us/azure/search/)
- [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/)
- [Azure AD Groups](https://learn.microsoft.com/en-us/azure/active-directory/fundamentals/how-to-manage-groups)

### Video Tutorials (Microsoft)

- Azure AI Foundry Overview
- Azure AI Search Deep Dive
- Azure AD Group Management
- OAuth 2.0 in Azure

---

## 💡 Best Practices

### Security

✅ Always validate tokens server-side  
✅ Use managed identities when possible  
✅ Implement least privilege access  
✅ Regular security audits  
✅ Monitor and log all access

### Performance

✅ Enable caching for frequent queries  
✅ Use semantic search for relevance  
✅ Implement pagination  
✅ Monitor API quotas and limits  
✅ Optimize index schema

### Maintenance

✅ Regular index rebuilds  
✅ Update group memberships quarterly  
✅ Monitor error logs daily  
✅ Test with real user accounts  
✅ Keep documentation updated

---

## 🚀 Deployment Checklist

### Development Environment

- [ ] All setup guides completed
- [ ] Local testing passed
- [ ] Documentation reviewed
- [ ] Environment variables configured

### Staging Environment

- [ ] Azure resources provisioned
- [ ] Security groups configured
- [ ] Test data indexed
- [ ] End-to-end testing
- [ ] Performance testing

### Production Environment

- [ ] Production resources configured
- [ ] Production data indexed
- [ ] Security hardening completed
- [ ] Monitoring and alerts set up
- [ ] Backup and disaster recovery plan
- [ ] User training completed

---

## 📞 Support

### For Azure Portal Issues

- [Azure Support](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade/overview)
- [Azure Community Forums](https://learn.microsoft.com/en-us/answers/products/azure)

### For Application Issues

- Check logs: Backend console output
- Review documentation in `docs/` folder
- Test with Swagger UI: http://localhost:8000/api/docs
- Check Azure AD sign-in logs

### For Setup Questions

1. Review the specific setup guide
2. Check troubleshooting section
3. Verify prerequisites are met
4. Test components independently
5. Check Azure Portal for resource status

---

## 🎯 Success Criteria

Your setup is successful when:

✅ **RBAC:**

- Different users see different agents
- Role assignment works automatically
- Group changes reflect in access

✅ **RAG:**

- Search returns relevant results
- Permission filtering works correctly
- Both AI Search and SharePoint work

✅ **MCP (if implemented):**

- MCP tools appear in agent
- OAuth consent flow works
- Foundry manages tokens
- External services accessible

---

## 📈 Next Steps After Setup

1. **Optimize Search**

   - Add more documents to index
   - Configure custom scoring profiles
   - Set up synonyms

2. **Enhance RBAC**

   - Add more granular permissions
   - Implement approval workflows
   - Create custom roles

3. **Expand MCP**

   - Connect more external services
   - Create custom MCP servers
   - Add more tools to agents

4. **Monitor and Improve**
   - Analyze usage patterns
   - Gather user feedback
   - Optimize performance
   - Update documentation

---

**Last Updated:** December 16, 2025  
**Maintained By:** Development Team  
**Version:** 1.0
