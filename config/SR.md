# config 및 데이터 스키마 설계서

***

# 02. MCP 에코시스템 - config 및 데이터 스키마 설계서

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/config/`, `/app/poc/mcps/data/`  
**목적**: 설정 파일 및 데이터베이스/Elasticsearch 스키마 정의

***

## 목차

1. [개요](#1-개요)
2. [설정 파일 (config/)](#2-설정-파일-config)
3. [MariaDB 스키마](#3-mariadb-스키마)
4. [Elasticsearch 인덱스](#4-elasticsearch-인덱스)
5. [데이터 마이그레이션](#5-데이터-마이그레이션)
6. [샘플 데이터](#6-샘플-데이터)

***

## 1. 개요

### 1.1 목적

이 문서는 MCP 에코시스템의 모든 설정 파일과 데이터 스키마를 정의합니다.

### 1.2 구조

```
/app/poc/mcps/
├── config/                      # 설정 파일
│   ├── registry.json            # Tool 레지스트리
│   ├── permissions.json         # 권한 설정
│   ├── users.json               # 사용자 목록
│   └── services.json            # MCP Server 설정
│
└── data/                        # 데이터 저장소
    ├── database/                # MariaDB
    │   ├── schema.sql           # 스키마 정의
    │   ├── indexes.sql          # 인덱스
    │   ├── triggers.sql         # 트리거
    │   └── seed_data.sql        # 초기 데이터
    │
    └── elasticsearch/           # Elasticsearch
        └── mappings/
            ├── documents.json   # 문서 인덱스 매핑
            └── audit_logs.json  # 감사 로그 매핑
```

***

## 2. 설정 파일 (config/)

### 2.1 registry.json - Tool 레지스트리

**목적**: Tool 메타데이터 중앙 관리

```json
{
  "version": "1.0.0",
  "updated_at": "2026-01-08T10:00:00Z",
  "tools": [
    {
      "name": "search_documents",
      "description": "문서 전문 검색",
      "category": "search",
      "department": "core",
      "version": "1.0.0",
      "server": "search_server",
      "enabled": true,
      "required_permissions": ["document:read"],
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "검색어"
          },
          "classification": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["public", "team", "confidential"]
            },
            "description": "문서 등급 필터"
          },
          "category": {
            "type": "string",
            "description": "카테고리 필터"
          },
          "limit": {
            "type": "integer",
            "default": 10,
            "minimum": 1,
            "maximum": 100
          }
        },
        "required": ["query"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "total": {
            "type": "integer"
          },
          "results": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "doc_id": {"type": "string"},
                "title": {"type": "string"},
                "snippet": {"type": "string"},
                "classification": {"type": "string"},
                "score": {"type": "number"}
              }
            }
          }
        }
      },
      "examples": [
        {
          "name": "공개 문서 검색",
          "input": {
            "query": "예산",
            "classification": ["public"],
            "limit": 10
          },
          "output": {
            "total": 5,
            "results": [
              {
                "doc_id": "DOC001",
                "title": "2026년 예산 계획",
                "snippet": "...예산...",
                "classification": "public",
                "score": 8.5
              }
            ]
          }
        }
      ]
    },
    {
      "name": "get_document",
      "description": "문서 상세 조회",
      "category": "document",
      "department": "core",
      "version": "1.0.0",
      "server": "document_server",
      "enabled": true,
      "required_permissions": ["document:read"],
      "input_schema": {
        "type": "object",
        "properties": {
          "doc_id": {
            "type": "string",
            "description": "문서 ID"
          }
        },
        "required": ["doc_id"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "doc_id": {"type": "string"},
          "title": {"type": "string"},
          "content": {"type": "string"},
          "classification": {"type": "string"},
          "author_id": {"type": "string"},
          "created_at": {"type": "string"},
          "updated_at": {"type": "string"}
        }
      }
    },
    {
      "name": "create_document",
      "description": "문서 생성",
      "category": "document",
      "department": "core",
      "version": "1.0.0",
      "server": "document_server",
      "enabled": true,
      "required_permissions": ["document:create"],
      "input_schema": {
        "type": "object",
        "properties": {
          "title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 255
          },
          "content": {
            "type": "string"
          },
          "classification": {
            "type": "string",
            "enum": ["public", "team", "confidential"]
          },
          "category": {
            "type": "string"
          }
        },
        "required": ["title", "content", "classification"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "doc_id": {"type": "string"},
          "message": {"type": "string"}
        }
      }
    },
    {
      "name": "update_document",
      "description": "문서 수정",
      "category": "document",
      "department": "core",
      "version": "1.0.0",
      "server": "document_server",
      "enabled": true,
      "required_permissions": ["document:update"],
      "input_schema": {
        "type": "object",
        "properties": {
          "doc_id": {"type": "string"},
          "title": {"type": "string"},
          "content": {"type": "string"},
          "classification": {"type": "string"}
        },
        "required": ["doc_id"]
      }
    },
    {
      "name": "delete_document",
      "description": "문서 삭제",
      "category": "document",
      "department": "core",
      "version": "1.0.0",
      "server": "document_server",
      "enabled": true,
      "required_permissions": ["document:delete"],
      "input_schema": {
        "type": "object",
        "properties": {
          "doc_id": {"type": "string"}
        },
        "required": ["doc_id"]
      }
    },
    {
      "name": "list_documents",
      "description": "문서 목록 조회",
      "category": "document",
      "department": "core",
      "version": "1.0.0",
      "server": "document_server",
      "enabled": true,
      "required_permissions": ["document:read"],
      "input_schema": {
        "type": "object",
        "properties": {
          "classification": {
            "type": "array",
            "items": {"type": "string"}
          },
          "category": {"type": "string"},
          "limit": {"type": "integer", "default": 20},
          "offset": {"type": "integer", "default": 0}
        }
      }
    },
    {
      "name": "get_document_versions",
      "description": "문서 버전 히스토리 조회",
      "category": "version",
      "department": "core",
      "version": "1.0.0",
      "server": "version_server",
      "enabled": true,
      "required_permissions": ["document:read"],
      "input_schema": {
        "type": "object",
        "properties": {
          "doc_id": {"type": "string"}
        },
        "required": ["doc_id"]
      }
    },
    {
      "name": "authenticate",
      "description": "사용자 인증 (PoC에서는 선택만)",
      "category": "auth",
      "department": "core",
      "version": "1.0.0",
      "server": "auth_server",
      "enabled": true,
      "required_permissions": [],
      "input_schema": {
        "type": "object",
        "properties": {
          "user_id": {"type": "string"}
        },
        "required": ["user_id"]
      }
    },
    {
      "name": "request_access",
      "description": "문서 접근 권한 요청",
      "category": "auth",
      "department": "core",
      "version": "1.0.0",
      "server": "auth_server",
      "enabled": true,
      "required_permissions": [],
      "input_schema": {
        "type": "object",
        "properties": {
          "doc_id": {"type": "string"},
          "reason": {"type": "string"}
        },
        "required": ["doc_id", "reason"]
      }
    },
    {
      "name": "get_audit_logs",
      "description": "감사 로그 조회",
      "category": "audit",
      "department": "core",
      "version": "1.0.0",
      "server": "audit_server",
      "enabled": true,
      "required_permissions": ["admin:manage"],
      "input_schema": {
        "type": "object",
        "properties": {
          "user_id": {"type": "string"},
          "action": {"type": "string"},
          "start_date": {"type": "string"},
          "end_date": {"type": "string"},
          "limit": {"type": "integer", "default": 100}
        }
      }
    }
  ]
}
```

### 2.2 permissions.json - 권한 설정

**목적**: RBAC 권한 매트릭스 정의

```json
{
  "version": "1.0.0",
  "roles": {
    "junior": {
      "description": "신입 사원",
      "level": 1,
      "document": {
        "public": ["read"],
        "team": [],
        "confidential": []
      },
      "tools": {
        "allowed": [
          "search_documents",
          "get_document",
          "list_documents"
        ],
        "denied": []
      },
      "admin": []
    },
    "staff": {
      "description": "일반 사원",
      "level": 2,
      "document": {
        "public": ["read", "create", "update"],
        "team": ["read", "create", "update"],
        "confidential": []
      },
      "tools": {
        "allowed": [
          "search_documents",
          "get_document",
          "list_documents",
          "create_document",
          "update_document",
          "get_document_versions"
        ],
        "denied": []
      },
      "admin": []
    },
    "manager": {
      "description": "팀 관리자",
      "level": 3,
      "document": {
        "public": ["read", "create", "update", "delete"],
        "team": ["read", "create", "update", "delete"],
        "confidential": []
      },
      "tools": {
        "allowed": ["*"],
        "denied": ["get_audit_logs"]
      },
      "admin": ["approve_access_request"]
    },
    "executive": {
      "description": "임원",
      "level": 4,
      "document": {
        "public": ["read"],
        "team": ["read"],
        "confidential": ["read"]
      },
      "tools": {
        "allowed": ["*"],
        "denied": ["get_audit_logs"]
      },
      "admin": []
    },
    "admin": {
      "description": "시스템 관리자",
      "level": 5,
      "document": {
        "all": ["read", "create", "update", "delete"]
      },
      "tools": {
        "allowed": ["*"],
        "denied": []
      },
      "admin": ["*"]
    }
  },
  "document_classifications": {
    "public": {
      "description": "공개 문서",
      "color": "#28a745",
      "min_role_level": 1
    },
    "team": {
      "description": "팀 문서",
      "color": "#ffc107",
      "min_role_level": 2,
      "team_restriction": true
    },
    "confidential": {
      "description": "기밀 문서",
      "color": "#dc3545",
      "min_role_level": 4
    }
  },
  "special_permissions": [
    {
      "user_id": "U001",
      "permissions": ["document:DOC999:read"],
      "reason": "특별 승인",
      "granted_by": "U000",
      "granted_at": "2026-01-01T00:00:00Z",
      "expires_at": "2026-12-31T23:59:59Z"
    }
  ]
}
```

### 2.3 users.json - 사용자 목록

**목적**: PoC용 사용자 데이터 (실제 운영에서는 DB)

```json
{
  "version": "1.0.0",
  "users": [
    {
      "id": "U001",
      "name": "김신입",
      "email": "junior@company.com",
      "role": "junior",
      "team": "dev_team",
      "department": "개발팀",
      "position": "사원",
      "created_at": "2026-01-01T00:00:00Z",
      "active": true
    },
    {
      "id": "U002",
      "name": "이사원",
      "email": "staff@company.com",
      "role": "staff",
      "team": "dev_team",
      "department": "개발팀",
      "position": "대리",
      "created_at": "2025-01-01T00:00:00Z",
      "active": true
    },
    {
      "id": "U003",
      "name": "박매니저",
      "email": "manager@company.com",
      "role": "manager",
      "team": "dev_team",
      "department": "개발팀",
      "position": "과장",
      "created_at": "2024-01-01T00:00:00Z",
      "active": true
    },
    {
      "id": "U004",
      "name": "최임원",
      "email": "executive@company.com",
      "role": "executive",
      "team": null,
      "department": "경영진",
      "position": "이사",
      "created_at": "2020-01-01T00:00:00Z",
      "active": true
    },
    {
      "id": "U000",
      "name": "관리자",
      "email": "admin@company.com",
      "role": "admin",
      "team": null,
      "department": "IT팀",
      "position": "시스템 관리자",
      "created_at": "2020-01-01T00:00:00Z",
      "active": true
    },
    {
      "id": "U005",
      "name": "정사원",
      "email": "staff2@company.com",
      "role": "staff",
      "team": "hr_team",
      "department": "인사팀",
      "position": "대리",
      "created_at": "2025-06-01T00:00:00Z",
      "active": true
    },
    {
      "id": "U006",
      "name": "강대리",
      "email": "staff3@company.com",
      "role": "staff",
      "team": "finance_team",
      "department": "재무팀",
      "position": "대리",
      "created_at": "2025-03-01T00:00:00Z",
      "active": true
    }
  ],
  "teams": [
    {
      "id": "dev_team",
      "name": "개발팀",
      "description": "소프트웨어 개발",
      "manager_id": "U003",
      "members": ["U001", "U002", "U003"]
    },
    {
      "id": "hr_team",
      "name": "인사팀",
      "description": "인사 관리",
      "manager_id": null,
      "members": ["U005"]
    },
    {
      "id": "finance_team",
      "name": "재무팀",
      "description": "재무 관리",
      "manager_id": null,
      "members": ["U006"]
    }
  ]
}
```

### 2.4 services.json - MCP Server 설정

**목적**: MCP Server 실행 설정

```json
{
  "version": "1.0.0",
  "servers": [
    {
      "name": "auth_server",
      "description": "인증 및 권한 관리",
      "path": "/app/poc/mcps/mcp-servers/core/auth_server",
      "python": "/app/poc/mcps/mcp-servers/core/auth_server/venv/bin/python",
      "main": "main.py",
      "enabled": true,
      "auto_start": true,
      "restart_on_failure": true,
      "max_restarts": 3,
      "env": {
        "PYTHONPATH": "/app/poc/mcps",
        "LOG_LEVEL": "INFO"
      },
      "timeout": 30,
      "health_check": {
        "enabled": true,
        "interval": 60,
        "timeout": 5
      }
    },
    {
      "name": "search_server",
      "description": "문서 검색",
      "path": "/app/poc/mcps/mcp-servers/core/search_server",
      "python": "/app/poc/mcps/mcp-servers/core/search_server/venv/bin/python",
      "main": "main.py",
      "enabled": true,
      "auto_start": true,
      "restart_on_failure": true,
      "max_restarts": 3,
      "env": {
        "PYTHONPATH": "/app/poc/mcps",
        "LOG_LEVEL": "INFO"
      },
      "timeout": 30
    },
    {
      "name": "document_server",
      "description": "문서 CRUD",
      "path": "/app/poc/mcps/mcp-servers/core/document_server",
      "python": "/app/poc/mcps/mcp-servers/core/document_server/venv/bin/python",
      "main": "main.py",
      "enabled": true,
      "auto_start": true,
      "restart_on_failure": true,
      "max_restarts": 3,
      "env": {
        "PYTHONPATH": "/app/poc/mcps",
        "LOG_LEVEL": "INFO"
      },
      "timeout": 30
    },
    {
      "name": "version_server",
      "description": "문서 버전 관리",
      "path": "/app/poc/mcps/mcp-servers/core/version_server",
      "python": "/app/poc/mcps/mcp-servers/core/version_server/venv/bin/python",
      "main": "main.py",
      "enabled": true,
      "auto_start": true,
      "restart_on_failure": true,
      "max_restarts": 3,
      "env": {
        "PYTHONPATH": "/app/poc/mcps",
        "LOG_LEVEL": "INFO"
      },
      "timeout": 30
    },
    {
      "name": "audit_server",
      "description": "감사 로그",
      "path": "/app/poc/mcps/mcp-servers/core/audit_server",
      "python": "/app/poc/mcps/mcp-servers/core/audit_server/venv/bin/python",
      "main": "main.py",
      "enabled": true,
      "auto_start": true,
      "restart_on_failure": true,
      "max_restarts": 3,
      "env": {
        "PYTHONPATH": "/app/poc/mcps",
        "LOG_LEVEL": "INFO"
      },
      "timeout": 30
    }
  ]
}
```

***

## 3. MariaDB 스키마

### 3.1 schema.sql - 전체 스키마

```sql
-- MariaDB 10.11+ 스키마
-- 데이터베이스: mcps_db
-- 문자셋: utf8mb4
-- 콜레이션: utf8mb4_unicode_ci

-- ============================================
-- 데이터베이스 생성
-- ============================================

CREATE DATABASE IF NOT EXISTS mcps_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE mcps_db;

-- ============================================
-- 1. 사용자 테이블 (users)
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(10) PRIMARY KEY COMMENT '사용자 ID (예: U001)',
    name VARCHAR(100) NOT NULL COMMENT '이름',
    email VARCHAR(255) UNIQUE COMMENT '이메일',
    role ENUM('junior', 'staff', 'manager', 'executive', 'admin') NOT NULL COMMENT '역할',
    team VARCHAR(50) COMMENT '팀 (예: dev_team)',
    department VARCHAR(100) COMMENT '부서',
    position VARCHAR(50) COMMENT '직급',
    active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    
    INDEX idx_role (role),
    INDEX idx_team (team),
    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='사용자';

-- ============================================
-- 2. 문서 테이블 (documents)
-- ============================================

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(50) PRIMARY KEY COMMENT '문서 ID (예: DOC_A1B2C3D4)',
    title VARCHAR(255) NOT NULL COMMENT '제목',
    content TEXT COMMENT '내용 (Markdown)',
    classification ENUM('public', 'team', 'confidential') NOT NULL DEFAULT 'public' COMMENT '등급',
    category VARCHAR(50) COMMENT '카테고리 (예: finance, hr)',
    author_id VARCHAR(10) NOT NULL COMMENT '작성자 ID',
    team VARCHAR(50) COMMENT '팀 (team 등급인 경우)',
    file_path VARCHAR(500) COMMENT '파일 경로',
    version INT DEFAULT 1 COMMENT '버전',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE RESTRICT,
    
    INDEX idx_classification (classification),
    INDEX idx_category (category),
    INDEX idx_author (author_id),
    INDEX idx_team (team),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at),
    
    FULLTEXT INDEX ft_title_content (title, content) WITH PARSER ngram
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='문서';

-- ============================================
-- 3. 문서 버전 테이블 (document_versions)
-- ============================================

CREATE TABLE IF NOT EXISTS document_versions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL COMMENT '문서 ID',
    version INT NOT NULL COMMENT '버전 번호',
    title VARCHAR(255) NOT NULL COMMENT '제목',
    content TEXT COMMENT '내용',
    changed_by VARCHAR(10) NOT NULL COMMENT '수정자 ID',
    change_summary VARCHAR(500) COMMENT '변경 요약',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE RESTRICT,
    
    UNIQUE KEY uk_doc_version (document_id, version),
    INDEX idx_document (document_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='문서 버전 히스토리';

-- ============================================
-- 4. 권한 테이블 (permissions)
-- ============================================

CREATE TABLE IF NOT EXISTS permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(10) COMMENT '사용자 ID (NULL이면 역할 기반)',
    role VARCHAR(20) COMMENT '역할 (NULL이면 사용자 기반)',
    resource_type VARCHAR(50) NOT NULL COMMENT '리소스 타입 (document, tool, server)',
    resource_id VARCHAR(100) NOT NULL COMMENT '리소스 ID',
    actions JSON NOT NULL COMMENT '허용된 액션 ["read", "write", "delete"]',
    granted_by VARCHAR(10) COMMENT '부여자 ID',
    reason VARCHAR(500) COMMENT '부여 사유',
    expires_at TIMESTAMP NULL COMMENT '만료일',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_user (user_id),
    INDEX idx_role (role),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='권한';

-- ============================================
-- 5. Tool 레지스트리 테이블 (tools)
-- ============================================

CREATE TABLE IF NOT EXISTS tools (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL COMMENT 'Tool 이름',
    description VARCHAR(500) COMMENT '설명',
    category VARCHAR(50) COMMENT '카테고리',
    department VARCHAR(50) COMMENT '부서',
    version VARCHAR(20) NOT NULL COMMENT '버전',
    server_name VARCHAR(100) NOT NULL COMMENT 'MCP Server 이름',
    metadata JSON COMMENT '메타데이터 (input_schema, output_schema 등)',
    enabled BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    usage_count INT DEFAULT 0 COMMENT '사용 횟수',
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '등록일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    
    INDEX idx_category (category),
    INDEX idx_department (department),
    INDEX idx_server (server_name),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tool 레지스트리';

-- ============================================
-- 6. MCP Server 테이블 (servers)
-- ============================================

CREATE TABLE IF NOT EXISTS servers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL COMMENT 'Server 이름',
    description VARCHAR(500) COMMENT '설명',
    status ENUM('running', 'stopped', 'error') DEFAULT 'stopped' COMMENT '상태',
    host VARCHAR(255) DEFAULT 'localhost' COMMENT '호스트',
    port INT COMMENT '포트 (선택)',
    pid INT COMMENT '프로세스 ID',
    started_at TIMESTAMP NULL COMMENT '시작 시간',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    
    INDEX idx_status (status),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='MCP Server';

-- ============================================
-- 7. 감사 로그 테이블 (audit_logs)
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(10) COMMENT '사용자 ID',
    action VARCHAR(100) NOT NULL COMMENT '액션 (예: document_view, tool_execute)',
    resource_type VARCHAR(50) COMMENT '리소스 타입',
    resource_id VARCHAR(100) COMMENT '리소스 ID',
    details JSON COMMENT '상세 정보',
    result ENUM('success', 'failure') DEFAULT 'success' COMMENT '결과',
    ip_address VARCHAR(45) COMMENT 'IP 주소',
    user_agent VARCHAR(500) COMMENT 'User Agent',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_result (result),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='감사 로그';

-- ============================================
-- 8. 접근 요청 테이블 (access_requests)
-- ============================================

CREATE TABLE IF NOT EXISTS access_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(10) NOT NULL COMMENT '요청자 ID',
    resource_type VARCHAR(50) NOT NULL COMMENT '리소스 타입',
    resource_id VARCHAR(100) NOT NULL COMMENT '리소스 ID',
    reason VARCHAR(1000) NOT NULL COMMENT '요청 사유',
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' COMMENT '상태',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '요청일',
    reviewed_at TIMESTAMP NULL COMMENT '검토일',
    reviewed_by VARCHAR(10) COMMENT '검토자 ID',
    review_comment VARCHAR(1000) COMMENT '검토 의견',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_requested_at (requested_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='접근 요청';

-- ============================================
-- 9. 시스템 설정 테이블 (system_settings)
-- ============================================

CREATE TABLE IF NOT EXISTS system_settings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(100) UNIQUE NOT NULL COMMENT '설정 키',
    value_text TEXT COMMENT '값 (텍스트)',
    value_json JSON COMMENT '값 (JSON)',
    description VARCHAR(500) COMMENT '설명',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    updated_by VARCHAR(10) COMMENT '수정자 ID',
    
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_key (key_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='시스템 설정';
```

### 3.2 indexes.sql - 추가 인덱스

```sql
-- 추가 인덱스 (성능 최적화)

USE mcps_db;

-- 복합 인덱스

-- documents: 등급 + 팀 (team 문서 필터링 최적화)
CREATE INDEX idx_classification_team ON documents(classification, team);

-- documents: 작성자 + 생성일 (작성자별 최신 문서)
CREATE INDEX idx_author_created ON documents(author_id, created_at DESC);

-- audit_logs: 사용자 + 생성일 (사용자별 활동 조회)
CREATE INDEX idx_user_created ON audit_logs(user_id, created_at DESC);

-- audit_logs: 액션 + 결과 (실패한 액션 조회)
CREATE INDEX idx_action_result ON audit_logs(action, result);

-- permissions: 리소스 + 만료일 (유효한 권한 조회)
CREATE INDEX idx_resource_expires ON permissions(resource_type, resource_id, expires_at);

-- 커버링 인덱스 (자주 조회되는 컬럼만 포함)

-- documents 목록 조회용
CREATE INDEX idx_list_documents ON documents(
    classification, 
    team, 
    updated_at DESC
) INCLUDE (id, title, author_id, category);

-- 통계 쿼리용 인덱스

-- 일별 문서 수
CREATE INDEX idx_documents_date ON documents(DATE(created_at));

-- 일별 감사 로그 수
CREATE INDEX idx_audit_date ON audit_logs(DATE(created_at));
```

### 3.3 triggers.sql - 트리거

```sql
-- 트리거

USE mcps_db;

-- ============================================
-- 1. 문서 버전 자동 생성
-- ============================================

DELIMITER //

CREATE TRIGGER trg_document_version_insert
AFTER INSERT ON documents
FOR EACH ROW
BEGIN
    INSERT INTO document_versions (
        document_id,
        version,
        title,
        content,
        changed_by,
        change_summary
    ) VALUES (
        NEW.id,
        NEW.version,
        NEW.title,
        NEW.content,
        NEW.author_id,
        'Initial version'
    );
END//

CREATE TRIGGER trg_document_version_update
AFTER UPDATE ON documents
FOR EACH ROW
BEGIN
    IF NEW.title != OLD.title OR NEW.content != OLD.content THEN
        INSERT INTO document_versions (
            document_id,
            version,
            title,
            content,
            changed_by,
            change_summary
        ) VALUES (
            NEW.id,
            NEW.version,
            NEW.title,
            NEW.content,
            NEW.author_id,
            'Document updated'
        );
    END IF;
END//

DELIMITER ;

-- ============================================
-- 2. Tool 사용 횟수 자동 증가
-- ============================================

-- Note: 애플리케이션 레벨에서 처리 권장
-- UPDATE tools SET usage_count = usage_count + 1 WHERE name = ?

-- ============================================
-- 3. 감사 로그 자동 기록 (선택)
-- ============================================

DELIMITER //

CREATE TRIGGER trg_audit_document_delete
BEFORE DELETE ON documents
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (
        user_id,
        action,
        resource_type,
        resource_id,
        details,
        result
    ) VALUES (
        @current_user_id,
        'document_delete',
        'document',
        OLD.id,
        JSON_OBJECT('title', OLD.title),
        'success'
    );
END//

DELIMITER ;
```




### 3.4 seed_data.sql - 초기 데이터

```sql
-- 초기 데이터 (샘플)

USE mcps_db;

-- ============================================
-- 1. 사용자 데이터
-- ============================================

INSERT INTO users (id, name, email, role, team, department, position, active) VALUES
('U000', '관리자', 'admin@company.com', 'admin', NULL, 'IT팀', '시스템 관리자', TRUE),
('U001', '김신입', 'junior@company.com', 'junior', 'dev_team', '개발팀', '사원', TRUE),
('U002', '이사원', 'staff@company.com', 'staff', 'dev_team', '개발팀', '대리', TRUE),
('U003', '박매니저', 'manager@company.com', 'manager', 'dev_team', '개발팀', '과장', TRUE),
('U004', '최임원', 'executive@company.com', 'executive', NULL, '경영진', '이사', TRUE),
('U005', '정사원', 'staff2@company.com', 'staff', 'hr_team', '인사팀', '대리', TRUE),
('U006', '강대리', 'staff3@company.com', 'staff', 'finance_team', '재무팀', '대리', TRUE);

-- ============================================
-- 2. 문서 데이터 (샘플)
-- ============================================

INSERT INTO documents (id, title, content, classification, category, author_id, team) VALUES
-- Public 문서
('DOC001', '회사 소개', 
'# 회사 소개

우리 회사는 2020년에 설립된 혁신적인 IT 기업입니다.

## 비전
글로벌 리더가 되는 것

## 미션
최고의 제품과 서비스 제공',
'public', 'general', 'U000', NULL),

('DOC002', '2026년 신년사', 
'# 2026년 신년사

존경하는 임직원 여러분,

새해를 맞이하여 모두에게 건강과 행복이 가득하기를 기원합니다.

올해 우리는 더 큰 도약을 준비하고 있습니다...',
'public', 'general', 'U004', NULL),

('DOC003', '복지 제도 안내', 
'# 복지 제도

## 1. 건강 검진
- 연 1회 종합 건강 검진 지원

## 2. 식사 지원
- 중식 지원 (1만원/일)

## 3. 교육 지원
- 외부 교육 수강료 지원 (연 300만원)',
'public', 'hr', 'U005', NULL),

-- Team 문서 (dev_team)
('DOC004', '개발팀 코딩 컨벤션', 
'# 코딩 컨벤션

## Python
- PEP 8 준수
- 함수명: snake_case
- 클래스명: PascalCase

## Git
- 커밋 메시지: [타입] 제목
- 브랜치: feature/기능명',
'team', 'development', 'U003', 'dev_team'),

('DOC005', 'Q1 개발 계획', 
'# 2026 Q1 개발 계획

## 목표
- MCP 에코시스템 구축
- 문서 관리 시스템 완성

## 일정
- 1월: 설계 완료
- 2월: 개발
- 3월: 테스트 및 배포',
'team', 'development', 'U002', 'dev_team'),

-- Team 문서 (hr_team)
('DOC006', '인사 평가 기준', 
'# 인사 평가 기준 (내부용)

## 평가 항목
1. 업무 성과 (50%)
2. 역량 (30%)
3. 태도 (20%)

## 평가 등급
- S: 탁월
- A: 우수
- B: 보통
- C: 미흡',
'team', 'hr', 'U005', 'hr_team'),

-- Team 문서 (finance_team)
('DOC007', '2026년 예산 계획', 
'# 2026년 예산 계획

## 총 예산
- 100억원 (전년 대비 10% 증가)

## 부서별 배분
- 개발팀: 40억
- 마케팅팀: 30억
- 인사팀: 10억
- 관리팀: 20억',
'team', 'finance', 'U006', 'finance_team'),

-- Confidential 문서
('DOC008', '경영 전략 (기밀)', 
'# 2026년 경영 전략

## 신규 사업
- AI 플랫폼 개발
- 글로벌 확장

## M&A 계획
- 목표: 중소 IT 기업 2곳 인수

## 재무 목표
- 매출: 500억
- 영업이익률: 20%',
'confidential', 'management', 'U004', NULL),

('DOC009', '임원 연봉 정보', 
'# 임원 연봉 정보 (극비)

## 2026년 연봉
- CEO: 2억
- CTO: 1.5억
- CFO: 1.5억
- 이사: 1억',
'confidential', 'hr', 'U004', NULL);

-- ============================================
-- 3. Tool 레지스트리
-- ============================================

INSERT INTO tools (name, description, category, department, version, server_name, enabled, metadata) VALUES
('search_documents', '문서 전문 검색', 'search', 'core', '1.0.0', 'search_server', TRUE, 
 JSON_OBJECT(
     'input_schema', JSON_OBJECT(
         'type', 'object',
         'properties', JSON_OBJECT(
             'query', JSON_OBJECT('type', 'string'),
             'limit', JSON_OBJECT('type', 'integer', 'default', 10)
         ),
         'required', JSON_ARRAY('query')
     )
 )),

('get_document', '문서 상세 조회', 'document', 'core', '1.0.0', 'document_server', TRUE, 
 JSON_OBJECT(
     'input_schema', JSON_OBJECT(
         'type', 'object',
         'properties', JSON_OBJECT(
             'doc_id', JSON_OBJECT('type', 'string')
         ),
         'required', JSON_ARRAY('doc_id')
     )
 )),

('create_document', '문서 생성', 'document', 'core', '1.0.0', 'document_server', TRUE, 
 JSON_OBJECT(
     'input_schema', JSON_OBJECT(
         'type', 'object',
         'properties', JSON_OBJECT(
             'title', JSON_OBJECT('type', 'string'),
             'content', JSON_OBJECT('type', 'string'),
             'classification', JSON_OBJECT('type', 'string', 'enum', JSON_ARRAY('public', 'team', 'confidential'))
         ),
         'required', JSON_ARRAY('title', 'content', 'classification')
     )
 )),

('update_document', '문서 수정', 'document', 'core', '1.0.0', 'document_server', TRUE, NULL),
('delete_document', '문서 삭제', 'document', 'core', '1.0.0', 'document_server', TRUE, NULL),
('list_documents', '문서 목록 조회', 'document', 'core', '1.0.0', 'document_server', TRUE, NULL),
('get_document_versions', '문서 버전 히스토리', 'version', 'core', '1.0.0', 'version_server', TRUE, NULL),
('authenticate', '사용자 인증', 'auth', 'core', '1.0.0', 'auth_server', TRUE, NULL),
('request_access', '접근 권한 요청', 'auth', 'core', '1.0.0', 'auth_server', TRUE, NULL),
('get_audit_logs', '감사 로그 조회', 'audit', 'core', '1.0.0', 'audit_server', TRUE, NULL);

-- ============================================
-- 4. MCP Server
-- ============================================

INSERT INTO servers (name, description, status) VALUES
('auth_server', '인증 및 권한 관리', 'stopped'),
('search_server', '문서 검색', 'stopped'),
('document_server', '문서 CRUD', 'stopped'),
('version_server', '문서 버전 관리', 'stopped'),
('audit_server', '감사 로그', 'stopped');

-- ============================================
-- 5. 시스템 설정
-- ============================================

INSERT INTO system_settings (key_name, value_text, value_json, description) VALUES
('system.version', '1.0.0', NULL, '시스템 버전'),
('system.name', 'MCP 에코시스템', NULL, '시스템 이름'),
('system.maintenance', 'false', NULL, '점검 모드'),

('document.max_size_mb', '10', NULL, '문서 최대 크기 (MB)'),
('document.allowed_extensions', NULL, JSON_ARRAY('md', 'txt', 'pdf'), '허용 확장자'),

('search.max_results', '100', NULL, '검색 최대 결과 수'),
('search.highlight', 'true', NULL, '하이라이트 활성화'),

('audit.retention_days', '90', NULL, '감사 로그 보관 기간 (일)'),
('audit.log_level', 'INFO', NULL, '로그 레벨'),

('rate_limit.per_minute', '100', NULL, '분당 요청 제한'),
('rate_limit.enabled', 'true', NULL, 'Rate Limiting 활성화');

-- ============================================
-- 6. 샘플 감사 로그
-- ============================================

INSERT INTO audit_logs (user_id, action, resource_type, resource_id, result, ip_address) VALUES
('U001', 'login', 'user', 'U001', 'success', '192.168.1.100'),
('U001', 'document_view', 'document', 'DOC001', 'success', '192.168.1.100'),
('U002', 'login', 'user', 'U002', 'success', '192.168.1.101'),
('U002', 'document_create', 'document', 'DOC005', 'success', '192.168.1.101'),
('U003', 'login', 'user', 'U003', 'success', '192.168.1.102'),
('U003', 'document_view', 'document', 'DOC004', 'success', '192.168.1.102');
```

***

## 4. Elasticsearch 인덱스

### 4.1 documents.json - 문서 인덱스 매핑

```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "max_result_window": 10000,
    "analysis": {
      "analyzer": {
        "nori": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": [
            "lowercase",
            "nori_part_of_speech",
            "nori_readingform"
          ]
        },
        "nori_mixed": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": [
            "lowercase",
            "nori_part_of_speech",
            "nori_readingform",
            "edge_ngram_filter"
          ]
        }
      },
      "tokenizer": {
        "nori_tokenizer": {
          "type": "nori_tokenizer",
          "decompound_mode": "mixed",
          "discard_punctuation": true
        }
      },
      "filter": {
        "nori_part_of_speech": {
          "type": "nori_part_of_speech",
          "stoptags": [
            "E",
            "IC",
            "J",
            "MAG",
            "MAJ",
            "MM",
            "SP",
            "SSC",
            "SSO",
            "SC",
            "SE",
            "XPN",
            "XSA",
            "XSN",
            "XSV",
            "UNA",
            "NA",
            "VSV"
          ]
        },
        "edge_ngram_filter": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 10
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "doc_id": {
        "type": "keyword"
      },
      "title": {
        "type": "text",
        "analyzer": "nori",
        "search_analyzer": "nori",
        "fields": {
          "keyword": {
            "type": "keyword"
          },
          "suggest": {
            "type": "text",
            "analyzer": "nori_mixed"
          }
        }
      },
      "content": {
        "type": "text",
        "analyzer": "nori",
        "search_analyzer": "nori",
        "term_vector": "with_positions_offsets"
      },
      "classification": {
        "type": "keyword"
      },
      "category": {
        "type": "keyword"
      },
      "author_id": {
        "type": "keyword"
      },
      "author_name": {
        "type": "text",
        "analyzer": "nori",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "team": {
        "type": "keyword"
      },
      "tags": {
        "type": "keyword"
      },
      "created_at": {
        "type": "date",
        "format": "strict_date_optional_time||epoch_millis"
      },
      "updated_at": {
        "type": "date",
        "format": "strict_date_optional_time||epoch_millis"
      },
      "version": {
        "type": "integer"
      },
      "file_path": {
        "type": "keyword",
        "index": false
      },
      "file_size": {
        "type": "long"
      },
      "view_count": {
        "type": "integer"
      }
    }
  }
}
```

### 4.2 audit_logs.json - 감사 로그 인덱스 매핑

```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "index": {
      "refresh_interval": "5s",
      "max_result_window": 10000
    }
  },
  "mappings": {
    "properties": {
      "user_id": {
        "type": "keyword"
      },
      "user_name": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "action": {
        "type": "keyword"
      },
      "action_description": {
        "type": "text"
      },
      "resource_type": {
        "type": "keyword"
      },
      "resource_id": {
        "type": "keyword"
      },
      "resource_title": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "details": {
        "type": "object",
        "enabled": true
      },
      "result": {
        "type": "keyword"
      },
      "error_message": {
        "type": "text"
      },
      "ip_address": {
        "type": "ip"
      },
      "user_agent": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "request_id": {
        "type": "keyword"
      },
      "execution_time_ms": {
        "type": "integer"
      },
      "timestamp": {
        "type": "date",
        "format": "strict_date_optional_time||epoch_millis"
      },
      "created_at": {
        "type": "date",
        "format": "strict_date_optional_time||epoch_millis"
      }
    }
  }
}
```

### 4.3 인덱스 생성 스크립트

```python
# scripts/init_elasticsearch.py
"""
Elasticsearch 인덱스 초기화
"""

import json
from pathlib import Path
from shared.elasticsearch import ElasticsearchManager
from shared.logging_config import setup_logging

logger = setup_logging("init_elasticsearch")

def load_mapping(mapping_file: Path) -> dict:
    """매핑 파일 로드"""
    with open(mapping_file, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    """Elasticsearch 인덱스 생성"""
    
    # Elasticsearch 연결
    es_config = {
        "hosts": ["localhost:9200"],
        "timeout": 30
    }
    
    es = ElasticsearchManager(es_config)
    
    # 매핑 파일 경로
    mappings_dir = Path("/app/poc/mcps/data/elasticsearch/mappings")
    
    # 인덱스 목록
    indexes = [
        {
            "name": "documents",
            "mapping_file": mappings_dir / "documents.json"
        },
        {
            "name": "audit_logs",
            "mapping_file": mappings_dir / "audit_logs.json"
        }
    ]
    
    # 인덱스 생성
    for index_info in indexes:
        index_name = index_info["name"]
        mapping_file = index_info["mapping_file"]
        
        logger.info(f"Creating index: {index_name}")
        
        # 기존 인덱스 삭제 (선택)
        if es.index_exists(index_name):
            logger.warning(f"Index already exists: {index_name}")
            response = input(f"Delete and recreate index '{index_name}'? (y/N): ")
            if response.lower() == 'y':
                es.delete_index(index_name)
                logger.info(f"Deleted index: {index_name}")
            else:
                logger.info(f"Skipped index: {index_name}")
                continue
        
        # 매핑 로드
        mapping_data = load_mapping(mapping_file)
        
        # 인덱스 생성
        es.create_index(
            index=index_name,
            mappings=mapping_data["mappings"],
            settings=mapping_data.get("settings")
        )
        
        logger.info(f"✅ Index created: {index_name}")
    
    # 헬스 체크
    health = es.health_check()
    logger.info(f"Elasticsearch health: {health}")
    
    es.close()
    
    logger.info("✅ Elasticsearch initialization completed")

if __name__ == "__main__":
    main()
```

***

## 5. 데이터 마이그레이션

### 5.1 문서 데이터 동기화 (MariaDB → Elasticsearch)

```python
# scripts/sync_documents_to_es.py
"""
MariaDB 문서 데이터를 Elasticsearch로 동기화
"""

from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from shared.queries import GET_ALL_DOCUMENTS
from shared.logging_config import setup_logging

logger = setup_logging("sync_documents")

def main():
    """문서 데이터 동기화"""
    
    # DB 연결
    db_config = {
        "host": "localhost",
        "port": 3306,
        "database": "mcps_db",
        "user": "mcps_user",
        "password": "your_password",
        "charset": "utf8mb4",
        "pool_size": {"min": 1, "max": 5}
    }
    
    db = DatabaseManager(db_config)
    
    # ES 연결
    es_config = {
        "hosts": ["localhost:9200"],
        "timeout": 30
    }
    
    es = ElasticsearchManager(es_config)
    
    logger.info("Starting document synchronization...")
    
    # 전체 문서 조회
    documents = db.execute_query(
        """
        SELECT 
            d.id, d.title, d.content, d.classification,
            d.category, d.author_id, d.team, d.version,
            d.created_at, d.updated_at,
            u.name AS author_name
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        ORDER BY d.created_at
        """
    )
    
    logger.info(f"Found {len(documents)} documents")
    
    # Elasticsearch에 색인
    indexed = 0
    failed = 0
    
    for doc in documents:
        try:
            # ES 문서 생성
            es_doc = {
                "doc_id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "classification": doc["classification"],
                "category": doc["category"],
                "author_id": doc["author_id"],
                "author_name": doc["author_name"],
                "team": doc["team"],
                "version": doc["version"],
                "created_at": doc["created_at"].isoformat() if doc["created_at"] else None,
                "updated_at": doc["updated_at"].isoformat() if doc["updated_at"] else None
            }
            
            # 색인
            es.index_document(
                index="documents",
                doc_id=doc["id"],
                body=es_doc
            )
            
            indexed += 1
            
            if indexed % 100 == 0:
                logger.info(f"Indexed {indexed} documents...")
        
        except Exception as e:
            logger.error(f"Failed to index document {doc['id']}: {e}")
            failed += 1
    
    logger.info(f"✅ Synchronization completed: indexed={indexed}, failed={failed}")
    
    # 통계
    doc_count = es.count("documents")
    logger.info(f"Total documents in Elasticsearch: {doc_count}")
    
    db.close()
    es.close()

if __name__ == "__main__":
    main()
```

### 5.2 감사 로그 동기화

```python
# scripts/sync_audit_logs_to_es.py
"""
MariaDB 감사 로그를 Elasticsearch로 동기화
"""

from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from shared.logging_config import setup_logging
from datetime import datetime, timedelta

logger = setup_logging("sync_audit_logs")

def main():
    """감사 로그 동기화"""
    
    # DB 연결
    db_config = {
        "host": "localhost",
        "port": 3306,
        "database": "mcps_db",
        "user": "mcps_user",
        "password": "your_password",
        "charset": "utf8mb4",
        "pool_size": {"min": 1, "max": 5}
    }
    
    db = DatabaseManager(db_config)
    
    # ES 연결
    es_config = {
        "hosts": ["localhost:9200"],
        "timeout": 30
    }
    
    es = ElasticsearchManager(es_config)
    
    logger.info("Starting audit log synchronization...")
    
    # 최근 30일 로그만 동기화
    start_date = datetime.now() - timedelta(days=30)
    
    # 감사 로그 조회
    logs = db.execute_query(
        """
        SELECT 
            a.id, a.user_id, a.action, a.resource_type, a.resource_id,
            a.details, a.result, a.ip_address, a.user_agent, a.created_at,
            u.name AS user_name
        FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE a.created_at >= %s
        ORDER BY a.created_at
        """,
        (start_date,)
    )
    
    logger.info(f"Found {len(logs)} audit logs")
    
    # Elasticsearch에 색인 (Bulk)
    es_docs = []
    
    for log in logs:
        es_doc = {
            "_id": str(log["id"]),
            "user_id": log["user_id"],
            "user_name": log["user_name"],
            "action": log["action"],
            "resource_type": log["resource_type"],
            "resource_id": log["resource_id"],
            "details": log["details"],
            "result": log["result"],
            "ip_address": log["ip_address"],
            "user_agent": log["user_agent"],
            "timestamp": log["created_at"].isoformat() if log["created_at"] else None,
            "created_at": log["created_at"].isoformat() if log["created_at"] else None
        }
        
        es_docs.append(es_doc)
    
    # Bulk 색인
    if es_docs:
        result = es.bulk_index("audit_logs", es_docs)
        logger.info(f"✅ Indexed {result['success']} logs, failed {result['failed']}")
    
    # 통계
    log_count = es.count("audit_logs")
    logger.info(f"Total logs in Elasticsearch: {log_count}")
    
    db.close()
    es.close()

if __name__ == "__main__":
    main()
```

### 5.3 재색인 스크립트

```python
# scripts/reindex_documents.py
"""
문서 재색인
"""

from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from shared.logging_config import setup_logging

logger = setup_logging("reindex_documents")

def main():
    """문서 재색인"""
    
    db_config = {
        "host": "localhost",
        "port": 3306,
        "database": "mcps_db",
        "user": "mcps_user",
        "password": "your_password",
        "charset": "utf8mb4",
        "pool_size": {"min": 1, "max": 5}
    }
    
    es_config = {
        "hosts": ["localhost:9200"],
        "timeout": 30
    }
    
    db = DatabaseManager(db_config)
    es = ElasticsearchManager(es_config)
    
    logger.info("Starting reindexing...")
    
    # 1. 기존 인덱스 삭제
    if es.index_exists("documents"):
        logger.info("Deleting existing index...")
        es.delete_index("documents")
    
    # 2. 인덱스 재생성
    logger.info("Creating new index...")
    import json
    from pathlib import Path
    
    mapping_file = Path("/app/poc/mcps/data/elasticsearch/mappings/documents.json")
    with open(mapping_file, "r") as f:
        mapping_data = json.load(f)
    
    es.create_index(
        "documents",
        mapping_data["mappings"],
        mapping_data["settings"]
    )
    
    # 3. 문서 색인
    logger.info("Indexing documents...")
    
    documents = db.execute_query(
        """
        SELECT 
            d.id, d.title, d.content, d.classification,
            d.category, d.author_id, d.team, d.version,
            d.created_at, d.updated_at,
            u.name AS author_name
        FROM documents d
        LEFT JOIN users u ON d.author_id = u.id
        """
    )
    
    es_docs = []
    for doc in documents:
        es_docs.append({
            "_id": doc["id"],
            "doc_id": doc["id"],
            "title": doc["title"],
            "content": doc["content"],
            "classification": doc["classification"],
            "category": doc["category"],
            "author_id": doc["author_id"],
            "author_name": doc["author_name"],
            "team": doc["team"],
            "version": doc["version"],
            "created_at": doc["created_at"].isoformat() if doc["created_at"] else None,
            "updated_at": doc["updated_at"].isoformat() if doc["updated_at"] else None
        })
    
    if es_docs:
        result = es.bulk_index("documents", es_docs)
        logger.info(f"✅ Reindexing completed: {result['success']} documents")
    
    db.close()
    es.close()

if __name__ == "__main__":
    main()
```

***

## 6. 샘플 데이터

### 6.1 추가 문서 생성 스크립트

```python
# scripts/generate_sample_documents.py
"""
샘플 문서 생성
"""

from shared.database import DatabaseManager
from shared.utils import generate_id
from shared.logging_config import setup_logging
import random

logger = setup_logging("generate_samples")

# 샘플 제목
SAMPLE_TITLES = {
    "public": [
        "회사 비전 2030",
        "직원 행동 강령",
        "보안 정책 안내",
        "출퇴근 관리 규정",
        "사무실 이용 안내",
        "재택근무 가이드",
        "휴가 사용 안내",
        "복지 포인트 사용법",
        "사내 동호회 소개",
        "신입사원 온보딩 가이드"
    ],
    "team_dev": [
        "개발 환경 설정",
        "Git 워크플로우",
        "코드 리뷰 가이드",
        "배포 프로세스",
        "API 설계 원칙",
        "데이터베이스 스키마",
        "테스트 전략",
        "성능 최적화 팁",
        "보안 체크리스트",
        "장애 대응 매뉴얼"
    ],
    "team_hr": [
        "채용 프로세스",
        "면접 가이드",
        "인사 평가 기준",
        "교육 계획",
        "복리후생 정책",
        "급여 체계",
        "승진 기준",
        "퇴직 절차",
        "근태 관리",
        "조직 문화"
    ],
    "confidential": [
        "2026년 사업 계획",
        "M&A 검토 보고서",
        "임원 회의록",
        "재무 실적 분석",
        "신제품 로드맵",
        "경쟁사 분석",
        "투자 유치 계획",
        "조직 개편안",
        "인력 계획",
        "예산 집행 현황"
    ]
}

SAMPLE_CONTENT = """
# {title}

## 개요
이 문서는 {title}에 관한 내용을 다룹니다.

## 상세 내용
### 1. 배경
{title}의 필요성과 배경을 설명합니다.

### 2. 목표
- 목표 1: 명확한 기준 수립
- 목표 2: 효율적인 프로세스 구축
- 목표 3: 지속적인 개선

### 3. 실행 계획
1. 1단계: 현황 분석
2. 2단계: 개선 방안 도출
3. 3단계: 실행 및 모니터링

## 결론
{title}를 통해 조직의 발전을 도모합니다.

---
작성일: 2026-01-08
"""

def main():
    """샘플 문서 생성"""
    
    db_config = {
        "host": "localhost",
        "port": 3306,
        "database": "mcps_db",
        "user": "mcps_user",
        "password": "your_password",
        "charset": "utf8mb4",
        "pool_size": {"min": 1, "max": 5}
    }
    
    db = DatabaseManager(db_config)
    
    logger.info("Generating sample documents...")
    
    users = {
        "admin": "U000",
        "junior": "U001",
        "staff_dev": "U002",
        "manager_dev": "U003",
        "executive": "U004",
        "staff_hr": "U005",
        "staff_finance": "U006"
    }
    
    # Public 문서 (10개)
    for title in SAMPLE_TITLES["public"]:
        doc_id = generate_id("DOC", 8)
        content = SAMPLE_CONTENT.format(title=title)
        
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (doc_id, title, content, "public", "general", users["admin"], None)
        )
        
        logger.info(f"Created public document: {doc_id} - {title}")
    
    # Team 문서 - dev_team (10개)
    for title in SAMPLE_TITLES["team_dev"]:
        doc_id = generate_id("DOC", 8)
        content = SAMPLE_CONTENT.format(title=title)
        
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (doc_id, title, content, "team", "development", users["staff_dev"], "dev_team")
        )
        
        logger.info(f"Created team document (dev): {doc_id} - {title}")
    
    # Team 문서 - hr_team (10개)
    for title in SAMPLE_TITLES["team_hr"]:
        doc_id = generate_id("DOC", 8)
        content = SAMPLE_CONTENT.format(title=title)
        
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (doc_id, title, content, "team", "hr", users["staff_hr"], "hr_team")
        )
        
        logger.info(f"Created team document (hr): {doc_id} - {title}")
    
    # Confidential 문서 (10개)
    for title in SAMPLE_TITLES["confidential"]:
        doc_id = generate_id("DOC", 8)
        content = SAMPLE_CONTENT.format(title=title)
        
        db.execute_insert(
            """
            INSERT INTO documents (id, title, content, classification, category, author_id, team)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (doc_id, title, content, "confidential", "management", users["executive"], None)
        )
        
        logger.info(f"Created confidential document: {doc_id} - {title}")
    
    # 문서 수 확인
    result = db.execute_query("SELECT COUNT(*) AS total FROM documents")
    total = result[0]["total"]
    
    logger.info(f"✅ Sample generation completed: {total} documents")
    
    db.close()

if __name__ == "__main__":
    main()
```

### 6.2 샘플 감사 로그 생성

```python
# scripts/generate_sample_audit_logs.py
"""
샘플 감사 로그 생성
"""

from shared.database import DatabaseManager
from shared.logging_config import setup_logging
from datetime import datetime, timedelta
import random

logger = setup_logging("generate_audit_logs")

ACTIONS = [
    "login",
    "logout",
    "document_view",
    "document_create",
    "document_update",
    "document_delete",
    "search",
    "tool_execute",
    "access_request"
]

def main():
    """샘플 감사 로그 생성"""
    
    db_config = {
        "host": "localhost",
        "port": 3306,
        "database": "mcps_db",
        "user": "mcps_user",
        "password": "your_password",
        "charset": "utf8mb4",
        "pool_size": {"min": 1, "max": 5}
    }
    
    db = DatabaseManager(db_config)
    
    logger.info("Generating sample audit logs...")
    
    # 사용자 목록
    users = ["U000", "U001", "U002", "U003", "U004", "U005", "U006"]
    
    # 최근 30일간 로그 생성
    start_date = datetime.now() - timedelta(days=30)
    
    logs = []
    
    for day in range(30):
        date = start_date + timedelta(days=day)
        
        # 하루에 각 사용자당 5-20개 액션
        for user_id in users:
            num_actions = random.randint(5, 20)
            
            for _ in range(num_actions):
                action = random.choice(ACTIONS)
                result = "success" if random.random() > 0.05 else "failure"
                
                # 시간 랜덤 (업무 시간)
                hour = random.randint(9, 18)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                timestamp = date.replace(hour=hour, minute=minute, second=second)
                
                logs.append((
                    user_id,
                    action,
                    "document" if "document" in action else "system",
                    f"DOC{random.randint(1, 100):03d}",
                    result,
                    f"192.168.1.{random.randint(100, 200)}",
                    timestamp
                ))
    
    # Batch insert
    db.execute_many(
        """
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, result, ip_address, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        logs
    )
    
    logger.info(f"✅ Generated {len(logs)} audit logs")
    
    db.close()

if __name__ == "__main__":
    main()
```

***

## 7. 데이터베이스 백업 및 복구

### 7.1 백업 스크립트

```bash
#!/bin/bash
# scripts/backup_database.sh

# 설정
DB_NAME="mcps_db"
DB_USER="mcps_user"
DB_PASSWORD="your_password"
BACKUP_DIR="/backup/mcps/database"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql.gz"

# 디렉토리 생성
mkdir -p $BACKUP_DIR

# 백업 실행
echo "=== Database Backup Started ==="
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"

mysqldump \
    -u $DB_USER \
    -p$DB_PASSWORD \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    $DB_NAME | gzip > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✅ Backup completed successfully"
    echo "File size: $(du -h $BACKUP_FILE | cut -f1)"
    
    # 30일 이상 오래된 백업 삭제
    find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
    echo "Old backups deleted (>30 days)"
else
    echo "❌ Backup failed"
    exit 1
fi
```

### 7.2 복구 스크립트

```bash
#!/bin/bash
# scripts/restore_database.sh

# 인자 확인
if [ -z "$1" ]; then
    echo "Usage: ./restore_database.sh BACKUP_FILE"
    exit 1
fi

BACKUP_FILE=$1
DB_NAME="mcps_db"
DB_USER="mcps_user"
DB_PASSWORD="your_password"

# 파일 존재 확인
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "=== Database Restore Started ==="
echo "Backup file: $BACKUP_FILE"
echo "Database: $DB_NAME"
echo ""
echo "⚠️  WARNING: This will drop and recreate the database!"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# 데이터베이스 재생성
echo "Dropping database..."
mysql -u root -p -e "DROP DATABASE IF EXISTS $DB_NAME; CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 복구 실행
echo "Restoring database..."
gunzip < $BACKUP_FILE | mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME

if [ $? -eq 0 ]; then
    echo "✅ Restore completed successfully"
    
    # 테이블 확인
    echo ""
    echo "Tables:"
    mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SHOW TABLES;"
else
    echo "❌ Restore failed"
    exit 1
fi
```

***

## 8. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 9. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **작성자** | | | |
| **검토자** | | | |
| **승인자** | | | |

***

**문서 끝**

***

