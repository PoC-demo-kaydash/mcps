-- ============================================
-- Additional Indexes for Performance Optimization
-- Database: mcps_db
-- ============================================

USE mcps_db;

-- ============================================
-- 복합 인덱스 (Composite Indexes)
-- ============================================

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

-- ============================================
-- 통계 쿼리용 인덱스
-- ============================================

-- 일별 문서 수
CREATE INDEX idx_documents_date ON documents(DATE(created_at));

-- 일별 감사 로그 수
CREATE INDEX idx_audit_date ON audit_logs(DATE(created_at));

-- 사용자 팀별 그룹화
CREATE INDEX idx_user_team ON users(team, role);

-- 문서 카테고리별 그룹화
CREATE INDEX idx_doc_category ON documents(category, classification);

-- ============================================
-- 신규 테이블 인덱스
-- ============================================

-- teams: 삭제되지 않은 팀 필터링
CREATE INDEX idx_teams_deleted ON teams(deleted_at);

-- teams: 상위 팀별 그룹화
CREATE INDEX idx_teams_parent_deleted ON teams(parent_team_id, deleted_at);

-- users: 삭제되지 않은 사용자 + 팀
CREATE INDEX idx_users_team_deleted ON users(team_id, deleted_at);

-- users: 활성 사용자 + 역할
CREATE INDEX idx_users_active_role ON users(active, role, deleted_at);

-- documents: 상태별 문서 필터링
CREATE INDEX idx_documents_status_deleted ON documents(status, deleted_at);

-- documents: 조회수 순 정렬
CREATE INDEX idx_documents_view_count ON documents(view_count DESC);

-- documents: 카테고리 + 상태
CREATE INDEX idx_documents_category_status ON documents(category, status, deleted_at);

-- sessions: 만료되지 않은 세션 조회
CREATE INDEX idx_sessions_user_expires ON sessions(user_id, expires_at);

-- sessions: 토큰으로 세션 조회
CREATE INDEX idx_sessions_token_expires ON sessions(token, expires_at);

-- permissions: 활성 권한 조회
CREATE INDEX idx_permissions_status_expires ON permissions(status, expires_at);

-- ============================================
-- 완료 메시지
-- ============================================

SELECT '✅ Additional indexes created!' AS Status;
