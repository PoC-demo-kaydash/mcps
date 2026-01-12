# Database DDL 및 데이터 스키마 상세 설계서

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/data/`  
**목적**: MariaDB DDL, Elasticsearch 매핑, 마이그레이션 스크립트 전체

***

## 목차

1. [개요](#1-개요)
2. [MariaDB 데이터베이스 스키마](#2-mariadb-데이터베이스-스키마)
3. [Elasticsearch 인덱스 매핑](#3-elasticsearch-인덱스-매핑)
4. [인덱스 전략](#4-인덱스-전략)
5. [마이그레이션 스크립트](#5-마이그레이션-스크립트)
6. [초기 데이터](#6-초기-데이터)
7. [데이터 관리](#7-데이터-관리)

***

## 1. 개요

### 1.1 데이터베이스 구조

```
┌─────────────────────────────────────────┐
│          데이터 계층 구조                │
├─────────────────────────────────────────┤
│                                          │
│  [MariaDB]                               │
│    ├─ users (사용자)                     │
│    ├─ teams (팀)                        │
│    ├─ documents (문서)                  │
│    ├─ document_versions (문서 버전)     │
│    ├─ permissions (권한)                │
│    ├─ access_requests (권한 요청)       │
│    ├─ audit_logs (감사 로그)            │
│    └─ sessions (세션)                   │
│                                          │
│  [Elasticsearch]                         │
│    └─ documents (문서 검색 인덱스)       │
│                                          │
└─────────────────────────────────────────┘
```

### 1.2 명명 규칙

| 항목 | 규칙 | 예시 |
|------|------|------|
| **테이블명** | 소문자, 복수형, 언더스코어 | `users`, `document_versions` |
| **컬럼명** | 소문자, 언더스코어 | `user_id`, `created_at` |
| **인덱스명** | `idx_테이블_컬럼` | `idx_documents_category` |
| **외래키명** | `fk_테이블1_테이블2` | `fk_documents_users` |
| **제약조건명** | `chk_테이블_설명` | `chk_users_role` |

### 1.3 공통 컬럼

모든 테이블에 공통으로 포함되는 컬럼:

```sql
-- 생성 시간
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

-- 수정 시간
updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

-- 삭제 시간 (Soft Delete)
deleted_at TIMESTAMP NULL DEFAULT NULL
```

***

## 2. MariaDB 데이터베이스 스키마

### 2.1 Database 생성

```sql
-- database/01_create_database.sql
-- Database 생성 스크립트

-- Database 생성
CREATE DATABASE IF NOT EXISTS mcps_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 사용자 생성
CREATE USER IF NOT EXISTS 'mcps_user'@'localhost' 
IDENTIFIED BY 'CHANGE_ME_PASSWORD';

CREATE USER IF NOT EXISTS 'mcps_user'@'%' 
IDENTIFIED BY 'CHANGE_ME_PASSWORD';

-- 권한 부여
GRANT ALL PRIVILEGES ON mcps_db.* TO 'mcps_user'@'localhost';
GRANT ALL PRIVILEGES ON mcps_db.* TO 'mcps_user'@'%';

-- 권한 적용
FLUSH PRIVILEGES;

-- Database 사용
USE mcps_db;
```

### 2.2 users (사용자)

```sql
-- database/02_create_tables.sql
-- 테이블 생성 스크립트

-- =============================================
-- 2.1 users (사용자)
-- =============================================

CREATE TABLE users (
    -- 기본키
    id VARCHAR(50) PRIMARY KEY COMMENT '사용자 ID (예: U001)',
    
    -- 기본 정보
    name VARCHAR(100) NOT NULL COMMENT '사용자 이름',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT '이메일',
    
    -- 조직 정보
    role ENUM('junior', 'staff', 'manager', 'admin') NOT NULL DEFAULT 'junior' COMMENT '역할',
    team VARCHAR(100) NULL COMMENT '팀명',
    department VARCHAR(100) NOT NULL COMMENT '부서명',
    
    -- 상태
    status ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active' COMMENT '상태',
    
    -- 인증 정보
    password_hash VARCHAR(255) NULL COMMENT '비밀번호 해시 (선택)',
    last_login_at TIMESTAMP NULL COMMENT '마지막 로그인',
    
    -- 메타데이터
    metadata JSON NULL COMMENT '추가 메타데이터',
    
    -- 공통 컬럼
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    
    -- 인덱스
    INDEX idx_users_email (email),
    INDEX idx_users_role (role),
    INDEX idx_users_team (team),
    INDEX idx_users_department (department),
    INDEX idx_users_status (status),
    INDEX idx_users_deleted_at (deleted_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자';
```

### 2.3 teams (팀)

```sql
-- =============================================
-- 2.2 teams (팀)
-- =============================================

CREATE TABLE teams (
    -- 기본키
    id VARCHAR(50) PRIMARY KEY COMMENT '팀 ID (예: TEAM001)',
    
    -- 기본 정보
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '팀명',
    description TEXT NULL COMMENT '팀 설명',
    
    -- 조직 정보
    department VARCHAR(100) NOT NULL COMMENT '부서명',
    parent_team_id VARCHAR(50) NULL COMMENT '상위 팀 ID',
    
    -- 관리자
    manager_id VARCHAR(50) NULL COMMENT '팀 관리자 ID',
    
    -- 상태
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active' COMMENT '상태',
    
    -- 메타데이터
    metadata JSON NULL COMMENT '추가 메타데이터',
    
    -- 공통 컬럼
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    
    -- 외래키
    FOREIGN KEY fk_teams_parent (parent_team_id) 
        REFERENCES teams(id) ON DELETE SET NULL,
    FOREIGN KEY fk_teams_manager (manager_id) 
        REFERENCES users(id) ON DELETE SET NULL,
    
    -- 인덱스
    INDEX idx_teams_name (name),
    INDEX idx_teams_department (department),
    INDEX idx_teams_parent (parent_team_id),
    INDEX idx_teams_manager (manager_id),
    INDEX idx_teams_status (status),
    INDEX idx_teams_deleted_at (deleted_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='팀';
```

### 2.4 documents (문서)

```sql
-- =============================================
-- 2.3 documents (문서)
-- =============================================

CREATE TABLE documents (
    -- 기본키
    id VARCHAR(50) PRIMARY KEY COMMENT '문서 ID (예: DOC001)',
    
    -- 기본 정보
    title VARCHAR(500) NOT NULL COMMENT '문서 제목',
    content LONGTEXT NOT NULL COMMENT '문서 내용 (Markdown)',
    
    -- 분류
    classification ENUM('public', 'team', 'department', 'confidential') NOT NULL DEFAULT 'public' COMMENT '공개 범위',
    category VARCHAR(100) NOT NULL COMMENT '카테고리',
    tags JSON NULL COMMENT '태그 배열',
    
    -- 작성자 정보
    author_id VARCHAR(50) NOT NULL COMMENT '작성자 ID',
    team VARCHAR(100) NULL COMMENT '팀명',
    department VARCHAR(100) NULL COMMENT '부서명',
    
    -- 버전 정보
    version INT NOT NULL DEFAULT 1 COMMENT '현재 버전',
    
    -- 상태
    status ENUM('draft', 'published', 'archived') NOT NULL DEFAULT 'draft' COMMENT '상태',
    
    -- 통계
    view_count INT NOT NULL DEFAULT 0 COMMENT '조회수',
    
    -- 메타데이터
    metadata JSON NULL COMMENT '추가 메타데이터',
    
    -- 공통 컬럼
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    
    -- 외래키
    FOREIGN KEY fk_documents_users (author_id) 
        REFERENCES users(id) ON DELETE RESTRICT,
    
    -- 인덱스
    INDEX idx_documents_title (title(255)),
    INDEX idx_documents_classification (classification),
    INDEX idx_documents_category (category),
    INDEX idx_documents_author (author_id),
    INDEX idx_documents_team (team),
    INDEX idx_documents_department (department),
    INDEX idx_documents_status (status),
    INDEX idx_documents_created_at (created_at),
    INDEX idx_documents_updated_at (updated_at),
    INDEX idx_documents_deleted_at (deleted_at),
    
    -- 복합 인덱스
    INDEX idx_documents_classification_category (classification, category),
    INDEX idx_documents_author_created (author_id, created_at),
    
    -- 전문 검색 인덱스 (선택)
    FULLTEXT INDEX ft_documents_title_content (title, content)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='문서';
```

### 2.5 document_versions (문서 버전)

```sql
-- =============================================
-- 2.4 document_versions (문서 버전)
-- =============================================

CREATE TABLE document_versions (
    -- 기본키
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- 문서 정보
    doc_id VARCHAR(50) NOT NULL COMMENT '문서 ID',
    version INT NOT NULL COMMENT '버전 번호',
    
    -- 버전 내용
    title VARCHAR(500) NOT NULL COMMENT '문서 제목',
    content LONGTEXT NOT NULL COMMENT '문서 내용',
    
    -- 분류
    classification ENUM('public', 'team', 'department', 'confidential') NOT NULL COMMENT '공개 범위',
    category VARCHAR(100) NOT NULL COMMENT '카테고리',
    tags JSON NULL COMMENT '태그 배열',
    
    -- 변경 정보
    changed_by VARCHAR(50) NOT NULL COMMENT '변경자 ID',
    change_summary VARCHAR(500) NULL COMMENT '변경 요약',
    
    -- 메타데이터
    metadata JSON NULL COMMENT '추가 메타데이터',
    
    -- 생성 시간
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키
    FOREIGN KEY fk_versions_documents (doc_id) 
        REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY fk_versions_users (changed_by) 
        REFERENCES users(id) ON DELETE RESTRICT,
    
    -- 유니크 제약
    UNIQUE KEY uk_versions_doc_version (doc_id, version),
    
    -- 인덱스
    INDEX idx_versions_doc_id (doc_id),
    INDEX idx_versions_version (version),
    INDEX idx_versions_changed_by (changed_by),
    INDEX idx_versions_created_at (created_at),
    INDEX idx_versions_doc_created (doc_id, created_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='문서 버전';
```

### 2.6 permissions (권한)

```sql
-- =============================================
-- 2.5 permissions (권한)
-- =============================================

CREATE TABLE permissions (
    -- 기본키
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- 대상
    user_id VARCHAR(50) NOT NULL COMMENT '사용자 ID',
    doc_id VARCHAR(50) NOT NULL COMMENT '문서 ID',
    
    -- 권한 유형
    permission_type ENUM('read', 'write', 'delete') NOT NULL COMMENT '권한 유형',
    
    -- 부여 정보
    granted_by VARCHAR(50) NOT NULL COMMENT '권한 부여자 ID',
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '부여 시간',
    
    -- 만료
    expires_at TIMESTAMP NULL COMMENT '만료 시간 (NULL = 무기한)',
    
    -- 상태
    status ENUM('active', 'revoked') NOT NULL DEFAULT 'active' COMMENT '상태',
    
    -- 메타데이터
    metadata JSON NULL COMMENT '추가 메타데이터',
    
    -- 공통 컬럼
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 외래키
    FOREIGN KEY fk_permissions_users (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY fk_permissions_documents (doc_id) 
        REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY fk_permissions_granter (granted_by) 
        REFERENCES users(id) ON DELETE RESTRICT,
    
    -- 유니크 제약
    UNIQUE KEY uk_permissions_user_doc_type (user_id, doc_id, permission_type),
    
    -- 인덱스
    INDEX idx_permissions_user_id (user_id),
    INDEX idx_permissions_doc_id (doc_id),
    INDEX idx_permissions_type (permission_type),
    INDEX idx_permissions_status (status),
    INDEX idx_permissions_expires_at (expires_at),
    INDEX idx_permissions_granted_by (granted_by)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='권한';
```

### 2.7 access_requests (권한 요청)

```sql
-- =============================================
-- 2.6 access_requests (권한 요청)
-- =============================================

CREATE TABLE access_requests (
    -- 기본키
    id VARCHAR(50) PRIMARY KEY COMMENT '요청 ID (예: REQ001)',
    
    -- 요청 정보
    user_id VARCHAR(50) NOT NULL COMMENT '요청자 ID',
    doc_id VARCHAR(50) NOT NULL COMMENT '문서 ID',
    
    -- 요청 내용
    permission_type ENUM('read', 'write', 'delete') NOT NULL COMMENT '요청 권한 유형',
    reason TEXT NOT NULL COMMENT '요청 사유',
    
    -- 상태
    status ENUM('pending', 'approved', 'rejected', 'cancelled') NOT NULL DEFAULT 'pending' COMMENT '상태',
    
    -- 처리 정보
    reviewed_by VARCHAR(50) NULL COMMENT '검토자 ID',
    reviewed_at TIMESTAMP NULL COMMENT '검토 시간',
    review_comment TEXT NULL COMMENT '검토 의견',
    
    -- 메타데이터
    metadata JSON NULL COMMENT '추가 메타데이터',
    
    -- 공통 컬럼
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 외래키
    FOREIGN KEY fk_requests_users (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY fk_requests_documents (doc_id) 
        REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY fk_requests_reviewers (reviewed_by) 
        REFERENCES users(id) ON DELETE SET NULL,
    
    -- 인덱스
    INDEX idx_requests_user_id (user_id),
    INDEX idx_requests_doc_id (doc_id),
    INDEX idx_requests_status (status),
    INDEX idx_requests_reviewed_by (reviewed_by),
    INDEX idx_requests_created_at (created_at),
    INDEX idx_requests_reviewed_at (reviewed_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='권한 요청';
```

### 2.8 audit_logs (감사 로그)

```sql
-- =============================================
-- 2.7 audit_logs (감사 로그)
-- =============================================

CREATE TABLE audit_logs (
    -- 기본키
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- 사용자 정보
    user_id VARCHAR(50) NOT NULL COMMENT '사용자 ID',
    
    -- 액션 정보
    action VARCHAR(100) NOT NULL COMMENT '액션 (예: create_document, update_document)',
    resource_type VARCHAR(50) NOT NULL COMMENT '리소스 유형 (예: document, user)',
    resource_id VARCHAR(50) NULL COMMENT '리소스 ID',
    
    -- 상세 정보
    details JSON NULL COMMENT '상세 정보 (변경 전/후 값 등)',
    
    -- 요청 정보
    ip_address VARCHAR(45) NULL COMMENT 'IP 주소',
    user_agent TEXT NULL COMMENT 'User Agent',
    
    -- 결과
    status ENUM('success', 'failure') NOT NULL COMMENT '결과',
    error_message TEXT NULL COMMENT '에러 메시지 (실패 시)',
    
    -- 시간
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키
    FOREIGN KEY fk_logs_users (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    
    -- 인덱스
    INDEX idx_logs_user_id (user_id),
    INDEX idx_logs_action (action),
    INDEX idx_logs_resource (resource_type, resource_id),
    INDEX idx_logs_status (status),
    INDEX idx_logs_created_at (created_at),
    
    -- 복합 인덱스
    INDEX idx_logs_user_created (user_id, created_at),
    INDEX idx_logs_resource_created (resource_type, resource_id, created_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='감사 로그';
```

### 2.9 sessions (세션)

```sql
-- =============================================
-- 2.8 sessions (세션)
-- =============================================

CREATE TABLE sessions (
    -- 기본키
    id VARCHAR(100) PRIMARY KEY COMMENT '세션 ID',
    
    -- 사용자 정보
    user_id VARCHAR(50) NOT NULL COMMENT '사용자 ID',
    
    -- 세션 데이터
    data JSON NOT NULL COMMENT '세션 데이터',
    
    -- 만료
    expires_at TIMESTAMP NOT NULL COMMENT '만료 시간',
    
    -- 메타데이터
    ip_address VARCHAR(45) NULL COMMENT 'IP 주소',
    user_agent TEXT NULL COMMENT 'User Agent',
    
    -- 공통 컬럼
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 외래키
    FOREIGN KEY fk_sessions_users (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    
    -- 인덱스
    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_expires_at (expires_at),
    INDEX idx_sessions_created_at (created_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='세션';
```

### 2.10 통계 뷰 (Views)

```sql
-- =============================================
-- 2.9 통계 뷰 (Views)
-- =============================================

-- 사용자별 문서 통계
CREATE OR REPLACE VIEW v_user_document_stats AS
SELECT 
    u.id AS user_id,
    u.name AS user_name,
    u.role,
    u.team,
    COUNT(d.id) AS total_documents,
    SUM(CASE WHEN d.status = 'published' THEN 1 ELSE 0 END) AS published_documents,
    SUM(CASE WHEN d.status = 'draft' THEN 1 ELSE 0 END) AS draft_documents,
    SUM(d.view_count) AS total_views,
    MAX(d.updated_at) AS last_document_update
FROM users u
LEFT JOIN documents d ON u.id = d.author_id AND d.deleted_at IS NULL
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.name, u.role, u.team;

-- 문서별 버전 통계
CREATE OR REPLACE VIEW v_document_version_stats AS
SELECT 
    d.id AS doc_id,
    d.title,
    d.classification,
    d.category,
    d.author_id,
    d.version AS current_version,
    COUNT(dv.id) AS total_versions,
    MIN(dv.created_at) AS first_version_at,
    MAX(dv.created_at) AS last_version_at
FROM documents d
LEFT JOIN document_versions dv ON d.id = dv.doc_id
WHERE d.deleted_at IS NULL
GROUP BY d.id, d.title, d.classification, d.category, d.author_id, d.version;

-- 카테고리별 문서 통계
CREATE OR REPLACE VIEW v_category_stats AS
SELECT 
    category,
    classification,
    COUNT(*) AS document_count,
    SUM(view_count) AS total_views,
    AVG(view_count) AS avg_views,
    MAX(updated_at) AS last_updated
FROM documents
WHERE deleted_at IS NULL
GROUP BY category, classification
ORDER BY document_count DESC;
```

***

## 3. Elasticsearch 인덱스 매핑

### 3.1 documents 인덱스

```json
// data/elasticsearch/mappings/documents.json
// Elasticsearch documents 인덱스 매핑

{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 2,
    "analysis": {
      "analyzer": {
        "korean_analyzer": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": [
            "lowercase",
            "nori_part_of_speech",
            "nori_readingform"
          ]
        },
        "english_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "stop",
            "snowball"
          ]
        },
        "mixed_analyzer": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": [
            "lowercase",
            "nori_part_of_speech",
            "stop",
            "snowball"
          ]
        }
      },
      "tokenizer": {
        "nori_tokenizer": {
          "type": "nori_tokenizer",
          "decompound_mode": "mixed"
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
        "analyzer": "mixed_analyzer",
        "fields": {
          "keyword": {
            "type": "keyword"
          },
          "korean": {
            "type": "text",
            "analyzer": "korean_analyzer"
          },
          "english": {
            "type": "text",
            "analyzer": "english_analyzer"
          },
          "ngram": {
            "type": "text",
            "analyzer": "standard",
            "search_analyzer": "standard"
          }
        }
      },
      "content": {
        "type": "text",
        "analyzer": "mixed_analyzer",
        "fields": {
          "korean": {
            "type": "text",
            "analyzer": "korean_analyzer"
          },
          "english": {
            "type": "text",
            "analyzer": "english_analyzer"
          }
        }
      },
      "classification": {
        "type": "keyword"
      },
      "category": {
        "type": "keyword"
      },
      "tags": {
        "type": "keyword"
      },
      "author_id": {
        "type": "keyword"
      },
      "author_name": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "team": {
        "type": "keyword"
      },
      "department": {
        "type": "keyword"
      },
      "status": {
        "type": "keyword"
      },
      "version": {
        "type": "integer"
      },
      "view_count": {
        "type": "integer"
      },
      "created_at": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
      },
      "updated_at": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
      }
    }
  }
}
```

### 3.2 인덱스 생성 스크립트

```python
# data/elasticsearch/create_index.py
"""
Elasticsearch 인덱스 생성 스크립트
"""

from elasticsearch import Elasticsearch
import json
from pathlib import Path


def create_documents_index(es_host: str = "localhost:9200"):
    """documents 인덱스 생성"""
    
    # Elasticsearch 연결
    es = Elasticsearch([f"http://{es_host}"])
    
    # 매핑 파일 로드
    mapping_file = Path(__file__).parent / "mappings" / "documents.json"
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    index_name = "documents"
    
    # 기존 인덱스 삭제 (선택)
    if es.indices.exists(index=index_name):
        print(f"기존 인덱스 삭제: {index_name}")
        es.indices.delete(index=index_name)
    
    # 인덱스 생성
    print(f"인덱스 생성: {index_name}")
    es.indices.create(index=index_name, body=mapping)
    
    print(f"✅ 인덱스 생성 완료: {index_name}")
    
    # 인덱스 정보 확인
    info = es.indices.get(index=index_name)
    print(f"Settings: {json.dumps(info[index_name]['settings'], indent=2)}")
    print(f"Mappings: {json.dumps(info[index_name]['mappings'], indent=2)}")
    
    es.close()


if __name__ == "__main__":
    create_documents_index()
```

***

## 4. 인덱스 전략

### 4.1 MariaDB 인덱스 전략

#### 4.1.1 인덱스 생성 원칙

```sql
-- database/03_create_indexes.sql
-- 추가 인덱스 생성 스크립트

-- =============================================
-- 1. 복합 인덱스 추가
-- =============================================

-- documents: 자주 함께 검색되는 컬럼
CREATE INDEX idx_documents_status_classification_category 
ON documents(status, classification, category);

-- documents: 팀/부서별 최신 문서 조회
CREATE INDEX idx_documents_team_updated 
ON documents(team, updated_at DESC);

CREATE INDEX idx_documents_department_updated 
ON documents(department, updated_at DESC);

-- audit_logs: 사용자별 최근 활동 조회
CREATE INDEX idx_logs_user_action_created 
ON audit_logs(user_id, action, created_at DESC);

-- permissions: 문서별 권한 조회
CREATE INDEX idx_permissions_doc_status 
ON permissions(doc_id, status);

-- access_requests: 대기중인 요청 조회
CREATE INDEX idx_requests_status_created 
ON access_requests(status, created_at);
```

#### 4.1.2 인덱스 분석 쿼리

```sql
-- 인덱스 사용률 확인
SELECT 
    table_schema,
    table_name,
    index_name,
    cardinality,
    seq_in_index,
    column_name
FROM information_schema.statistics
WHERE table_schema = 'mcps_db'
ORDER BY table_name, index_name, seq_in_index;

-- 중복/불필요 인덱스 확인
SELECT 
    t1.table_schema,
    t1.table_name,
    t1.index_name AS index1,
    t2.index_name AS index2,
    GROUP_CONCAT(t1.column_name ORDER BY t1.seq_in_index) AS columns1,
    GROUP_CONCAT(t2.column_name ORDER BY t2.seq_in_index) AS columns2
FROM information_schema.statistics t1
JOIN information_schema.statistics t2 
    ON t1.table_schema = t2.table_schema
    AND t1.table_name = t2.table_name
    AND t1.index_name < t2.index_name
WHERE t1.table_schema = 'mcps_db'
GROUP BY t1.table_schema, t1.table_name, t1.index_name, t2.index_name
HAVING columns1 = columns2;
```

### 4.2 쿼리 최적화 팁

```sql
-- =============================================
-- 자주 사용되는 쿼리 최적화
-- =============================================

-- 1. 문서 목록 조회 (페이징)
EXPLAIN SELECT 
    d.id,
    d.title,
    d.classification,
    d.category,
    d.author_id,
    u.name AS author_name,
    d.view_count,
    d.created_at,
    d.updated_at
FROM documents d
INNER JOIN users u ON d.author_id = u.id
WHERE d.deleted_at IS NULL
    AND d.status = 'published'
    AND d.classification IN ('public', 'team')
ORDER BY d.updated_at DESC
LIMIT 20 OFFSET 0;

-- 2. 사용자별 권한 확인
EXPLAIN SELECT p.*
FROM permissions p
WHERE p.user_id = 'U001'
    AND p.doc_id = 'DOC001'
    AND p.status = 'active'
    AND (p.expires_at IS NULL OR p.expires_at > NOW());

-- 3. 감사 로그 조회
EXPLAIN SELECT *
FROM audit_logs
WHERE user_id = 'U001'
    AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY created_at DESC
LIMIT 100;
```

***

## 5. 마이그레이션 스크립트

### 5.1 버전 관리

```sql
-- database/migrations/00_migration_history.sql
-- 마이그레이션 히스토리 테이블

CREATE TABLE IF NOT EXISTS migration_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(20) NOT NULL UNIQUE COMMENT '버전 (예: 1.0.0)',
    description VARCHAR(255) NOT NULL COMMENT '설명',
    script_name VARCHAR(255) NOT NULL COMMENT '스크립트 파일명',
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '적용 시간',
    applied_by VARCHAR(50) NOT NULL COMMENT '적용자',
    checksum VARCHAR(64) NULL COMMENT 'SHA256 체크섬',
    
    INDEX idx_migration_version (version),
    INDEX idx_migration_applied_at (applied_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='마이그레이션 히스토리';
```

### 5.2 마이그레이션 예시

```sql
-- database/migrations/01_add_document_tags.sql
-- v1.1.0: 문서 태그 기능 추가

-- 마이그레이션 시작
START TRANSACTION;

-- 1. tags 컬럼이 없으면 추가
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS tags JSON NULL COMMENT '태그 배열'
AFTER category;

-- 2. 태그 인덱스 추가 (JSON 배열의 각 요소)
-- MariaDB 10.11+ 지원
CREATE INDEX IF NOT EXISTS idx_documents_tags 
ON documents((CAST(tags AS CHAR(1000) ARRAY)));

-- 3. 마이그레이션 기록
INSERT INTO migration_history (version, description, script_name, applied_by)
VALUES ('1.1.0', '문서 태그 기능 추가', '01_add_document_tags.sql', 'admin');

-- 커밋
COMMIT;
```

```sql
-- database/migrations/02_add_user_metadata.sql
-- v1.2.0: 사용자 메타데이터 추가

START TRANSACTION;

-- 1. metadata 컬럼 추가
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS metadata JSON NULL COMMENT '추가 메타데이터'
AFTER last_login_at;

-- 2. 마이그레이션 기록
INSERT INTO migration_history (version, description, script_name, applied_by)
VALUES ('1.2.0', '사용자 메타데이터 추가', '02_add_user_metadata.sql', 'admin');

COMMIT;
```

### 5.3 마이그레이션 실행 스크립트

```python
# database/migrations/run_migration.py
"""
마이그레이션 실행 스크립트
"""

import sys
from pathlib import Path
import hashlib
import pymysql

# PYTHONPATH 설정
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class MigrationRunner:
    """마이그레이션 실행"""
    
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.conn = None
    
    def connect(self):
        """Database 연결"""
        self.conn = pymysql.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database'],
            charset='utf8mb4'
        )
    
    def get_applied_migrations(self) -> set:
        """적용된 마이그레이션 조회"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT version FROM migration_history")
            return {row[0] for row in cursor.fetchall()}
    
    def calculate_checksum(self, file_path: Path) -> str:
        """파일 체크섬 계산"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            sha256.update(f.read())
        return sha256.hexdigest()
    
    def run_migration(self, file_path: Path, version: str, applied_by: str):
        """마이그레이션 실행"""
        print(f"마이그레이션 실행: {file_path.name}")
        
        # SQL 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # 체크섬 계산
        checksum = self.calculate_checksum(file_path)
        
        # 실행
        with self.conn.cursor() as cursor:
            # SQL 실행
            for statement in sql.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    cursor.execute(statement)
            
            self.conn.commit()
        
        print(f"✅ 마이그레이션 완료: {version}")
    
    def run_all(self, migration_dir: Path, applied_by: str = 'admin'):
        """모든 마이그레이션 실행"""
        self.connect()
        
        try:
            # 적용된 마이그레이션 조회
            applied = self.get_applied_migrations()
            print(f"적용된 마이그레이션: {len(applied)}개")
            
            # 마이그레이션 파일 목록
            migration_files = sorted(migration_dir.glob('*.sql'))
            
            for file_path in migration_files:
                # 버전 추출 (파일명에서)
                # 예: 01_add_document_tags.sql -> 1.1.0
                # 실제로는 파일 내 주석에서 버전 추출
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # v1.1.0 형식 찾기
                    import re
                    match = re.search(r'v(\d+\.\d+\.\d+)', content)
                    if not match:
                        print(f"⚠️  버전 정보 없음: {file_path.name}")
                        continue
                    
                    version = match.group(1)
                
                # 이미 적용됨
                if version in applied:
                    print(f"⏭️  스킵 (이미 적용): {version}")
                    continue
                
                # 마이그레이션 실행
                self.run_migration(file_path, version, applied_by)
            
            print("\n✅ 모든 마이그레이션 완료")
        
        finally:
            if self.conn:
                self.conn.close()


def main():
    """메인"""
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'mcps_user',
        'password': 'your_password',
        'database': 'mcps_db'
    }
    
    migration_dir = Path(__file__).parent
    
    runner = MigrationRunner(db_config)
    runner.run_all(migration_dir)


if __name__ == "__main__":
    main()
```

***

## 6. 초기 데이터

### 6.1 초기 사용자

```sql
-- database/seed_data/01_users.sql
-- 초기 사용자 데이터

INSERT INTO users (id, name, email, role, team, department, status) VALUES
-- Admin
('U000', '시스템 관리자', 'admin@company.com', 'admin', NULL, 'admin', 'active'),

-- Managers
('U001', '김팀장', 'kim.manager@company.com', 'manager', 'dev_team', 'engineering', 'active'),
('U002', '이팀장', 'lee.manager@company.com', 'manager', 'data_team', 'engineering', 'active'),

-- Staff
('U003', '박대리', 'park.staff@company.com', 'staff', 'dev_team', 'engineering', 'active'),
('U004', '최대리', 'choi.staff@company.com', 'staff', 'data_team', 'engineering', 'active'),
('U005', '정대리', 'jung.staff@company.com', 'staff', 'dev_team', 'engineering', 'active'),

-- Junior
('U006', '강사원', 'kang.junior@company.com', 'junior', NULL, 'engineering', 'active'),
('U007', '조사원', 'jo.junior@company.com', 'junior', NULL, 'engineering', 'active');
```

### 6.2 초기 팀

```sql
-- database/seed_data/02_teams.sql
-- 초기 팀 데이터

INSERT INTO teams (id, name, description, department, manager_id, status) VALUES
('TEAM001', 'dev_team', '개발팀', 'engineering', 'U001', 'active'),
('TEAM002', 'data_team', '데이터팀', 'engineering', 'U002', 'active'),
('TEAM003', 'infra_team', '인프라팀', 'engineering', NULL, 'active');
```

### 6.3 초기 문서

```sql
-- database/seed_data/03_documents.sql
-- 초기 문서 데이터

INSERT INTO documents (id, title, content, classification, category, author_id, team, department, status) VALUES
-- Public 문서
('DOC001', 'MCP 프로토콜 소개', '# MCP 프로토콜\n\nModel Context Protocol은...', 'public', 'documentation', 'U000', NULL, 'admin', 'published'),
('DOC002', '시스템 사용 가이드', '# 사용 가이드\n\n이 시스템은...', 'public', 'guide', 'U000', NULL, 'admin', 'published'),

-- Team 문서
('DOC003', '개발팀 코딩 컨벤션', '# 코딩 컨벤션\n\n1. 네이밍...', 'team', 'standard', 'U001', 'dev_team', 'engineering', 'published'),
('DOC004', '데이터팀 분석 가이드', '# 분석 가이드\n\n데이터 분석 시...', 'team', 'guide', 'U002', 'data_team', 'engineering', 'published');
```

### 6.4 초기 데이터 로드 스크립트

```bash
#!/bin/bash
# database/seed_data/load_seed_data.sh
# 초기 데이터 로드

set -e

DB_USER="mcps_user"
DB_PASSWORD="your_password"
DB_NAME="mcps_db"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== 초기 데이터 로드 ==="

# 1. 사용자
echo "사용자 로드..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < "$SCRIPT_DIR/01_users.sql"

# 2. 팀
echo "팀 로드..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < "$SCRIPT_DIR/02_teams.sql"

# 3. 문서
echo "문서 로드..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < "$SCRIPT_DIR/03_documents.sql"

echo "✅ 초기 데이터 로드 완료"
```

***

## 7. 데이터 관리

### 7.1 데이터 정리 프로시저

```sql
-- database/procedures/01_cleanup_procedures.sql
-- 데이터 정리 프로시저

DELIMITER //

-- =============================================
-- 오래된 세션 삭제
-- =============================================
CREATE PROCEDURE sp_cleanup_expired_sessions()
BEGIN
    DELETE FROM sessions
    WHERE expires_at < NOW();
    
    SELECT ROW_COUNT() AS deleted_count;
END //

-- =============================================
-- 오래된 감사 로그 아카이브
-- =============================================
CREATE PROCEDURE sp_archive_old_audit_logs(IN days INT)
BEGIN
    DECLARE cutoff_date TIMESTAMP;
    SET cutoff_date = DATE_SUB(NOW(), INTERVAL days DAY);
    
    -- 아카이브 테이블이 있다면 이동
    -- INSERT INTO audit_logs_archive SELECT * FROM audit_logs WHERE created_at < cutoff_date;
    
    -- 삭제
    DELETE FROM audit_logs
    WHERE created_at < cutoff_date;
    
    SELECT ROW_COUNT() AS archived_count;
END //

-- =============================================
-- 오래된 문서 버전 정리
-- =============================================
CREATE PROCEDURE sp_cleanup_old_document_versions(
    IN keep_versions INT,
    IN days INT
)
BEGIN
    DECLARE cutoff_date TIMESTAMP;
    SET cutoff_date = DATE_SUB(NOW(), INTERVAL days DAY);
    
    -- 각 문서의 최근 N개 버전만 유지
    DELETE dv FROM document_versions dv
    WHERE dv.created_at < cutoff_date
    AND dv.id NOT IN (
        SELECT id FROM (
            SELECT id
            FROM document_versions
            WHERE doc_id = dv.doc_id
            ORDER BY version DESC
            LIMIT keep_versions
        ) AS keep
    );
    
    SELECT ROW_COUNT() AS deleted_count;
END //

-- =============================================
-- Soft Delete된 문서 완전 삭제
-- =============================================
CREATE PROCEDURE sp_purge_deleted_documents(IN days INT)
BEGIN
    DECLARE cutoff_date TIMESTAMP;
    SET cutoff_date = DATE_SUB(NOW(), INTERVAL days DAY);
    
    -- 관련 데이터 삭제 (외래키 CASCADE로 자동)
    DELETE FROM documents
    WHERE deleted_at IS NOT NULL
    AND deleted_at < cutoff_date;
    
    SELECT ROW_COUNT() AS purged_count;
END //

DELIMITER ;
```

### 7.2 통계 프로시저

```sql
-- database/procedures/02_stats_procedures.sql
-- 통계 프로시저

DELIMITER //

-- =============================================
-- 시스템 통계
-- =============================================
CREATE PROCEDURE sp_get_system_stats()
BEGIN
    SELECT 
        (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) AS total_users,
        (SELECT COUNT(*) FROM teams WHERE deleted_at IS NULL) AS total_teams,
        (SELECT COUNT(*) FROM documents WHERE deleted_at IS NULL) AS total_documents,
        (SELECT COUNT(*) FROM documents WHERE deleted_at IS NULL AND status = 'published') AS published_documents,
        (SELECT COUNT(*) FROM document_versions) AS total_versions,
        (SELECT COUNT(*) FROM sessions WHERE expires_at > NOW()) AS active_sessions,
        (SELECT COUNT(*) FROM audit_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)) AS logs_24h;
END //

-- =============================================
-- 사용자 활동 통계
-- =============================================
CREATE PROCEDURE sp_get_user_activity_stats(IN target_user_id VARCHAR(50))
BEGIN
    SELECT 
        (SELECT COUNT(*) FROM documents WHERE author_id = target_user_id AND deleted_at IS NULL) AS created_documents,
        (SELECT COUNT(*) FROM document_versions WHERE changed_by = target_user_id) AS document_edits,
        (SELECT COUNT(*) FROM audit_logs WHERE user_id = target_user_id AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)) AS actions_7d,
        (SELECT COUNT(*) FROM access_requests WHERE user_id = target_user_id) AS access_requests,
        (SELECT MAX(created_at) FROM audit_logs WHERE user_id = target_user_id) AS last_activity;
END //

DELIMITER ;
```

### 7.3 정기 작업 (Cron)

```bash
#!/bin/bash
# database/cron/daily_cleanup.sh
# 일일 데이터 정리 작업

set -e

DB_USER="mcps_user"
DB_PASSWORD="your_password"
DB_NAME="mcps_db"

echo "=== 일일 데이터 정리 $(date) ==="

# 1. 만료된 세션 삭제
echo "만료된 세션 삭제..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "CALL sp_cleanup_expired_sessions();"

# 2. 오래된 감사 로그 아카이브 (180일)
echo "오래된 감사 로그 아카이브..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "CALL sp_archive_old_audit_logs(180);"

# 3. 오래된 문서 버전 정리 (최근 10개 버전 유지, 90일 이전)
echo "오래된 문서 버전 정리..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "CALL sp_cleanup_old_document_versions(10, 90);"

# 4. Soft Delete된 문서 완전 삭제 (30일 이전)
echo "삭제된 문서 완전 제거..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "CALL sp_purge_deleted_documents(30);"

# 5. 테이블 최적화
echo "테이블 최적화..."
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "
    OPTIMIZE TABLE documents;
    OPTIMIZE TABLE document_versions;
    OPTIMIZE TABLE audit_logs;
    OPTIMIZE TABLE sessions;
"

echo "✅ 일일 데이터 정리 완료"
```

### 7.4 백업 스크립트

```bash
#!/bin/bash
# database/backup/backup_database.sh
# Database 백업

set -e

DB_USER="mcps_user"
DB_PASSWORD="your_password"
DB_NAME="mcps_db"

BACKUP_DIR="/app/poc/mcps/data/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mcps_db_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "=== Database 백업 ==="
echo "시작: $(date)"

# 백업 실행
mysqldump -u $DB_USER -p$DB_PASSWORD \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --add-drop-database \
    --databases $DB_NAME \
    | gzip > "$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "완료: $(date)"
echo "파일: $BACKUP_FILE"
echo "크기: $BACKUP_SIZE"

# 오래된 백업 삭제 (30일 이전)
find "$BACKUP_DIR" -name "mcps_db_*.sql.gz" -mtime +30 -delete

echo "✅ 백업 완료"
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
