"""
검색 State

문서 검색 상태
"""

import reflex as rx
from typing import List, Dict
import os

from frontend.state.base import BaseState


class SearchState(BaseState):
    """검색 State"""
    
    # 검색 쿼리
    query: str = ""
    
    # 검색 결과
    results: List[Dict] = []
    
    # 총 개수
    total: int = 0
    
    # 필터
    classification_filter: List[str] = []
    category_filter: str = ""
    tags_filter: List[str] = []
    
    def set_query(self, query: str):
        """검색 쿼리 설정"""
        self.query = query
    
    def set_category_filter(self, category: str):
        """카테고리 필터 설정"""
        self.category_filter = category
    
    async def search(self):
        """검색 실행"""
        
        if not self.query:
            self.set_error("검색어를 입력하세요")
            return
        
        self.set_loading(True)
        self.clear_messages()
        
        try:
            from frontend.state.auth_state import AuthState
            auth_state = await self.get_state(AuthState)
            
            if not auth_state.is_authenticated:
                self.set_error("로그인이 필요합니다")
                return
            
            import httpx
            
            api_url = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
            
            # 검색 Tool 실행
            data = {
                "session_id": auth_state.session_id,
                "tool": "search_documents",
                "arguments": {
                    "query": self.query,
                    "limit": 20
                }
            }
            
            if self.category_filter:
                data["arguments"]["category"] = self.category_filter
            
            if self.classification_filter:
                data["arguments"]["classification"] = self.classification_filter
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_url}/api/v1/tools/execute",
                    json=data,
                    headers={"Authorization": f"Bearer {auth_state.token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("status") == "success":
                        data = result.get("data", {})
                        self.results = data.get("results", [])
                        self.total = data.get("total", 0)
                    else:
                        error = result.get("error", {})
                        self.set_error(error.get("message", "검색 실패"))
                else:
                    self.set_error(f"HTTP {response.status_code}")
        
        except Exception as e:
            self.set_error(f"검색 실패: {str(e)}")
        
        finally:
            self.set_loading(False)
    
    def clear_search(self):
        """검색 초기화"""
        self.query = ""
        self.results = []
        self.total = 0
        self.classification_filter = []
        self.category_filter = ""
        self.tags_filter = []
        self.clear_messages()
