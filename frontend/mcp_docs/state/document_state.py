"""
문서 State

문서 관리 상태
"""

import reflex as rx
from typing import List, Dict
import os

from frontend.state.base import BaseState


class DocumentState(BaseState):
    """문서 State"""
    
    # 문서 목록
    documents: List[Dict] = []
    
    # 현재 문서
    current_document: Dict = {}
    
    # 총 개수
    total: int = 0
    
    # 페이지네이션
    page: int = 1
    page_size: int = 20
    
    # 필터
    classification: str = ""
    category: str = ""
    
    # 문서 폼
    doc_title: str = ""
    doc_content: str = ""
    doc_classification: str = "public"
    doc_category: str = ""
    doc_tags: str = ""
    
    def set_page(self, page: int):
        """페이지 설정"""
        self.page = page
    
    def set_classification(self, classification: str):
        """공개 범위 설정"""
        self.classification = classification
    
    def set_category(self, category: str):
        """카테고리 설정"""
        self.category = category
    
    def set_doc_title(self, title: str):
        """문서 제목 설정"""
        self.doc_title = title
    
    def set_doc_content(self, content: str):
        """문서 내용 설정"""
        self.doc_content = content
    
    def set_doc_classification(self, classification: str):
        """문서 공개 범위 설정"""
        self.doc_classification = classification
    
    def set_doc_category(self, category: str):
        """문서 카테고리 설정"""
        self.doc_category = category
    
    def set_doc_tags(self, tags: str):
        """문서 태그 설정"""
        self.doc_tags = tags
    
    async def load_documents(self):
        """문서 목록 로드"""
        
        self.set_loading(True)
        self.clear_messages()
        
        try:
            # AuthState에서 토큰 가져오기
            from frontend.state.auth_state import AuthState
            auth_state = await self.get_state(AuthState)
            
            if not auth_state.is_authenticated:
                self.set_error("로그인이 필요합니다")
                return
            
            import httpx
            
            api_url = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
            
            # 쿼리 파라미터
            params = {
                "limit": self.page_size,
                "offset": (self.page - 1) * self.page_size
            }
            
            if self.classification:
                params["classification"] = self.classification
            
            if self.category:
                params["category"] = self.category
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{api_url}/api/v1/documents",
                    params=params,
                    headers={"Authorization": f"Bearer {auth_state.token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("status") == "success":
                        data = result.get("data", {})
                        self.documents = data.get("documents", [])
                        self.total = data.get("total", 0)
                    else:
                        self.set_error("문서 목록 조회 실패")
                else:
                    self.set_error(f"HTTP {response.status_code}")
        
        except Exception as e:
            self.set_error(f"문서 목록 조회 실패: {str(e)}")
        
        finally:
            self.set_loading(False)
    
    async def load_document(self, doc_id: str):
        """문서 상세 로드"""
        
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
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{api_url}/api/v1/documents/{doc_id}",
                    headers={"Authorization": f"Bearer {auth_state.token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("status") == "success":
                        self.current_document = result.get("data", {})
                    else:
                        error = result.get("error", {})
                        self.set_error(error.get("message", "문서 조회 실패"))
                else:
                    self.set_error(f"HTTP {response.status_code}")
        
        except Exception as e:
            self.set_error(f"문서 조회 실패: {str(e)}")
        
        finally:
            self.set_loading(False)
    
    async def create_document(self):
        """문서 생성"""
        
        # 유효성 검증
        if not self.doc_title:
            self.set_error("제목을 입력하세요")
            return
        
        if not self.doc_content:
            self.set_error("내용을 입력하세요")
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
            
            # 문서 데이터
            data = {
                "title": self.doc_title,
                "content": self.doc_content,
                "classification": self.doc_classification,
                "category": self.doc_category
            }
            
            if self.doc_tags:
                data["tags"] = [t.strip() for t in self.doc_tags.split(",")]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_url}/api/v1/documents",
                    json=data,
                    headers={"Authorization": f"Bearer {auth_state.token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("status") == "success":
                        self.set_success("문서가 생성되었습니다")
                        
                        # 폼 초기화
                        self.doc_title = ""
                        self.doc_content = ""
                        self.doc_classification = "public"
                        self.doc_category = ""
                        self.doc_tags = ""
                        
                        # 문서 목록으로 이동
                        return rx.redirect("/documents")
                    else:
                        error = result.get("error", {})
                        self.set_error(error.get("message", "문서 생성 실패"))
                else:
                    self.set_error(f"HTTP {response.status_code}")
        
        except Exception as e:
            self.set_error(f"문서 생성 실패: {str(e)}")
        
        finally:
            self.set_loading(False)
    
    async def delete_document(self, doc_id: str):
        """문서 삭제"""
        
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
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{api_url}/api/v1/documents/{doc_id}",
                    headers={"Authorization": f"Bearer {auth_state.token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("status") == "success":
                        self.set_success("문서가 삭제되었습니다")
                        
                        # 목록 새로고침
                        await self.load_documents()
                    else:
                        error = result.get("error", {})
                        self.set_error(error.get("message", "문서 삭제 실패"))
                else:
                    self.set_error(f"HTTP {response.status_code}")
        
        except Exception as e:
            self.set_error(f"문서 삭제 실패: {str(e)}")
        
        finally:
            self.set_loading(False)
