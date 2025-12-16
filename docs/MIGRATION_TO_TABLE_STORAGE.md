# Migration to Azure Table Storage

This document explains the changes made to migrate from Supabase to Azure Table Storage.

## What Changed

### Database Layer
**Before:** Supabase PostgreSQL with Row Level Security
**After:** Azure Table Storage with application-level security

### Key Benefits
- **Fully Azure Native**: All services now in Azure ecosystem
- **Simpler Setup**: No external database service needed
- **Better Integration**: Native Azure SDK support
- **Cost Effective**: Pay only for what you use
- **Auto-scaling**: No capacity planning needed

## Architecture Changes

### Data Storage

#### Tables in Azure Table Storage

1. **users**
   - PartitionKey: `azure_id` (user's Azure AD ID)
   - RowKey: `azure_id`
   - Stores: User profile from Azure Entra ID
   - Created: On first login

2. **agents**
   - PartitionKey: `"agents"` (all agents in one partition)
   - RowKey: `azure_agent_id`
   - Stores: AI agents from Azure Foundry
   - Synced: On agent list request

3. **sessions**
   - PartitionKey: `user_azure_id` (efficient user queries)
   - RowKey: `session_id` (UUID)
   - Stores: Chat sessions
   - Created: When user starts new chat

4. **messages**
   - PartitionKey: `session_id` (efficient session queries)
   - RowKey: `timestamp_messageid` (for ordering)
   - Stores: Chat messages
   - Created: On each message send/receive

### OAuth Identity Passthrough (MCP) with Table Storage

The MCP implementation remains the same but now works with Azure Table Storage:

1. **User Authentication**
   ```
   User → Azure AD → Access Token
   ```

2. **Token Validation & User Lookup**
   ```
   Frontend → Backend (with token)
   Backend validates token → Extracts azure_id
   Backend → Table Storage → Gets/Creates user
   ```

3. **MCP Context Creation**
   ```python
   mcp_context = {
       "oauth_token": original_user_token,
       "user_identity": {
           "azure_id": user.azure_id,
           "email": user.email,
           "name": user.name
       },
       "mcp_enabled": True,
       "timestamp": current_time
   }
   ```

4. **Agent Call with User Context**
   ```
   Backend → Azure Foundry (with MCP context)
   Agent receives user token → Can access user resources
   Agent response → Backend → Saves to Table Storage
   ```

5. **Data Persistence**
   ```
   Message saved → Table Storage (with user's azure_id)
   History retrieved → Filtered by user's azure_id
   Complete audit trail → All actions tied to user
   ```

## Code Changes

### New Files

1. **backend/table_storage.py**
   - Complete Azure Table Storage client
   - CRUD operations for all entities
   - Automatic table creation
   - Entity serialization/deserialization

### Modified Files

1. **backend/requirements.txt**
   - Added: `azure-data-tables==12.5.0`
   - Added: `azure-core==1.30.0`
   - Removed: `supabase==2.9.1`

2. **backend/config.py**
   - Added: Azure Storage connection settings
   - Removed: Supabase URL and key settings

3. **backend/auth.py**
   - Changed: `self.supabase` → `table_storage`
   - Updated: `get_or_create_user()` to use Table Storage
   - MCP: No changes - still creates same context

4. **backend/azure_foundry.py**
   - Changed: Agent sync to use Table Storage
   - Updated: `_sync_agent_to_db()` method
   - MCP: No changes - context passing unchanged

5. **backend/main.py**
   - Removed: Supabase client initialization
   - Added: `table_storage` import
   - Updated: All endpoints to use Table Storage
   - MCP: OAuth Identity Passthrough still maintained

6. **backend/.env.example**
   - Removed: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
   - Added: `AZURE_STORAGE_CONNECTION_STRING`

7. **Frontend .env**
   - Removed: Supabase configuration variables
   - No changes to MCP flow

### Deleted Files

- `/supabase/migrations/*` - No longer needed
- Supabase configuration and migration files

## OAuth Identity Passthrough (MCP) Flow

The MCP flow remains **exactly the same** from the user and agent perspective:

### 1. Authentication Flow
```
User logs in with Azure AD
↓
Frontend receives access token
↓
Frontend includes token in all API calls
```

### 2. Backend Token Processing
```
Backend receives request with token
↓
Validates token with Azure AD JWKS
↓
Extracts user identity (azure_id, email, name)
↓
Gets/Creates user in Table Storage
↓
Creates MCP context with token + identity
```

### 3. Agent Communication
```
Backend calls Azure Foundry agent
↓
Includes MCP context in request
↓
Agent receives:
  - User's original Azure AD token
  - User identity information
  - Timestamp
↓
Agent can access user-specific resources
↓
Agent response returned
```

### 4. Data Persistence
```
User message → Saved to Table Storage
Agent response → Saved to Table Storage
Both linked to user via azure_id
Complete conversation history maintained
```

### Key MCP Features Preserved

✅ **User Identity Maintained**: User's Azure AD token passed to agents
✅ **Authorization**: Agents use user's permissions
✅ **Audit Trail**: All actions logged with user identity
✅ **Security**: Token validated at every step
✅ **Compliance**: User context never lost

## Migration Steps (For Existing Deployments)

If migrating an existing deployment:

### 1. Backup Existing Data
```bash
# Export from Supabase (if needed)
# Tables: users, agents, sessions, messages
```

### 2. Create Azure Storage Account
```bash
# See AZURE_STORAGE_SETUP.md
```

### 3. Update Backend Code
```bash
cd backend
pip install -r requirements.txt
```

### 4. Update Configuration
```env
# Remove from backend/.env:
# SUPABASE_URL
# SUPABASE_SERVICE_KEY

# Add to backend/.env:
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
```

### 5. (Optional) Import Data
```python
# If you need to import existing data
# Write a migration script using table_storage.py methods
```

### 6. Start Application
```bash
cd backend
python main.py
```

Tables are created automatically on first run.

## Testing the Migration

### 1. Backend Health Check
```bash
curl http://localhost:8000/api/health
```

Should show: `"azure_table_storage": "operational"`

### 2. Authentication Test
1. Log in with Azure AD
2. User should be created in `users` table

### 3. Agent Test
1. View agents list
2. Agents should be synced to `agents` table

### 4. Chat Test
1. Create new chat session
2. Send message
3. Check `sessions` and `messages` tables

### 5. History Test
1. Refresh page
2. Previous chat should load
3. History retrieved from Table Storage

## Differences from Supabase

| Feature | Supabase | Azure Table Storage |
|---------|----------|-------------------|
| Database Type | PostgreSQL (SQL) | NoSQL (Key-Value) |
| Security | Row Level Security (RLS) | Application-level |
| Schema | Rigid tables with migrations | Flexible entities |
| Queries | SQL queries | Partition/Row key lookups |
| Relationships | Foreign keys | Application-managed |
| Auto-increment IDs | Yes | No (use UUIDs) |
| Setup | Manual schema creation | Automatic table creation |
| Ecosystem | Standalone service | Native Azure |

## Performance Considerations

### Table Storage Advantages
- **Faster Writes**: No transaction overhead
- **Partition Keys**: Efficient data distribution
- **Scalability**: Automatic scaling to petabytes
- **Cost**: Only pay for storage used

### Query Patterns
Table Storage is optimized for:
- ✅ Get entity by Partition + Row key (fast)
- ✅ Query all entities in a partition (fast)
- ✅ Get user's sessions (user_azure_id partition)
- ✅ Get session messages (session_id partition)

Not optimized for:
- ❌ Complex joins across tables
- ❌ Full table scans
- ❌ Complex WHERE clauses

Our application uses optimal query patterns!

## Troubleshooting

### "Table not found"
- Tables are created automatically
- Check backend logs for creation errors
- Verify connection string is correct

### "Unauthorized"
- Check storage account access keys
- Verify connection string is complete
- Ensure no firewall blocking access

### "Data not showing"
- Check partition key matches user's azure_id
- Verify session IDs are correct UUIDs
- Look at raw table data in Azure Portal

## Rollback Plan

If needed to rollback to Supabase:

1. Keep Supabase project active during migration
2. Don't delete old code immediately
3. Use git to revert to previous version
4. Restore environment variables
5. Reinstall Supabase dependencies

## Conclusion

The migration to Azure Table Storage simplifies the architecture while maintaining all OAuth Identity Passthrough (MCP) functionality. The application is now fully Azure-native, easier to deploy, and more cost-effective.

**MCP Benefits Retained:**
- User identity passed to agents
- Secure authorization throughout
- Complete audit trail
- Compliance maintained

**Additional Benefits:**
- Simpler setup and deployment
- Better Azure ecosystem integration
- Auto-scaling storage
- Cost-effective pricing

The OAuth Identity Passthrough (MCP) pattern works seamlessly with Azure Table Storage, providing the same security and functionality as before.
