-- ===========================================
-- MCP Ecosystem Database Schema
-- MariaDB 10.x+
-- ===========================================

-- 문자셋 설정
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ===========================================
-- 테이블 삭제 (역순)
-- ===========================================

DROP TABLE IF EXISTS access_requests;
DROP TABLE IF EXISTS document_versions;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS tools;
DROP TABLE IF EXISTS servers;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS users;

-- ===========================================
-- 사용자 테이블
-- ===========================================

CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY COMMENT '사용자 ID (예: U001)',
    username VARCHAR(100) NOT NULL COMMENT '사용자명',
    email VARCHAR(255) NOT NULL COMMENT '이메일',
    password_hash VARCHAR(255) NOT NULL COMMENT '비밀번호 해시 (bcrypt)',
    role ENUM('viewer', 'editor', 'manager', 'admin', 'super_admin') NOT NULL DEFAULT 'viewer' COMMENT '역할',
    department VARCHAR(100) DEFAULT '' COMMENT '부서',
    classification_level TINYINT NOT NULL DEFAULT 1 COMMENT '보안 등급 (1-5)',
    status ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active' COMMENT '상태',
    last_login DATETIME NULL COMMENT '마지막 로그인',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email),
    KEY idx_role (role),
    KEY idx_status (status),
    KEY idx_department (department),
    KEY idx_classification (classification_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자';


-- ===========================================
-- 문서 테이블
-- ===========================================

CREATE TABLE documents (
    doc_id VARCHAR(50) PRIMARY KEY COMMENT '문서 ID (예: DOC001)',
    title VARCHAR(500) NOT NULL COMMENT '제목',
    content LONGTEXT COMMENT '문서 내용 (마크다운)',
    summary TEXT COMMENT '요약',
    author_id VARCHAR(50) NOT NULL COMMENT '작성자 ID',
    classification ENUM('public', 'internal', 'confidential', 'secret', 'top_secret') NOT NULL DEFAULT 'internal' COMMENT '보안등급',
    doc_type VARCHAR(50) NOT NULL DEFAULT 'general' COMMENT '문서 유형 (general, report, policy, manual, ...)',
    status ENUM('draft', 'published', 'archived', 'deleted') NOT NULL DEFAULT 'draft' COMMENT '상태',
    file_path VARCHAR(1000) DEFAULT '' COMMENT '파일 경로',
    file_size BIGINT DEFAULT 0 COMMENT '파일 크기 (bytes)',
    version INT NOT NULL DEFAULT 1 COMMENT '버전',
    tags JSON COMMENT '태그 ["tag1", "tag2"]',
    metadata JSON COMMENT '메타데이터',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    
    FOREIGN KEY fk_author (author_id) REFERENCES users(user_id) ON DELETE RESTRICT,
    KEY idx_classification (classification),
    KEY idx_status (status),
    KEY idx_doc_type (doc_type),
    KEY idx_author (author_id),
    KEY idx_created (created_at),
    FULLTEXT KEY ft_title (title) WITH PARSER ngram
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='문서';


-- ===========================================
-- MCP 서버 테이블
-- ===========================================

CREATE TABLE servers (
    server_id VARCHAR(50) PRIMARY KEY COMMENT '서버 ID (예: SRV001)',
    name VARCHAR(100) NOT NULL COMMENT '서버 이름',
    description TEXT COMMENT '설명',
    command VARCHAR(500) NOT NULL COMMENT '실행 명령어',
    args JSON COMMENT '실행 인자 ["arg1", "arg2"]',
    env JSON COMMENT '환경 변수 {"KEY": "VALUE"}',
    category VARCHAR(50) NOT NULL DEFAULT 'general' COMMENT '카테고리',
    status ENUM('active', 'inactive', 'maintenance') NOT NULL DEFAULT 'active' COMMENT '상태',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    
    UNIQUE KEY uk_name (name),
    KEY idx_category (category),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='MCP 서버';


-- ===========================================
-- MCP Tool 테이블
-- ===========================================

CREATE TABLE tools (
    tool_id VARCHAR(50) PRIMARY KEY COMMENT 'Tool ID (예: TOOL001)',
    server_id VARCHAR(50) NOT NULL COMMENT '서버 ID',
    name VARCHAR(100) NOT NULL COMMENT 'Tool 이름',
    description TEXT COMMENT '설명',
    input_schema JSON NOT NULL COMMENT '입력 스키마 (JSON Schema)',
    category VARCHAR(50) NOT NULL DEFAULT 'general' COMMENT '카테고리',
    required_role ENUM('viewer', 'editor', 'manager', 'admin', 'super_admin') NOT NULL DEFAULT 'viewer' COMMENT '필요 역할',
    status ENUM('active', 'inactive', 'deprecated') NOT NULL DEFAULT 'active' COMMENT '상태',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    
    FOREIGN KEY fk_server (server_id) REFERENCES servers(server_id) ON DELETE CASCADE,
    UNIQUE KEY uk_server_name (server_id, name),
    KEY idx_name (name),
    KEY idx_category (category),
    KEY idx_status (status),
    KEY idx_required_role (required_role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='MCP Tool';


-- ===========================================
-- 권한 테이블
-- ===========================================

CREATE TABLE permissions (
    perm_id VARCHAR(50) PRIMARY KEY COMMENT '권한 ID (예: PERM001)',
    user_id VARCHAR(50) NOT NULL COMMENT '사용자 ID',
    doc_id VARCHAR(50) NOT NULL COMMENT '문서 ID',
    action ENUM('read', 'write', 'delete', 'share', 'manage') NOT NULL COMMENT '액션',
    granted_by VARCHAR(50) NOT NULL COMMENT '권한 부여자 ID',
    expires_at DATETIME NULL COMMENT '만료 일시',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY fk_user (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY fk_doc (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY fk_granter (granted_by) REFERENCES users(user_id) ON DELETE RESTRICT,
    
    UNIQUE KEY uk_user_doc_action (user_id, doc_id, action),
    KEY idx_user (user_id),
    KEY idx_doc (doc_id),
    KEY idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='문서 권한';


-- ===========================================
-- 감사 로그 테이블
-- ===========================================

CREATE TABLE audit_logs (
    log_id VARCHAR(50) PRIMARY KEY COMMENT '로그 ID (예: LOG001)',
    user_id VARCHAR(50) NOT NULL COMMENT '사용자 ID',
    action VARCHAR(50) NOT NULL COMMENT '액션 (login, logout, read, write, delete, ...)',
    resource_type VARCHAR(50) NOT NULL COMMENT '리소스 유형 (user, document, tool, ...)',
    resource_id VARCHAR(50) NOT NULL COMMENT '리소스 ID',
    details JSON COMMENT '상세 정보',
    status ENUM('success', 'failure', 'error') NOT NULL DEFAULT 'success' COMMENT '결과',
    ip_address VARCHAR(45) DEFAULT '' COMMENT 'IP 주소 (IPv6 지원)',
    user_agent VARCHAR(500) DEFAULT '' COMMENT 'User Agent',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    KEY idx_user (user_id),
    KEY idx_action (action),
    KEY idx_resource (resource_type, resource_id),
    KEY idx_status (status),
    KEY idx_created (created_at),
    KEY idx_ip (ip_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='감사 로그';


-- ===========================================
-- 문서 버전 테이블
-- ===========================================

CREATE TABLE document_versions (
    version_id VARCHAR(50) PRIMARY KEY COMMENT '버전 ID (예: VER001)',
    doc_id VARCHAR(50) NOT NULL COMMENT '문서 ID',
    version INT NOT NULL COMMENT '버전 번호',
    content LONGTEXT NOT NULL COMMENT '문서 내용',
    modified_by VARCHAR(50) NOT NULL COMMENT '수정자 ID',
    change_summary VARCHAR(500) DEFAULT '' COMMENT '변경 요약',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY fk_doc (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY fk_modifier (modified_by) REFERENCES users(user_id) ON DELETE RESTRICT,
    
    UNIQUE KEY uk_doc_version (doc_id, version),
    KEY idx_doc (doc_id),
    KEY idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='문서 버전 이력';


-- ===========================================
-- 접근 요청 테이블
-- ===========================================

CREATE TABLE access_requests (
    request_id VARCHAR(50) PRIMARY KEY COMMENT '요청 ID (예: REQ001)',
    requester_id VARCHAR(50) NOT NULL COMMENT '요청자 ID',
    doc_id VARCHAR(50) NOT NULL COMMENT '문서 ID',
    requested_action ENUM('read', 'write', 'delete', 'share') NOT NULL COMMENT '요청 액션',
    reason TEXT NOT NULL COMMENT '요청 사유',
    status ENUM('pending', 'approved', 'rejected', 'cancelled') NOT NULL DEFAULT 'pending' COMMENT '상태',
    approved_by VARCHAR(50) NULL COMMENT '처리자 ID',
    approver_comment VARCHAR(500) DEFAULT '' COMMENT '처리자 코멘트',
    processed_at DATETIME NULL COMMENT '처리 일시',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY fk_requester (requester_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY fk_doc (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY fk_approver (approved_by) REFERENCES users(user_id) ON DELETE SET NULL,
    
    KEY idx_requester (requester_id),
    KEY idx_doc (doc_id),
    KEY idx_status (status),
    KEY idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='접근 요청';


-- ===========================================
-- 초기 데이터
-- ===========================================

-- 기본 관리자 계정 (비밀번호: admin123)
-- bcrypt 해시는 Python에서 생성해야 함
INSERT INTO users (
    user_id, username, email, password_hash, 
    role, department, classification_level, status
) VALUES (
    'U001', 'admin', 'admin@mcps.local', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4UxMYzK2c8HvXLW.', -- admin123
    'super_admin', '시스템관리', 5, 'active'
);

-- 테스트 사용자
INSERT INTO users (
    user_id, username, email, password_hash,
    role, department, classification_level, status
) VALUES 
    ('U002', 'editor1', 'editor1@mcps.local', 
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4UxMYzK2c8HvXLW.', 
     'editor', '개발팀', 3, 'active'),
    ('U003', 'viewer1', 'viewer1@mcps.local',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4UxMYzK2c8HvXLW.',
     'viewer', '개발팀', 2, 'active');

-- 기본 MCP 서버
INSERT INTO servers (
    server_id, name, description, command, args, env, category, status
) VALUES 
    ('SRV001', 'document-mcp', '문서 관리 MCP 서버', 
     'python', '["mcp-servers/document/main.py"]', '{}',
     'document', 'active'),
    ('SRV002', 'search-mcp', '검색 MCP 서버',
     'python', '["mcp-servers/search/main.py"]', '{}',
     'search', 'active'),
    ('SRV003', 'admin-mcp', '관리 MCP 서버',
     'python', '["mcp-servers/admin/main.py"]', '{}',
     'admin', 'active');

-- 기본 Tool
INSERT INTO tools (
    tool_id, server_id, name, description, input_schema, category, required_role, status
) VALUES 
    ('TOOL001', 'SRV001', 'create_document', '새 문서를 생성합니다',
     '{"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}, "classification": {"type": "string"}}, "required": ["title", "content"]}',
     'document', 'editor', 'active'),
    ('TOOL002', 'SRV001', 'read_document', '문서를 조회합니다',
     '{"type": "object", "properties": {"doc_id": {"type": "string"}}, "required": ["doc_id"]}',
     'document', 'viewer', 'active'),
    ('TOOL003', 'SRV002', 'search_documents', '문서를 검색합니다',
     '{"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}',
     'search', 'viewer', 'active');


-- ===========================================
-- 완료 메시지
-- ===========================================

SELECT 'Schema created successfully!' as message;
SELECT 
    (SELECT COUNT(*) FROM users) as users,
    (SELECT COUNT(*) FROM servers) as servers,
    (SELECT COUNT(*) FROM tools) as tools;
