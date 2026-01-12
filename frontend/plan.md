# Frontend 구현 계획서

**프로젝트**: MCP 문서 관리 시스템 - Frontend  
**프레임워크**: Reflex 0.4.0+ (Pure Python Fullstack)  
**작성일**: 2026-01-08  
**목적**: Reflex 프레임워크 기반 Frontend 구현

---

## 목차

1. [개요](#1-개요)
2. [구현 목표](#2-구현-목표)
3. [기술 스택](#3-기술-스택)
4. [프로젝트 구조](#4-프로젝트-구조)
5. [Phase별 구현 계획](#5-phase별-구현-계획)
6. [To-Do List](#6-to-do-list)
7. [진행 상태](#7-진행-상태)

---

## 1. 개요

### 1.1 목적

Reflex 프레임워크를 사용하여 **MCP 문서 관리 시스템의 Frontend**를 구현합니다.

- **Pure Python**: JavaScript 없이 Python만으로 풀스택 개발
- **React 기반**: 내부적으로 React로 컴파일되어 성능 우수
- **실시간 통신**: WebSocket 기반 상태 동기화
- **Chakra UI**: 기본 제공되는 UI 컴포넌트 라이브러리

### 1.2 주요 기능

| 기능 | 설명 |
|------|------|
| **인증 관리** | JWT 토큰 기반 로그인/로그아웃 |
| **문서 CRUD** | 문서 생성, 조회, 수정, 삭제 |
| **검색** | 문서 전문 검색 (API Gateway → MCP Host → Search Server) |
| **권한 기반 UI** | 역할에 따른 메뉴/버튼 노출 제어 |
| **대시보드** | 사용자별 통계 및 최근 문서 |
| **관리자 페이지** | 시스템 통계, 감사 로그 조회 |

### 1.3 API Gateway 연동

```
Frontend (Reflex)
    │
    ▼
API Gateway (FastAPI)
    │
    ├─ /api/v1/sessions      (인증)
    ├─ /api/v1/users         (사용자 정보)
    ├─ /api/v1/documents     (문서 CRUD)
    ├─ /api/v1/tools         (검색 등)
    └─ /api/v1/admin         (관리자)
```

---

## 2. 구현 목표

### 2.1 기능 목표

- [x] **인증 시스템**: 로그인, 로그아웃, 세션 관리
- [x] **문서 관리**: 목록 조회, 상세 보기, 생성, 수정, 삭제
- [x] **검색 기능**: 키워드 기반 문서 검색, 필터링
- [x] **권한 기반 UI**: Role에 따른 메뉴/버튼 제어
- [x] **반응형 디자인**: 다양한 화면 크기 대응
- [x] **에러 처리**: 사용자 친화적 에러 메시지

### 2.2 비기능 목표

- [x] **성능**: 초기 로딩 3초 이내
- [x] **보안**: JWT 토큰 저장 및 자동 갱신
- [x] **UX**: 직관적인 네비게이션, 로딩 상태 표시
- [x] **유지보수성**: State 관리 중앙화, 컴포넌트 재사용

---

## 3. 기술 스택

### 3.1 프레임워크 & 라이브러리

```yaml
Framework: Reflex 0.4.0+
Python: 3.11+
UI Library: Chakra UI (Reflex 기본 제공)
HTTP Client: httpx 0.25+
State Management: Reflex State
Styling: Chakra UI Theme + Custom CSS
Environment: python-dotenv
```

### 3.2 Reflex 특징

| 특징 | 설명 |
|------|------|
| **Pure Python** | JavaScript 없이 Python만으로 개발 |
| **자동 변환** | Python → React 자동 컴파일 |
| **상태 동기화** | WebSocket 기반 실시간 상태 업데이트 |
| **타입 안전** | Python 타입 힌트 지원 |
| **핫 리로드** | 개발 중 자동 새로고침 |

---

## 4. 프로젝트 구조

```
frontend/
├── rxconfig.py                  # Reflex 설정
├── requirements.txt             # Python 의존성
├── .env                         # 환경 변수
├── .env.example                 # 환경 변수 템플릿
├── Dockerfile                   # Docker 이미지
├── docker-compose.yml           # Docker Compose
├── deploy.sh                    # 배포 스크립트
├── run.sh                       # 실행 스크립트
│
├── frontend/                    # 메인 애플리케이션
│   ├── __init__.py
│   ├── app.py                   # 앱 엔트리포인트
│   │
│   ├── state/                   # State 관리
│   │   ├── __init__.py
│   │   ├── base.py             # 기본 State
│   │   ├── auth_state.py       # 인증 상태
│   │   ├── document_state.py   # 문서 상태
│   │   ├── search_state.py     # 검색 상태
│   │   └── ui_state.py         # UI 상태
│   │
│   ├── pages/                   # 페이지
│   │   ├── __init__.py
│   │   ├── index.py            # 홈 (리다이렉트)
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
│   │   │   ├── card.py         # 카드
│   │   │   ├── table.py        # 테이블
│   │   │   ├── modal.py        # 모달
│   │   │   └── loading.py      # 로딩
│   │   │
│   │   ├── document/           # 문서 컴포넌트
│   │   │   ├── __init__.py
│   │   │   ├── list_item.py    # 목록 아이템
│   │   │   ├── viewer.py       # 뷰어
│   │   │   └── editor.py       # 에디터
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
│   │   └── storage_service.py  # 로컬 스토리지
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
└── tests/                       # 테스트 (선택)
    ├── __init__.py
    └── test_components.py
```

**총 파일 수**: 약 **42개** (테스트 제외 시 40개)

---

## 5. Phase별 구현 계획

### Phase 1: 프로젝트 설정 (5개 파일)

**목적**: Reflex 프로젝트 초기화 및 기본 설정

| 파일 | 설명 |
|------|------|
| `rxconfig.py` | Reflex 설정 (포트, DB URL 등) |
| `requirements.txt` | Python 의존성 (reflex, httpx 등) |
| `.env.example` | 환경 변수 템플릿 |
| `frontend/__init__.py` | 패키지 초기화 |
| `frontend/app.py` | Reflex 앱 생성 및 라우트 등록 |

### Phase 2: State 관리 (6개 파일)

**목적**: Reflex State를 이용한 상태 관리

| 파일 | 설명 |
|------|------|
| `state/__init__.py` | State 패키지 |
| `state/base.py` | 기본 State (로딩, 에러 메시지) |
| `state/auth_state.py` | 인증 상태 (토큰, 사용자 정보, 로그인/로그아웃) |
| `state/document_state.py` | 문서 CRUD 상태 (목록, 상세, 생성, 수정, 삭제) |
| `state/search_state.py` | 검색 상태 (쿼리, 결과, 필터) |
| `state/ui_state.py` | UI 상태 (사이드바, 모달 등) |

### Phase 3: Services (4개 파일)

**목적**: API 통신 및 비즈니스 로직

| 파일 | 설명 |
|------|------|
| `services/__init__.py` | Services 패키지 |
| `services/api_client.py` | httpx 기반 API 클라이언트 (GET, POST, PUT, DELETE) |
| `services/auth_service.py` | 인증 서비스 (세션 생성/삭제) |
| `services/storage_service.py` | 로컬 스토리지 (토큰 저장/조회) |

### Phase 4: 컴포넌트 (18개 파일)

**목적**: 재사용 가능한 UI 컴포넌트

#### 4.1 Layout (5개 파일)
- `components/layout/__init__.py`
- `components/layout/header.py` - 헤더 (로고, 네비게이션, 사용자 메뉴)
- `components/layout/sidebar.py` - 사이드바 (메뉴 리스트)
- `components/layout/footer.py` - 푸터
- `components/layout/layout.py` - 전체 레이아웃 (헤더 + 사이드바 + 컨텐츠)

#### 4.2 Common (6개 파일)
- `components/common/__init__.py`
- `components/common/button.py` - 버튼 컴포넌트
- `components/common/card.py` - 카드 컴포넌트
- `components/common/table.py` - 테이블 컴포넌트
- `components/common/modal.py` - 모달 컴포넌트
- `components/common/loading.py` - 로딩 스피너

#### 4.3 Document (4개 파일)
- `components/document/__init__.py`
- `components/document/list_item.py` - 문서 목록 아이템
- `components/document/viewer.py` - Markdown 뷰어
- `components/document/editor.py` - Markdown 에디터

#### 4.4 Search (3개 파일)
- `components/search/__init__.py`
- `components/search/search_bar.py` - 검색바
- `components/search/result_item.py` - 검색 결과 아이템

### Phase 5: 페이지 (13개 파일)

**목적**: 사용자 인터페이스 페이지

#### 5.1 기본 페이지 (4개)
- `pages/__init__.py`
- `pages/index.py` - 홈 (대시보드로 리다이렉트)
- `pages/login.py` - 로그인 페이지
- `pages/dashboard.py` - 대시보드 (통계, 최근 문서)

#### 5.2 문서 페이지 (5개)
- `pages/documents/__init__.py`
- `pages/documents/list.py` - 문서 목록 (페이징, 필터링)
- `pages/documents/detail.py` - 문서 상세 (Markdown 렌더링)
- `pages/documents/create.py` - 문서 생성 폼
- `pages/documents/edit.py` - 문서 수정 폼

#### 5.3 검색 & 관리자 (4개)
- `pages/search.py` - 검색 페이지
- `pages/admin/__init__.py`
- `pages/admin/users.py` - 사용자 관리 (목록, 권한 부여)
- `pages/admin/stats.py` - 시스템 통계, 감사 로그

### Phase 6: 유틸리티 & 스타일 (7개 파일)

**목적**: 헬퍼 함수 및 테마

| 파일 | 설명 |
|------|------|
| `utils/__init__.py` | Utils 패키지 |
| `utils/constants.py` | 상수 (API URL, 역할, 분류 색상) |
| `utils/validators.py` | 유효성 검증 (이메일, 필수 필드) |
| `utils/formatters.py` | 포맷터 (날짜, 파일 크기) |
| `styles/__init__.py` | Styles 패키지 |
| `styles/theme.py` | Chakra UI 테마 커스터마이징 |
| `styles/colors.py` | 색상 팔레트 (Classification, Role 색상) |

### Phase 7: 배포 (4개 파일)

**목적**: Docker 배포 및 실행 스크립트

| 파일 | 설명 |
|------|------|
| `Dockerfile` | Python 3.11 + Node.js + Reflex |
| `docker-compose.yml` | Frontend 서비스 정의 |
| `deploy.sh` | 배포 자동화 스크립트 |
| `run.sh` | 로컬 실행 스크립트 |

---

## 6. To-Do List

### Phase 1: 프로젝트 설정

- [x] **rxconfig.py** - Reflex 설정 파일
  - [x] app_name, api_url, deploy_url 설정
  - [x] backend_port=8000, frontend_port=3000
  - [x] db_url (SQLite)

- [x] **requirements.txt** - Python 의존성
  - [x] reflex==0.4.0
  - [x] httpx==0.25.2
  - [x] python-dotenv==1.0.0

- [x] **.env.example** - 환경 변수 템플릿
  - [x] API_GATEWAY_URL (기본값: http://localhost:8080)
  - [x] REFLEX_BACKEND_PORT, REFLEX_FRONTEND_PORT

- [x] **frontend/__init__.py** - 패키지 초기화

- [x] **frontend/app.py** - Reflex 앱 엔트리포인트
  - [x] rx.App() 생성
  - [x] theme 설정
  - [x] 라우트 등록 (add_page)

---

### Phase 2: State 관리

- [x] **state/__init__.py** - State 패키지

- [x] **state/base.py** - 기본 State
  - [x] BaseState 클래스 (rx.State 상속)
  - [x] is_loading: bool
  - [x] error_message: str
  - [x] success_message: str
  - [x] set_loading(), set_error(), set_success(), clear_messages()

- [x] **state/auth_state.py** - 인증 상태
  - [x] AuthState 클래스 (BaseState 상속)
  - [x] is_authenticated: bool
  - [x] user: Dict (user_id, name, role, team)
  - [x] session_id: str
  - [x] token: str
  - [x] user_id: str (로그인 폼)
  - [x] set_user_id()
  - [x] async login() - POST /api/v1/sessions
  - [x] async logout() - DELETE /api/v1/sessions/{session_id}
  - [x] async check_auth() - 로컬 스토리지에서 토큰 확인

- [x] **state/document_state.py** - 문서 상태
  - [x] DocumentState 클래스 (BaseState 상속)
  - [x] documents: List[Dict]
  - [x] current_document: Dict
  - [x] total: int
  - [x] page: int, page_size: int
  - [x] classification: str, category: str (필터)
  - [x] doc_title, doc_content, doc_classification, doc_category, doc_tags (폼)
  - [x] set_page(), set_classification(), set_category()
  - [x] set_doc_title(), set_doc_content(), set_doc_classification(), set_doc_category(), set_doc_tags()
  - [x] async load_documents() - GET /api/v1/documents
  - [x] async load_document(doc_id) - GET /api/v1/documents/{doc_id}
  - [x] async create_document() - POST /api/v1/documents
  - [x] async delete_document(doc_id) - DELETE /api/v1/documents/{doc_id}

- [x] **state/search_state.py** - 검색 상태
  - [x] SearchState 클래스 (BaseState 상속)
  - [x] query: str
  - [x] results: List[Dict]
  - [x] total: int
  - [x] classification_filter: List[str]
  - [x] category_filter: str
  - [x] set_query(), set_category_filter()
  - [x] async search() - POST /api/v1/tools/execute (tool="search_documents")
  - [x] clear_search()

- [x] **state/ui_state.py** - UI 상태
  - [x] UIState 클래스 (rx.State 상속)
  - [x] sidebar_open: bool
  - [x] modal_open: bool
  - [x] toggle_sidebar()
  - [x] open_modal(), close_modal()

---

### Phase 3: Services

- [x] **services/__init__.py** - Services 패키지

- [x] **services/api_client.py** - API 클라이언트
  - [x] APIClient 클래스
  - [x] __init__(token: Optional[str])
  - [x] base_url: str (환경 변수에서 로드)
  - [x] timeout: float = 30.0
  - [x] _get_headers() - Authorization 헤더 생성
  - [x] async get(path, params) - httpx.AsyncClient
  - [x] async post(path, json)
  - [x] async put(path, json)
  - [x] async delete(path)

- [x] **services/auth_service.py** - 인증 서비스
  - [x] AuthService 클래스
  - [x] async create_session(user_id) - POST /api/v1/sessions
  - [x] async get_session(session_id, token) - GET /api/v1/sessions/{session_id}
  - [x] async delete_session(session_id, token) - DELETE /api/v1/sessions/{session_id}

- [x] **services/storage_service.py** - 로컬 스토리지
  - [x] StorageService 클래스
  - [x] set_token(token)
  - [x] get_token() -> Optional[str]
  - [x] remove_token()
  - [x] set_session_id(session_id)
  - [x] get_session_id() -> Optional[str]
  - [x] remove_session_id()

---

### Phase 4: 컴포넌트

#### 4.1 Layout

- [x] **components/layout/__init__.py**

- [x] **components/layout/header.py** - 헤더
  - [x] header() -> rx.Component
  - [x] 로고 (파일 아이콘 + "MCP Docs")
  - [x] 네비게이션 (대시보드, 문서, 검색)
  - [x] 사용자 메뉴 (Avatar + 드롭다운: 내 정보, 로그아웃)
  - [x] rx.cond(AuthState.is_authenticated) 조건부 렌더링

- [x] **components/layout/sidebar.py** - 사이드바
  - [x] sidebar() -> rx.Component
  - [x] 네비게이션 링크 (홈, 대시보드, 문서, 검색)
  - [x] Admin 메뉴 (rx.cond(AuthState.user["role"] == "admin"))
  - [x] Hover 효과 (_hover={"background": "gray.100"})

- [x] **components/layout/footer.py** - 푸터
  - [x] footer() -> rx.Component
  - [x] 저작권 정보
  - [x] 링크 (도움말, 문의)

- [x] **components/layout/layout.py** - 전체 레이아웃
  - [x] layout(*children, show_sidebar: bool = True) -> rx.Component
  - [x] header() 포함
  - [x] rx.cond(AuthState.is_authenticated and show_sidebar, sidebar(), rx.box())
  - [x] 메인 컨텐츠 영역 (flex="1")

#### 4.2 Common

- [x] **components/common/__init__.py**

- [x] **components/common/button.py** - 버튼
  - [x] primary_button(text, on_click, **kwargs)
  - [x] secondary_button(text, on_click, **kwargs)
  - [x] danger_button(text, on_click, **kwargs)

- [x] **components/common/card.py** - 카드
  - [x] card(*children, **kwargs) -> rx.Component
  - [x] padding, border, border_radius, background

- [x] **components/common/table.py** - 테이블
  - [x] data_table(headers: List[str], rows: List[List], **kwargs)
  - [x] rx.table() 기반

- [x] **components/common/modal.py** - 모달
  - [x] modal(is_open, on_close, title, *children) -> rx.Component
  - [x] rx.modal(), rx.modal_overlay(), rx.modal_content()

- [x] **components/common/loading.py** - 로딩
  - [x] loading_spinner(size="xl") -> rx.Component
  - [x] full_page_loading() -> rx.Component (화면 중앙 스피너)

#### 4.3 Document

- [x] **components/document/__init__.py**

- [x] **components/document/list_item.py** - 문서 목록 아이템
  - [x] document_list_item(document: dict) -> rx.Component
  - [x] rx.link + rx.card
  - [x] 제목, 내용 미리보기 (200자)
  - [x] 배지 (classification, category)
  - [x] 메타 정보 (작성자, 버전, 조회수)

- [x] **components/document/viewer.py** - Markdown 뷰어
  - [x] document_viewer(document: dict) -> rx.Component
  - [x] rx.markdown(document["content"])
  - [x] 스타일링 (border, padding)

- [x] **components/document/editor.py** - Markdown 에디터
  - [x] document_editor(value, on_change) -> rx.Component
  - [x] rx.text_area(min_height="400px")
  - [x] Markdown 미리보기 (선택)

#### 4.4 Search

- [x] **components/search/__init__.py**

- [x] **components/search/search_bar.py** - 검색바
  - [x] search_bar() -> rx.Component
  - [x] rx.input (SearchState.query)
  - [x] rx.button("검색", on_click=SearchState.search)
  - [x] rx.form (on_submit=SearchState.search)

- [x] **components/search/result_item.py** - 검색 결과 아이템
  - [x] search_result_item(result: dict) -> rx.Component
  - [x] rx.link + rx.card
  - [x] 하이라이트된 내용 (result.get("highlight"))
  - [x] 점수 표시 (result.get("score"))

---

### Phase 5: 페이지

#### 5.1 기본 페이지

- [x] **pages/__init__.py**

- [x] **pages/index.py** - 홈
  - [x] index() -> rx.Component
  - [x] layout() 사용
  - [x] 시스템 소개 (헤더, 주요 기능 카드)
  - [x] CTA 버튼 ("시작하기" → /login)

- [x] **pages/login.py** - 로그인
  - [x] login() -> rx.Component
  - [x] 중앙 정렬 (rx.center)
  - [x] 로그인 폼 (rx.form_control)
  - [x] 사용자 ID 입력 (AuthState.user_id)
  - [x] 로그인 버튼 (AuthState.login)
  - [x] 에러/성공 메시지 (rx.cond)

- [x] **pages/dashboard.py** - 대시보드
  - [x] dashboard() -> rx.Component
  - [x] layout() 사용
  - [x] 환영 메시지 (AuthState.user["name"])
  - [x] 통계 카드 (내 문서, 오늘 조회, 최근 수정)
  - [x] 최근 문서 목록
  - [x] 빠른 액션 (새 문서, 검색)

#### 5.2 문서 페이지

- [x] **pages/documents/__init__.py**

- [x] **pages/documents/list.py** - 문서 목록
  - [x] documents_list() -> rx.Component
  - [x] layout() 사용
  - [x] 헤더 (제목 + "새 문서" 버튼)
  - [x] 필터 (공개 범위, 카테고리)
  - [x] rx.cond(DocumentState.is_loading, loading, document_list)
  - [x] rx.foreach(DocumentState.documents, document_list_item)
  - [x] 페이지네이션 (이전/다음 버튼)
  - [x] on_mount=DocumentState.load_documents

- [x] **pages/documents/detail.py** - 문서 상세
  - [x] document_detail(doc_id: str) -> rx.Component
  - [x] layout() 사용
  - [x] 헤더 (뒤로가기, 제목, 수정/삭제 버튼)
  - [x] 메타 정보 (배지, 작성자, 버전)
  - [x] document_viewer(DocumentState.current_document)
  - [x] on_mount=DocumentState.load_document(doc_id)

- [x] **pages/documents/create.py** - 문서 생성
  - [x] document_create() -> rx.Component
  - [x] layout() 사용
  - [x] 헤더 (뒤로가기, "새 문서 작성")
  - [x] 문서 폼 (제목, 공개 범위, 카테고리, 태그, 내용)
  - [x] rx.form_control (is_required=True)
  - [x] rx.text_area (Markdown 입력, min_height="400px")
  - [x] 버튼 (취소, 생성)

- [x] **pages/documents/edit.py** - 문서 수정
  - [x] document_edit(doc_id: str) -> rx.Component
  - [x] layout() 사용
  - [x] create.py와 유사하지만 기존 데이터 로드
  - [x] on_mount=DocumentState.load_document(doc_id)
  - [x] async update_document() 구현

#### 5.3 검색 & 관리자

- [x] **pages/search.py** - 검색
  - [x] search() -> rx.Component
  - [x] layout() 사용
  - [x] search_bar() 컴포넌트
  - [x] 필터 (카테고리)
  - [x] rx.cond(SearchState.is_loading, loading, results)
  - [x] rx.cond(SearchState.total > 0, result_list, "검색 결과가 없습니다")
  - [x] rx.foreach(SearchState.results, search_result_item)

- [x] **pages/admin/__init__.py**

- [x] **pages/admin/users.py** - 사용자 관리
  - [x] admin_users() -> rx.Component
  - [x] layout() 사용
  - [x] 사용자 목록 테이블
  - [x] 권한 부여 버튼 (AdminState.grant_permission)
  - [x] rx.cond(AuthState.user["role"] == "admin") 권한 체크

- [x] **pages/admin/stats.py** - 통계
  - [x] admin_stats() -> rx.Component
  - [x] layout() 사용
  - [x] 시스템 통계 (GET /api/v1/admin/stats)
  - [x] 감사 로그 목록 (GET /api/v1/admin/audit-logs)
  - [x] 차트 (선택 사항)

---

### Phase 6: 유틸리티 & 스타일

- [x] **utils/__init__.py**

- [x] **utils/constants.py** - 상수
  - [x] API_BASE_URL
  - [x] ROLES = ["junior", "staff", "manager", "executive", "admin"]
  - [x] CLASSIFICATION_COLORS = {"public": "blue", "team": "green", ...}
  - [x] ROLE_COLORS = {"junior": "gray", "staff": "blue", ...}

- [x] **utils/validators.py** - 검증
  - [x] validate_required(value, field_name) -> bool
  - [x] validate_email(email) -> bool
  - [x] validate_document_form(title, content) -> Tuple[bool, str]

- [x] **utils/formatters.py** - 포맷터
  - [x] format_date(date_str) -> str ("YYYY-MM-DD HH:MM")
  - [x] format_file_size(bytes) -> str ("1.2 MB")
  - [x] format_time_ago(date_str) -> str ("2시간 전")

- [x] **styles/__init__.py**

- [x] **styles/theme.py** - 테마
  - [x] colors = {...} (primary, gray 팔레트)
  - [x] theme = rx.theme(appearance="light", accent_color="blue", ...)
  - [x] global_styles = {...} (body, a 스타일)

- [x] **styles/colors.py** - 색상
  - [x] CLASSIFICATION_COLORS
  - [x] STATUS_COLORS = {"draft": "gray", "published": "green", ...}
  - [x] ROLE_COLORS

---

### Phase 7: 배포

- [x] **Dockerfile** - Docker 이미지
  - [x] FROM python:3.11-slim
  - [x] Node.js 18.x 설치 (Reflex 필요)
  - [x] WORKDIR /app
  - [x] requirements.txt 복사 및 pip install
  - [x] 애플리케이션 복사
  - [x] reflex init
  - [x] EXPOSE 3000 8000
  - [x] CMD ["reflex", "run", "--env", "prod"]

- [x] **docker-compose.yml** - Docker Compose
  - [x] services:
    - [x] frontend:
      - [ ] build: .
      - [ ] ports: ["3000:3000", "8000:8000"]
      - [ ] environment: API_GATEWAY_URL=http://api-gateway:8080
      - [ ] depends_on: [api-gateway]

- [x] **deploy.sh** - 배포 스크립트
  - [x] #!/bin/bash
  - [x] pip install -r requirements.txt
  - [x] reflex init
  - [x] reflex export (프로덕션 빌드)
  - [x] 정적 파일 복사 (선택)
  - [x] chmod +x deploy.sh

- [x] **run.sh** - 실행 스크립트
  - [x] #!/bin/bash
  - [x] .env 로드
  - [x] reflex run
  - [x] chmod +x run.sh

---

## 7. 진행 상태

### 7.1 Phase별 진행률

| Phase | 설명 | 파일 수 | 상태 | 진행률 |
|-------|------|---------|------|--------|
| **Phase 1** | 프로젝트 설정 | 5 | ✅ 완료 | 100% |
| **Phase 2** | State 관리 | 6 | ✅ 완료 | 100% |
| **Phase 3** | Services | 4 | ✅ 완료 | 100% |
| **Phase 4** | 컴포넌트 | 18 | ✅ 완료 | 100% |
| **Phase 5** | 페이지 | 13 | ✅ 완료 | 100% |
| **Phase 6** | 유틸리티 & 스타일 | 7 | ✅ 완료 | 100% |
| **Phase 7** | 배포 | 4 | ✅ 완료 | 100% |
| **전체** | - | **57** | ✅ 완료 | **100%** |

### 7.2 API 연동 체크리스트

| API | Method | Endpoint | State | 상태 |
|-----|--------|----------|-------|------|
| 세션 생성 | POST | `/api/v1/sessions` | AuthState.login | ✅ |
| 세션 조회 | GET | `/api/v1/sessions/{id}` | AuthState.check_auth | ✅ |
| 세션 삭제 | DELETE | `/api/v1/sessions/{id}` | AuthState.logout | ✅ |
| 문서 목록 | GET | `/api/v1/documents` | DocumentState.load_documents | ✅ |
| 문서 조회 | GET | `/api/v1/documents/{id}` | DocumentState.load_document | ✅ |
| 문서 생성 | POST | `/api/v1/documents` | DocumentState.create_document | ✅ |
| 문서 삭제 | DELETE | `/api/v1/documents/{id}` | DocumentState.delete_document | ✅ |
| 검색 | POST | `/api/v1/tools/execute` | SearchState.search | ✅ |
| 시스템 통계 | GET | `/api/v1/admin/stats` | AdminState | ✅ |

### 7.3 주요 마일스톤

- [x] **M1**: Phase 1-2 완료 (프로젝트 설정 + State) - 로그인 가능
- [x] **M2**: Phase 3-4 완료 (Services + 컴포넌트) - UI 구조 완성
- [x] **M3**: Phase 5 완료 (페이지) - 모든 기능 구현
- [x] **M4**: Phase 6-7 완료 (스타일 + 배포) - 프로덕션 준비

---

## 8. 구현 세부 사항

### 8.1 Reflex State 패턴

```python
# State 정의
class AuthState(BaseState):
    is_authenticated: bool = False
    user: Dict = {}
    
    async def login(self):
        # API 호출
        result = await api_client.post("/api/v1/sessions", ...)
        # 상태 업데이트
        self.is_authenticated = True
        self.user = result["user"]

# 컴포넌트에서 사용
def login_page():
    return rx.button(
        "로그인",
        on_click=AuthState.login  # State 메서드 직접 바인딩
    )
```

### 8.2 조건부 렌더링

```python
# 인증 여부에 따라 UI 변경
rx.cond(
    AuthState.is_authenticated,
    rx.text(f"환영합니다, {AuthState.user['name']}님"),
    rx.button("로그인", on_click=rx.redirect("/login"))
)
```

### 8.3 라우트 등록

```python
# app.py
app = rx.App(theme=theme)

# 페이지 등록
app.add_page(index, route="/", title="홈")
app.add_page(login, route="/login", title="로그인")
app.add_page(document_detail, route="/documents/[doc_id]", title="문서 상세")
```

### 8.4 API 클라이언트 패턴

```python
# services/api_client.py
class APIClient:
    def __init__(self, token: Optional[str] = None):
        self.base_url = os.getenv("API_GATEWAY_URL")
        self.token = token
    
    async def get(self, path, params=None):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {self.token}"},
                params=params,
                timeout=30.0
            )
            return response.json()
```

---

## 9. 다음 단계

1. **Phase 1 시작**: `rxconfig.py`, `requirements.txt`, `app.py` 생성
2. **Reflex 초기화**: `reflex init` 실행
3. **Phase 2 구현**: State 관리 클래스 작성
4. **API 연동 테스트**: 로그인 기능 먼저 구현 및 테스트
5. **순차적 구현**: Phase 3 → 7 순서대로 진행

---

## 10. 참고 자료

- **Reflex 공식 문서**: https://reflex.dev/docs
- **Chakra UI**: https://chakra-ui.com/
- **API Gateway SR.md**: `/app/poc/mcps/api-gateway/SR.md`
- **Frontend SR.md**: `/app/poc/mcps/frontend/SR.md`

---

## 11. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

---

## 12. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **작성자** | | | |
| **검토자** | | | |
| **승인자** | | | |

---

**✅ 이 계획서를 To-Do List로 관리하여 체계적으로 Frontend를 구현하세요!**
