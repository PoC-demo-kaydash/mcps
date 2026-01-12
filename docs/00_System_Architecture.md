# 시스템 아키텍처 및 기술스택 설계서

***

# 00. MCP 에코시스템 - 시스템 아키텍처 및 기술스택 설계서

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/`  
**목적**: 전체 시스템의 아키텍처, 기술 스택, 데이터 흐름, 배포 전략 정의

***

## 1. 개요

### 1.1 프로젝트 목적

**MCP 에코시스템**은 망분리 환경에서 동작하는 엔터프라이즈급 문서 관리 시스템입니다. Model Context Protocol (MCP)을 기반으로 다양한 Tool과 Server를 동적으로 관리하며, 역할 기반 접근 제어(RBAC)를 통해 안전한 문서 관리를 제공합니다.

**핵심 목표**:
- ✅ 망분리 환경에서 외부 네트워크 없이 완전 독립 실행
- ✅ 역할별 문서 접근 제어 (public, team, confidential)
- ✅ 동적 Tool/Server 등록 및 관리
- ✅ 전문 검색 엔진 기반 빠른 문서 검색
- ✅ 감사 로그를 통한 모든 활동 추적
- ✅ 외부 AI Agent 연동 API 제공

### 1.2 주요 기능

1. **문서 관리**
   - 문서 생성/수정/삭제/조회
   - 파일 첨부 (Markdown, PDF, 텍스트)
   - 버전 관리 (히스토리 추적)
   - 문서 등급별 접근 제어

2. **검색**
   - Elasticsearch 기반 전문 검색
   - 한글 형태소 분석 (nori tokenizer)
   - 권한 필터링 (사용자 역할 기반)
   - 하이라이트 및 스니펫

3. **권한 관리**
   - 5단계 역할 (junior, staff, manager, executive, admin)
   - Tool/Server 실행 권한
   - 문서 접근 권한
   - 접근 요청 승인 워크플로우

4. **Tool/Server 관리**
   - 동적 Tool 등록/해제
   - MCP Server 상태 모니터링
   - Tool 실행 통계
   - YAML 기반 메타데이터

5. **감사 및 로깅**
   - 모든 사용자 활동 기록
   - Tool 실행 로그
   - 문서 접근 로그
   - 시스템 이벤트 로그

6. **외부 연동**
   - REST API (타 부서 AI Agent 연동)
   - JWT 인증
   - Rate Limiting
   - API 문서 (OpenAPI/Swagger)

### 1.3 제약 사항

| 제약 사항 | 설명 | 해결 방법 |
|----------|------|----------|
| **망분리 환경** | 외부 인터넷 연결 불가 | 모든 패키지 사전 설치, tarball 배포 |
| **단일 서버** | 초기 배포는 1대 서버 | 향후 수평 확장 가능한 구조 설계 |
| **Python 3.10+** | RHEL8 기본 Python 버전 | venv 사용, 패키지 호환성 확인 |
| **제한된 리소스** | CPU 8코어, 메모리 32GB | 경량 아키텍처, 효율적 자원 사용 |
| **보안 요구사항** | 내부 보안 정책 준수 | JWT, RBAC, SQL Injection 방지 |

### 1.4 대상 사용자

| 역할 | 인원 | 주요 활동 |
|------|------|----------|
| **Junior** | 10명 | Public 문서 조회, 기본 검색 |
| **Staff** | 15명 | Public/Team 문서 조회/생성, 고급 검색 |
| **Manager** | 8명 | 팀 문서 관리, 권한 승인 |
| **Executive** | 3명 | 전체 문서 조회 (confidential 포함) |
| **Admin** | 2명 | 시스템 관리, Tool/Server 관리 |

**총 예상 사용자**: 38명 (동시 접속 최대 20명)

***

## 2. 시스템 아키텍처

### 2.1 전체 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                        외부 AI Agent (타 부서)                    │
│                    (REST API 호출, JWT 인증)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS (외부망)
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                     API Gateway (FastAPI)                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │   인증      │  │Rate Limiting│ │   라우팅    │                │
│  │Middleware  │  │  Middleware │ │   Router   │                │
│  └────────────┘  └────────────┘  └────────────┘                │
│  - JWT 검증                                                      │
│  - 요청/응답 로깅                                                │
│  - CORS 처리                                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP (내부망)
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Frontend   │  │  MCP Host    │  │   Scripts    │
│   (Reflex)   │  │  (FastAPI)   │  │   (Bash/Py)  │
│              │  │              │  │              │
│ - UI/UX      │  │ - Tool       │  │ - 배포       │
│ - 상태관리    │  │   Registry   │  │ - 초기화     │
│ - API 호출   │  │ - Server     │  │ - 백업       │
│              │  │   Manager    │  │              │
└──────┬───────┘  └──────┬───────┘  └──────────────┘
       │                 │
       │                 │ STDIO (JSON-RPC)
       │                 │
       │        ┌────────┼────────┬────────┬────────┐
       │        ▼        ▼        ▼        ▼        ▼
       │   ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
       │   │ Auth   ││Search  ││Document││Version ││ Audit  │
       │   │ Server ││ Server ││ Server ││ Server ││ Server │
       │   └────┬───┘└────┬───┘└────┬───┘└────┬───┘└────┬───┘
       │        │         │         │         │         │
       │        └─────────┴─────────┴─────────┴─────────┘
       │                          │
       └──────────────────────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
          ┌────────────┐  ┌────────────┐  ┌────────────┐
          │  MariaDB   │  │Elasticsearch│ │File System │
          │            │  │            │  │            │
          │ - 사용자    │  │ - 문서색인  │  │ - 문서파일  │
          │ - 문서정보  │  │ - 로그색인  │  │ - 첨부파일  │
          │ - 권한     │  │ - 검색API  │  │ - 로그파일  │
          │ - 감사로그  │  │            │  │            │
          └────────────┘  └────────────┘  └────────────┘
```

### 2.2 3-Tier 아키텍처

#### Tier 1: Presentation Layer (프레젠테이션 계층)

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐         ┌──────────────────┐     │
│  │  Reflex Frontend │         │   API Gateway    │     │
│  │                  │         │                  │     │
│  │  - 웹 UI         │         │  - REST API      │     │
│  │  - 상태 관리     │◄────────┤  - JWT 인증      │     │
│  │  - 페이지 라우팅 │         │  - Rate Limiting │     │
│  │  - 컴포넌트      │         │  - 라우팅        │     │
│  └──────────────────┘         └──────────────────┘     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**역할**:
- 사용자 인터페이스 제공
- 외부 AI Agent API 제공
- 인증/인가 처리
- 요청 라우팅

**기술 스택**:
- Reflex 0.4+ (Python Web Framework)
- FastAPI 0.109+ (API Gateway)
- JWT (JSON Web Tokens)

#### Tier 2: Business Logic Layer (비즈니스 로직 계층)

```
┌─────────────────────────────────────────────────────────┐
│                 Business Logic Layer                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────┐       │
│  │             MCP Host (Core)                  │       │
│  │                                              │       │
│  │  ┌────────────────┐    ┌────────────────┐   │       │
│  │  │ Tool Registry  │    │ Server Manager │   │       │
│  │  │                │    │                │   │       │
│  │  │ - 동적 등록    │    │ - STDIO 통신   │   │       │
│  │  │ - 메타데이터   │    │ - 프로세스관리 │   │       │
│  │  │ - 검색         │    │ - 헬스체크     │   │       │
│  │  └────────────────┘    └────────────────┘   │       │
│  │                                              │       │
│  │  ┌────────────────┐    ┌────────────────┐   │       │
│  │  │Permission      │    │  Audit Logger  │   │       │
│  │  │Engine          │    │                │   │       │
│  │  │                │    │ - 활동기록     │   │       │
│  │  │ - RBAC         │    │ - DB/ES 저장   │   │       │
│  │  │ - 권한체크     │    │                │   │       │
│  │  └────────────────┘    └────────────────┘   │       │
│  │                                              │       │
│  └──────────────────────────────────────────────┘       │
│                                                          │
│  ┌──────────────────────────────────────────────┐       │
│  │          MCP Servers (Workers)               │       │
│  │                                              │       │
│  │  [Auth] [Search] [Document] [Version] [Audit]│       │
│  │                                              │       │
│  │  - Tool 실행                                 │       │
│  │  - 비즈니스 로직                             │       │
│  │  - 데이터 처리                               │       │
│  └──────────────────────────────────────────────┘       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**역할**:
- Tool 오케스트레이션
- 권한 엔진
- 비즈니스 로직 실행
- 감사 로깅

**기술 스택**:
- Python 3.10+
- FastAPI (MCP Host)
- subprocess (MCP Server 관리)
- JSON-RPC over STDIO

#### Tier 3: Data Layer (데이터 계층)

```
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   MariaDB    │  │Elasticsearch │  │ File System  │  │
│  │              │  │              │  │              │  │
│  │ - users      │  │ - documents  │  │ /documents/  │  │
│  │ - documents  │  │   (index)    │  │   public/    │  │
│  │ - permissions│  │              │  │   team/      │  │
│  │ - tools      │  │ - audit_logs │  │   confid*/   │  │
│  │ - servers    │  │   (index)    │  │              │  │
│  │ - audit_logs │  │              │  │ /logs/       │  │
│  │ - versions   │  │ - 한글분석기  │  │   *.log      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**역할**:
- 구조화된 데이터 저장 (MariaDB)
- 전문 검색 (Elasticsearch)
- 파일 저장 (File System)

**기술 스택**:
- MariaDB 10.11
- Elasticsearch 8.x
- Linux File System (ext4)

### 2.3 데이터 흐름

#### 2.3.1 문서 검색 플로우

```
[사용자] 
   │
   │ 1. 검색어 입력
   │
   ▼
[Frontend - Search Page]
   │
   │ 2. POST /api/search
   │    { "query": "예산", "user_id": "U001" }
   │
   ▼
[API Gateway]
   │
   │ 3. JWT 검증
   │ 4. Rate Limiting 체크
   │
   ▼
[MCP Host]
   │
   │ 5. 권한 확인
   │    permission_engine.get_accessible_documents(U001)
   │    → MariaDB 쿼리
   │
   ▼
[Permission Engine] ──────┐
   │                      │
   │ 6. 역할 조회         │ SELECT role, team 
   │    role: staff       │ FROM users 
   │    team: dev_team    │ WHERE id = 'U001'
   │                      │
   │◄─────────────────────┘
   │
   │ 7. Tool 호출 요청
   │    call_tool("search_server", "search_documents", {...})
   │
   ▼
[Server Manager]
   │
   │ 8. STDIO 통신
   │    JSON-RPC Request:
   │    {
   │      "method": "tools/call",
   │      "params": {
   │        "name": "search_documents",
   │        "arguments": {
   │          "query": "예산",
   │          "classification": ["public", "team"],
   │          "team": "dev_team"
   │        }
   │      }
   │    }
   │
   ▼
[Search Server]
   │
   │ 9. Elasticsearch 쿼리
   │    {
   │      "query": {
   │        "bool": {
   │          "must": [{"match": {"content": "예산"}}],
   │          "filter": [
   │            {"terms": {"classification": ["public", "team"]}},
   │            {"term": {"team": "dev_team"}}
   │          ]
   │        }
   │      },
   │      "highlight": {"fields": {"content": {}}}
   │    }
   │
   ▼
[Elasticsearch] ───────────┐
   │                       │
   │ 10. 검색 실행         │ documents index
   │     결과 반환         │ - 5건 매칭
   │                       │
   │◄──────────────────────┘
   │
   │ 11. JSON-RPC Response
   │     { "result": { "total": 5, "hits": [...] } }
   │
   ▼
[Server Manager]
   │
   │ 12. 결과 파싱
   │
   ▼
[MCP Host]
   │
   │ 13. 감사 로그 기록
   │     audit_logger.log(user_id, action="search", ...)
   │
   ▼
[Audit Logger] ────────────┐
   │                       │
   │ 14. DB 저장           │ INSERT INTO audit_logs
   │     ES 색인           │ (user_id, action, timestamp, ...)
   │                       │
   │◄──────────────────────┤ MariaDB
   │                       │ Elasticsearch
   │                       │
   │                       │
   ▼                       │
[API Gateway]              │
   │                       │
   │ 15. 응답 반환         │
   │     { "results": [...], "total": 5 }
   │                       │
   ▼                       │
[Frontend]                 │
   │                       │
   │ 16. 결과 표시         │
   │     - 문서 카드       │
   │     - 하이라이트      │
   │                       │
   ▼                       │
[사용자]                   │
```

#### 2.3.2 문서 생성 플로우

```
[사용자]
   │
   │ 1. 문서 작성
   │    title: "2026 예산 계획"
   │    content: "..."
   │    classification: "team"
   │
   ▼
[Frontend - Document Page]
   │
   │ 2. POST /api/documents/create
   │
   ▼
[API Gateway] → [MCP Host]
   │
   │ 3. 권한 확인
   │    can_create_document(user_id, classification="team")
   │
   ▼
[Permission Engine] → MariaDB
   │
   │ 4. Tool 호출
   │    call_tool("document_server", "create_document", {...})
   │
   ▼
[Document Server]
   │
   │ 5. DB 저장
   ├────────────────────┐
   │                    │
   ▼                    ▼
[MariaDB]         [Elasticsearch]
   │                    │
   │ INSERT INTO        │ Index Document
   │ documents          │ {
   │ (id, title,        │   "doc_id": "DOC001",
   │  content,          │   "title": "...",
   │  classification,   │   "content": "...",
   │  author_id, ...)   │   ...
   │                    │ }
   │                    │
   │ 6. 트랜잭션 커밋   │
   │                    │
   └────────────────────┘
   │
   │ 7. 파일 저장 (선택)
   │
   ▼
[File System]
   │
   │ /data/documents/team/dev_team/DOC001.md
   │
   │
   │ 8. 응답 반환
   │
   ▼
[사용자] (문서 생성 완료)
```

#### 2.3.3 외부 AI Agent 연동 플로우

```
[외부 AI Agent (타 부서)]
   │
   │ 1. API 호출 (JWT 토큰 포함)
   │    POST /api/external/execute_tool
   │    Authorization: Bearer eyJhbGc...
   │    {
   │      "tool_name": "search_documents",
   │      "params": {"query": "계약서"}
   │    }
   │
   ▼
[API Gateway]
   │
   │ 2. JWT 검증
   │    - 서명 확인
   │    - 만료 시간 확인
   │    - 권한 스코프 확인
   │
   │ 3. Rate Limiting
   │    - 부서별 요청 제한 (100 req/min)
   │
   ▼
[MCP Host]
   │
   │ 4. Tool 실행 (내부와 동일)
   │
   ▼
[응답 반환]
   │
   │ {
   │   "result": {...},
   │   "execution_time_ms": 245,
   │   "request_id": "req_abc123"
   │ }
   │
   ▼
[외부 AI Agent]
```

### 2.4 네트워크 구조

#### 2.4.1 망분리 환경 (Air-Gapped)

```
┌─────────────────────────────────────────────────────────────┐
│                       격리된 내부망                          │
│  (외부 인터넷 연결 없음)                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Application Server (192.168.1.100)              │       │
│  │                                                  │       │
│  │  Ports:                                          │       │
│  │  - 8501: Reflex Frontend                         │       │
│  │  - 8000: API Gateway                             │       │
│  │  - 8080: MCP Host (internal)                     │       │
│  │                                                  │       │
│  │  Services:                                       │       │
│  │  - frontend (Reflex)                             │       │
│  │  - api-gateway (FastAPI)                         │       │
│  │  - mcp-host (FastAPI)                            │       │
│  │  - mcp-servers (5개 프로세스)                    │       │
│  └──────────────────────────────────────────────────┘       │
│                          │                                   │
│                          │ (내부망)                          │
│                          │                                   │
│  ┌───────────────────┐  │  ┌───────────────────┐           │
│  │  MariaDB Server   │◄─┼─►│ Elasticsearch     │           │
│  │  (192.168.1.101)  │  │  │ (192.168.1.102)   │           │
│  │                   │  │  │                   │           │
│  │  Port: 3306       │  │  │  Port: 9200       │           │
│  └───────────────────┘  │  └───────────────────┘           │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │
                           │ (One-way 파일 전송만 가능)
                           │
                  ┌────────▼──────────┐
                  │  외부 연결된 PC   │
                  │  (패키지 다운로드) │
                  └───────────────────┘
```

#### 2.4.2 포트 구성

| 서비스 | 포트 | 프로토콜 | 접근 범위 | 목적 |
|--------|------|---------|----------|------|
| **Reflex Frontend** | 8501 | HTTP | 내부 사용자 | 웹 UI |
| **API Gateway** | 8000 | HTTP | 내부 사용자 + AI Agent | REST API |
| **MCP Host** | 8080 | HTTP | 내부 (localhost) | 내부 API |
| **MariaDB** | 3306 | TCP | App Server만 | 데이터베이스 |
| **Elasticsearch** | 9200 | HTTP | App Server만 | 검색 엔진 |
| **Elasticsearch** | 9300 | TCP | 클러스터 노드 간 | 내부 통신 (향후) |

#### 2.4.3 보안 그룹 규칙

```
# Application Server
ALLOW   tcp/8501  FROM 192.168.1.0/24  (Frontend)
ALLOW   tcp/8000  FROM 192.168.1.0/24  (API Gateway)
DENY    tcp/8080  FROM *               (MCP Host - localhost만)

# MariaDB Server
ALLOW   tcp/3306  FROM 192.168.1.100  (App Server만)
DENY    tcp/3306  FROM *

# Elasticsearch Server
ALLOW   tcp/9200  FROM 192.168.1.100  (App Server만)
DENY    tcp/9200  FROM *
```

### 2.5 배포 아키텍처

#### 2.5.1 단일 서버 배포 (Phase 1 - PoC)

```
┌─────────────────────────────────────────────────────────────┐
│  Application Server (RHEL8)                                  │
│  CPU: 8 cores / RAM: 32GB / Disk: 500GB                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  /app/poc/mcps/                                              │
│  ├── frontend/venv/       (Python 3.10)                      │
│  ├── api-gateway/venv/    (Python 3.10)                      │
│  ├── mcp-host/venv/       (Python 3.10)                      │
│  ├── mcp-servers/         (5 × venv)                         │
│  │                                                           │
│  ├── data/                                                   │
│  │   ├── database/        (MariaDB 데이터)                   │
│  │   ├── elasticsearch/   (ES 데이터)                        │
│  │   ├── documents/       (파일)                             │
│  │   └── logs/            (로그)                             │
│  │                                                           │
│  └── scripts/             (운영 스크립트)                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**장점**:
- ✅ 간단한 설치/관리
- ✅ 망분리 환경 최적
- ✅ 낮은 복잡도

**단점**:
- ⚠️ SPOF (Single Point of Failure)
- ⚠️ 확장성 제한

#### 2.5.2 다중 서버 배포 (Phase 2 - 운영)

```
┌───────────────────────────────────────────────────────────────┐
│                      Load Balancer (HAProxy)                  │
│                      (192.168.1.200)                           │
└─────────────┬─────────────────────────┬───────────────────────┘
              │                         │
      ┌───────▼────────┐        ┌───────▼────────┐
      │  App Server 1  │        │  App Server 2  │
      │ (192.168.1.100)│        │ (192.168.1.101)│
      │                │        │                │
      │ - Frontend     │        │ - Frontend     │
      │ - API Gateway  │        │ - API Gateway  │
      │ - MCP Host     │        │ - MCP Host     │
      │ - MCP Servers  │        │ - MCP Servers  │
      └────────┬───────┘        └────────┬───────┘
               │                         │
               └─────────┬───────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
    ┌─────▼─────┐  ┌─────▼─────┐  ┌────▼─────┐
    │ MariaDB   │  │ElasticSearch│ │   NFS    │
    │  Primary  │  │  Cluster   │  │  Share   │
    │           │  │            │  │          │
    │  + Replica│  │ 3 nodes    │  │ Documents│
    └───────────┘  └────────────┘  └──────────┘
```

**장점**:
- ✅ 고가용성
- ✅ 수평 확장
- ✅ 부하 분산

**단점**:
- ⚠️ 복잡도 증가
- ⚠️ 추가 서버 필요

***

## 3. 기술 스택

### 3.1 프로그래밍 언어

| 언어 | 버전 | 용도 | 이유 |
|------|------|------|------|
| **Python** | 3.10+ | 전체 시스템 | 생산성, 풍부한 라이브러리, 팀 역량 |
| **Bash** | 4.0+ | 운영 스크립트 | 시스템 자동화, RHEL8 표준 |
| **SQL** | - | 데이터베이스 | 직접 쿼리 작성 (ORM 미사용) |

### 3.2 백엔드 프레임워크

| 프레임워크 | 버전 | 용도 | 선택 이유 |
|-----------|------|------|----------|
| **FastAPI** | 0.109+ | API Gateway, MCP Host | 비동기 지원, 자동 문서화, 빠른 성능 |
| **Uvicorn** | 0.27+ | ASGI 서버 | FastAPI 권장 서버 |

### 3.3 프론트엔드 프레임워크

| 프레임워크 | 버전 | 용도 | 선택 이유 |
|-----------|------|------|----------|
| **Reflex** | 0.4+ | 웹 UI | 순수 Python, React 기반, 커스터마이징 |

### 3.4 데이터베이스

| 데이터베이스 | 버전 | 용도 | 선택 이유 |
|------------|------|------|----------|
| **MariaDB** | 10.11+ | 관계형 데이터 | 안정성, 성능, MySQL 호환 |
| **Elasticsearch** | 8.x | 전문 검색 | 빠른 검색, 한글 분석기, 확장성 |

**ORM 미사용 이유**:
- ✅ 성능 최적화 (직접 SQL 튜닝)
- ✅ 복잡한 쿼리 작성 용이
- ✅ 학습 곡선 감소
- ✅ 의존성 감소

### 3.5 주요 라이브러리

#### 3.5.1 공통 (shared)

```txt
# Database
pymysql==1.1.0              # MariaDB 드라이버
DBUtils==3.0.3              # Connection Pool

# Search
elasticsearch==8.11.1       # Elasticsearch 클라이언트

# Validation
pydantic==2.5.3             # 데이터 검증

# Configuration
python-dotenv==1.0.0        # 환경 변수

# Parsing
PyYAML==6.0.1               # YAML 파서
python-frontmatter==1.1.0   # Markdown frontmatter
```

#### 3.5.2 백엔드 (mcp-host, api-gateway)

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0                    # 비동기 HTTP 클라이언트
python-jose[cryptography]==3.3.0 # JWT
passlib[bcrypt]==1.7.4           # 비밀번호 해싱
python-multipart==0.0.6          # 파일 업로드
aiofiles==23.2.1                 # 비동기 파일 I/O
```

#### 3.5.3 프론트엔드 (Reflex)

```txt
reflex==0.4.0
requests==2.31.0
```

#### 3.5.4 개발 도구 (선택)

```txt
pytest==7.4.3            # 테스트
black==23.12.1           # 코드 포맷팅
ruff==0.1.9              # Linting
mypy==1.7.1              # 타입 체크
```

### 3.6 인프라

| 항목 | 기술 | 버전 | 비고 |
|------|------|------|------|
| **OS** | RHEL 8 | 8.x | 표준 엔터프라이즈 Linux |
| **Python** | CPython | 3.10+ | 시스템 Python 또는 별도 설치 |
| **가상환경** | venv | 내장 | Python 표준 라이브러리 |
| **프로세스 관리** | systemd | 내장 | 서비스 자동 시작 (선택) |
| **웹 서버** | Uvicorn | 0.27+ | ASGI 서버 |

### 3.7 전체 의존성 맵

```
┌─────────────────────────────────────────────────────────────┐
│                          Python 3.10+                        │
└─────────────┬───────────────────────────────────────────────┘
              │
    ┌─────────┼─────────┬─────────┬─────────┐
    │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│Frontend││ API    ││  MCP   ││  MCP   ││Scripts │
│        ││Gateway ││  Host  ││Servers ││        │
└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘
    │         │         │         │         │
    │  Reflex │ FastAPI │ FastAPI │  shared │  Bash
    │         │   JWT   │  httpx  │         │  Python
    │         │         │         │         │
    └─────────┴─────────┴─────────┴─────────┘
                        │
              ┌─────────┼─────────┐
              │         │         │
              ▼         ▼         ▼
        ┌─────────┐┌─────────┐┌─────────┐
        │ pymysql ││elastics-││pydantic │
        │ DBUtils ││earch-py ││ PyYAML  │
        └────┬────┘└────┬────┘└─────────┘
             │          │
             ▼          ▼
        ┌─────────┐┌─────────┐
        │ MariaDB ││Elastics-│
        │  10.11  ││ earch   │
        │         ││   8.x   │
        └─────────┘└─────────┘
```

***

## 4. 디렉토리 구조

### 4.1 전체 구조

```
/app/poc/mcps/
│
├── config/                           # 전역 설정 파일
│   ├── registry.json                 # Tool 레지스트리
│   ├── permissions.json              # 권한 정의
│   ├── users.json                    # 사용자 목록
│   └── services.json                 # MCP 서버 설정
│
├── shared/                           # 공유 모듈
│   ├── __init__.py
│   ├── database.py                   # MariaDB 연결 관리
│   ├── queries.py                    # SQL 쿼리 모음
│   ├── elasticsearch.py              # ES 클라이언트
│   ├── permissions.py                # 권한 시스템
│   ├── logging_config.py             # 로깅 설정
│   ├── mcp_protocol.py               # MCP 프로토콜
│   ├── utils.py                      # 유틸리티
│   └── cache.py                      # 캐시 (dict 기반)
│
├── mcp-tools/                        # Tool 구현체
│   ├── core/                         # 핵심 Tool
│   │   ├── search/
│   │   ├── document/
│   │   └── auth/
│   └── custom/                       # 커스텀 Tool (부서별)
│       ├── finance/
│       └── hr/
│
├── mcp-servers/                      # MCP Server 구현체
│   ├── core/                         # 핵심 Server
│   │   ├── auth_server/
│   │   │   ├── server.yaml
│   │   │   ├── main.py
│   │   │   ├── handlers.py
│   │   │   ├── requirements.txt
│   │   │   └── venv/
│   │   ├── search_server/
│   │   ├── document_server/
│   │   ├── version_server/
│   │   └── audit_server/
│   └── custom/                       # 커스텀 Server (부서별)
│
├── mcp-host/                         # MCP Host (핵심 백엔드)
│   ├── main.py                       # FastAPI 진입점
│   ├── requirements.txt
│   ├── venv/
│   ├── core/                         # 핵심 모듈
│   │   ├── __init__.py
│   │   ├── tool_registry.py          # Tool 레지스트리
│   │   ├── server_manager.py         # Server 관리
│   │   ├── permission_engine.py      # 권한 엔진
│   │   ├── audit_logger.py           # 감사 로거
│   │   └── llm_service.py            # LLM 통합 (선택)
│   └── api/                          # API 라우터
│       ├── __init__.py
│       ├── admin.py                  # 관리자 API
│       ├── tools.py                  # Tool 조회 API
│       └── execute.py                # Tool 실행 API
│
├── api-gateway/                      # API Gateway
│   ├── main.py                       # FastAPI 진입점
│   ├── requirements.txt
│   ├── venv/
│   ├── middleware/                   # 미들웨어
│   │   ├── __init__.py
│   │   ├── auth.py                   # JWT 인증
│   │   ├── rate_limiting.py          # Rate Limiting
│   │   └── logging.py                # 요청/응답 로깅
│   └── routers/                      # 라우터
│       ├── __init__.py
│       ├── proxy.py                  # MCP Host 프록시
│       └── external.py               # 외부 Agent API
│
├── frontend/                         # Reflex 프론트엔드
│   ├── rxconfig.py                   # Reflex 설정
│   ├── requirements.txt
│   ├── venv/
│   ├── assets/                       # 정적 파일
│   │   └── favicon.ico
│   └── frontend/                     # 메인 패키지
│       ├── __init__.py
│       ├── app.py                    # 앱 진입점
│       ├── state/                    # 상태 관리
│       │   ├── __init__.py
│       │   ├── auth_state.py
│       │   ├── search_state.py
│       │   ├── document_state.py
│       │   ├── chat_state.py
│       │   └── admin_state.py
│       ├── pages/                    # 페이지
│       │   ├── __init__.py
│       │   ├── login.py
│       │   ├── dashboard.py
│       │   ├── search.py
│       │   ├── documents.py
│       │   ├── chat.py
│       │   └── admin/
│       │       ├── __init__.py
│       │       ├── tools.py
│       │       ├── servers.py
│       │       ├── users.py
│       │       └── stats.py
│       ├── components/               # 컴포넌트
│       │   ├── __init__.py
│       │   ├── navbar.py
│       │   ├── sidebar.py
│       │   ├── document_card.py
│       │   ├── tool_card.py
│       │   └── server_status.py
│       ├── services/                 # API 서비스
│       │   ├── __init__.py
│       │   ├── api_client.py
│       │   ├── auth_service.py
│       │   ├── mcp_service.py
│       │   └── admin_service.py
│       └── styles/                   # 스타일
│           ├── __init__.py
│           ├── colors.py
│           └── common.py
│
├── data/                             # 데이터 저장소
│   ├── database/                     # MariaDB 데이터
│   │   └── mcps.sql                  # 초기 스키마
│   ├── elasticsearch/                # ES 데이터
│   │   ├── mappings/
│   │   │   ├── documents.json
│   │   │   └── audit_logs.json
│   │   └── data/                     # ES 데이터 디렉토리
│   ├── documents/                    # 문서 파일
│   │   ├── public/
│   │   ├── team/
│   │   │   └── dev_team/
│   │   └── confidential/
│   └── logs/                         # 로그 파일
│       ├── mcp-host/
│       │   ├── app.log
│       │   └── error.log
│       ├── mcp-servers/
│       │   ├── auth_server.log
│       │   ├── search_server.log
│       │   └── ...
│       ├── api-gateway/
│       │   ├── access.log
│       │   └── error.log
│       └── frontend/
│           └── reflex.log
│
├── scripts/                          # 운영 스크립트
│   ├── setup.sh                      # 초기 설치
│   ├── start_all.sh                  # 전체 시작
│   ├── stop_all.sh                   # 전체 종료
│   ├── status.sh                     # 상태 확인
│   ├── restart_service.sh            # 서비스 재시작
│   ├── package_for_deployment.sh     # 배포 패키징
│   ├── init_database.py              # DB 초기화
│   ├── seed_data.py                  # 샘플 데이터
│   ├── init_elasticsearch.py         # ES 초기화
│   └── reindex_documents.py          # 문서 재색인
│
├── tests/                            # 테스트
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                             # 설계서 (이 문서)
│   ├── 00_시스템_아키텍처.md
│   ├── 01_shared_모듈_설계서.md
│   └── ...
│
├── pids/                             # 프로세스 ID
│   ├── mcp-host.pid
│   ├── api-gateway.pid
│   ├── frontend.pid
│   └── *.pid
│
├── .env.example                      # 환경 변수 예제
├── .gitignore
├── README.md
└── requirements.txt                  # 루트 공통 의존성
```

### 4.2 각 폴더 역할

| 폴더 | 역할 | 주요 파일 |
|------|------|----------|
| **config/** | 전역 설정 JSON | registry.json, permissions.json |
| **shared/** | 공유 모듈 (모든 컴포넌트가 import) | database.py, queries.py, elasticsearch.py |
| **mcp-tools/** | Tool 구현체 (YAML + Python) | tool.yaml, handler.py |
| **mcp-servers/** | MCP Server (STDIO 프로세스) | main.py, handlers.py |
| **mcp-host/** | 핵심 백엔드 (FastAPI) | main.py, core/*, api/* |
| **api-gateway/** | API Gateway (FastAPI) | main.py, middleware/*, routers/* |
| **frontend/** | Reflex 프론트엔드 | app.py, pages/*, components/* |
| **data/** | 데이터 저장소 | DB, ES, 파일, 로그 |
| **scripts/** | 운영 스크립트 | setup.sh, start_all.sh |
| **tests/** | 테스트 코드 | unit/, integration/, e2e/ |
| **docs/** | 설계서 | *.md |

***

## 5. 인터페이스 정의

### 5.1 MCP Protocol (JSON-RPC over STDIO)

#### 5.1.1 Tool 호출 요청

```json
{
  "jsonrpc": "2.0",
  "id": "req_12345",
  "method": "tools/call",
  "params": {
    "name": "search_documents",
    "arguments": {
      "query": "예산",
      "classification": ["public", "team"],
      "user_id": "U001"
    }
  }
}
```

#### 5.1.2 Tool 호출 응답 (성공)

```json
{
  "jsonrpc": "2.0",
  "id": "req_12345",
  "result": {
    "total": 5,
    "results": [
      {
        "doc_id": "DOC001",
        "title": "2026년 예산 계획",
        "snippet": "...예산...",
        "classification": "team",
        "score": 8.5
      }
    ]
  }
}
```

#### 5.1.3 Tool 호출 응답 (에러)

```json
{
  "jsonrpc": "2.0",
  "id": "req_12345",
  "error": {
    "code": -32600,
    "message": "Permission denied",
    "data": {
      "required_permission": "document:read:team",
      "user_role": "junior"
    }
  }
}
```

### 5.2 REST API (외부 Agent 연동)

#### 5.2.1 인증 (JWT 발급)

```http
POST /api/auth/token
Content-Type: application/json

{
  "client_id": "finance_dept",
  "client_secret": "secret_key_here"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 5.2.2 Tool 실행

```http
POST /api/external/execute_tool
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "tool_name": "search_documents",
  "params": {
    "query": "계약서",
    "limit": 10
  }
}

Response:
{
  "result": {
    "total": 3,
    "results": [...]
  },
  "execution_time_ms": 245,
  "request_id": "req_abc123"
}
```

#### 5.2.3 에러 응답

```http
Response: 403 Forbidden
{
  "error": "Permission denied",
  "code": "PERMISSION_DENIED",
  "details": {
    "tool": "search_documents",
    "required_scope": "document:read"
  }
}
```

### 5.3 내부 함수 호출

#### 5.3.1 Database Query

```python
from shared.database import DatabaseManager
from shared.queries import GET_USER_BY_ID

db = DatabaseManager(config)
result = db.execute_query(GET_USER_BY_ID, (user_id,))
# result = [{"id": "U001", "name": "김신입", ...}]
```

#### 5.3.2 Elasticsearch Search

```python
from shared.elasticsearch import ElasticsearchManager

es = ElasticsearchManager(config)
results = es.search("documents", {
    "query": {
        "match": {"content": "예산"}
    }
})
# results = [{"doc_id": "DOC001", ...}, ...]
```

#### 5.3.3 Permission Check

```python
from shared.permissions import PermissionEngine

perm_engine = PermissionEngine()
has_permission = perm_engine.check_permission(
    user_id="U001",
    resource_type="document",
    resource_id="DOC001",
    action="read"
)
# has_permission = True/False
```

***

## 6. 보안 아키텍처

### 6.1 인증 (Authentication)

#### 6.1.1 JWT 토큰 구조

```
Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "sub": "U001",           # 사용자 ID
  "name": "김신입",        # 이름
  "role": "staff",         # 역할
  "team": "dev_team",      # 팀
  "iat": 1704700800,       # 발급 시간
  "exp": 1704704400,       # 만료 시간 (1시간)
  "scopes": [              # 권한 스코프
    "document:read",
    "document:create",
    "tool:execute"
  ]
}

Signature:
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  SECRET_KEY
)
```

#### 6.1.2 로그인 플로우

```
[사용자] → [Frontend] → [API Gateway]
                             │
                             │ 1. 사용자 선택 (PoC는 비밀번호 없음)
                             │
                             ▼
                        [MCP Host]
                             │
                             │ 2. DB에서 사용자 조회
                             │    SELECT * FROM users WHERE id = 'U001'
                             │
                             ▼
                        [MariaDB]
                             │
                             │ 3. 사용자 정보 반환
                             │
                             ▼
                        [MCP Host]
                             │
                             │ 4. JWT 생성
                             │    jwt.encode(payload, SECRET_KEY)
                             │
                             ▼
                        [Frontend]
                             │
                             │ 5. 토큰 저장 (State)
                             │    st.session_state.token = ...
```

### 6.2 인가 (Authorization) - RBAC

#### 6.2.1 역할 정의

| 역할 | 코드 | 문서 접근 | Tool 실행 | 서버 관리 | 사용자 관리 |
|------|------|----------|----------|----------|------------|
| **Junior** | `junior` | Public만 | 기본 Tool | ❌ | ❌ |
| **Staff** | `staff` | Public, 자기 팀 | 기본 Tool | ❌ | ❌ |
| **Manager** | `manager` | Public, 자기 팀 | 모든 Tool | ❌ | 팀원만 |
| **Executive** | `executive` | 모든 문서 | 모든 Tool | ❌ | ❌ |
| **Admin** | `admin` | 모든 문서 | 모든 Tool | ✅ | ✅ |

#### 6.2.2 권한 매트릭스

```python
PERMISSION_MATRIX = {
    "junior": {
        "document": {
            "public": ["read"],
            "team": [],
            "confidential": []
        },
        "tool": {
            "search_documents": ["execute"],
            "get_document": ["execute"]
        },
        "admin": []
    },
    "staff": {
        "document": {
            "public": ["read", "create", "update"],
            "team": ["read", "create", "update"],  # 자기 팀만
            "confidential": []
        },
        "tool": {
            "search_documents": ["execute"],
            "get_document": ["execute"],
            "create_document": ["execute"],
            "update_document": ["execute"]
        },
        "admin": []
    },
    "manager": {
        "document": {
            "public": ["read", "create", "update", "delete"],
            "team": ["read", "create", "update", "delete"],
            "confidential": []
        },
        "tool": {
            "*": ["execute"]  # 모든 Tool
        },
        "admin": ["approve_access_request"]  # 팀원 승인만
    },
    "executive": {
        "document": {
            "public": ["read"],
            "team": ["read"],
            "confidential": ["read"]
        },
        "tool": {
            "*": ["execute"]
        },
        "admin": []
    },
    "admin": {
        "document": {
            "*": ["read", "create", "update", "delete"]
        },
        "tool": {
            "*": ["execute", "register", "unregister"]
        },
        "admin": ["*"]  # 모든 관리 기능
    }
}
```

#### 6.2.3 권한 체크 로직

```python
def check_permission(user_id, resource_type, resource_id, action):
    """권한 확인"""
    
    # 1. 사용자 조회
    user = db.execute_query(queries.GET_USER_BY_ID, (user_id,))[0]
    role = user["role"]
    team = user["team"]
    
    # 2. 문서 권한 체크 (예시)
    if resource_type == "document":
        doc = db.execute_query(queries.GET_DOCUMENT_BY_ID, (resource_id,))[0]
        classification = doc["classification"]
        doc_team = doc["team"]
        
        # Admin은 모든 접근 허용
        if role == "admin":
            return True
        
        # Executive는 모든 문서 읽기 가능
        if role == "executive" and action == "read":
            return True
        
        # Manager/Staff는 자기 팀 문서만
        if role in ["manager", "staff"]:
            if classification == "public":
                return True
            elif classification == "team" and doc_team == team:
                return action in ["read", "create", "update", "delete"]
            else:
                return False
        
        # Junior는 public만
        if role == "junior":
            return classification == "public" and action == "read"
        
        return False
    
    # 3. Tool 권한 체크
    elif resource_type == "tool":
        permissions = PERMISSION_MATRIX.get(role, {}).get("tool", {})
        
        if "*" in permissions:
            return True
        
        if resource_id in permissions:
            return action in permissions[resource_id]
        
        return False
    
    return False
```

### 6.3 SQL Injection 방지

#### 6.3.1 Parameterized Query 사용

```python
# ❌ 취약한 코드 (절대 사용 금지)
query = f"SELECT * FROM users WHERE id = '{user_id}'"
result = db.execute_query(query)

# ✅ 안전한 코드 (Parameterized Query)
query = "SELECT * FROM users WHERE id = %s"
result = db.execute_query(query, (user_id,))
```

#### 6.3.2 쿼리 검증

```python
# queries.py에 모든 쿼리 정의
GET_USER_BY_ID = """
    SELECT id, name, role, team, created_at
    FROM users
    WHERE id = %s
"""

# 사용
result = db.execute_query(queries.GET_USER_BY_ID, (user_id,))
```

### 6.4 API Rate Limiting

#### 6.4.1 Rate Limit 정책

| API 유형 | 제한 | 시간 | 대상 |
|---------|------|------|------|
| **내부 사용자** | 100 req/min | 60초 | IP 기반 |
| **외부 Agent** | 100 req/min | 60초 | 클라이언트 ID 기반 |
| **검색 API** | 30 req/min | 60초 | 사용자별 |
| **로그인** | 10 req/min | 60초 | IP 기반 |

#### 6.4.2 구현

```python
# api-gateway/middleware/rate_limiting.py

from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Rate limit 체크"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=window)
        
        # 오래된 요청 제거
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > cutoff
        ]
        
        # 현재 요청 카운트
        current_count = len(self.requests[key])
        
        if current_count >= limit:
            return False
        
        # 요청 기록
        self.requests[key].append(now)
        return True

# 미들웨어
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # IP 또는 클라이언트 ID 추출
    client_id = request.client.host
    if request.headers.get("X-Client-ID"):
        client_id = request.headers["X-Client-ID"]
    
    # Rate limit 체크
    if not rate_limiter.is_allowed(client_id, limit=100, window=60):
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests"}
        )
    
    response = await call_next(request)
    return response
```

### 6.5 보안 체크리스트

| 항목 | 구현 | 설명 |
|------|------|------|
| ✅ **JWT 인증** | O | 모든 API 요청에 토큰 필요 |
| ✅ **RBAC** | O | 역할 기반 접근 제어 |
| ✅ **SQL Injection 방지** | O | Parameterized Query |
| ✅ **XSS 방지** | O | Reflex 자동 이스케이핑 |
| ✅ **CSRF 방지** | O | Same-Origin 정책 |
| ✅ **Rate Limiting** | O | 요청 제한 |
| ✅ **로깅** | O | 모든 활동 기록 |
| ✅ **에러 메시지** | O | 민감 정보 노출 방지 |
| ✅ **HTTPS** | 운영 시 | TLS 1.3 |
| ✅ **비밀번호 해싱** | 향후 | bcrypt |

***

## 7. 성능 목표

### 7.1 시스템 성능 요구사항

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| **동시 접속** | 50명 | Apache Bench |
| **문서 수** | 5,000개 | DB + ES 용량 |
| **검색 응답 시간** | < 500ms | 95 percentile |
| **문서 조회 응답** | < 200ms | 95 percentile |
| **문서 생성 응답** | < 1,000ms | 95 percentile |
| **Tool 실행 시간** | < 2,000ms | 평균 |
| **DB 쿼리 시간** | < 100ms | 단순 SELECT |
| **DB 연결 풀** | 5-20개 | Connection Pool |
| **메모리 사용** | < 8GB | 전체 시스템 |
| **CPU 사용률** | < 60% | 평균 부하 |
| **디스크 I/O** | < 50MB/s | 쓰기 |

### 7.2 부하 시나리오

#### 7.2.1 정상 부하

```
동시 사용자: 20명
- 검색: 10 req/min
- 문서 조회: 30 req/min
- 문서 생성: 5 req/min
- Tool 실행: 15 req/min

예상 응답 시간:
- 검색: 200-400ms
- 조회: 50-150ms
- 생성: 300-800ms
```

#### 7.2.2 피크 부하

```
동시 사용자: 50명 (전체 사용자)
- 검색: 30 req/min
- 문서 조회: 80 req/min
- 문서 생성: 10 req/min
- Tool 실행: 40 req/min

예상 응답 시간:
- 검색: 300-500ms
- 조회: 100-200ms
- 생성: 500-1000ms
```

### 7.3 성능 최적화 전략

#### 7.3.1 데이터베이스

| 전략 | 구현 | 효과 |
|------|------|------|
| **인덱스** | 자주 조회되는 컬럼에 인덱스 | SELECT 속도 10배 향상 |
| **Connection Pool** | DBUtils (min=5, max=20) | 연결 오버헤드 감소 |
| **쿼리 최적화** | EXPLAIN으로 분석 | 불필요한 스캔 제거 |
| **파티셔닝** | 날짜별 파티션 (향후) | 대용량 데이터 처리 |

#### 7.3.2 Elasticsearch

| 전략 | 구현 | 효과 |
|------|------|------|
| **샤드 설정** | primary=1, replica=1 | 적정 샤드 수 |
| **refresh_interval** | 30s (실시간 불필요) | 색인 속도 향상 |
| **캐싱** | query cache, filter cache | 반복 검색 빠름 |
| **bulk indexing** | 문서 일괄 색인 | 색인 속도 향상 |

#### 7.3.3 애플리케이션

| 전략 | 구현 | 효과 |
|------|------|------|
| **메모리 캐시** | dict 기반 Tool/User 캐시 | DB 쿼리 감소 |
| **비동기 처리** | FastAPI async/await | 동시 요청 처리 |
| **Connection Reuse** | httpx 세션 | HTTP 오버헤드 감소 |
| **로그 버퍼링** | 메모리 버퍼 → 배치 쓰기 | I/O 감소 |

***

## 8. 확장 전략

### 8.1 수평 확장 (Scale-Out)

#### 8.1.1 애플리케이션 서버

```
┌──────────────────────────────────────────────────────────┐
│                Load Balancer (HAProxy)                    │
│           Round-Robin / Least Connections                 │
└───────────┬──────────────────────────┬───────────────────┘
            │                          │
    ┌───────▼────────┐        ┌───────▼────────┐
    │  App Server 1  │        │  App Server 2  │
    │                │        │                │
    │  - Frontend    │        │  - Frontend    │
    │  - API Gateway │        │  - API Gateway │
    │  - MCP Host    │        │  - MCP Host    │
    │  - MCP Servers │        │  - MCP Servers │
    └────────────────┘        └────────────────┘
```

**고려사항**:
- ✅ Stateless 설계 (JWT 토큰 사용)
- ✅ 세션 공유 불필요
- ⚠️ MCP Server 상태 동기화 필요

#### 8.1.2 데이터베이스

```
┌─────────────────────────────────────────┐
│         App Servers (Multiple)          │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│        MariaDB Primary (Read/Write)     │
└────────┬────────────────────────────────┘
         │ (Replication)
         ├──────────┬──────────┐
         ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │Replica1│ │Replica2│ │Replica3│
    │(Read)  │ │(Read)  │ │(Read)  │
    └────────┘ └────────┘ └────────┘
```

**고려사항**:
- ✅ 읽기 부하 분산
- ⚠️ 복제 지연 (일반적으로 < 1초)
- ⚠️ Primary 장애 시 Failover 필요

#### 8.1.3 Elasticsearch

```
┌─────────────────────────────────────────┐
│         App Servers (Multiple)          │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│       Elasticsearch Cluster             │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │  Node 1  │  │  Node 2  │  │  Node 3  ││
│  │          │  │          │  │          ││
│  │ Primary  │  │ Primary  │  │ Primary  ││
│  │ Shard 0  │  │ Shard 1  │  │ Shard 2  ││
│  │          │  │          │  │          ││
│  │ Replica  │  │ Replica  │  │ Replica  ││
│  │ Shard 1  │  │ Shard 2  │  │ Shard 0  ││
│  └──────────┘  └──────────┘  └──────────┘│
└─────────────────────────────────────────┘
```

**고려사항**:
- ✅ 자동 샤드 분산
- ✅ 고가용성
- ⚠️ 최소 3노드 권장

### 8.2 수직 확장 (Scale-Up)

| 리소스 | 현재 | 확장 후 | 효과 |
|--------|------|---------|------|
| **CPU** | 8 cores | 16 cores | 동시 처리량 2배 |
| **RAM** | 32GB | 64GB | 캐시 증가, ES 성능 향상 |
| **Disk** | 500GB HDD | 1TB SSD | I/O 속도 10배 |
| **Network** | 1Gbps | 10Gbps | 대용량 전송 빠름 |

### 8.3 확장 시나리오

| 사용자 수 | 문서 수 | 아키텍처 | 예상 비용 |
|----------|---------|---------|----------|
| **< 50명** | < 5,000 | 단일 서버 | 1대 |
| **50-200명** | 5,000-20,000 | 2 App + DB Replica | 4대 |
| **200-500명** | 20,000-50,000 | 3 App + DB Primary/Replica + ES 3노드 | 7대 |
| **500명+** | 50,000+ | LB + 5 App + DB Cluster + ES Cluster | 12대+ |

***

## 9. 배포 전략

### 9.1 망분리 환경 배포 절차

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 외부 인터넷이 연결된 PC에서 패키지 다운로드          │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ 1. pip download
                         │ 2. MariaDB RPM
                         │ 3. Elasticsearch TAR.GZ
                         │ 4. 소스 코드
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: tarball 생성                                        │
│  scripts/package_for_deployment.sh                           │
│  → mcps_v1.0.0_20260108.tar.gz                              │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ USB 또는 내부 파일 전송
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: 망분리 서버로 전송                                  │
│  /tmp/mcps_v1.0.0_20260108.tar.gz                           │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ tar -xzf
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: 설치 스크립트 실행                                  │
│  ./scripts/setup.sh                                          │
│  - MariaDB 설치                                              │
│  - Elasticsearch 설치                                        │
│  - Python venv 생성                                          │
│  - 패키지 설치 (offline)                                     │
│  - DB 초기화                                                 │
│  - ES 인덱스 생성                                            │
└─────────────────────────────────────────────────────────────┘
                         │
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: 시스템 시작                                         │
│  ./scripts/start_all.sh                                      │
│  - MariaDB 시작                                              │
│  - Elasticsearch 시작                                        │
│  - MCP Servers 시작                                          │
│  - MCP Host 시작                                             │
│  - API Gateway 시작                                          │
│  - Frontend 시작                                             │
└─────────────────────────────────────────────────────────────┘
                         │
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 6: 검증                                                │
│  - 헬스 체크: ./scripts/status.sh                           │
│  - 웹 접속: http://192.168.1.100:8501                       │
│  - API 테스트: curl http://192.168.1.100:8000/health       │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 패키징 구조

```
mcps_v1.0.0_20260108.tar.gz
│
├── install/
│   ├── mariadb-10.11.x.rpm           # MariaDB RPM
│   ├── elasticsearch-8.x.tar.gz      # Elasticsearch
│   └── python-packages/               # pip packages
│       ├── fastapi-0.109.0.whl
│       ├── reflex-0.4.0.whl
│       └── ...
│
├── app/
│   ├── config/
│   ├── shared/
│   ├── mcp-tools/
│   ├── mcp-servers/
│   ├── mcp-host/
│   ├── api-gateway/
│   ├── frontend/
│   ├── data/
│   │   ├── database/
│   │   │   └── schema.sql            # 초기 스키마
│   │   └── elasticsearch/
│   │       └── mappings/
│   ├── scripts/
│   └── README.md
│
├── install.sh                         # 설치 스크립트
└── README.txt                         # 설치 가이드
```

### 9.3 업데이트 전략

```
┌─────────────────────────────────────────────────────────────┐
│  Blue-Green Deployment (향후)                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐                    ┌──────────────┐       │
│  │    Blue      │                    │    Green     │       │
│  │  (현재 운영)  │                    │  (새 버전)    │       │
│  │              │                    │              │       │
│  │  v1.0.0      │                    │  v1.1.0      │       │
│  └──────┬───────┘                    └──────┬───────┘       │
│         │                                   │               │
│         │                                   │               │
│         │  1. 트래픽 전환                    │               │
│         └───────────────────────────────────┘               │
│                                                              │
│  2. Blue 환경 유지 (롤백 대비)                               │
│  3. 검증 후 Blue 제거                                        │
└─────────────────────────────────────────────────────────────┘
```

***

## 10. 모니터링 및 운영

### 10.1 헬스 체크

#### 10.1.1 엔드포인트

```http
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2026-01-08T10:00:00Z",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5,
      "connections": {
        "active": 3,
        "idle": 7,
        "total": 10
      }
    },
    "elasticsearch": {
      "status": "healthy",
      "response_time_ms": 12,
      "cluster_status": "green",
      "nodes": 1,
      "indices": 2
    },
    "mcp_servers": {
      "auth_server": "running",
      "search_server": "running",
      "document_server": "running",
      "version_server": "running",
      "audit_server": "running"
    }
  },
  "uptime_seconds": 86400,
  "version": "1.0.0"
}
```

#### 10.1.2 모니터링 스크립트

```bash
#!/bin/bash
# scripts/monitor.sh

while true; do
    # 헬스 체크
    curl -s http://localhost:8000/health | jq .
    
    # 프로세스 확인
    ./scripts/status.sh
    
    # 리소스 확인
    echo "=== CPU/Memory ==="
    top -bn1 | head -20
    
    echo "=== Disk ==="
    df -h
    
    echo "=== Network ==="
    netstat -anp | grep LISTEN
    
    sleep 60
done
```

### 10.2 로그 관리

#### 10.2.1 로그 위치

```
/app/poc/mcps/data/logs/
├── mcp-host/
│   ├── app.log           # 애플리케이션 로그
│   ├── error.log         # 에러 로그
│   └── access.log        # API 접근 로그
├── mcp-servers/
│   ├── auth_server.log
│   ├── search_server.log
│   ├── document_server.log
│   ├── version_server.log
│   └── audit_server.log
├── api-gateway/
│   ├── access.log        # 외부 API 접근
│   └── error.log
└── frontend/
    └── reflex.log
```

#### 10.2.2 로그 포맷

```
# 표준 로그 포맷
[2026-01-08 10:00:00] [INFO] [mcp-host] [user:U001] Tool executed: search_documents
[2026-01-08 10:00:01] [ERROR] [search_server] [user:U001] Elasticsearch timeout

# JSON 로그 (선택)
{
  "timestamp": "2026-01-08T10:00:00Z",
  "level": "INFO",
  "service": "mcp-host",
  "user_id": "U001",
  "action": "tool_execute",
  "tool_name": "search_documents",
  "execution_time_ms": 245,
  "status": "success"
}
```

#### 10.2.3 로그 로테이션

```bash
# /etc/logrotate.d/mcps

/app/poc/mcps/data/logs/*/*.log {
    daily                    # 매일 로테이션
    rotate 30                # 30일 보관
    compress                 # gzip 압축
    delaycompress            # 다음 로테이션까지 압축 지연
    missingok                # 파일 없어도 에러 안냄
    notifempty               # 빈 파일은 로테이션 안함
    create 0640 root root    # 새 파일 권한
    sharedscripts            # 스크립트 한번만 실행
    postrotate
        # 서비스 재시작 없이 로그 파일 다시 열기
        /usr/bin/killall -SIGUSR1 uvicorn 2>/dev/null || true
    endscript
}
```

#### 10.2.4 로그 분석

```bash
#!/bin/bash
# scripts/analyze_logs.sh

# 에러 로그 분석
echo "=== Top 10 Errors ==="
cat /app/poc/mcps/data/logs/*/error.log | \
    grep ERROR | \
    awk '{print $6}' | \
    sort | uniq -c | sort -rn | head -10

# Tool 실행 통계
echo "=== Tool Execution Stats ==="
cat /app/poc/mcps/data/logs/mcp-host/app.log | \
    grep "Tool executed" | \
    awk '{print $7}' | \
    sort | uniq -c | sort -rn

# 응답 시간 분석
echo "=== Slow Requests (> 1000ms) ==="
cat /app/poc/mcps/data/logs/api-gateway/access.log | \
    awk '$10 > 1000 {print $0}' | \
    tail -20
```

### 10.3 트러블슈팅

#### 10.3.1 일반적인 문제

| 문제 | 증상 | 원인 | 해결 방법 |
|------|------|------|----------|
| **서비스 시작 실패** | `start_all.sh` 에러 | 포트 충돌 | `netstat -tulpn | grep 8501` 확인 후 프로세스 종료 |
| **DB 연결 실패** | `Can't connect to MySQL server` | MariaDB 미실행 | `systemctl start mariadb` |
| **ES 연결 실패** | `Connection refused [9200]` | Elasticsearch 미실행 | `systemctl start elasticsearch` |
| **MCP Server 응답 없음** | Timeout | 프로세스 좀비 | `./scripts/restart_service.sh search_server` |
| **검색 결과 없음** | Empty results | 인덱스 미생성 | `python scripts/init_elasticsearch.py` |
| **권한 에러** | `Permission denied` | 역할 설정 오류 | `config/permissions.json` 확인 |
| **느린 응답** | > 5초 | DB 또는 ES 과부하 | `top`, `iostat` 확인, 인덱스 추가 |
| **메모리 부족** | OOM Killer | ES 메모리 설정 과다 | `ES_JAVA_OPTS="-Xms2g -Xmx2g"` 조정 |

#### 10.3.2 MariaDB 문제

```bash
# 1. 연결 확인
mysql -u mcps_user -p -e "SELECT 1"

# 2. 프로세스 리스트
mysql -u root -p -e "SHOW PROCESSLIST"

# 3. 느린 쿼리 확인
mysql -u root -p -e "SHOW VARIABLES LIKE 'slow_query_log'"
tail -f /var/log/mysql/slow-query.log

# 4. Connection Pool 상태
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_%'"
# Threads_connected: 현재 연결 수
# Threads_running: 실행 중인 스레드

# 5. 테이블 크기
mysql -u mcps_user -p mcps_db -e "
SELECT 
    table_name,
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'mcps_db'
ORDER BY size_mb DESC;
"

# 6. 인덱스 사용 확인
mysql -u mcps_user -p mcps_db -e "
EXPLAIN SELECT * FROM documents WHERE classification = 'public';
"
```

#### 10.3.3 Elasticsearch 문제

```bash
# 1. 클러스터 상태
curl -X GET "localhost:9200/_cluster/health?pretty"

# 2. 노드 상태
curl -X GET "localhost:9200/_cat/nodes?v"

# 3. 인덱스 상태
curl -X GET "localhost:9200/_cat/indices?v"

# 4. 샤드 상태
curl -X GET "localhost:9200/_cat/shards?v"

# 5. 느린 검색 로그
tail -f /var/log/elasticsearch/mcps-cluster_index_search_slowlog.log

# 6. 메모리 사용
curl -X GET "localhost:9200/_cat/nodes?v&h=name,heap.percent,ram.percent"

# 7. 인덱스 재생성 (문제 시)
curl -X DELETE "localhost:9200/documents"
python scripts/init_elasticsearch.py
python scripts/reindex_documents.py
```

#### 10.3.4 MCP Server 문제

```bash
# 1. 프로세스 확인
ps aux | grep "mcp-servers"

# 2. STDIO 통신 테스트
echo '{"jsonrpc":"2.0","id":"1","method":"tools/list"}' | \
    /app/poc/mcps/mcp-servers/core/auth_server/venv/bin/python \
    /app/poc/mcps/mcp-servers/core/auth_server/main.py

# 3. 로그 확인
tail -f /app/poc/mcps/data/logs/mcp-servers/auth_server.log

# 4. 좀비 프로세스 정리
./scripts/stop_all.sh
rm -f /app/poc/mcps/pids/*.pid
./scripts/start_all.sh

# 5. venv 문제
cd /app/poc/mcps/mcp-servers/core/auth_server
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 10.3.5 성능 디버깅

```bash
# 1. CPU 사용률
top -bn1 | head -20

# 2. 메모리 사용
free -h
ps aux --sort=-%mem | head -10

# 3. 디스크 I/O
iostat -x 1 5

# 4. 네트워크
netstat -s | grep -i "retransmit"
iftop -i eth0

# 5. 프로세스별 리소스
pidstat -p $(cat /app/poc/mcps/pids/mcp-host.pid) 1

# 6. Python 프로파일링 (개발 시)
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats
```

#### 10.3.6 긴급 복구 절차

```bash
#!/bin/bash
# scripts/emergency_recovery.sh

echo "=== 긴급 복구 시작 ==="

# 1. 모든 서비스 강제 종료
echo "1. 서비스 종료 중..."
./scripts/stop_all.sh
killall -9 python3 2>/dev/null
killall -9 uvicorn 2>/dev/null

# 2. PID 파일 정리
echo "2. PID 파일 정리..."
rm -f /app/poc/mcps/pids/*.pid

# 3. 로그 백업
echo "3. 로그 백업..."
timestamp=$(date +%Y%m%d_%H%M%S)
tar -czf /tmp/mcps_logs_$timestamp.tar.gz /app/poc/mcps/data/logs/

# 4. DB 연결 테스트
echo "4. DB 연결 테스트..."
mysql -u mcps_user -p${DB_PASSWORD} -e "SELECT 1" || {
    echo "DB 연결 실패. MariaDB 재시작..."
    systemctl restart mariadb
    sleep 5
}

# 5. ES 연결 테스트
echo "5. ES 연결 테스트..."
curl -s http://localhost:9200/_cluster/health > /dev/null || {
    echo "ES 연결 실패. Elasticsearch 재시작..."
    systemctl restart elasticsearch
    sleep 30
}

# 6. 서비스 재시작
echo "6. 서비스 재시작..."
./scripts/start_all.sh

# 7. 헬스 체크
echo "7. 헬스 체크..."
sleep 10
./scripts/status.sh

echo "=== 복구 완료 ==="
```

### 10.4 백업 및 복구

#### 10.4.1 백업 전략

| 대상 | 주기 | 방법 | 보관 기간 |
|------|------|------|----------|
| **MariaDB** | 매일 01:00 | mysqldump | 30일 |
| **Elasticsearch** | 매주 일요일 | snapshot | 12주 |
| **문서 파일** | 매일 02:00 | rsync | 30일 |
| **설정 파일** | 변경 시 | git commit | 영구 |
| **로그** | 매주 | tar.gz | 12주 |

#### 10.4.2 백업 스크립트

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backup/mcps"
DATE=$(date +%Y%m%d)

# 1. MariaDB 백업
echo "=== MariaDB 백업 ==="
mysqldump \
    -u mcps_user \
    -p${DB_PASSWORD} \
    --single-transaction \
    --routines \
    --triggers \
    mcps_db | gzip > $BACKUP_DIR/db/mcps_db_$DATE.sql.gz

# 2. Elasticsearch 스냅샷
echo "=== Elasticsearch 백업 ==="
curl -X PUT "localhost:9200/_snapshot/backup_repo/snapshot_$DATE?wait_for_completion=true"

# 3. 문서 파일 백업
echo "=== 문서 파일 백업 ==="
rsync -av --delete \
    /app/poc/mcps/data/documents/ \
    $BACKUP_DIR/documents/

# 4. 설정 파일 백업
echo "=== 설정 파일 백업 ==="
tar -czf $BACKUP_DIR/config/config_$DATE.tar.gz \
    /app/poc/mcps/config/ \
    /app/poc/mcps/.env

# 5. 오래된 백업 삭제 (30일 이상)
echo "=== 오래된 백업 삭제 ==="
find $BACKUP_DIR/db/ -name "*.sql.gz" -mtime +30 -delete
find $BACKUP_DIR/config/ -name "*.tar.gz" -mtime +30 -delete

# 6. 백업 검증
echo "=== 백업 검증 ==="
if [ -f "$BACKUP_DIR/db/mcps_db_$DATE.sql.gz" ]; then
    echo "✅ DB 백업 성공"
else
    echo "❌ DB 백업 실패"
    exit 1
fi

echo "=== 백업 완료 ==="
```

#### 10.4.3 복구 스크립트

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_DIR="/backup/mcps"
RESTORE_DATE=$1

if [ -z "$RESTORE_DATE" ]; then
    echo "사용법: ./restore.sh YYYYMMDD"
    exit 1
fi

echo "=== $RESTORE_DATE 백업으로 복구 시작 ==="

# 1. 서비스 중지
echo "1. 서비스 중지..."
./scripts/stop_all.sh

# 2. MariaDB 복구
echo "2. MariaDB 복구..."
mysql -u root -p -e "DROP DATABASE IF EXISTS mcps_db; CREATE DATABASE mcps_db;"
zcat $BACKUP_DIR/db/mcps_db_$RESTORE_DATE.sql.gz | \
    mysql -u mcps_user -p${DB_PASSWORD} mcps_db

# 3. Elasticsearch 복구
echo "3. Elasticsearch 복구..."
# 기존 인덱스 삭제
curl -X DELETE "localhost:9200/documents"
curl -X DELETE "localhost:9200/audit_logs"

# 스냅샷 복구
curl -X POST "localhost:9200/_snapshot/backup_repo/snapshot_$RESTORE_DATE/_restore?wait_for_completion=true"

# 4. 문서 파일 복구
echo "4. 문서 파일 복구..."
rsync -av --delete \
    $BACKUP_DIR/documents/ \
    /app/poc/mcps/data/documents/

# 5. 설정 파일 복구
echo "5. 설정 파일 복구..."
tar -xzf $BACKUP_DIR/config/config_$RESTORE_DATE.tar.gz -C /

# 6. 서비스 재시작
echo "6. 서비스 재시작..."
./scripts/start_all.sh

# 7. 검증
echo "7. 복구 검증..."
sleep 10
./scripts/status.sh

# 문서 수 확인
doc_count=$(mysql -u mcps_user -p${DB_PASSWORD} mcps_db -se "SELECT COUNT(*) FROM documents")
echo "문서 수: $doc_count"

es_count=$(curl -s "localhost:9200/documents/_count" | jq '.count')
echo "ES 문서 수: $es_count"

echo "=== 복구 완료 ==="
```

#### 10.4.4 재해 복구 계획 (DR)

```
┌─────────────────────────────────────────────────────────────┐
│  재해 복구 시나리오                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 디스크 장애                                              │
│     - 백업 서버에서 최신 백업 복구                           │
│     - RTO: 2시간                                             │
│     - RPO: 1일 (매일 백업)                                   │
│                                                              │
│  2. 서버 전체 장애                                           │
│     - 새 서버에 설치 (setup.sh)                              │
│     - 백업 복구 (restore.sh)                                 │
│     - RTO: 4시간                                             │
│     - RPO: 1일                                               │
│                                                              │
│  3. 데이터센터 장애                                          │
│     - 원격 백업 사이트에서 복구                              │
│     - RTO: 8시간                                             │
│     - RPO: 1주 (주간 백업)                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘

RTO (Recovery Time Objective): 복구 목표 시간
RPO (Recovery Point Objective): 복구 목표 시점 (데이터 손실 허용 범위)
```

### 10.5 유지보수 작업

#### 10.5.1 정기 유지보수 체크리스트

```markdown
# 일일 점검 (Daily)
- [ ] 헬스 체크 확인 (./scripts/status.sh)
- [ ] 에러 로그 확인 (tail -100 data/logs/*/error.log)
- [ ] 디스크 사용량 확인 (df -h)
- [ ] 백업 성공 확인 (ls -lh /backup/mcps/db/)

# 주간 점검 (Weekly)
- [ ] 느린 쿼리 분석 (slow-query.log)
- [ ] ES 클러스터 상태 (/_cluster/health)
- [ ] 로그 파일 정리 (logrotate 확인)
- [ ] 사용자 활동 통계 (audit_logs 분석)
- [ ] 보안 업데이트 확인 (yum check-update)

# 월간 점검 (Monthly)
- [ ] DB 인덱스 최적화 (OPTIMIZE TABLE)
- [ ] ES 인덱스 최적화 (/_forcemerge)
- [ ] 사용하지 않는 문서 아카이빙
- [ ] 권한 설정 검토 (config/permissions.json)
- [ ] 성능 벤치마크 (ab, jmeter)
- [ ] 용량 계획 검토

# 분기별 점검 (Quarterly)
- [ ] 전체 백업/복구 테스트
- [ ] 재해 복구 훈련
- [ ] 보안 감사
- [ ] 아키텍처 리뷰
- [ ] 확장성 검토
```

#### 10.5.2 DB 최적화

```sql
-- 1. 테이블 최적화
OPTIMIZE TABLE documents;
OPTIMIZE TABLE users;
OPTIMIZE TABLE audit_logs;

-- 2. 인덱스 재구성
ALTER TABLE documents DROP INDEX idx_classification;
ALTER TABLE documents ADD INDEX idx_classification (classification);

-- 3. 통계 업데이트
ANALYZE TABLE documents;

-- 4. 오래된 감사 로그 아카이빙 (90일 이상)
CREATE TABLE audit_logs_archive LIKE audit_logs;

INSERT INTO audit_logs_archive
SELECT * FROM audit_logs
WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);

DELETE FROM audit_logs
WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

#### 10.5.3 ES 최적화

```bash
#!/bin/bash
# scripts/optimize_elasticsearch.sh

# 1. 세그먼트 병합 (Forcemerge)
curl -X POST "localhost:9200/documents/_forcemerge?max_num_segments=1"

# 2. 캐시 클리어
curl -X POST "localhost:9200/_cache/clear"

# 3. 인덱스 설정 최적화
curl -X PUT "localhost:9200/documents/_settings" -H 'Content-Type: application/json' -d'
{
  "index": {
    "refresh_interval": "30s",
    "number_of_replicas": 1
  }
}
'

# 4. 오래된 인덱스 삭제 (audit_logs는 월별 인덱스 사용 시)
# audit_logs-2025-10, audit_logs-2025-11, ...
curl -X DELETE "localhost:9200/audit_logs-2025-*"
```

***

## 11. 확장 가이드

### 11.1 새로운 Tool 추가

#### 11.1.1 Tool 개발 절차

```
1. Tool YAML 작성
   /app/poc/mcps/mcp-tools/custom/finance/budget_tool/tool.yaml

2. Handler 구현
   /app/poc/mcps/mcp-tools/custom/finance/budget_tool/handler.py

3. MCP Server 수정 (또는 새 Server 생성)
   /app/poc/mcps/mcp-servers/custom/finance_server/

4. Tool 등록
   ./scripts/register_tool.sh budget_tool finance

5. 테스트
   curl -X POST "localhost:8000/api/tools/execute" \
       -H "Authorization: Bearer $TOKEN" \
       -d '{"tool_name": "budget_tool", "params": {...}}'

6. 권한 설정
   config/permissions.json 업데이트
```

#### 11.1.2 Tool YAML 템플릿

```yaml
# mcp-tools/custom/finance/budget_tool/tool.yaml

name: budget_tool
version: 1.0.0
description: 예산 조회 및 분석 Tool
category: finance
department: finance
author: "재무팀"

server: finance_server

input_schema:
  type: object
  properties:
    year:
      type: integer
      description: 조회할 연도
    department:
      type: string
      description: 부서명
  required:
    - year

output_schema:
  type: object
  properties:
    total_budget:
      type: number
    spent:
      type: number
    remaining:
      type: number

required_permissions:
  - budget:read

examples:
  - name: "2026년 재무팀 예산 조회"
    input:
      year: 2026
      department: "finance"
    output:
      total_budget: 1000000000
      spent: 450000000
      remaining: 550000000
```

### 11.2 새로운 MCP Server 추가

#### 11.2.1 Server 생성 절차

```bash
#!/bin/bash
# scripts/create_mcp_server.sh

SERVER_NAME=$1

if [ -z "$SERVER_NAME" ]; then
    echo "사용법: ./create_mcp_server.sh finance_server"
    exit 1
fi

SERVER_DIR="/app/poc/mcps/mcp-servers/custom/$SERVER_NAME"

# 1. 디렉토리 생성
mkdir -p $SERVER_DIR

# 2. server.yaml 생성
cat > $SERVER_DIR/server.yaml <<EOF
name: $SERVER_NAME
version: 1.0.0
description: Custom MCP Server
tools: []
EOF

# 3. main.py 생성
cat > $SERVER_DIR/main.py <<'EOF'
import sys
import json
from pathlib import Path

# shared 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from database import DatabaseManager
from queries import *
from logging_config import get_logger

logger = get_logger(__name__)

def handle_tool_call(tool_name, params):
    """Tool 호출 처리"""
    # TODO: Tool 로직 구현
    return {"result": "success"}

def main():
    """STDIO 메시지 처리 루프"""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            message = json.loads(line)
            
            if message["method"] == "tools/call":
                tool_name = message["params"]["name"]
                tool_params = message["params"]["arguments"]
                
                result = handle_tool_call(tool_name, tool_params)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "result": result
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                }
            
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        
        except Exception as e:
            logger.error(f"Error: {e}")
            response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
EOF

# 4. requirements.txt 생성
cat > $SERVER_DIR/requirements.txt <<EOF
# shared 모듈 의존성 사용
-e ../../../shared
EOF

# 5. venv 생성
python3 -m venv $SERVER_DIR/venv
source $SERVER_DIR/venv/bin/activate
pip install -r $SERVER_DIR/requirements.txt
deactivate

echo "✅ MCP Server '$SERVER_NAME' 생성 완료"
echo "   경로: $SERVER_DIR"
echo ""
echo "다음 단계:"
echo "  1. $SERVER_DIR/main.py 편집 (Tool 로직 구현)"
echo "  2. $SERVER_DIR/server.yaml 편집 (Tool 메타데이터)"
echo "  3. config/services.json에 서버 추가"
echo "  4. ./scripts/restart_service.sh mcp-host"
```

### 11.3 새로운 부서 추가

#### 11.3.1 부서 온보딩 체크리스트

```markdown
# 새 부서 추가 체크리스트: HR 부서

## 1. 사용자 추가
- [ ] DB에 사용자 추가 (INSERT INTO users)
- [ ] 역할 할당 (junior/staff/manager)
- [ ] 팀 설정 (team = 'hr_team')

## 2. 문서 디렉토리 생성
- [ ] /app/poc/mcps/data/documents/team/hr_team/ 생성
- [ ] 권한 설정 (chown, chmod)

## 3. Tool 개발
- [ ] /app/poc/mcps/mcp-tools/custom/hr/ 생성
- [ ] Tool YAML 작성
- [ ] Handler 구현

## 4. MCP Server 생성 (선택)
- [ ] /app/poc/mcps/mcp-servers/custom/hr_server/ 생성
- [ ] server.yaml 작성
- [ ] main.py 구현

## 5. 권한 설정
- [ ] config/permissions.json 업데이트
  - hr_team 멤버는 hr_team 문서만 접근
  - HR Tool 실행 권한 추가

## 6. 테스트
- [ ] 로그인 테스트
- [ ] 문서 생성/조회 테스트
- [ ] Tool 실행 테스트
- [ ] 권한 체크 테스트

## 7. 문서화
- [ ] Tool 사용 가이드 작성
- [ ] 부서별 권한 매트릭스 업데이트
```

#### 11.3.2 부서별 격리 전략

```
┌─────────────────────────────────────────────────────────────┐
│  부서별 데이터 격리                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 문서 저장소                                              │
│     /data/documents/                                         │
│     ├── public/           (모든 부서 읽기)                   │
│     ├── team/                                                │
│     │   ├── dev_team/    (개발팀만 읽기/쓰기)               │
│     │   ├── hr_team/     (HR팀만 읽기/쓰기)                 │
│     │   └── finance_team/ (재무팀만 읽기/쓰기)              │
│     └── confidential/     (임원, 관리자만)                   │
│                                                              │
│  2. 데이터베이스                                             │
│     documents.team = 'dev_team'  → 개발팀만                 │
│     documents.classification = 'team' → 같은 팀만           │
│                                                              │
│  3. Elasticsearch                                            │
│     filter: {"term": {"team": "dev_team"}}                  │
│                                                              │
│  4. Tool 접근                                                │
│     permissions.json:                                        │
│     {                                                        │
│       "tool": "hr_tool",                                     │
│       "allowed_departments": ["hr"]                          │
│     }                                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 11.4 성능 확장

#### 11.4.1 캐싱 레이어 추가

```python
# shared/cache.py 고도화

from functools import wraps
from datetime import datetime, timedelta
import pickle

class AdvancedCache:
    """고급 캐시 (TTL, LRU)"""
    
    def __init__(self, max_size=1000, default_ttl=300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
    
    def get(self, key):
        """캐시 조회"""
        if key in self.cache:
            entry = self.cache[key]
            
            # TTL 확인
            if datetime.now() < entry["expires_at"]:
                self.access_times[key] = datetime.now()
                return entry["value"]
            else:
                # 만료된 항목 삭제
                del self.cache[key]
                del self.access_times[key]
        
        return None
    
    def set(self, key, value, ttl=None):
        """캐시 저장"""
        if ttl is None:
            ttl = self.default_ttl
        
        # 캐시 크기 초과 시 LRU 제거
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl)
        }
        self.access_times[key] = datetime.now()
    
    def delete(self, key):
        """캐시 삭제"""
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
    
    def clear(self):
        """전체 삭제"""
        self.cache.clear()
        self.access_times.clear()

# 데코레이터
def cached(ttl=300):
    """함수 결과 캐싱 데코레이터"""
    def decorator(func):
        cache = AdvancedCache(default_ttl=ttl)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}:{pickle.dumps((args, kwargs))}"
            
            # 캐시 조회
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 캐시 미스 - 함수 실행
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            
            return result
        
        wrapper.cache = cache  # 캐시 접근용
        return wrapper
    
    return decorator

# 사용 예제
@cached(ttl=600)
def get_user_permissions(user_id):
    """사용자 권한 조회 (10분 캐싱)"""
    return db.execute_query(queries.GET_USER_PERMISSIONS, (user_id,))
```

#### 11.4.2 Read Replica 추가 (향후)

```python
# shared/database.py 확장

class DatabaseManager:
    """DB 연결 관리 (Primary + Replica)"""
    
    def __init__(self, config):
        # Primary (Write)
        self.primary_pool = self._create_pool(config["primary"])
        
        # Replicas (Read)
        self.replica_pools = [
            self._create_pool(replica_config)
            for replica_config in config.get("replicas", [])
        ]
        self.replica_index = 0
    
    def get_connection(self, readonly=False):
        """연결 획득 (readonly 여부에 따라 primary/replica 선택)"""
        if readonly and self.replica_pools:
            # Round-robin으로 replica 선택
            pool = self.replica_pools[self.replica_index]
            self.replica_index = (self.replica_index + 1) % len(self.replica_pools)
            return pool.connection()
        else:
            return self.primary_pool.connection()
    
    def execute_query(self, sql, params=None, readonly=True):
        """쿼리 실행"""
        conn = self.get_connection(readonly=readonly)
        # ... 나머지 동일
```

***

## 12. 참고 자료

### 12.1 외부 문서

| 항목 | 링크 | 설명 |
|------|------|------|
| **MCP Specification** | https://modelcontextprotocol.io/spec | MCP 프로토콜 공식 명세 |
| **FastAPI** | https://fastapi.tiangolo.com | FastAPI 공식 문서 |
| **Reflex** | https://reflex.dev/docs | Reflex 공식 문서 |
| **MariaDB** | https://mariadb.com/kb/en | MariaDB 지식 베이스 |
| **Elasticsearch** | https://www.elastic.co/guide/en/elasticsearch/reference/8.x | ES 8.x 문서 |
| **Python** | https://docs.python.org/3.10 | Python 3.10 문서 |

### 12.2 내부 문서

| 문서명 | 경로 | 설명 |
|--------|------|------|
| **01. shared 공유모듈 설계서** | docs/01_shared_설계서.md | 공유 모듈 상세 설계 |
| **02. config 및 스키마 설계서** | docs/02_config_설계서.md | DB/ES 스키마 정의 |
| **04. MCP Servers 설계서** | docs/04_mcp_servers_설계서.md | 5개 서버 상세 설계 |
| **05. MCP Host 설계서** | docs/05_mcp_host_설계서.md | 백엔드 상세 설계 |
| **Tool 개발 가이드** | docs/03_mcp_tools_설계서.md | Tool 작성 방법 |
| **배포 가이드** | docs/10_배포_가이드.md | 설치 및 배포 절차 |

### 12.3 관련 기술

| 기술 | 버전 | 학습 자료 |
|------|------|----------|
| **JSON-RPC 2.0** | 2.0 | https://www.jsonrpc.org/specification |
| **JWT** | RFC 7519 | https://jwt.io/introduction |
| **RESTful API** | - | https://restfulapi.net |
| **RBAC** | - | https://en.wikipedia.org/wiki/Role-based_access_control |
| **ACID** | - | https://en.wikipedia.org/wiki/ACID |

### 12.4 예제 코드

```python
# examples/simple_mcp_client.py
"""간단한 MCP 클라이언트 예제"""

import subprocess
import json

def call_mcp_tool(server_path, tool_name, params):
    """MCP Server에 Tool 호출"""
    
    # MCP Server 프로세스 시작
    process = subprocess.Popen(
        ["python", f"{server_path}/main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # JSON-RPC 요청 생성
    request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": params
        }
    }
    
    # STDIO로 전송
    process.stdin.write((json.dumps(request) + "\n").encode())
    process.stdin.flush()
    
    # 응답 읽기
    response_line = process.stdout.readline().decode()
    response = json.loads(response_line)
    
    # 프로세스 종료
    process.terminate()
    
    if "result" in response:
        return response["result"]
    else:
        raise Exception(response["error"]["message"])

# 사용 예제
if __name__ == "__main__":
    result = call_mcp_tool(
        server_path="mcp-servers/core/search_server",
        tool_name="search_documents",
        params={
            "query": "예산",
            "limit": 10
        }
    )
    
    print(f"검색 결과: {result['total']}건")
    for doc in result['results']:
        print(f"  - {doc['title']}")
```

***

## 13. 부록

### 13.1 용어 정의

| 용어 | 설명 |
|------|------|
| **MCP** | Model Context Protocol - AI 모델과 도구 간 통신 프로토콜 |
| **Tool** | 특정 작업을 수행하는 실행 가능한 함수 |
| **MCP Server** | Tool을 호스팅하고 STDIO로 통신하는 프로세스 |
| **MCP Host** | MCP Server를 관리하고 Tool을 라우팅하는 중앙 시스템 |
| **STDIO** | Standard Input/Output - 표준 입출력 스트림 |
| **JSON-RPC** | JSON 기반 원격 프로시저 호출 프로토콜 |
| **RBAC** | Role-Based Access Control - 역할 기반 접근 제어 |
| **JWT** | JSON Web Token - JSON 기반 인증 토큰 |
| **TTL** | Time To Live - 캐시 유효 시간 |
| **RTO** | Recovery Time Objective - 복구 목표 시간 |
| **RPO** | Recovery Point Objective - 복구 목표 시점 |

### 13.2 에러 코드

| 코드 | 이름 | 설명 | 해결 방법 |
|------|------|------|----------|
| **-32700** | Parse error | JSON 파싱 실패 | 요청 형식 확인 |
| **-32600** | Invalid Request | 잘못된 요청 구조 | JSON-RPC 명세 확인 |
| **-32601** | Method not found | 메서드 없음 | Tool 이름 확인 |
| **-32602** | Invalid params | 파라미터 오류 | 파라미터 스키마 확인 |
| **-32603** | Internal error | 내부 에러 | 서버 로그 확인 |
| **1001** | Permission denied | 권한 없음 | 권한 설정 확인 |
| **1002** | Resource not found | 리소스 없음 | ID 확인 |
| **1003** | Database error | DB 에러 | DB 연결 확인 |
| **1004** | Elasticsearch error | ES 에러 | ES 상태 확인 |
| **1005** | Timeout | 타임아웃 | 서버 부하 확인 |

### 13.3 환경 변수

```bash
# .env 예제

# Application
APP_NAME=mcps
APP_VERSION=1.0.0
APP_ENV=production
DEBUG=false

# Network
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8000
MCP_HOST_HOST=127.0.0.1
MCP_HOST_PORT=8080
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=8501

# Database (MariaDB)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mcps_db
DB_USER=mcps_user
DB_PASSWORD=secure_password_here
DB_POOL_MIN=5
DB_POOL_MAX=20

# Elasticsearch
ES_HOSTS=localhost:9200
ES_USER=elastic
ES_PASSWORD=elastic_password_here
ES_TIMEOUT=30

# JWT
JWT_SECRET_KEY=super_secret_key_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=10

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# MCP
MCP_STDIO_TIMEOUT=30
MCP_SERVER_RESTART_DELAY=5
```

### 13.4 SQL 스키마 요약

```sql
-- 핵심 테이블 (간략)

CREATE TABLE users (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role ENUM('junior', 'staff', 'manager', 'executive', 'admin'),
    team VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    classification ENUM('public', 'team', 'confidential'),
    author_id VARCHAR(10),
    team VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id)
);

CREATE TABLE permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(10),
    role VARCHAR(20),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    actions JSON,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(10),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    result VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 13.5 Elasticsearch 인덱스 요약

```json
{
  "documents": {
    "mappings": {
      "properties": {
        "doc_id": {"type": "keyword"},
        "title": {"type": "text", "analyzer": "nori"},
        "content": {"type": "text", "analyzer": "nori"},
        "classification": {"type": "keyword"},
        "team": {"type": "keyword"},
        "created_at": {"type": "date"}
      }
    }
  },
  "audit_logs": {
    "mappings": {
      "properties": {
        "user_id": {"type": "keyword"},
        "action": {"type": "keyword"},
        "resource_type": {"type": "keyword"},
        "timestamp": {"type": "date"}
      }
    }
  }
}
```

***

## 14. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 15. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **작성자** | | | |
| **검토자** | | | |
| **승인자** | | | |

***

**문서 끝**

***

