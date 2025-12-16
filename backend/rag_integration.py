"""
RAG Integration with Azure AI Search and SharePoint

This module implements RAG (Retrieval-Augmented Generation) capabilities
using Azure AI Search and SharePoint as knowledge sources.

Features:
- Azure AI Search integration for document retrieval
- SharePoint MCP server connector
- OAuth consent flow for SharePoint access
- Knowledge base querying with user permissions
"""

from typing import List, Dict, Any, Optional
import logging
import httpx
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)


class AzureAISearchClient:
    """
    Client for Azure AI Search RAG integration.
    
    This client handles document retrieval from Azure AI Search indexes
    with user context for permission-aware searches.
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None,
        index_name: str = "documents"
    ):
        """
        Initialize Azure AI Search client.
        
        Args:
            endpoint: Azure AI Search service endpoint
            api_key: API key for authentication (or use DefaultAzureCredential)
            index_name: Name of the search index
        """
        self.endpoint = endpoint.rstrip('/')
        self.index_name = index_name
        
        # Use API key if provided, otherwise use DefaultAzureCredential
        if api_key:
            self.credential = AzureKeyCredential(api_key)
            logger.info("Azure AI Search client initialized with API key")
        else:
            self.credential = DefaultAzureCredential()
            logger.info("Azure AI Search client initialized with DefaultAzureCredential")
        
        self.search_url = f"{self.endpoint}/indexes/{self.index_name}/docs/search"
        logger.info(f"Azure AI Search URL: {self.search_url}")
    
    async def search(
        self,
        query: str,
        top: int = 5,
        user_email: Optional[str] = None,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents in Azure AI Search.
        
        Args:
            query: Search query text
            top: Number of results to return
            user_email: User's email for permission filtering
            filters: OData filter expression
        
        Returns:
            List of search results with relevance scores
        """
        try:
            search_request = {
                "search": query,
                "top": top,
                "select": "id,content,title,url,metadata",
                "queryType": "semantic",
                "semanticConfiguration": "default",
                "captions": "extractive",
                "answers": "extractive|count-3"
            }
            
            # Add user-based filtering if provided
            if user_email and filters:
                search_request["filter"] = filters
            elif user_email:
                # Default filter: only show documents accessible to user
                search_request["filter"] = f"permissions/any(p: p eq '{user_email}' or p eq 'everyone')"
            
            headers = {
                "Content-Type": "application/json",
                "api-key": self.credential.key if isinstance(self.credential, AzureKeyCredential) else ""
            }
            
            # If using DefaultAzureCredential, get token
            if not isinstance(self.credential, AzureKeyCredential):
                token = await self.credential.get_token("https://search.azure.com/.default")
                headers["Authorization"] = f"Bearer {token.token}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.search_url}?api-version=2023-11-01",
                    json=search_request,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                documents = result.get("value", [])
                
                logger.info(f"Azure AI Search returned {len(documents)} results for query: {query}")
                return documents
        
        except Exception as e:
            logger.error(f"Azure AI Search error: {str(e)}")
            raise
    
    async def get_document(
        self,
        document_id: str,
        user_email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID.
        
        Args:
            document_id: Document identifier
            user_email: User's email for permission check
        
        Returns:
            Document data or None if not found/accessible
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "api-key": self.credential.key if isinstance(self.credential, AzureKeyCredential) else ""
            }
            
            if not isinstance(self.credential, AzureKeyCredential):
                token = await self.credential.get_token("https://search.azure.com/.default")
                headers["Authorization"] = f"Bearer {token.token}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoint}/indexes/{self.index_name}/docs('{document_id}')?api-version=2023-11-01",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 404:
                    return None
                
                response.raise_for_status()
                document = response.json()
                
                # Check user permissions
                if user_email:
                    permissions = document.get("permissions", [])
                    if user_email not in permissions and "everyone" not in permissions:
                        logger.warning(f"User {user_email} denied access to document {document_id}")
                        return None
                
                return document
        
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return None


class SharePointMCPConnector:
    """
    MCP (Model Context Protocol) connector for SharePoint.
    
    This connector enables agents to access SharePoint documents
    using the user's OAuth token (identity passthrough).
    """
    
    def __init__(self, tenant_id: str, site_url: str):
        """
        Initialize SharePoint MCP connector.
        
        Args:
            tenant_id: Azure AD tenant ID
            site_url: SharePoint site URL
        """
        self.tenant_id = tenant_id
        self.site_url = site_url
        self.graph_api_base = "https://graph.microsoft.com/v1.0"
        logger.info(f"SharePoint MCP connector initialized for site: {site_url}")
    
    async def search_sharepoint(
        self,
        query: str,
        user_token: str,
        top: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search SharePoint using Microsoft Graph API with user's token.
        
        Args:
            query: Search query
            user_token: User's OAuth access token
            top: Number of results to return
        
        Returns:
            List of SharePoint search results
        """
        try:
            headers = {
                "Authorization": f"Bearer {user_token}",
                "Content-Type": "application/json"
            }
            
            search_request = {
                "requests": [
                    {
                        "entityTypes": ["driveItem"],
                        "query": {
                            "queryString": query
                        },
                        "from": 0,
                        "size": top
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.graph_api_base}/search/query",
                    json=search_request,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                hits = result.get("value", [{}])[0].get("hitsContainers", [{}])[0].get("hits", [])
                
                documents = []
                for hit in hits:
                    resource = hit.get("resource", {})
                    documents.append({
                        "id": resource.get("id"),
                        "title": resource.get("name"),
                        "url": resource.get("webUrl"),
                        "content": resource.get("content", ""),
                        "created": resource.get("createdDateTime"),
                        "modified": resource.get("lastModifiedDateTime"),
                        "author": resource.get("createdBy", {}).get("user", {}).get("displayName")
                    })
                
                logger.info(f"SharePoint search returned {len(documents)} results for: {query}")
                return documents
        
        except Exception as e:
            logger.error(f"SharePoint search error: {str(e)}")
            raise
    
    async def get_file_content(
        self,
        file_id: str,
        user_token: str
    ) -> Optional[str]:
        """
        Retrieve file content from SharePoint using user's token.
        
        Args:
            file_id: SharePoint file/drive item ID
            user_token: User's OAuth access token
        
        Returns:
            File content as text or None if not accessible
        """
        try:
            headers = {
                "Authorization": f"Bearer {user_token}"
            }
            
            async with httpx.AsyncClient() as client:
                # Get file metadata
                response = await client.get(
                    f"{self.graph_api_base}/me/drive/items/{file_id}",
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                file_info = response.json()
                download_url = file_info.get("@microsoft.graph.downloadUrl")
                
                if download_url:
                    # Download file content
                    content_response = await client.get(download_url, timeout=30.0)
                    content_response.raise_for_status()
                    return content_response.text
                
                return None
        
        except Exception as e:
            logger.error(f"Error retrieving file {file_id}: {str(e)}")
            return None


class RAGService:
    """
    Unified RAG service combining Azure AI Search and SharePoint.
    """
    
    def __init__(
        self,
        ai_search_endpoint: Optional[str] = None,
        ai_search_key: Optional[str] = None,
        sharepoint_tenant_id: Optional[str] = None,
        sharepoint_site_url: Optional[str] = None
    ):
        """
        Initialize RAG service with optional Azure AI Search and SharePoint.
        
        Args:
            ai_search_endpoint: Azure AI Search endpoint
            ai_search_key: Azure AI Search API key
            sharepoint_tenant_id: Azure AD tenant ID for SharePoint
            sharepoint_site_url: SharePoint site URL
        """
        self.ai_search_client = None
        self.sharepoint_connector = None
        
        if ai_search_endpoint:
            self.ai_search_client = AzureAISearchClient(
                endpoint=ai_search_endpoint,
                api_key=ai_search_key
            )
            logger.info("✓ Azure AI Search RAG enabled")
        
        if sharepoint_tenant_id and sharepoint_site_url:
            self.sharepoint_connector = SharePointMCPConnector(
                tenant_id=sharepoint_tenant_id,
                site_url=sharepoint_site_url
            )
            logger.info("✓ SharePoint RAG enabled")
    
    async def search_knowledge_base(
        self,
        query: str,
        user_email: Optional[str] = None,
        user_token: Optional[str] = None,
        sources: List[str] = ["ai_search", "sharepoint"],
        top: int = 5
    ) -> Dict[str, Any]:
        """
        Search across all enabled knowledge sources.
        
        Args:
            query: Search query
            user_email: User's email for AI Search filtering
            user_token: User's OAuth token for SharePoint
            sources: List of sources to search (ai_search, sharepoint)
            top: Number of results per source
        
        Returns:
            Combined search results from all sources
        """
        results = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": {}
        }
        
        # Search Azure AI Search
        if "ai_search" in sources and self.ai_search_client:
            try:
                ai_search_results = await self.ai_search_client.search(
                    query=query,
                    top=top,
                    user_email=user_email
                )
                results["sources"]["ai_search"] = {
                    "count": len(ai_search_results),
                    "documents": ai_search_results
                }
            except Exception as e:
                logger.error(f"AI Search failed: {e}")
                results["sources"]["ai_search"] = {"error": str(e)}
        
        # Search SharePoint
        if "sharepoint" in sources and self.sharepoint_connector and user_token:
            try:
                sharepoint_results = await self.sharepoint_connector.search_sharepoint(
                    query=query,
                    user_token=user_token,
                    top=top
                )
                results["sources"]["sharepoint"] = {
                    "count": len(sharepoint_results),
                    "documents": sharepoint_results
                }
            except Exception as e:
                logger.error(f"SharePoint search failed: {e}")
                results["sources"]["sharepoint"] = {"error": str(e)}
        
        return results
