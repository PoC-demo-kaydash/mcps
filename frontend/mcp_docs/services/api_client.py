"""
API 클라이언트

API Gateway와 HTTP 통신
"""

import httpx
from typing import Dict, Optional, Any
import os


class APIClient:
    """API 클라이언트"""
    
    def __init__(self, token: Optional[str] = None):
        """
        초기화
        
        Args:
            token: JWT 토큰 (선택)
        """
        self.base_url = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
        self.token = token
        self.timeout = 30.0
    
    def _get_headers(self) -> Dict[str, str]:
        """헤더 생성"""
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        return headers
    
    async def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        GET 요청
        
        Args:
            path: API 경로
            params: 쿼리 파라미터
            
        Returns:
            응답 JSON
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{path}",
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
    
    async def post(self, path: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        """
        POST 요청
        
        Args:
            path: API 경로
            json: 요청 본문
            
        Returns:
            응답 JSON
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{path}",
                json=json,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
    
    async def put(self, path: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        """
        PUT 요청
        
        Args:
            path: API 경로
            json: 요청 본문
            
        Returns:
            응답 JSON
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}{path}",
                json=json,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
    
    async def delete(self, path: str) -> Dict[str, Any]:
        """
        DELETE 요청
        
        Args:
            path: API 경로
            
        Returns:
            응답 JSON
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}{path}",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
