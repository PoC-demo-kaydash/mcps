-- ============================================
-- Stored Procedures for Data Management
-- Database: mcps_db
-- ============================================

USE mcps_db;

DELIMITER $$

-- ============================================
-- 1. 만료된 세션 정리
-- ============================================

DROP PROCEDURE IF EXISTS sp_cleanup_expired_sessions$$

CREATE PROCEDURE sp_cleanup_expired_sessions()
BEGIN
    DECLARE deleted_count INT DEFAULT 0;
    
    -- 만료된 세션 삭제
    DELETE FROM sessions 
    WHERE expires_at < NOW();
    
    SET deleted_count = ROW_COUNT();
    
    -- 결과 반환
    SELECT 
        deleted_count AS sessions_deleted,
        NOW() AS cleanup_time,
        'Expired sessions cleaned up successfully' AS message;
END$$

-- ============================================
-- 2. 오래된 감사 로그 아카이브
-- ============================================

DROP PROCEDURE IF EXISTS sp_archive_old_audit_logs$$

CREATE PROCEDURE sp_archive_old_audit_logs(
    IN days_to_keep INT
)
BEGIN
    DECLARE archived_count INT DEFAULT 0;
    DECLARE archive_date DATETIME;
    
    SET archive_date = DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    -- 임시 아카이브 테이블 생성 (존재하지 않는 경우)
    CREATE TABLE IF NOT EXISTS audit_logs_archive LIKE audit_logs;
    
    -- 오래된 로그를 아카이브로 이동
    INSERT INTO audit_logs_archive
    SELECT * FROM audit_logs
    WHERE created_at < archive_date;
    
    SET archived_count = ROW_COUNT();
    
    -- 원본에서 삭제
    DELETE FROM audit_logs
    WHERE created_at < archive_date;
    
    -- 결과 반환
    SELECT 
        archived_count AS logs_archived,
        days_to_keep AS retention_days,
        archive_date AS archived_before,
        NOW() AS archive_time,
        'Old audit logs archived successfully' AS message;
END$$

-- ============================================
-- 3. 오래된 문서 버전 정리
-- ============================================

DROP PROCEDURE IF EXISTS sp_cleanup_old_document_versions$$

CREATE PROCEDURE sp_cleanup_old_document_versions(
    IN versions_to_keep INT
)
BEGIN
    DECLARE deleted_count INT DEFAULT 0;
    
    -- 각 문서별로 최신 N개 버전만 유지
    DELETE dv FROM document_versions dv
    INNER JOIN (
        SELECT document_id, version
        FROM (
            SELECT 
                document_id, 
                version,
                ROW_NUMBER() OVER (PARTITION BY document_id ORDER BY version DESC) AS rn
            FROM document_versions
        ) ranked
        WHERE rn > versions_to_keep
    ) old_versions ON dv.document_id = old_versions.document_id 
                   AND dv.version = old_versions.version;
    
    SET deleted_count = ROW_COUNT();
    
    -- 결과 반환
    SELECT 
        deleted_count AS versions_deleted,
        versions_to_keep AS versions_kept_per_document,
        NOW() AS cleanup_time,
        'Old document versions cleaned up successfully' AS message;
END$$

-- ============================================
-- 4. 삭제된 문서 영구 제거
-- ============================================

DROP PROCEDURE IF EXISTS sp_purge_deleted_documents$$

CREATE PROCEDURE sp_purge_deleted_documents(
    IN days_since_deletion INT
)
BEGIN
    DECLARE purged_count INT DEFAULT 0;
    DECLARE purge_date DATETIME;
    
    SET purge_date = DATE_SUB(NOW(), INTERVAL days_since_deletion DAY);
    
    -- Soft Delete된 지 N일 이상 지난 문서들 영구 삭제
    -- 연관된 버전도 CASCADE로 자동 삭제됨
    DELETE FROM documents
    WHERE deleted_at IS NOT NULL 
      AND deleted_at < purge_date;
    
    SET purged_count = ROW_COUNT();
    
    -- 결과 반환
    SELECT 
        purged_count AS documents_purged,
        days_since_deletion AS retention_days,
        purge_date AS deleted_before,
        NOW() AS purge_time,
        'Deleted documents purged successfully' AS message;
END$$

-- ============================================
-- 5. 시스템 통계 조회
-- ============================================

DROP PROCEDURE IF EXISTS sp_get_system_stats$$

CREATE PROCEDURE sp_get_system_stats()
BEGIN
    -- 전체 시스템 통계
    SELECT 
        'System Statistics' AS category,
        (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) AS total_users,
        (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL AND active = TRUE) AS active_users,
        (SELECT COUNT(*) FROM teams WHERE deleted_at IS NULL) AS total_teams,
        (SELECT COUNT(*) FROM documents WHERE deleted_at IS NULL) AS total_documents,
        (SELECT COUNT(*) FROM documents WHERE deleted_at IS NULL AND status = 'published') AS published_documents,
        (SELECT COUNT(*) FROM document_versions) AS total_versions,
        (SELECT COUNT(*) FROM permissions WHERE status = 'active' AND (expires_at IS NULL OR expires_at > NOW())) AS active_permissions,
        (SELECT COUNT(*) FROM sessions WHERE expires_at > NOW()) AS active_sessions,
        (SELECT COUNT(*) FROM audit_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)) AS actions_last_24h,
        (SELECT COUNT(*) FROM access_requests WHERE status = 'pending') AS pending_requests;
    
    -- 문서 분류별 통계
    SELECT 
        'Document Classification' AS category,
        classification,
        COUNT(*) AS count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM documents WHERE deleted_at IS NULL), 2) AS percentage
    FROM documents
    WHERE deleted_at IS NULL
    GROUP BY classification;
    
    -- 문서 상태별 통계
    SELECT 
        'Document Status' AS category,
        status,
        COUNT(*) AS count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM documents WHERE deleted_at IS NULL), 2) AS percentage
    FROM documents
    WHERE deleted_at IS NULL
    GROUP BY status;
    
    -- 최근 활동 통계 (최근 30일)
    SELECT 
        'Recent Activity (Last 30 Days)' AS category,
        DATE(created_at) AS date,
        COUNT(*) AS total_actions,
        COUNT(DISTINCT user_id) AS unique_users
    FROM audit_logs
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY DATE(created_at)
    ORDER BY date DESC
    LIMIT 30;
END$$

-- ============================================
-- 6. 사용자 활동 통계 조회
-- ============================================

DROP PROCEDURE IF EXISTS sp_get_user_activity_stats$$

CREATE PROCEDURE sp_get_user_activity_stats(
    IN target_user_id VARCHAR(10),
    IN days_back INT
)
BEGIN
    DECLARE start_date DATETIME;
    
    SET start_date = DATE_SUB(NOW(), INTERVAL days_back DAY);
    
    -- 사용자 기본 정보
    SELECT 
        'User Information' AS category,
        u.id,
        u.name,
        u.email,
        u.role,
        u.team,
        u.department,
        u.active,
        u.last_login_at,
        u.created_at
    FROM users u
    WHERE u.id = target_user_id AND u.deleted_at IS NULL;
    
    -- 문서 작성 통계
    SELECT 
        'Document Statistics' AS category,
        COUNT(*) AS total_documents,
        COUNT(CASE WHEN status = 'draft' THEN 1 END) AS draft_docs,
        COUNT(CASE WHEN status = 'published' THEN 1 END) AS published_docs,
        COUNT(CASE WHEN status = 'archived' THEN 1 END) AS archived_docs,
        SUM(COALESCE(view_count, 0)) AS total_views,
        AVG(COALESCE(view_count, 0)) AS avg_views_per_doc
    FROM documents
    WHERE author_id = target_user_id 
      AND deleted_at IS NULL
      AND created_at >= start_date;
    
    -- 활동 로그 통계
    SELECT 
        'Activity Statistics' AS category,
        COUNT(*) AS total_actions,
        COUNT(DISTINCT DATE(created_at)) AS active_days,
        COUNT(CASE WHEN result = 'success' THEN 1 END) AS successful_actions,
        COUNT(CASE WHEN result = 'failure' THEN 1 END) AS failed_actions,
        COUNT(DISTINCT action) AS unique_action_types
    FROM audit_logs
    WHERE user_id = target_user_id
      AND created_at >= start_date;
    
    -- 일별 활동 추이
    SELECT 
        'Daily Activity Trend' AS category,
        DATE(created_at) AS date,
        COUNT(*) AS actions,
        COUNT(DISTINCT action) AS unique_actions
    FROM audit_logs
    WHERE user_id = target_user_id
      AND created_at >= start_date
    GROUP BY DATE(created_at)
    ORDER BY date DESC;
    
    -- 액션 타입별 분포
    SELECT 
        'Action Distribution' AS category,
        action,
        COUNT(*) AS count,
        ROUND(COUNT(*) * 100.0 / (
            SELECT COUNT(*) FROM audit_logs 
            WHERE user_id = target_user_id AND created_at >= start_date
        ), 2) AS percentage
    FROM audit_logs
    WHERE user_id = target_user_id
      AND created_at >= start_date
    GROUP BY action
    ORDER BY count DESC
    LIMIT 10;
END$$

DELIMITER ;

-- ============================================
-- 완료 메시지
-- ============================================

SELECT '✅ Stored procedures created successfully!' AS Status;
SELECT 'Procedures: sp_cleanup_expired_sessions, sp_archive_old_audit_logs, sp_cleanup_old_document_versions, sp_purge_deleted_documents, sp_get_system_stats, sp_get_user_activity_stats' AS Summary;
