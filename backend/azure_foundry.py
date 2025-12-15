"""
Azure Foundry Integration

This module handles all interactions with Azure Foundry including:
- Discovering and listing available agents
- Sending messages to agents with OAuth Identity Passthrough (MCP)
- Managing agent responses and streaming
- Synchronizing agents with local database

OAuth Identity Passthrough (MCP) Implementation:
The MCP pattern ensures that agent calls are made with the user's
original authentication context, allowing agents to:
1. Access user-specific resources securely
2. Maintain audit trails with actual user identity
3. Implement proper authorization at the agent level
"""

import httpx
from typing import List, Dict, Any, Optional, AsyncGenerator
from uuid import UUID
from datetime import datetime
import json
import logging
import asyncio

from config import settings
# table_storage is the singleton instance of TableStorageClient
from table_storage import table_storage 
from models import Agent
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


class AzureFoundryClient:
    """
    Client for interacting with Azure Foundry services.

    This client manages agent discovery, message sending, and
    implements OAuth Identity Passthrough for secure user context
    propagation to AI agents.
    """

    def __init__(self):
        self.endpoint = settings.AZURE_FOUNDRY_ENDPOINT
        self.api_key = settings.AZURE_FOUNDRY_API_KEY
        self.project_id = settings.AZURE_FOUNDRY_PROJECT_ID
        self.credential = None
        self.client = None
        self.token = None
        self.token_expires_at = None

        logger.info(f"Azure Foundry Endpoint: {self.endpoint}")
        logger.info(f"Project ID: {self.project_id}")
        
        # Initialize Azure credential for authentication
        try:
            from azure.identity import AzureCliCredential, ManagedIdentityCredential
            
            # Try Azure CLI first (for local development)
            try:
                self.credential = AzureCliCredential()
                logger.info("✓ Azure CLI credential initialized successfully")
            except Exception as e:
                logger.warning(f"Azure CLI credential failed: {e}")
                # Try Managed Identity (for production in Azure App Service)
                try:
                    self.credential = ManagedIdentityCredential()
                    logger.info("✓ Managed Identity credential initialized")
                except Exception as e2:
                    logger.warning(f"Managed Identity credential failed: {e2}")
                    # Fallback to DefaultAzureCredential
                    self.credential = DefaultAzureCredential()
                    logger.info("✓ DefaultAzureCredential initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Azure credential: {e}")
            raise
        
        # Construct the full base URL with the API path and project ID
        # Format: https://endpoint/api/projects/{project_id}
        self.full_base_url = f"{self.endpoint}/api/projects/{self.project_id}"
        logger.info(f"Full base URL: {self.full_base_url}")

    async def get_agent_by_azure_id(self, azure_agent_id: str) -> Optional[Agent]:
        """
        Get agent information from Azure Table Storage by its Foundry ID.
        Delegates the synchronous call to table_storage via asyncio.to_thread.

        Args:
            azure_agent_id: Azure Foundry agent identifier.

        Returns:
            Agent object or None if not found
        """
        # Wrap blocking I/O in asyncio.to_thread()
        agent_entity = await asyncio.to_thread(
            table_storage.get_agent_by_azure_id,
            azure_agent_id
        )
        if agent_entity:
            # Note: Assuming the Agent model initialization is robust
            return Agent(**agent_entity)
        return None

    async def list_agents(self) -> List[Agent]:
        """
        Retrieve list of available agents from Azure Foundry.
        ... (docstring content omitted for brevity) ...
        """
        try:
            # Get bearer token from Azure credentials
            logger.info("Getting bearer token for Azure AI...")
            token = await asyncio.to_thread(
                self.credential.get_token,
                "https://ai.azure.com/.default"
            )
            
            # Create async HTTP client with bearer token
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token.token}"
            }
            
            async with httpx.AsyncClient(
                base_url=self.full_base_url,
                headers=headers,
                timeout=120.0
            ) as client:
                logger.info(f"Fetching agents from: {self.full_base_url}/assistants")
                
                # Azure AI Foundry API uses /assistants endpoint with api-version=v1
                response = await client.get("/assistants", params={"api-version": "v1"})
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch agents: {response.status_code}")
                    logger.error(f"Response body: {response.text}")
                    logger.error(f"Response headers: {dict(response.headers)}")
                
                response.raise_for_status()
                agents_data = response.json()
                
                logger.info(f"Raw response from Azure Foundry: {agents_data}")

            # Sync agents with database
            # Azure Foundry returns agents in "data" array
            agents = []
            agent_list = agents_data.get("data", [])
            logger.info(f"Number of agents in response: {len(agent_list)}")
            
            for agent_data in agent_list:
                logger.info(f"Processing agent: {agent_data}")
                agent = await self._sync_agent_to_db(agent_data)
                if agent:
                    logger.info(f"Raw response from Azure Foundry: {agents_data}")
                    agents.append(agent)
                else:
                    logger.warning(f"Failed to sync agent: {agent_data.get('id', 'unknown')}")

            logger.info(f"✓ Successfully fetched {len(agents)} agents")
            return agents

        except Exception as e:
            logger.error(f"Failed to fetch agents from Azure Foundry: {str(e)}", exc_info=True)
            raise Exception(f"Failed to fetch agents from Azure Foundry: {str(e)}")

    async def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authorization headers with fresh token from Azure credentials.
        ... (docstring content omitted for brevity) ...
        """
        try:
            logger.info("Getting bearer token for Azure AI...")
            token = await asyncio.to_thread(
                self.credential.get_token,
                "https://ai.azure.com/.default"
            )
            
            return {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token.token}"
            }
        except Exception as e:
            logger.error(f"Failed to get authorization headers: {str(e)}")
            raise

    async def _sync_agent_to_db(self, agent_data: Dict[str, Any]) -> Optional[Agent]:
        """
        Synchronize agent data from Azure Foundry to Azure Table Storage.
        
        CORRECTION: Extracts the underlying model name and stores it in capabilities.

        Args:
            agent_data: Agent data from Azure Foundry API

        Returns:
            Agent object or None if sync fails
        """
        try:
            azure_agent_id = agent_data.get("id")
            name = agent_data.get("name", "Unknown Agent")
            description = agent_data.get("description", "")
            capabilities = agent_data.get("capabilities", {})

            # --- CORRECTION 1: Extract the model name and store it in capabilities ---
            # Assuming the model deployment name is exposed under the 'model' key in 
            # the raw Azure Foundry assistant response payload.
            deployment_model_name = agent_data.get("model") 
            
            if deployment_model_name:
                capabilities["deployment_model_name"] = deployment_model_name
            # --- END CORRECTION 1 ---

            # Wrap blocking I/O in asyncio.to_thread() to avoid blocking the event loop
            agent_entity = await asyncio.to_thread(
                table_storage.create_or_update_agent,
                azure_agent_id=azure_agent_id,
                name=name,
                description=description,
                capabilities=capabilities # capabilities now includes deployment_model_name
            )

            return Agent(**agent_entity)

        except Exception as e:
            logger.error(f"Error syncing agent {agent_data.get('id', 'unknown')}: {str(e)}", exc_info=True)
            return None

    async def send_message(
        self,
        agent_id: str,
        message: str,
        conversation_history: List[Dict[str, str]],
        mcp_context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send a message to an Azure Foundry agent using the Model Inference API.
        ... (docstring content omitted for brevity) ...
        """
        try:
            agent = await self.get_agent_by_azure_id(agent_id)
            if not agent:
                raise Exception(f"Agent {agent_id} not found")
            
            logger.info(f"Sending message to agent {agent.name} ({agent_id})")

            # --- CORRECTION 2a: Get the correct model name ---
            model_name = agent.capabilities.get("deployment_model_name")
            if not model_name:
                 raise Exception(f"Agent {agent_id} is missing 'deployment_model_name' in capabilities. Please ensure agent sync has run correctly.")

            logger.info(f"Using deployment model name: {model_name}")
            # --- END CORRECTION 2a ---

            # Build conversation messages in OpenAI format
            messages = []
            
            # Add conversation history first
            for msg in conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": message
            })

            # Prepare request payload for chat completions
            payload = {
                "model": model_name, # --- CORRECTION 2b: Use the deployment model name ---
                "messages": messages,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048
            }

            # Get fresh auth headers
            headers = await self._get_auth_headers()
            
            # Add MCP context headers if provided (OAuth Identity Passthrough)
            if mcp_context and settings.MCP_ENABLED:
                # Include user context in headers for audit trail
                user_identity = mcp_context.get("user_identity", {})

# FIX: Ensure both values are non-None strings before assigning to headers
                user_id = str(user_identity.get("azure_id") or "unknown")
                user_email = str(user_identity.get("email") or "unknown")

                headers["X-User-Id"] = user_id
                headers["X-User-Email"] = user_email
                logger.info(f"MCP enabled - User: {user_identity.get('email')}")

            # Call the Model Inference API chat completions endpoint
            # Endpoint: POST /models/chat/completions?api-version=2024-05-01-preview
            endpoint = f"{self.endpoint}/models/chat/completions"
            
            logger.info(f"Calling endpoint: {endpoint}")
            logger.info(f"Request payload: {json.dumps(payload, indent=2)}")
            
            async with httpx.AsyncClient(
                headers=headers,
                timeout=120.0
            ) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    params={"api-version": "2024-05-01-preview"}
                )
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"API Error: {response.status_code}")
                    logger.error(f"Response body: {response.text}")
                    logger.error(f"Response headers: {dict(response.headers)}")
                
                response.raise_for_status()
                chat_response = response.json()

            logger.info(f"Received response from agent {agent.name}")
            
            # Extract the assistant's response message
            if "choices" in chat_response and len(chat_response["choices"]) > 0:
                assistant_message = chat_response["choices"][0].get("message", {})
                return {
                    "content": assistant_message.get("content", ""),
                    "metadata": {
                        "usage": chat_response.get("usage", {}),
                        "model": chat_response.get("model", ""),
                        "created": chat_response.get("created")
                    }
                }
            else:
                raise Exception("No response content in chat completions response")

        except httpx.HTTPError as e:
            logger.error(f"Failed to send message to agent: {str(e)}")
            raise Exception(f"Failed to send message to agent: {str(e)}")
        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}", exc_info=True)
            raise

    async def send_message_stream(
        self,
        agent_id: str,
        message: str,
        conversation_history: List[Dict[str, str]],
        mcp_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Send a message to an agent and stream the chat completions response.
        ... (docstring content omitted for brevity) ...
        """
        try:
            agent = await self.get_agent_by_azure_id(agent_id)
            if not agent:
                raise Exception(f"Agent {agent_id} not found")
            
            logger.info(f"Streaming message to agent {agent.name} ({agent_id})")

            # --- CORRECTION 3a: Get the correct model name ---
            model_name = agent.capabilities.get("deployment_model_name")
            if not model_name:
                 raise Exception(f"Agent {agent_id} is missing 'deployment_model_name' in capabilities. Please ensure agent sync has run correctly.")

            logger.info(f"Using deployment model name for stream: {model_name}")
            # --- END CORRECTION 3a ---

            # Build conversation messages in OpenAI format
            messages = []
            
            # Add conversation history first
            for msg in conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": message
            })

            # Prepare request payload for chat completions with streaming
            payload = {
                "model": model_name, # --- CORRECTION 3b: Use the deployment model name ---
                "messages": messages,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048,
                "stream": True
            }

            # Get fresh auth headers
            headers = await self._get_auth_headers()
            
            # Add MCP context headers if provided (OAuth Identity Passthrough)
            if mcp_context and settings.MCP_ENABLED:
                user_identity = mcp_context.get("user_identity", {})
                
                user_id = str(user_identity.get("azure_id") or "unknown")
                user_email = str(user_identity.get("email") or "unknown")
                
                headers["X-User-Id"] = user_id
                headers["X-User-Email"] = user_email
                
                logger.info(f"MCP enabled - User: {user_identity.get('email')}")

            # Call the Model Inference API chat completions endpoint with streaming
            endpoint = f"{self.endpoint}/models/chat/completions"
            
            logger.info(f"Streaming from endpoint: {endpoint}")
            
            async with httpx.AsyncClient(
                headers=headers,
                timeout=120.0
            ) as client:
                async with client.stream(
                    "POST",
                    endpoint,
                    json=payload,
                    params={"api-version": "2024-05-01-preview"}
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        # Parse Server-Sent Events (SSE) format
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                logger.info("Stream completed")
                                break
                            
                            try:
                                data = json.loads(data_str)
                                
                                # Extract token from choices
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    
                                    if content:
                                        logger.debug(f"Streamed token: {content}")
                                        yield content
                                        
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse SSE data: {data_str}")
                                continue

        except httpx.HTTPError as e:
            logger.error(f"Failed to stream message to agent: {str(e)}")
            raise Exception(f"Failed to stream message to agent: {str(e)}")
        except Exception as e:
            logger.error(f"Error in send_message_stream: {str(e)}", exc_info=True)
            raise

    async def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """
        Get agent information from Azure Table Storage by UUID.
        ... (docstring content omitted for brevity) ...
        """
        # Wrap blocking I/O in asyncio.to_thread()
        agent_entity = await asyncio.to_thread(
            table_storage.get_agent_by_id,
            str(agent_id)
        )
        if agent_entity:
            return Agent(**agent_entity)
        return None

    async def get_agent_by_azure_id(self, azure_agent_id: str) -> Optional[Agent]:
        """
        Get agent information from Azure Table Storage by Azure Foundry ID.
        ... (docstring content omitted for brevity) ...
        """
        # Wrap blocking I/O in asyncio.to_thread()
        agent_entity = await asyncio.to_thread(
            table_storage.get_agent_by_azure_id,
            str(azure_agent_id)
        )
        if agent_entity:
            return Agent(**agent_entity)
        return None

    async def close(self):
        """Close HTTP client connections"""
        pass


foundry_client = AzureFoundryClient()