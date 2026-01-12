-- ============================================
-- MCP Ecosystem - Database Schema
-- MariaDB 10.x+
-- Database: mcps_db
-- Charset: utf8mb4
-- ============================================

-- 문자셋 설정
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ============================================
-- 데이터베이스 생성
-- ============================================

CREATE DATABASE IF NOT EXISTS mcps_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE mcps_db;

-- ============================================
-- 테이블 삭제 (역순 - FK 의존성 고려)
-- ============================================

DROP TABLE IF EXISTS access_requests;
DROP TABLE IF EXISTS document_versions;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS tools;
DROP TABLE IF EXISTS servers;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS system_settings;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS migration_history;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS teams;

-- ============================================
-- 1. 팀 테이블 (teams)
-- ============================================

CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR(50) PRIMARY KEY COMMENT '팀 ID (예: T001)',
    name VARCHAR(100) NOT NULL COMMENT '팀 이름',
    description VARCHAR(500) COMMENT '팀 설명',
    parent_team_id VARCHAR(50) COMMENT '상위 팀 ID',
    manager_id VARCHAR(10) COMMENT '팀 관리자 ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    deleted_at TIMESTAMP NULL COMMENT '삭제일 (Soft Delete)',
    
    FOREIGN KEY (parent_team_id) REFERENCES teams(id) ON DELETE SET NULL,
    
    INDEX idx_parent_team (parent_team_id),
    INDEX idx_manager (manager_id),
    INDEX idx_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='팀';

-- ============================================
-- 2. 사용자 테이블 (users)
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(10) PRIMARY KEY COMMENT '사용자 ID (예: U001)',
    name VARCHAR(100) NOT NULL COMMENT '이름',
    email VARCHAR(255) UNIQUE COMMENT '이메일',
    password_hash VARCHAR(255) COMMENT '비밀번호 해시',
    role ENUM('junior', 'staff', 'manager', 'executive', 'admin') NOT NULL COMMENT '역할',
    team VARCHAR(50) COMMENT '팀 (예: dev_team)',
    team_id VARCHAR(50) COMMENT '팀 ID (FK)',
    department VARCHAR(100) COMMENT '부서',
    position VARCHAR(50) COMMENT '직급',
    active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    last_login_at TIMESTAMP NULL COMMENT '마지막 로그인',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    deleted_at TIMESTAMP NULL COMMENT '삭제일 (Soft Delete)',
    
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL,
    
    INDEX idx_role (role),
    INDEX idx_team (team),
    INDEX idx_team_id (team_id),
    INDEX idx_active (active),
    INDEX idx_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='사용자';

-- teams 테이블의 manager_id 외래키 추가 (순환 참조 해결)
ALTER TABLE teams ADD FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL;

-- ============================================
-- 3. 문서 테이블 (documents)
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
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft' COMMENT '문서 상태',
    view_count INT DEFAULT 0 COMMENT '조회수',
    tags JSON COMMENT '태그 배열',
    version INT DEFAULT 1 COMMENT '버전',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    deleted_at TIMESTAMP NULL COMMENT '삭제일 (Soft Delete)',
    
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE RESTRICT,
    
    INDEX idx_classification (classification),
    INDEX idx_category (category),
    INDEX idx_author (author_id),
    INDEX idx_team (team),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at),
    INDEX idx_deleted_at (deleted_at),
    
    FULLTEXT INDEX ft_title_content (title, content) WITH PARSER ngram
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='문서';

-- ============================================
-- 4. 문서 버전 테이블 (document_versions)
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
-- 5. 권한 테이블 (permissions)
-- ============================================

CREATE TABLE IF NOT EXISTS permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(10) COMMENT '사용자 ID (NULL이면 역할 기반)',
    role VARCHAR(20) COMMENT '역할 (NULL이면 사용자 기반)',
    resource_type VARCHAR(50) NOT NULL COMMENT '리소스 타입 (document, tool, server)',
    resource_id VARCHAR(100) NOT NULL COMMENT '리소스 ID',
    actions JSON NOT NULL COMMENT '허용된 액션 ["read", "write", "delete"]',
    status ENUM('active', 'revoked') DEFAULT 'active' COMMENT '권한 상태',
    granted_by VARCHAR(10) COMMENT '부여자 ID',
    reason VARCHAR(500) COMMENT '부여 사유',
    expires_at TIMESTAMP NULL COMMENT '만료일',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_user (user_id),
    INDEX idx_role (role),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='권한';

-- ============================================
-- 6. Tool 레지스트리 테이블 (tools)
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
-- 7. MCP Server 테이블 (servers)
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
-- 8. 감사 로그 테이블 (audit_logs)
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
-- 9. 접근 요청 테이블 (access_requests)
-- ============================================

CREATE TABLE IF NOT EXISTS access_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(10) NOT NULL COMMENT '요청자 ID',
    resource_type VARCHAR(50) NOT NULL COMMENT '리소스 타입',
    resource_id VARCHAR(100) NOT NULL COMMENT '리소스 ID',
    reason VARCHAR(1000) NOT NULL COMMENT '요청 사유',
    status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending' COMMENT '상태',
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
-- 10. 시스템 설정 테이블 (system_settings)
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

-- ============================================
-- 11. 세션 테이블 (sessions)
-- ============================================

CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(100) PRIMARY KEY COMMENT '세션 ID (UUID)',
    user_id VARCHAR(10) NOT NULL COMMENT '사용자 ID',
    token VARCHAR(500) UNIQUE NOT NULL COMMENT '인증 토큰',
    ip_address VARCHAR(45) COMMENT 'IP 주소',
    user_agent VARCHAR(500) COMMENT 'User Agent',
    expires_at TIMESTAMP NOT NULL COMMENT '만료일',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '마지막 접근일',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_user (user_id),
    INDEX idx_token (token),
    INDEX idx_expires_at (expires_at),
    INDEX idx_last_accessed (last_accessed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='사용자 세션';

-- ============================================
-- 12. 마이그레이션 히스토리 테이블 (migration_history)
-- ============================================

CREATE TABLE IF NOT EXISTS migration_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(50) NOT NULL COMMENT '마이그레이션 버전',
    description VARCHAR(500) COMMENT '마이그레이션 설명',
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '실행일',
    checksum VARCHAR(64) COMMENT 'SQL 체크섬 (SHA256)',
    
    UNIQUE KEY uk_version (version),
    INDEX idx_executed_at (executed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='마이그레이션 히스토리';

-- ============================================
-- 완료 메시지
-- ============================================

SELECT '✅ Schema creation completed!' AS Status;
SELECT CONCAT('Total tables created: ', COUNT(*)) AS Summary
FROM information_schema.tables 
WHERE table_schema = 'mcps_db';
