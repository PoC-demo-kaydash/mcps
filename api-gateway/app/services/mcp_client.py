"""
MCP Host HTTP client for communication with MCP Host
"""
from typing import Optional, Dict, Any
import httpx
from ..core.config import settings
from ..core.exceptions import MCPHostError, ServiceUnavailable
from ..utils.logger import logger


class MCPClient:
    """HTTP client for MCP Host communication"""
    
    def __init__(self):
        self.base_url = settings.mcp_host_url
        self.timeout = settings.mcp_host_timeout
        self.client = None
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
        return self.client
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to MCP Host
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters (headers, json, params, etc.)
            
        Returns:
            Response data as dictionary
            
        Raises:
            MCPHostError: If request fails
            ServiceUnavailable: If MCP Host is unavailable
        """
        client = self._get_client()
        
        try:
            logger.info(f"MCP Host request: {method} {endpoint}")
            
            response = await client.request(method, endpoint, **kwargs)
            
            # Check if response is JSON
            try:
                data = response.json()
            except Exception:
                data = {"status": "error", "error": {"message": response.text}}
            
            # Log response
            logger.info(f"MCP Host response: {response.status_code} - {endpoint}")
            
            # Check for HTTP errors
            if response.status_code >= 500:
                raise ServiceUnavailable(
                    "MCP Host is temporarily unavailable",
                    details={"status_code": response.status_code, "endpoint": endpoint}
                )
            
            if response.status_code >= 400:
                error_msg = data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise MCPHostError(
                    error_msg,
                    details={"status_code": response.status_code, "endpoint": endpoint}
                )
            
            return data
            
        except (ServiceUnavailable, MCPHostError):
            raise
        except httpx.TimeoutException:
            logger.error(f"MCP Host timeout: {endpoint}")
            raise ServiceUnavailable(
                "MCP Host request timed out",
                details={"endpoint": endpoint, "timeout": self.timeout}
            )
        except httpx.ConnectError:
            logger.error(f"MCP Host connection error: {endpoint}")
            raise ServiceUnavailable(
                "Cannot connect to MCP Host",
                details={"endpoint": endpoint, "base_url": self.base_url}
            )
        except Exception as e:
            logger.error(f"MCP Host request error: {str(e)}")
            raise MCPHostError(
                f"MCP Host request failed: {str(e)}",
                details={"endpoint": endpoint}
            )
    
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        return await self.request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        return await self.request("POST", endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make PUT request"""
        return await self.request("PUT", endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self.request("DELETE", endpoint, **kwargs)
    
    async def patch(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make PATCH request"""
        return await self.request("PATCH", endpoint, **kwargs)
    
    async def health_check(self) -> bool:
        """
        Check if MCP Host is healthy
        
        Returns:
            True if MCP Host is responding
        """
        try:
            response = await self.get("/health")
            return response.get("status") == "healthy"
        except Exception:
            return False
