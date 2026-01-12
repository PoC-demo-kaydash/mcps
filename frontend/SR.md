# Frontend 전체 설계서

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/frontend/`  
**목적**: Reflex 프레임워크 기반 Frontend 전체 설계

***

## 목차

1. [개요](#1-개요)
2. [Reflex 아키텍처](#2-reflex-아키텍처)
3. [프로젝트 구조](#3-프로젝트-구조)
4. [State 관리](#4-state-관리)
5. [Pages](#5-pages)
6. [Components](#6-components)
7. [API 연동](#7-api-연동)
8. [스타일링](#8-스타일링)
9. [라우팅](#9-라우팅)
10. [인증 처리](#10-인증-처리)
11. [배포](#11-배포)

***

## 1. 개요

### 1.1 Reflex 소개

```
┌─────────────────────────────────────────┐
│           Reflex 프레임워크              │
├─────────────────────────────────────────┤
│                                          │
│  [Python 코드]                           │
│       │                                  │
│       ├─ State (상태 관리)              │
│       ├─ Components (UI 컴포넌트)       │
│       └─ Pages (페이지)                 │
│                                          │
│       ▼                                  │
│  [자동 변환]                             │
│       │                                  │
│       ├─ React (Frontend)               │
│       └─ FastAPI (Backend)              │
│                                          │
│       ▼                                  │
│  [실행 환경]                             │
│       ├─ Web Browser                    │
│       └─ WebSocket (실시간 통신)        │
│                                          │
└─────────────────────────────────────────┘
```

### 1.2 주요 특징

| 특징 | 설명 | 장점 |
|------|------|------|
| **Pure Python** | Python만으로 풀스택 개발 | JavaScript 불필요 |
| **React 기반** | 내부적으로 React 사용 | 성능 우수 |
| **상태 관리** | 자동 상태 동기화 | 간단한 상태 관리 |
| **Chakra UI** | 기본 UI 컴포넌트 제공 | 빠른 개발 |
| **실시간 통신** | WebSocket 기반 | 반응형 UI |
| **타입 안전** | Python 타입 힌트 | 안정성 향상 |

### 1.3 기술 스택

```yaml
Framework: Reflex 0.4.0+
Python: 3.11+
UI Library: Chakra UI
HTTP Client: httpx
State Management: Reflex State
Styling: Chakra UI + Custom CSS
```

***

## 2. Reflex 아키텍처

### 2.1 컴포넌트 구조

```
┌─────────────────────────────────────────┐
│         Reflex 컴포넌트 구조             │
├─────────────────────────────────────────┤
│                                          │
│  [App]                                   │
│    │                                     │
│    ├─ [Layout]                          │
│    │    ├─ Header                       │
│    │    ├─ Sidebar                      │
│    │    └─ Footer                       │
│    │                                     │
│    ├─ [Pages]                           │
│    │    ├─ Home                         │
│    │    ├─ Login                        │
│    │    ├─ Documents                    │
│    │    └─ Admin                        │
│    │                                     │
│    └─ [State]                           │
│         ├─ AppState                     │
│         ├─ AuthState                    │
│         ├─ DocumentState                │
│         └─ UIState                      │
│                                          │
└─────────────────────────────────────────┘
```

### 2.2 데이터 흐름

```
User Action
    │
    ▼
[Event Handler] ──────┐
    │                 │
    ▼                 │
[State Update]        │
    │                 │
    ▼                 │
[Backend Processing] ──┘
    │
    ▼
[API Call]
    │
    ▼
[Response]
    │
    ▼
[State Update]
    │
    ▼
[UI Re-render]
```

***

## 3. 프로젝트 구조

```
frontend/
├── rxconfig.py                  # Reflex 설정
├── requirements.txt             # 의존성
├── .env                         # 환경 변수
│
├── frontend/                    # 메인 애플리케이션
│   ├── __init__.py
│   ├── app.py                   # 애플리케이션 엔트리포인트
│   │
│   ├── state/                   # 상태 관리
│   │   ├── __init__.py
│   │   ├── base.py             # 기본 State
│   │   ├── auth_state.py       # 인증 상태
│   │   ├── document_state.py   # 문서 상태
│   │   ├── search_state.py     # 검색 상태
│   │   └── ui_state.py         # UI 상태
│   │
│   ├── pages/                   # 페이지
│   │   ├── __init__.py
│   │   ├── index.py            # 홈
│   │   ├── login.py            # 로그인
│   │   ├── dashboard.py        # 대시보드
│   │   ├── documents/          # 문서
│   │   │   ├── __init__.py
│   │   │   ├── list.py         # 목록
│   │   │   ├── detail.py       # 상세
│   │   │   ├── create.py       # 생성
│   │   │   └── edit.py         # 수정
│   │   ├── search.py           # 검색
│   │   └── admin/              # 관리자
│   │       ├── __init__.py
│   │       ├── users.py        # 사용자 관리
│   │       └── stats.py        # 통계
│   │
│   ├── components/              # 컴포넌트
│   │   ├── __init__.py
│   │   ├── layout/             # 레이아웃
│   │   │   ├── __init__.py
│   │   │   ├── header.py       # 헤더
│   │   │   ├── sidebar.py      # 사이드바
│   │   │   ├── footer.py       # 푸터
│   │   │   └── layout.py       # 전체 레이아웃
│   │   │
│   │   ├── common/             # 공통 컴포넌트
│   │   │   ├── __init__.py
│   │   │   ├── button.py       # 버튼
│   │   │   ├── input.py        # 입력
│   │   │   ├── card.py         # 카드
│   │   │   ├── table.py        # 테이블
│   │   │   ├── modal.py        # 모달
│   │   │   └── loading.py      # 로딩
│   │   │
│   │   ├── document/           # 문서 컴포넌트
│   │   │   ├── __init__.py
│   │   │   ├── list_item.py    # 목록 아이템
│   │   │   ├── viewer.py       # 뷰어
│   │   │   ├── editor.py       # 에디터
│   │   │   └── version.py      # 버전 정보
│   │   │
│   │   └── search/             # 검색 컴포넌트
│   │       ├── __init__.py
│   │       ├── search_bar.py   # 검색바
│   │       └── result_item.py  # 결과 아이템
│   │
│   ├── services/                # 서비스
│   │   ├── __init__.py
│   │   ├── api_client.py       # API 클라이언트
│   │   ├── auth_service.py     # 인증 서비스
│   │   └── storage_service.py  # 스토리지 서비스
│   │
│   ├── utils/                   # 유틸리티
│   │   ├── __init__.py
│   │   ├── constants.py        # 상수
│   │   ├── validators.py       # 검증
│   │   └── formatters.py       # 포맷터
│   │
│   └── styles/                  # 스타일
│       ├── __init__.py
│       ├── theme.py            # 테마
│       └── colors.py           # 색상
│
├── assets/                      # 정적 파일
│   ├── images/
│   ├── icons/
│   └── fonts/
│
└── tests/                       # 테스트
    ├── __init__.py
    └── test_components.py
```

***

## 4. State 관리

### 4.1 base.py (기본 State)

```python
# frontend/state/base.py
"""
기본 State

모든 State의 부모 클래스
"""

import reflex as rx
from typing import Optional


class BaseState(rx.State):
    """기본 State"""
    
    # 로딩 상태
    is_loading: bool = False
    
    # 에러 메시지
    error_message: str = ""
    
    # 성공 메시지
    success_message: str = ""
    
    def set_loading(self, loading: bool):
        """로딩 상태 설정"""
        self.is_loading = loading
    
    def set_error(self, message: str):
        """에러 메시지 설정"""
        self.error_message = message
        self.success_message = ""
    
    def set_success(self, message: str):
        """성공 메시지 설정"""
        self.success_message = message
        self.error_message = ""
    
    def clear_messages(self):
        """메시지 초기화"""
        self.error_message = ""
        self.success_message = ""
```

### 4.2 auth_state.py (인증 상태)

```python
# frontend/state/auth_state.py
"""
인증 State

사용자 인증 및 세션 관리
"""

import reflex as rx
from typing import Optional, Dict
import httpx

from frontend.state.base import BaseState
from frontend.services.api_client import APIClient
from frontend.services.auth_service import AuthService


class AuthState(BaseState):
    """인증 State"""
    
    # 로그인 여부
    is_authenticated: bool = False
    
    # 사용자 정보
    user: Dict = {}
    
    # 세션 ID
    session_id: str = ""
    
    # 토큰
    token: str = ""
    
    # 로그인 폼
    user_id: str = ""
    
    def set_user_id(self, user_id: str):
        """사용자 ID 설정"""
        self.user_id = user_id
    
    async def login(self):
        """로그인"""
        
        if not self.user_id:
            self.set_error("사용자 ID를 입력하세요")
            return
        
        self.set_loading(True)
        self.clear_messages()
        
        try:
            # 세션 생성
            auth_service = AuthService()
            result = await auth_service.create_session(self.user_id)
            
            # 상태 업데이트
            self.is_authenticated = True
            self.user = result.get("user", {})
            self.session_id = result.get("session_id", "")
            self.token = result.get("token", "")
            
            # 로컬 스토리지에 저장
            rx.local_storage.setItem("token", self.token)
            rx.local_storage.setItem("session_id", self.session_id)
            
            self.set_success("로그인 성공")
            
            # 대시보드로 이동
            return rx.redirect("/dashboard")
        
        except Exception as e:
            self.set_error(f"로그인 실패: {str(e)}")
        
        finally:
            self.set_loading(False)
    
    async def logout(self):
        """로그아웃"""
        
        self.set_loading(True)
        
        try:
            # 세션 삭제
            if self.session_id:
                auth_service = AuthService()
                await auth_service.delete_session(self.session_id, self.token)
            
            # 상태 초기화
            self.is_authenticated = False
            self.user = {}
            self.session_id = ""
            self.token = ""
            self.user_id = ""
            
            # 로컬 스토리지 삭제
            rx.local_storage.removeItem("token")
            rx.local_storage.removeItem("session_id")
            
            self.set_success("로그아웃 되었습니다")
            
            # 로그인 페이지로 이동
            return rx.redirect("/login")
        
        except Exception as e:
            self.set_error(f"로그아웃 실패: {str(e)}")
        
        finally:
            self.set_loading(False)
    
    async def check_auth(self):
        """인증 확인"""
        
        # 로컬 스토리지에서 토큰 확인
        token = rx.local_storage.getItem("token")
        session_id = rx.local_storage.getItem("session_id")
        
        if token and session_id:
            self.token = token
            self.session_id = session_id
            
            try:
                # 세션 확인
                auth_service = AuthService()
                session = await auth_service.get_session(session_id, token)
                
                if session:
                    self.is_authenticated = True
                    self.user = session.get("user", {})
                else:
                    # 세션 없음
                    self.is_authenticated = False
                    rx.local_storage.removeItem("token")
                    rx.local_storage.removeItem("session_id")
            
            except:
                self.is_authenticated = False
        
        else:
            self.is_authenticated = False
```

### 4.3 document_state.py (문서 상태)

```python
# frontend/state/document_state.py
"""
문서 State

문서 관리 상태
"""

import reflex as rx
from typing import List, Dict, Optional

from frontend.state.base import BaseState
from frontend.services.api_client import APIClient


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
            from frontend.state.auth_state import AuthState
            auth_state = await self.get_state(AuthState)
            
            if not auth_state.is_authenticated:
                self.set_error("로그인이 필요합니다")
                return
            
            client = APIClient(auth_state.token)
            
            # 문서 목록 조회
            params = {
                "limit": self.page_size,
                "offset": (self.page - 1) * self.page_size
            }
            
            if self.classification:
                params["classification"] = self.classification
            
            if self.category:
                params["category"] = self.category
            
            result = await client.get("/api/v1/documents", params=params)
            
            if result.get("status") == "success":
                data = result.get("data", {})
                self.documents = data.get("documents", [])
                self.total = data.get("total", 0)
            else:
                self.set_error("문서 목록 조회 실패")
        
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
            
            client = APIClient(auth_state.token)
            
            # 문서 조회
            result = await client.get(f"/api/v1/documents/{doc_id}")
            
            if result.get("status") == "success":
                self.current_document = result.get("data", {})
            else:
                error = result.get("error", {})
                self.set_error(error.get("message", "문서 조회 실패"))
        
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
            
            client = APIClient(auth_state.token)
            
            # 문서 생성
            data = {
                "title": self.doc_title,
                "content": self.doc_content,
                "classification": self.doc_classification,
                "category": self.doc_category
            }
            
            if self.doc_tags:
                data["tags"] = [t.strip() for t in self.doc_tags.split(",")]
            
            result = await client.post("/api/v1/documents", json=data)
            
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
            
            client = APIClient(auth_state.token)
            
            # 문서 삭제
            result = await client.delete(f"/api/v1/documents/{doc_id}")
            
            if result.get("status") == "success":
                self.set_success("문서가 삭제되었습니다")
                
                # 목록 새로고침
                await self.load_documents()
            else:
                error = result.get("error", {})
                self.set_error(error.get("message", "문서 삭제 실패"))
        
        except Exception as e:
            self.set_error(f"문서 삭제 실패: {str(e)}")
        
        finally:
            self.set_loading(False)
```

### 4.4 search_state.py (검색 상태)

```python
# frontend/state/search_state.py
"""
검색 State

문서 검색 상태
"""

import reflex as rx
from typing import List, Dict

from frontend.state.base import BaseState
from frontend.services.api_client import APIClient


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
            
            client = APIClient(auth_state.token)
            
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
            
            result = await client.post("/api/v1/tools/execute", json=data)
            
            if result.get("status") == "success":
                data = result.get("data", {})
                self.results = data.get("results", [])
                self.total = data.get("total", 0)
            else:
                error = result.get("error", {})
                self.set_error(error.get("message", "검색 실패"))
        
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
```

***

## 5. Pages

### 5.1 index.py (홈)

```python
# frontend/pages/index.py
"""
홈 페이지
"""

import reflex as rx
from frontend.components.layout.layout import layout


def index() -> rx.Component:
    """홈 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 헤더
                rx.heading(
                    "MCP 문서 관리 시스템",
                    size="2xl",
                    color="blue.600"
                ),
                rx.text(
                    "Model Context Protocol 기반 문서 관리 및 검색 시스템",
                    font_size="lg",
                    color="gray.600"
                ),
                
                # 주요 기능
                rx.hstack(
                    rx.card(
                        rx.vstack(
                            rx.icon("file-text", size=40, color="blue.500"),
                            rx.heading("문서 관리", size="md"),
                            rx.text("문서 생성, 수정, 삭제 및 버전 관리", text_align="center"),
                            spacing="3"
                        ),
                        padding="6"
                    ),
                    rx.card(
                        rx.vstack(
                            rx.icon("search", size=40, color="green.500"),
                            rx.heading("전문 검색", size="md"),
                            rx.text("강력한 검색 기능으로 문서 빠르게 찾기", text_align="center"),
                            spacing="3"
                        ),
                        padding="6"
                    ),
                    rx.card(
                        rx.vstack(
                            rx.icon("shield", size=40, color="red.500"),
                            rx.heading("권한 관리", size="md"),
                            rx.text("세밀한 권한 관리로 보안 강화", text_align="center"),
                            spacing="3"
                        ),
                        padding="6"
                    ),
                    spacing="6"
                ),
                
                # CTA
                rx.button(
                    "시작하기",
                    on_click=rx.redirect("/login"),
                    size="lg",
                    color_scheme="blue"
                ),
                
                spacing="8",
                align="center"
            ),
            padding_y="16"
        )
    )
```

### 5.2 login.py (로그인)

```python
# frontend/pages/login.py
"""
로그인 페이지
"""

import reflex as rx
from frontend.state.auth_state import AuthState


def login() -> rx.Component:
    """로그인 페이지"""
    
    return rx.center(
        rx.card(
            rx.vstack(
                # 제목
                rx.heading("로그인", size="xl"),
                
                # 에러/성공 메시지
                rx.cond(
                    AuthState.error_message,
                    rx.alert(
                        rx.alert_icon(),
                        rx.alert_title(AuthState.error_message),
                        status="error"
                    )
                ),
                rx.cond(
                    AuthState.success_message,
                    rx.alert(
                        rx.alert_icon(),
                        rx.alert_title(AuthState.success_message),
                        status="success"
                    )
                ),
                
                # 로그인 폼
                rx.form_control(
                    rx.form_label("사용자 ID"),
                    rx.input(
                        placeholder="사용자 ID를 입력하세요",
                        value=AuthState.user_id,
                        on_change=AuthState.set_user_id,
                        disabled=AuthState.is_loading
                    ),
                    is_required=True
                ),
                
                # 로그인 버튼
                rx.button(
                    rx.cond(
                        AuthState.is_loading,
                        rx.spinner(size="sm"),
                        "로그인"
                    ),
                    on_click=AuthState.login,
                    width="100%",
                    color_scheme="blue",
                    is_loading=AuthState.is_loading
                ),
                
                spacing="4",
                width="100%"
            ),
            padding="8",
            max_width="400px"
        ),
        height="100vh"
    )
```

### 5.3 dashboard.py (대시보드)

```python
# frontend/pages/dashboard.py
"""
대시보드 페이지
"""

import reflex as rx
from frontend.state.auth_state import AuthState
from frontend.components.layout.layout import layout


def dashboard() -> rx.Component:
    """대시보드 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 환영 메시지
                rx.heading(
                    f"환영합니다, {AuthState.user['name']}님!",
                    size="xl"
                ),
                
                # 통계 카드
                rx.hstack(
                    rx.stat(
                        rx.stat_label("내 문서"),
                        rx.stat_number("24"),
                        rx.stat_help_text("전체 문서 수")
                    ),
                    rx.stat(
                        rx.stat_label("오늘 조회"),
                        rx.stat_number("128"),
                        rx.stat_help_text("오늘 조회된 문서")
                    ),
                    rx.stat(
                        rx.stat_label("최근 수정"),
                        rx.stat_number("3"),
                        rx.stat_help_text("최근 7일간 수정")
                    ),
                    spacing="6",
                    width="100%"
                ),
                
                # 최근 문서
                rx.heading("최근 문서", size="md"),
                rx.divider(),
                
                # 빠른 액션
                rx.hstack(
                    rx.button(
                        rx.icon("plus", margin_right="2"),
                        "새 문서",
                        on_click=rx.redirect("/documents/create"),
                        color_scheme="blue"
                    ),
                    rx.button(
                        rx.icon("search", margin_right="2"),
                        "검색",
                        on_click=rx.redirect("/search"),
                        color_scheme="green"
                    ),
                    spacing="4"
                ),
                
                spacing="6",
                width="100%"
            ),
            padding_y="8"
        )
    )
```




### 5.4 documents/list.py (문서 목록)

```python
# frontend/pages/documents/list.py
"""
문서 목록 페이지
"""

import reflex as rx
from frontend.state.document_state import DocumentState
from frontend.components.layout.layout import layout
from frontend.components.document.list_item import document_list_item


def documents_list() -> rx.Component:
    """문서 목록 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 헤더
                rx.hstack(
                    rx.heading("문서 목록", size="xl"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", margin_right="2"),
                        "새 문서",
                        on_click=rx.redirect("/documents/create"),
                        color_scheme="blue"
                    ),
                    width="100%"
                ),
                
                # 필터
                rx.hstack(
                    rx.select(
                        ["전체", "public", "team", "department", "confidential"],
                        placeholder="공개 범위",
                        value=DocumentState.classification,
                        on_change=DocumentState.set_classification
                    ),
                    rx.input(
                        placeholder="카테고리",
                        value=DocumentState.category,
                        on_change=DocumentState.set_category
                    ),
                    rx.button(
                        "검색",
                        on_click=DocumentState.load_documents,
                        color_scheme="green"
                    ),
                    spacing="3",
                    width="100%"
                ),
                
                # 에러/성공 메시지
                rx.cond(
                    DocumentState.error_message,
                    rx.alert(
                        rx.alert_icon(),
                        rx.alert_title(DocumentState.error_message),
                        status="error"
                    )
                ),
                rx.cond(
                    DocumentState.success_message,
                    rx.alert(
                        rx.alert_icon(),
                        rx.alert_title(DocumentState.success_message),
                        status="success"
                    )
                ),
                
                # 로딩
                rx.cond(
                    DocumentState.is_loading,
                    rx.center(
                        rx.spinner(size="xl"),
                        padding="8"
                    ),
                    # 문서 목록
                    rx.vstack(
                        rx.foreach(
                            DocumentState.documents,
                            document_list_item
                        ),
                        spacing="4",
                        width="100%"
                    )
                ),
                
                # 페이지네이션
                rx.hstack(
                    rx.text(f"총 {DocumentState.total}개"),
                    rx.spacer(),
                    rx.button_group(
                        rx.button(
                            "이전",
                            on_click=DocumentState.set_page(DocumentState.page - 1),
                            is_disabled=DocumentState.page <= 1
                        ),
                        rx.text(f"{DocumentState.page} 페이지"),
                        rx.button(
                            "다음",
                            on_click=DocumentState.set_page(DocumentState.page + 1),
                            is_disabled=DocumentState.page * DocumentState.page_size >= DocumentState.total
                        )
                    ),
                    width="100%"
                ),
                
                spacing="6",
                width="100%"
            ),
            padding_y="8",
            on_mount=DocumentState.load_documents
        )
    )
```

### 5.5 documents/detail.py (문서 상세)

```python
# frontend/pages/documents/detail.py
"""
문서 상세 페이지
"""

import reflex as rx
from frontend.state.document_state import DocumentState
from frontend.state.auth_state import AuthState
from frontend.components.layout.layout import layout
from frontend.components.document.viewer import document_viewer


def document_detail(doc_id: str) -> rx.Component:
    """문서 상세 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 헤더
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left"),
                        on_click=rx.redirect("/documents"),
                        variant="ghost"
                    ),
                    rx.heading(DocumentState.current_document["title"], size="xl"),
                    rx.spacer(),
                    rx.button_group(
                        rx.button(
                            rx.icon("edit"),
                            on_click=rx.redirect(f"/documents/{doc_id}/edit"),
                            variant="outline"
                        ),
                        rx.button(
                            rx.icon("trash"),
                            on_click=DocumentState.delete_document(doc_id),
                            color_scheme="red",
                            variant="outline"
                        )
                    ),
                    width="100%"
                ),
                
                # 메타 정보
                rx.hstack(
                    rx.badge(DocumentState.current_document["classification"]),
                    rx.badge(DocumentState.current_document["category"], color_scheme="green"),
                    rx.text(f"작성자: {DocumentState.current_document['author_name']}"),
                    rx.text(f"버전: {DocumentState.current_document['version']}"),
                    spacing="3"
                ),
                
                # 문서 내용
                rx.cond(
                    DocumentState.is_loading,
                    rx.center(rx.spinner(size="xl"), padding="8"),
                    document_viewer(DocumentState.current_document)
                ),
                
                spacing="6",
                width="100%"
            ),
            padding_y="8",
            on_mount=DocumentState.load_document(doc_id)
        )
    )
```

### 5.6 documents/create.py (문서 생성)

```python
# frontend/pages/documents/create.py
"""
문서 생성 페이지
"""

import reflex as rx
from frontend.state.document_state import DocumentState
from frontend.components.layout.layout import layout


def document_create() -> rx.Component:
    """문서 생성 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 헤더
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left"),
                        on_click=rx.redirect("/documents"),
                        variant="ghost"
                    ),
                    rx.heading("새 문서 작성", size="xl"),
                    width="100%"
                ),
                
                # 에러/성공 메시지
                rx.cond(
                    DocumentState.error_message,
                    rx.alert(
                        rx.alert_icon(),
                        rx.alert_title(DocumentState.error_message),
                        status="error"
                    )
                ),
                
                # 문서 폼
                rx.form(
                    rx.vstack(
                        # 제목
                        rx.form_control(
                            rx.form_label("제목"),
                            rx.input(
                                placeholder="문서 제목을 입력하세요",
                                value=DocumentState.doc_title,
                                on_change=DocumentState.set_doc_title,
                                size="lg"
                            ),
                            is_required=True
                        ),
                        
                        # 공개 범위
                        rx.form_control(
                            rx.form_label("공개 범위"),
                            rx.select(
                                ["public", "team", "department", "confidential"],
                                value=DocumentState.doc_classification,
                                on_change=DocumentState.set_doc_classification
                            ),
                            is_required=True
                        ),
                        
                        # 카테고리
                        rx.form_control(
                            rx.form_label("카테고리"),
                            rx.input(
                                placeholder="카테고리를 입력하세요",
                                value=DocumentState.doc_category,
                                on_change=DocumentState.set_doc_category
                            ),
                            is_required=True
                        ),
                        
                        # 태그
                        rx.form_control(
                            rx.form_label("태그"),
                            rx.input(
                                placeholder="태그를 쉼표로 구분하여 입력하세요",
                                value=DocumentState.doc_tags,
                                on_change=DocumentState.set_doc_tags
                            )
                        ),
                        
                        # 내용
                        rx.form_control(
                            rx.form_label("내용 (Markdown)"),
                            rx.text_area(
                                placeholder="문서 내용을 Markdown으로 작성하세요",
                                value=DocumentState.doc_content,
                                on_change=DocumentState.set_doc_content,
                                min_height="400px"
                            ),
                            is_required=True
                        ),
                        
                        # 버튼
                        rx.hstack(
                            rx.button(
                                "취소",
                                on_click=rx.redirect("/documents"),
                                variant="outline"
                            ),
                            rx.button(
                                rx.cond(
                                    DocumentState.is_loading,
                                    rx.spinner(size="sm"),
                                    "생성"
                                ),
                                on_click=DocumentState.create_document,
                                color_scheme="blue",
                                is_loading=DocumentState.is_loading
                            ),
                            spacing="3"
                        ),
                        
                        spacing="4",
                        width="100%"
                    ),
                    width="100%"
                ),
                
                spacing="6",
                width="100%"
            ),
            max_width="800px",
            padding_y="8"
        )
    )
```

### 5.7 search.py (검색)

```python
# frontend/pages/search.py
"""
검색 페이지
"""

import reflex as rx
from frontend.state.search_state import SearchState
from frontend.components.layout.layout import layout
from frontend.components.search.search_bar import search_bar
from frontend.components.search.result_item import search_result_item


def search() -> rx.Component:
    """검색 페이지"""
    
    return layout(
        rx.container(
            rx.vstack(
                # 검색바
                search_bar(),
                
                # 필터
                rx.hstack(
                    rx.select(
                        ["전체", "documentation", "guide", "standard"],
                        placeholder="카테고리",
                        value=SearchState.category_filter,
                        on_change=SearchState.set_category_filter
                    ),
                    spacing="3"
                ),
                
                # 에러 메시지
                rx.cond(
                    SearchState.error_message,
                    rx.alert(
                        rx.alert_icon(),
                        rx.alert_title(SearchState.error_message),
                        status="error"
                    )
                ),
                
                # 검색 결과
                rx.cond(
                    SearchState.is_loading,
                    rx.center(rx.spinner(size="xl"), padding="8"),
                    rx.vstack(
                        rx.cond(
                            SearchState.total > 0,
                            rx.vstack(
                                rx.text(f"{SearchState.total}개의 결과", font_weight="bold"),
                                rx.foreach(
                                    SearchState.results,
                                    search_result_item
                                ),
                                spacing="4",
                                width="100%"
                            ),
                            rx.center(
                                rx.text("검색 결과가 없습니다", color="gray.500"),
                                padding="8"
                            )
                        ),
                        width="100%"
                    )
                ),
                
                spacing="6",
                width="100%"
            ),
            padding_y="8"
        )
    )
```

***

## 6. Components

### 6.1 layout/header.py (헤더)

```python
# frontend/components/layout/header.py
"""
헤더 컴포넌트
"""

import reflex as rx
from frontend.state.auth_state import AuthState


def header() -> rx.Component:
    """헤더"""
    
    return rx.box(
        rx.container(
            rx.hstack(
                # 로고
                rx.link(
                    rx.hstack(
                        rx.icon("file-text", size=24, color="blue.500"),
                        rx.heading("MCP Docs", size="md"),
                        spacing="2"
                    ),
                    href="/"
                ),
                
                rx.spacer(),
                
                # 네비게이션
                rx.cond(
                    AuthState.is_authenticated,
                    rx.hstack(
                        rx.link("대시보드", href="/dashboard"),
                        rx.link("문서", href="/documents"),
                        rx.link("검색", href="/search"),
                        
                        # 사용자 메뉴
                        rx.menu(
                            rx.menu_button(
                                rx.hstack(
                                    rx.avatar(
                                        name=AuthState.user["name"],
                                        size="sm"
                                    ),
                                    rx.text(AuthState.user["name"]),
                                    rx.icon("chevron-down", size=16),
                                    spacing="2"
                                )
                            ),
                            rx.menu_list(
                                rx.menu_item(
                                    rx.icon("user", margin_right="2"),
                                    "내 정보",
                                    on_click=rx.redirect("/profile")
                                ),
                                rx.menu_divider(),
                                rx.menu_item(
                                    rx.icon("log-out", margin_right="2"),
                                    "로그아웃",
                                    on_click=AuthState.logout
                                )
                            )
                        ),
                        
                        spacing="6"
                    ),
                    rx.button(
                        "로그인",
                        on_click=rx.redirect("/login"),
                        color_scheme="blue"
                    )
                ),
                
                align="center",
                width="100%"
            ),
            max_width="1200px"
        ),
        padding_y="4",
        border_bottom="1px solid",
        border_color="gray.200",
        background="white",
        position="sticky",
        top="0",
        z_index="10"
    )
```

### 6.2 layout/sidebar.py (사이드바)

```python
# frontend/components/layout/sidebar.py
"""
사이드바 컴포넌트
"""

import reflex as rx
from frontend.state.auth_state import AuthState


def sidebar() -> rx.Component:
    """사이드바"""
    
    return rx.box(
        rx.vstack(
            # 네비게이션
            rx.link(
                rx.hstack(
                    rx.icon("home", size=20),
                    rx.text("대시보드"),
                    spacing="3",
                    padding="3",
                    border_radius="md",
                    _hover={"background": "gray.100"}
                ),
                href="/dashboard",
                width="100%"
            ),
            
            rx.link(
                rx.hstack(
                    rx.icon("file-text", size=20),
                    rx.text("문서"),
                    spacing="3",
                    padding="3",
                    border_radius="md",
                    _hover={"background": "gray.100"}
                ),
                href="/documents",
                width="100%"
            ),
            
            rx.link(
                rx.hstack(
                    rx.icon("search", size=20),
                    rx.text("검색"),
                    spacing="3",
                    padding="3",
                    border_radius="md",
                    _hover={"background": "gray.100"}
                ),
                href="/search",
                width="100%"
            ),
            
            # Admin 메뉴 (admin만)
            rx.cond(
                AuthState.user["role"] == "admin",
                rx.vstack(
                    rx.divider(),
                    rx.text("관리자", font_weight="bold", font_size="sm", color="gray.600"),
                    
                    rx.link(
                        rx.hstack(
                            rx.icon("users", size=20),
                            rx.text("사용자 관리"),
                            spacing="3",
                            padding="3",
                            border_radius="md",
                            _hover={"background": "gray.100"}
                        ),
                        href="/admin/users",
                        width="100%"
                    ),
                    
                    rx.link(
                        rx.hstack(
                            rx.icon("bar-chart", size=20),
                            rx.text("통계"),
                            spacing="3",
                            padding="3",
                            border_radius="md",
                            _hover={"background": "gray.100"}
                        ),
                        href="/admin/stats",
                        width="100%"
                    ),
                    
                    spacing="2",
                    width="100%"
                )
            ),
            
            spacing="2",
            width="100%",
            align="stretch"
        ),
        width="250px",
        padding="4",
        border_right="1px solid",
        border_color="gray.200",
        min_height="calc(100vh - 72px)"
    )
```

### 6.3 layout/layout.py (전체 레이아웃)

```python
# frontend/components/layout/layout.py
"""
전체 레이아웃
"""

import reflex as rx
from frontend.components.layout.header import header
from frontend.components.layout.sidebar import sidebar
from frontend.state.auth_state import AuthState


def layout(*children, show_sidebar: bool = True) -> rx.Component:
    """전체 레이아웃"""
    
    return rx.box(
        header(),
        rx.hstack(
            # 사이드바 (로그인 시 & show_sidebar=True)
            rx.cond(
                AuthState.is_authenticated and show_sidebar,
                sidebar(),
                rx.box()
            ),
            
            # 메인 컨텐츠
            rx.box(
                *children,
                flex="1",
                padding="4"
            ),
            
            spacing="0",
            align="stretch",
            width="100%"
        ),
        min_height="100vh"
    )
```

### 6.4 document/list_item.py (문서 목록 아이템)

```python
# frontend/components/document/list_item.py
"""
문서 목록 아이템 컴포넌트
"""

import reflex as rx


def document_list_item(document: dict) -> rx.Component:
    """문서 목록 아이템"""
    
    return rx.link(
        rx.card(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.heading(document["title"], size="md"),
                        rx.spacer(),
                        rx.badge(document["classification"]),
                        width="100%"
                    ),
                    
                    rx.text(
                        document["content"][:200] + "..." if len(document["content"]) > 200 else document["content"],
                        color="gray.600",
                        no_of_lines=2
                    ),
                    
                    rx.hstack(
                        rx.badge(document["category"], color_scheme="green"),
                        rx.text(f"작성자: {document['author_name']}", font_size="sm", color="gray.500"),
                        rx.text(f"버전: {document['version']}", font_size="sm", color="gray.500"),
                        rx.text(f"조회: {document['view_count']}", font_size="sm", color="gray.500"),
                        spacing="3"
                    ),
                    
                    spacing="2",
                    align="start",
                    width="100%"
                ),
                
                rx.icon("chevron-right", size=24, color="gray.400"),
                
                width="100%"
            ),
            padding="4",
            _hover={"background": "gray.50"},
            cursor="pointer"
        ),
        href=f"/documents/{document['id']}",
        width="100%"
    )
```

### 6.5 document/viewer.py (문서 뷰어)

```python
# frontend/components/document/viewer.py
"""
문서 뷰어 컴포넌트
"""

import reflex as rx


def document_viewer(document: dict) -> rx.Component:
    """문서 뷰어 (Markdown 렌더링)"""
    
    return rx.box(
        rx.markdown(document["content"]),
        padding="6",
        border="1px solid",
        border_color="gray.200",
        border_radius="md",
        background="white",
        width="100%"
    )
```

### 6.6 search/search_bar.py (검색바)

```python
# frontend/components/search/search_bar.py
"""
검색바 컴포넌트
"""

import reflex as rx
from frontend.state.search_state import SearchState


def search_bar() -> rx.Component:
    """검색바"""
    
    return rx.form(
        rx.hstack(
            rx.input(
                placeholder="문서 검색...",
                value=SearchState.query,
                on_change=SearchState.set_query,
                size="lg",
                flex="1"
            ),
            rx.button(
                rx.icon("search", margin_right="2"),
                "검색",
                on_click=SearchState.search,
                color_scheme="blue",
                size="lg",
                is_loading=SearchState.is_loading
            ),
            spacing="3",
            width="100%"
        ),
        width="100%",
        on_submit=SearchState.search
    )
```

### 6.7 search/result_item.py (검색 결과 아이템)

```python
# frontend/components/search/result_item.py
"""
검색 결과 아이템 컴포넌트
"""

import reflex as rx


def search_result_item(result: dict) -> rx.Component:
    """검색 결과 아이템"""
    
    return rx.link(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading(result["title"], size="md"),
                    rx.spacer(),
                    rx.badge(result["classification"]),
                    width="100%"
                ),
                
                # 하이라이트된 내용
                rx.text(
                    result.get("highlight", result["content"][:200]),
                    color="gray.600",
                    no_of_lines=2
                ),
                
                rx.hstack(
                    rx.badge(result["category"], color_scheme="green"),
                    rx.text(f"작성자: {result.get('author_name', 'Unknown')}", font_size="sm", color="gray.500"),
                    rx.text(f"점수: {result.get('score', 0):.2f}", font_size="sm", color="gray.500"),
                    spacing="3"
                ),
                
                spacing="2",
                align="start",
                width="100%"
            ),
            padding="4",
            _hover={"background": "gray.50"},
            cursor="pointer"
        ),
        href=f"/documents/{result['doc_id']}",
        width="100%"
    )
```

***

## 7. API 연동

### 7.1 api_client.py (API 클라이언트)

```python
# frontend/services/api_client.py
"""
API 클라이언트

API Gateway와 통신
"""

import httpx
from typing import Dict, Optional, Any
import os


class APIClient:
    """API 클라이언트"""
    
    def __init__(self, token: Optional[str] = None):
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
        """GET 요청"""
        
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
        """POST 요청"""
        
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
        """PUT 요청"""
        
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
        """DELETE 요청"""
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}{path}",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
```

### 7.2 auth_service.py (인증 서비스)

```python
# frontend/services/auth_service.py
"""
인증 서비스
"""

from typing import Dict
from frontend.services.api_client import APIClient


class AuthService:
    """인증 서비스"""
    
    async def create_session(self, user_id: str) -> Dict:
        """세션 생성"""
        
        client = APIClient()
        result = await client.post(
            "/api/v1/sessions",
            json={"user_id": user_id}
        )
        
        if result.get("status") != "success":
            raise Exception(result.get("error", {}).get("message", "세션 생성 실패"))
        
        return result.get("data", {})
    
    async def get_session(self, session_id: str, token: str) -> Dict:
        """세션 조회"""
        
        client = APIClient(token)
        result = await client.get(f"/api/v1/sessions/{session_id}")
        
        if result.get("status") != "success":
            raise Exception(result.get("error", {}).get("message", "세션 조회 실패"))
        
        return result.get("data", {})
    
    async def delete_session(self, session_id: str, token: str):
        """세션 삭제"""
        
        client = APIClient(token)
        result = await client.delete(f"/api/v1/sessions/{session_id}")
        
        if result.get("status") != "success":
            raise Exception(result.get("error", {}).get("message", "세션 삭제 실패"))
```

***

## 8. 스타일링

### 8.1 theme.py (테마)

```python
# frontend/styles/theme.py
"""
애플리케이션 테마
"""

import reflex as rx


# 색상 팔레트
colors = {
    "primary": {
        "50": "#E6F2FF",
        "100": "#BAE0FF",
        "200": "#7CC4FA",
        "300": "#47A3F3",
        "400": "#2186EB",
        "500": "#0967D2",
        "600": "#0552B5",
        "700": "#03449E",
        "800": "#01337D",
        "900": "#002159"
    },
    "gray": {
        "50": "#F7FAFC",
        "100": "#EDF2F7",
        "200": "#E2E8F0",
        "300": "#CBD5E0",
        "400": "#A0AEC0",
        "500": "#718096",
        "600": "#4A5568",
        "700": "#2D3748",
        "800": "#1A202C",
        "900": "#171923"
    }
}


# 테마 설정
theme = rx.theme(
    appearance="light",
    accent_color="blue",
    gray_color="gray",
    radius="medium",
    scaling="100%"
)


# 글로벌 스타일
global_styles = {
    "body": {
        "font_family": "system-ui, -apple-system, sans-serif",
        "background": colors["gray"]["50"]
    },
    "a": {
        "text_decoration": "none",
        "_hover": {
            "text_decoration": "none"
        }
    }
}
```

### 8.2 colors.py (색상)

```python
# frontend/styles/colors.py
"""
색상 상수
"""

# Classification 색상
CLASSIFICATION_COLORS = {
    "public": "blue",
    "team": "green",
    "department": "orange",
    "confidential": "red"
}

# Status 색상
STATUS_COLORS = {
    "draft": "gray",
    "published": "green",
    "archived": "orange"
}

# Role 색상
ROLE_COLORS = {
    "junior": "gray",
    "staff": "blue",
    "manager": "purple",
    "admin": "red"
}
```

***

## 9. 라우팅

### 9.1 app.py (애플리케이션)

```python
# frontend/app.py
"""
Reflex 애플리케이션

라우팅 및 앱 설정
"""

import reflex as rx
from frontend.styles.theme import theme, global_styles

# Pages
from frontend.pages import index, login, dashboard
from frontend.pages.documents import list as doc_list, detail as doc_detail, create as doc_create
from frontend.pages import search


# 앱 생성
app = rx.App(
    theme=theme,
    stylesheets=[],
)

# 라우트 등록
app.add_page(index.index, route="/", title="홈 | MCP Docs")
app.add_page(login.login, route="/login", title="로그인 | MCP Docs")
app.add_page(dashboard.dashboard, route="/dashboard", title="대시보드 | MCP Docs")

# 문서 라우트
app.add_page(doc_list.documents_list, route="/documents", title="문서 목록 | MCP Docs")
app.add_page(doc_detail.document_detail, route="/documents/[doc_id]", title="문서 상세 | MCP Docs")
app.add_page(doc_create.document_create, route="/documents/create", title="문서 생성 | MCP Docs")

# 검색
app.add_page(search.search, route="/search", title="검색 | MCP Docs")
```

***

## 10. 인증 처리

### 10.1 AuthGuard (인증 가드)

```python
# frontend/utils/auth_guard.py
"""
인증 가드

로그인 필요 페이지 보호
"""

import reflex as rx
from frontend.state.auth_state import AuthState


def require_auth(component_fn):
    """인증 필요 데코레이터"""
    
    def wrapper(*args, **kwargs):
        # 인증 확인
        return rx.cond(
            AuthState.is_authenticated,
            component_fn(*args, **kwargs),
            rx.redirect("/login")
        )
    
    return wrapper
```

### 10.2 Protected Page 예시

```python
# 보호된 페이지 예시

from frontend.utils.auth_guard import require_auth

@require_auth
def protected_page():
    return rx.text("보호된 페이지")
```

***

## 11. 배포

### 11.1 rxconfig.py (Reflex 설정)

```python
# frontend/rxconfig.py
"""
Reflex 설정
"""

import reflex as rx


config = rx.Config(
    app_name="frontend",
    api_url="http://localhost:8000",
    deploy_url="https://your-domain.com",
    backend_port=8000,
    frontend_port=3000,
    db_url="sqlite:///reflex.db",
    env=rx.Env.PROD,
)
```

### 11.2 requirements.txt

```txt
# frontend/requirements.txt
# Python 의존성

# Reflex
reflex==0.4.0

# HTTP Client
httpx==0.25.2

# Environment
python-dotenv==1.0.0
```

### 11.3 .env

```bash
# frontend/.env
# 환경 변수

# API Gateway URL
API_GATEWAY_URL=http://localhost:8080

# Reflex
REFLEX_BACKEND_PORT=8000
REFLEX_FRONTEND_PORT=3000
```

### 11.4 Dockerfile

```dockerfile
# frontend/Dockerfile
# Frontend Docker 이미지

FROM python:3.11-slim

# Node.js 설치 (Reflex 필요)
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리
WORKDIR /app

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# Reflex 초기화
RUN reflex init

# 포트 노출
EXPOSE 3000 8000

# 실행
CMD ["reflex", "run", "--env", "prod"]
```

### 11.5 배포 스크립트

```bash
#!/bin/bash
# frontend/deploy.sh
# Frontend 배포 스크립트

set -e

echo "=== Frontend 배포 ==="

# 1. 의존성 설치
echo "의존성 설치..."
pip install -r requirements.txt

# 2. Reflex 초기화
echo "Reflex 초기화..."
reflex init

# 3. 프로덕션 빌드
echo "프로덕션 빌드..."
reflex export

# 4. 배포
echo "배포..."
# 빌드된 파일을 웹 서버로 복사
# cp -r .web/_static/* /var/www/html/

echo "✅ 배포 완료"
```

### 11.6 실행 스크립트

```bash
#!/bin/bash
# frontend/run.sh
# Frontend 실행 스크립트

set -e

# 환경 변수 로드
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Reflex 실행
reflex run
```

***

## 12. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 13. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **작성자** | | | |
| **검토자** | | | |
| **승인자** | | | |

***
