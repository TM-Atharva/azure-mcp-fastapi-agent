# Azure Table Storage Setup Guide

This guide will help you set up Azure Table Storage for the chatbot application.

## Create Azure Storage Account

### Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → Search for **Storage account**
3. Click **Create**

### Configure Storage Account

Fill in the details:

**Basics Tab:**
- **Subscription**: Select your subscription
- **Resource group**: Create new or use existing
- **Storage account name**: Choose a unique name (lowercase, no spaces)
- **Region**: Choose a region close to you
- **Performance**: Standard
- **Redundancy**: Locally-redundant storage (LRS) is fine for development

**Advanced Tab:**
- Keep defaults

**Networking Tab:**
- **Network access**: Public endpoint (all networks)

**Data protection Tab:**
- Keep defaults

**Review + create:**
- Click **Create** and wait for deployment

## Get Connection String

After deployment:

1. Go to your Storage account
2. Click **Access keys** in the left menu
3. Under **key1**, click **Show** next to Connection string
4. Click **Copy** to copy the entire connection string

The connection string looks like:
```
DefaultEndpointsProtocol=https;AccountName=youraccount;AccountKey=yourkey==;EndpointSuffix=core.windows.net
```

## Configure Backend

1. Open `backend/.env` file
2. Add your connection string:

```env
AZURE_STORAGE_CONNECTION_STRING=<paste_your_connection_string_here>
```

That's it! The application will automatically create the required tables when it starts.

## Tables Created Automatically

The application creates these tables automatically:

- **users**: User profiles from Azure Entra ID
- **agents**: AI agents from Azure Foundry
- **sessions**: Chat sessions
- **messages**: Chat messages

No manual setup required!

## Viewing Data (Optional)

To view your data in Azure Portal:

1. Go to your Storage account
2. Click **Storage browser** in the left menu
3. Expand **Tables**
4. Click on any table to view data

## Alternative: Use Storage Explorer

Download [Azure Storage Explorer](https://azure.microsoft.com/features/storage-explorer/) for a better experience viewing and managing table data.

## Cost

Azure Table Storage is very affordable:
- **Storage**: $0.045 per GB per month
- **Transactions**: $0.00036 per 10,000 transactions

For a small chatbot application, monthly costs are typically under $1.

## Troubleshooting

### "Connection string not configured"
- Make sure you copied the entire connection string
- Check that there are no extra spaces or line breaks
- Verify the variable name is exactly `AZURE_STORAGE_CONNECTION_STRING`

### "Tables not created"
- The tables are created automatically on first use
- Check backend logs for any errors
- Ensure your storage account is accessible

### "Access denied"
- Verify your connection string is correct
- Check that your storage account allows public access
- Ensure the account key hasn't been regenerated

## Production Considerations

For production deployments:

1. **Redundancy**: Consider upgrading to GRS (Geo-redundant storage)
2. **Network**: Restrict access using firewall rules or private endpoints
3. **Backup**: Enable soft delete for tables
4. **Monitoring**: Set up alerts for storage metrics
5. **Security**: Rotate access keys regularly

## Next Steps

Once Azure Table Storage is configured:

1. Start the backend server: `cd backend && python main.py`
2. The application will automatically create tables
3. Start using the chatbot!

Your chat history will be persisted in Azure Table Storage with OAuth Identity Passthrough (MCP) maintaining user context throughout.
