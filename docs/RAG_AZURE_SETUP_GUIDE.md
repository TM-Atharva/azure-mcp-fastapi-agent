# RAG (Retrieval-Augmented Generation) - Azure Setup Guide

## Overview

This guide provides step-by-step instructions to set up RAG capabilities using **Azure AI Search** and **SharePoint** in your Azure environment.

---

## Table of Contents

1. [Azure AI Search Setup](#azure-ai-search-setup)
2. [SharePoint Configuration](#sharepoint-configuration)
3. [Document Indexing](#document-indexing)
4. [Testing RAG](#testing-rag)

---

## Azure AI Search Setup

### Prerequisites

- Azure subscription with appropriate permissions
- Resource group for your AI resources
- Sample documents to index

### Step 1: Create Azure AI Search Service

#### 1.1 Navigate to Azure Portal

1. Go to [Azure Portal](https://portal.azure.com/)
2. Sign in with your credentials
3. Click **"+ Create a resource"**

#### 1.2 Create Search Service

1. Search for **"Azure AI Search"** (formerly "Cognitive Search")
2. Click **"Create"**
3. Fill in the details:

   ```
   Subscription: [Your subscription]
   Resource Group: [Your resource group or create new]
   Service Name: your-search-service
   Location: [Same as your other resources, e.g., East US]
   Pricing Tier: Basic (or higher for production)
   ```

4. Click **"Review + Create"**
5. Click **"Create"**
6. Wait for deployment (takes 2-3 minutes)

#### 1.3 Get API Keys

1. Go to your Search Service in Azure Portal
2. Click **"Keys"** (left menu under Settings)
3. Copy the following:

   - **Primary admin key** - Save this as `AZURE_AI_SEARCH_KEY`
   - **URL** - Save this as `AZURE_AI_SEARCH_ENDPOINT`

   Example:

   ```
   AZURE_AI_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
   AZURE_AI_SEARCH_KEY=1234567890ABCDEF...
   ```

### Step 2: Create Search Index

#### 2.1 Navigate to Search Explorer

1. In your Search Service, click **"Search explorer"** (top menu)
2. Click **"Index"** → **"+ Add index"**

#### 2.2 Define Index Schema

**Option A: Using Portal (Visual)**

1. Click **"Add index"**
2. Enter index name: `documents`
3. Add fields:

| Field Name    | Type               | Attributes                         |
| ------------- | ------------------ | ---------------------------------- |
| `id`          | String             | Key, Retrievable                   |
| `content`     | String             | Searchable, Retrievable            |
| `title`       | String             | Searchable, Retrievable, Facetable |
| `url`         | String             | Retrievable                        |
| `permissions` | Collection(String) | Filterable, Retrievable            |
| `created`     | DateTimeOffset     | Filterable, Sortable, Retrievable  |
| `modified`    | DateTimeOffset     | Filterable, Sortable, Retrievable  |
| `author`      | String             | Facetable, Filterable, Retrievable |
| `category`    | String             | Facetable, Filterable, Retrievable |

4. Click **"Create"**

**Option B: Using REST API (Recommended)**

1. Use the following JSON to create index:

```json
{
  "name": "documents",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true,
      "searchable": false,
      "filterable": false,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "content",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "title",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "sortable": true,
      "facetable": true
    },
    {
      "name": "url",
      "type": "Edm.String",
      "searchable": false,
      "filterable": false,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "permissions",
      "type": "Collection(Edm.String)",
      "searchable": false,
      "filterable": true,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "created",
      "type": "Edm.DateTimeOffset",
      "searchable": false,
      "filterable": true,
      "sortable": true,
      "facetable": false
    },
    {
      "name": "modified",
      "type": "Edm.DateTimeOffset",
      "searchable": false,
      "filterable": true,
      "sortable": true,
      "facetable": false
    },
    {
      "name": "author",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "sortable": false,
      "facetable": true
    },
    {
      "name": "category",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "sortable": false,
      "facetable": true
    }
  ],
  "semantic": {
    "configurations": [
      {
        "name": "default",
        "prioritizedFields": {
          "titleField": {
            "fieldName": "title"
          },
          "contentFields": [
            {
              "fieldName": "content"
            }
          ]
        }
      }
    ]
  }
}
```

2. Send POST request:

```bash
curl -X POST \
  "https://your-search-service.search.windows.net/indexes?api-version=2023-11-01" \
  -H "Content-Type: application/json" \
  -H "api-key: YOUR_ADMIN_KEY" \
  -d @index-definition.json
```

### Step 3: Configure Semantic Search (Optional but Recommended)

#### 3.1 Enable Semantic Search

1. In Azure Portal, go to your Search Service
2. Click **"Semantic ranker"** (left menu)
3. Click **"Enable semantic ranker"**
4. Select pricing tier: **Free** (50 queries/month) or **Standard**
5. Click **"Save"**

#### 3.2 Configure Semantic Configuration

Already included in index definition above with `semantic.configurations`.

### Step 4: Set Up Document Indexing

#### 4.1 Option A: Manual Upload (For Testing)

Create a Python script to upload sample documents:

```python
# scripts/index_documents.py
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from datetime import datetime

endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
key = os.getenv("AZURE_AI_SEARCH_KEY")
index_name = "documents"

client = SearchClient(
    endpoint=endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(key)
)

# Sample documents
documents = [
    {
        "id": "doc1",
        "content": "Q4 2024 financial report shows 20% revenue growth...",
        "title": "Q4 2024 Financial Report",
        "url": "https://sharepoint.com/reports/q4-2024.pdf",
        "permissions": ["user@company.com", "analyst@company.com", "everyone"],
        "created": datetime(2024, 12, 1).isoformat(),
        "modified": datetime(2024, 12, 15).isoformat(),
        "author": "Finance Team",
        "category": "Financial Reports"
    },
    {
        "id": "doc2",
        "content": "Product roadmap for 2025 includes AI features...",
        "title": "2025 Product Roadmap",
        "url": "https://sharepoint.com/roadmap/2025.pdf",
        "permissions": ["admin@company.com", "pm@company.com"],
        "created": datetime(2024, 11, 15).isoformat(),
        "modified": datetime(2024, 12, 10).isoformat(),
        "author": "Product Team",
        "category": "Product Planning"
    },
    {
        "id": "doc3",
        "content": "Employee handbook covers policies, benefits, and procedures...",
        "title": "Employee Handbook 2025",
        "url": "https://sharepoint.com/hr/handbook.pdf",
        "permissions": ["everyone"],
        "created": datetime(2024, 12, 1).isoformat(),
        "modified": datetime(2024, 12, 1).isoformat(),
        "author": "HR Team",
        "category": "Human Resources"
    }
]

# Upload documents
result = client.upload_documents(documents=documents)
print(f"Uploaded {len(result)} documents")
for r in result:
    print(f"  - {r.key}: {'Success' if r.succeeded else 'Failed'}")
```

Run the script:

```bash
python scripts/index_documents.py
```

#### 4.2 Option B: Azure Blob Storage Indexer (For Production)

1. **Create Azure Blob Storage**

   - In Azure Portal, create a Storage Account
   - Create a container named `documents`
   - Upload your PDF, Word, Excel files

2. **Create Data Source**

   In Azure Portal → Your Search Service → Data sources:

   ```
   Name: blob-datasource
   Type: Azure Blob Storage
   Connection string: [Your storage account connection string]
   Container name: documents
   ```

3. **Create Indexer**

   In Azure Portal → Your Search Service → Indexers:

   ```
   Name: blob-indexer
   Data source: blob-datasource
   Target index: documents
   Schedule: Daily (or as needed)
   ```

4. **Configure AI Enrichment (Optional)**

   Enable AI skills for:

   - OCR (extract text from images)
   - Key phrase extraction
   - Entity recognition
   - Language detection

### Step 5: Test Search Index

#### 5.1 Using Search Explorer (Portal)

1. In Azure Portal, go to your Search Service
2. Click **"Search explorer"**
3. Select index: `documents`
4. Try a search query:
   ```json
   {
     "search": "financial report",
     "filter": "permissions/any(p: p eq 'everyone')",
     "top": 5
   }
   ```

#### 5.2 Using REST API

```bash
curl -X POST \
  "https://your-search-service.search.windows.net/indexes/documents/docs/search?api-version=2023-11-01" \
  -H "Content-Type: application/json" \
  -H "api-key: YOUR_API_KEY" \
  -d '{
    "search": "financial report",
    "filter": "permissions/any(p: p eq '\''user@company.com'\'' or p eq '\''everyone'\'')",
    "top": 5,
    "queryType": "semantic",
    "semanticConfiguration": "default"
  }'
```

#### 5.3 Using Python SDK

```python
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

client = SearchClient(
    endpoint="https://your-search-service.search.windows.net",
    index_name="documents",
    credential=AzureKeyCredential("YOUR_API_KEY")
)

results = client.search(
    search_text="financial report",
    filter="permissions/any(p: p eq 'user@company.com' or p eq 'everyone')",
    top=5
)

for result in results:
    print(f"Title: {result['title']}")
    print(f"Content: {result['content'][:100]}...")
    print(f"Score: {result['@search.score']}")
    print("---")
```

---

## SharePoint Configuration

### Prerequisites

- Microsoft 365 subscription with SharePoint
- Azure AD admin access
- SharePoint site with documents

### Step 1: Create SharePoint Site (If Needed)

#### 1.1 Access SharePoint Admin Center

1. Go to [SharePoint Admin Center](https://admin.microsoft.com/sharepoint)
2. Sign in as admin

#### 1.2 Create Site

1. Click **"Active sites"**
2. Click **"+ Create"**
3. Choose **"Team site"** or **"Communication site"**
4. Fill in details:
   ```
   Site name: Knowledge Base
   Site address: /sites/knowledge
   Primary administrator: [Your email]
   Language: English
   ```
5. Click **"Finish"**

#### 1.3 Add Sample Documents

1. Navigate to your new site
2. Click **"Documents"**
3. Upload sample files (PDF, Word, Excel, PowerPoint)
4. Organize in folders if needed

### Step 2: Configure Azure AD App Permissions

#### 2.1 Navigate to Azure AD

1. Go to [Azure Portal](https://portal.azure.com/)
2. Click **"Azure Active Directory"**
3. Click **"App registrations"**
4. Select your existing app (from main setup)

#### 2.2 Add Microsoft Graph API Permissions

1. Click **"API permissions"** (left menu)
2. Click **"+ Add a permission"**
3. Select **"Microsoft Graph"**
4. Select **"Delegated permissions"**
5. Add these permissions:

   ```
   ✅ Sites.Read.All          - Read items in all site collections
   ✅ Files.Read.All          - Read all files user can access
   ✅ User.Read               - Sign in and read user profile
   ✅ offline_access          - Maintain access to data
   ```

6. Click **"Add permissions"**
7. Click **"Grant admin consent for [Your Tenant]"** (admin required)
8. Confirm by clicking **"Yes"**

#### 2.3 Configure Redirect URIs

1. Click **"Authentication"** (left menu)
2. Under **"Platform configurations"**, ensure you have:

   ```
   Platform: Single-page application
   Redirect URI: http://localhost:5173

   Platform: Web
   Redirect URI: http://localhost:8000/auth/callback
   ```

3. Under **"Implicit grant and hybrid flows"**, enable:
   - ✅ Access tokens
   - ✅ ID tokens
4. Click **"Save"**

### Step 3: Test SharePoint Access

#### 3.1 Test with Microsoft Graph Explorer

1. Go to [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
2. Sign in with your account
3. Try this query:
   ```
   GET https://graph.microsoft.com/v1.0/sites/root/sites
   ```
4. Should see list of SharePoint sites

#### 3.2 Test Search

Try searching SharePoint:

```
POST https://graph.microsoft.com/v1.0/search/query
Content-Type: application/json

{
  "requests": [
    {
      "entityTypes": ["driveItem"],
      "query": {
        "queryString": "financial report"
      },
      "from": 0,
      "size": 25
    }
  ]
}
```

### Step 4: Configure Permissions on Documents

#### 4.1 Set Item-Level Permissions (Optional)

For sensitive documents:

1. In SharePoint, go to your document
2. Click **"..."** → **"Manage access"**
3. Click **"Advanced"**
4. Remove inherited permissions if needed
5. Add specific users/groups:
   ```
   User/Group: Finance Team
   Permission: Read
   ```

#### 4.2 Test Permission Enforcement

1. Log in as different users
2. Try to access documents
3. Verify users only see what they should

---

## Document Indexing

### Option 1: Real-Time SharePoint Indexing

#### Using Microsoft Graph API

Your application searches SharePoint in real-time (current implementation):

**Pros:**

- Always up-to-date
- No indexing delay
- Respects SharePoint permissions automatically

**Cons:**

- Slower than pre-indexed search
- Requires active SharePoint connection
- API rate limits

**Configuration:**

```env
SHAREPOINT_ENABLED=true
SHAREPOINT_SITE_URL=https://company.sharepoint.com/sites/knowledge
```

### Option 2: Hybrid Approach

Index SharePoint content in Azure AI Search for faster queries:

#### 2.1 Create SharePoint Data Source

In Azure AI Search:

1. Click **"Data sources"** → **"+ Add data source"**
2. Select **"SharePoint Online"**
3. Configure:
   ```
   Name: sharepoint-datasource
   SharePoint URL: https://company.sharepoint.com/sites/knowledge
   Authentication: Managed Identity (recommended) or OAuth
   ```

#### 2.2 Create SharePoint Indexer

1. Click **"Indexers"** → **"+ Add indexer"**
2. Configure:

   ```
   Name: sharepoint-indexer
   Data source: sharepoint-datasource
   Target index: documents
   Schedule: Every 1 hour
   ```

3. Field mappings:
   ```
   SharePoint Field → Index Field
   - Title → title
   - Body → content
   - Created → created
   - Modified → modified
   - Author → author
   - FileType → category
   ```

---

## Testing RAG

### Step 1: Update Environment Variables

Add to your `.env`:

```env
# Azure AI Search
AZURE_AI_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_AI_SEARCH_KEY=your_api_key_here
AZURE_AI_SEARCH_INDEX=documents

# SharePoint
SHAREPOINT_ENABLED=true
SHAREPOINT_SITE_URL=https://company.sharepoint.com/sites/knowledge
```

### Step 2: Test Azure AI Search

```bash
# Test RAG config
curl http://localhost:8000/api/rag/config

# Test AI Search
curl -X POST "http://localhost:8000/api/rag/search?query=financial%20report&sources=ai_search&top=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected response:

```json
{
  "query": "financial report",
  "timestamp": "2024-12-16T...",
  "sources": {
    "ai_search": {
      "count": 3,
      "documents": [
        {
          "id": "doc1",
          "title": "Q4 2024 Financial Report",
          "content": "Q4 2024 financial report shows...",
          "url": "https://sharepoint.com/reports/q4-2024.pdf",
          "@search.score": 5.23
        }
      ]
    }
  }
}
```

### Step 3: Test SharePoint Search

```bash
# Test SharePoint search
curl -X POST "http://localhost:8000/api/rag/search?query=roadmap&sources=sharepoint&top=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 4: Test Permission Filtering

1. Log in as different users
2. Search for documents
3. Verify each user only sees documents they can access

```bash
# User A (should see financial docs)
curl -X POST "http://localhost:8000/api/rag/search?query=financial" \
  -H "Authorization: Bearer USER_A_TOKEN"

# User B (should NOT see financial docs if not in permissions)
curl -X POST "http://localhost:8000/api/rag/search?query=financial" \
  -H "Authorization: Bearer USER_B_TOKEN"
```

### Step 5: Test Combined Search

```bash
# Search both sources
curl -X POST "http://localhost:8000/api/rag/search?query=report&sources=ai_search,sharepoint&top=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Monitoring and Maintenance

### Azure AI Search Monitoring

1. **View Search Analytics**

   - In Azure Portal → Your Search Service
   - Click **"Monitoring"** → **"Metrics"**
   - Monitor: Search queries, latency, throttling

2. **Enable Diagnostic Logs**

   - Click **"Diagnostic settings"** → **"+ Add diagnostic setting"**
   - Enable: Search queries, indexing operations
   - Send to: Log Analytics workspace

3. **Check Index Statistics**
   - Click **"Indexes"** → Select your index
   - View: Document count, storage size

### SharePoint Monitoring

1. **Check API Usage**

   - Go to [Microsoft 365 Admin Center](https://admin.microsoft.com/)
   - Click **"Reports"** → **"Usage"**
   - Monitor Microsoft Graph API calls

2. **Review Permissions**
   - Regularly audit who has access
   - Check **"Sharing"** settings on sensitive documents

---

## Troubleshooting

### Issue: Azure AI Search returns no results

**Solutions:**

1. Check index has documents: Portal → Indexes → documents → Document count
2. Verify API key is correct
3. Test with simple query: `{"search": "*"}` (returns all)
4. Check field definitions match your data

### Issue: SharePoint 401/403 errors

**Solutions:**

1. Verify Azure AD app has required permissions
2. Check admin consent was granted
3. Ensure user's token has correct scopes
4. Test with Graph Explorer first

### Issue: Permission filtering not working

**Solutions:**

1. **Azure AI Search**: Verify `permissions` field exists and is populated
2. **SharePoint**: Microsoft Graph enforces permissions automatically
3. Check filter syntax: `permissions/any(p: p eq 'email')`

### Issue: Slow search performance

**Solutions:**

1. Enable semantic search
2. Add more search units in pricing tier
3. Consider caching frequent queries
4. Use pagination (limit `top` parameter)

---

## Best Practices

### Security

✅ **Always filter by user permissions**  
✅ **Use managed identities when possible**  
✅ **Regularly audit access logs**  
✅ **Encrypt data at rest and in transit**  
✅ **Implement rate limiting**

### Performance

✅ **Enable semantic search for better relevance**  
✅ **Use field projections (select specific fields)**  
✅ **Implement caching for common queries**  
✅ **Monitor and optimize index size**  
✅ **Use pagination for large result sets**

### Maintenance

✅ **Schedule regular index rebuilds**  
✅ **Monitor indexer success rates**  
✅ **Review and update permissions regularly**  
✅ **Clean up stale documents**  
✅ **Test with real user accounts**

---

## Success Checklist

✅ Azure AI Search service created  
✅ Search index defined with schema  
✅ Semantic search enabled  
✅ Sample documents indexed  
✅ Search returns results  
✅ Permission filtering works  
✅ SharePoint permissions configured  
✅ Azure AD app has Graph API permissions  
✅ SharePoint search returns results  
✅ Users see only authorized documents  
✅ Environment variables configured  
✅ Backend RAG endpoints work  
✅ End-to-end testing passed

---

## Next Steps

1. **Index Production Documents**

   - Set up Azure Blob Storage or SharePoint indexer
   - Configure automatic indexing schedule

2. **Enhance Search**

   - Add custom scoring profiles
   - Configure synonyms
   - Enable autocomplete/suggestions

3. **Monitor Usage**

   - Set up alerts for errors
   - Track search analytics
   - Optimize based on user queries

4. **Integrate with Agents**
   - Configure agents to use RAG search
   - Add RAG results to agent context
   - Test agent responses with RAG data

---

**Estimated Setup Time:** 2-3 hours  
**Complexity:** Medium  
**Prerequisites:** Azure subscription, SharePoint access
