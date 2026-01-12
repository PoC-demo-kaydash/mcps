-- ============================================
-- Initial Seed Data
-- Database: mcps_db
-- ============================================

USE mcps_db;

-- ============================================
-- 1. 팀 데이터
-- ============================================

INSERT INTO teams (id, name, description, parent_team_id, manager_id) VALUES
('T001', '경영진', '회사 경영진', NULL, 'U004'),
('T002', '개발팀', '소프트웨어 개발', NULL, 'U003'),
('T003', '인사팀', '인사 관리', NULL, 'U005'),
('T004', '재무팀', '재무 및 회계', NULL, 'U006'),
('T005', 'IT팀', '시스템 관리', NULL, 'U000'),
('T006', '백엔드팀', '백엔드 개발', 'T002', 'U002'),
('T007', '프론트엔드팀', '프론트엔드 개발', 'T002', 'U002');

-- ============================================
-- 2. 사용자 데이터
-- ============================================

INSERT INTO users (id, name, email, password_hash, role, team, team_id, department, position, active) VALUES
('U000', '관리자', 'admin@company.com', '$2b$12$example_hash_admin', 'admin', NULL, 'T005', 'IT팀', '시스템 관리자', TRUE),
('U001', '김신입', 'junior@company.com', '$2b$12$example_hash_junior', 'junior', 'dev_team', 'T002', '개발팀', '사원', TRUE),
('U002', '이사원', 'staff@company.com', '$2b$12$example_hash_staff', 'staff', 'dev_team', 'T006', '개발팀', '대리', TRUE),
('U003', '박매니저', 'manager@company.com', '$2b$12$example_hash_manager', 'manager', 'dev_team', 'T002', '개발팀', '과장', TRUE),
('U004', '최임원', 'executive@company.com', '$2b$12$example_hash_exec', 'executive', NULL, 'T001', '경영진', '이사', TRUE),
('U005', '정사원', 'staff2@company.com', '$2b$12$example_hash_staff2', 'staff', 'hr_team', 'T003', '인사팀', '대리', TRUE),
('U006', '강대리', 'staff3@company.com', '$2b$12$example_hash_staff3', 'staff', 'finance_team', 'T004', '재무팀', '대리', TRUE);

-- ============================================
-- 3. 문서 데이터 (샘플 9개)
-- ============================================

-- Public 문서 (3개)
INSERT INTO documents (id, title, content, classification, category, author_id, team) VALUES
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

올해 우리는 더 큰 도약을 준비하고 있습니다.',
'public', 'general', 'U004', NULL),

('DOC003', '복지 제도 안내', 
'# 복지 제도

## 1. 건강 검진
- 연 1회 종합 건강 검진 지원

## 2. 식사 지원
- 중식 지원 (1만원/일)

## 3. 교육 지원
- 외부 교육 수강료 지원 (연 300만원)',
'public', 'hr', 'U005', NULL);

-- Team 문서 (4개)
INSERT INTO documents (id, title, content, classification, category, author_id, team) VALUES
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

('DOC007', '2026년 예산 계획', 
'# 2026년 예산 계획

## 총 예산
- 100억원 (전년 대비 10% 증가)

## 부서별 배분
- 개발팀: 40억
- 마케팅팀: 30억
- 인사팀: 10억
- 관리팀: 20억',
'team', 'finance', 'U006', 'finance_team');

-- Confidential 문서 (2개)
INSERT INTO documents (id, title, content, classification, category, author_id, team) VALUES
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
-- 4. Tool 레지스트리
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
-- 5. MCP Server
-- ============================================

INSERT INTO servers (name, description, status) VALUES
('auth_server', '인증 및 권한 관리', 'stopped'),
('search_server', '문서 검색', 'stopped'),
('document_server', '문서 CRUD', 'stopped'),
('version_server', '문서 버전 관리', 'stopped'),
('audit_server', '감사 로그', 'stopped');

-- ============================================
-- 6. 시스템 설정
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
-- 7. 샘플 감사 로그
-- ============================================

INSERT INTO audit_logs (user_id, action, resource_type, resource_id, result, ip_address) VALUES
('U001', 'login', 'user', 'U001', 'success', '192.168.1.100'),
('U001', 'document_view', 'document', 'DOC001', 'success', '192.168.1.100'),
('U002', 'login', 'user', 'U002', 'success', '192.168.1.101'),
('U002', 'document_create', 'document', 'DOC005', 'success', '192.168.1.101'),
('U003', 'login', 'user', 'U003', 'success', '192.168.1.102'),
('U003', 'document_view', 'document', 'DOC004', 'success', '192.168.1.102');

-- ============================================
-- 완료 메시지
-- ============================================

SELECT '✅ Seed data insertion completed!' AS Status;
SELECT CONCAT('Users: ', COUNT(*)) FROM users UNION ALL
SELECT CONCAT('Documents: ', COUNT(*)) FROM documents UNION ALL
SELECT CONCAT('Tools: ', COUNT(*)) FROM tools UNION ALL
SELECT CONCAT('Servers: ', COUNT(*)) FROM servers UNION ALL
SELECT CONCAT('Settings: ', COUNT(*)) FROM system_settings UNION ALL
SELECT CONCAT('Audit Logs: ', COUNT(*)) FROM audit_logs;
