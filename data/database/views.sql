-- ============================================
-- Database Views for Statistics
-- Database: mcps_db
-- ============================================

USE mcps_db;

-- ============================================
-- 1. 사용자별 문서 통계 뷰
-- ============================================

CREATE OR REPLACE VIEW v_user_document_stats AS
SELECT 
    u.id AS user_id,
    u.name AS user_name,
    u.role,
    u.team,
    u.department,
    COUNT(DISTINCT d.id) AS total_documents,
    COUNT(DISTINCT CASE WHEN d.classification = 'public' THEN d.id END) AS public_docs,
    COUNT(DISTINCT CASE WHEN d.classification = 'team' THEN d.id END) AS team_docs,
    COUNT(DISTINCT CASE WHEN d.classification = 'confidential' THEN d.id END) AS confidential_docs,
    COUNT(DISTINCT CASE WHEN d.status = 'draft' THEN d.id END) AS draft_docs,
    COUNT(DISTINCT CASE WHEN d.status = 'published' THEN d.id END) AS published_docs,
    COUNT(DISTINCT CASE WHEN d.status = 'archived' THEN d.id END) AS archived_docs,
    SUM(COALESCE(d.view_count, 0)) AS total_views,
    COUNT(DISTINCT dv.id) AS total_versions,
    MAX(d.created_at) AS last_document_created,
    MAX(d.updated_at) AS last_document_updated
FROM 
    users u
    LEFT JOIN documents d ON u.id = d.author_id AND d.deleted_at IS NULL
    LEFT JOIN document_versions dv ON d.id = dv.document_id
WHERE 
    u.deleted_at IS NULL
GROUP BY 
    u.id, u.name, u.role, u.team, u.department;

-- ============================================
-- 2. 문서별 버전 통계 뷰
-- ============================================

CREATE OR REPLACE VIEW v_document_version_stats AS
SELECT 
    d.id AS document_id,
    d.title,
    d.classification,
    d.category,
    d.status,
    d.author_id,
    u.name AS author_name,
    d.version AS current_version,
    COUNT(dv.id) AS total_versions,
    COUNT(DISTINCT dv.changed_by) AS unique_contributors,
    MIN(dv.created_at) AS first_version_date,
    MAX(dv.created_at) AS last_version_date,
    DATEDIFF(MAX(dv.created_at), MIN(dv.created_at)) AS version_lifespan_days,
    d.view_count,
    d.created_at AS document_created_at,
    d.updated_at AS document_updated_at
FROM 
    documents d
    LEFT JOIN document_versions dv ON d.id = dv.document_id
    LEFT JOIN users u ON d.author_id = u.id
WHERE 
    d.deleted_at IS NULL
GROUP BY 
    d.id, d.title, d.classification, d.category, d.status, 
    d.author_id, u.name, d.version, d.view_count, 
    d.created_at, d.updated_at;

-- ============================================
-- 3. 카테고리별 문서 통계 뷰
-- ============================================

CREATE OR REPLACE VIEW v_category_stats AS
SELECT 
    d.category,
    d.classification,
    d.status,
    COUNT(DISTINCT d.id) AS total_documents,
    COUNT(DISTINCT d.author_id) AS unique_authors,
    SUM(COALESCE(d.view_count, 0)) AS total_views,
    AVG(COALESCE(d.view_count, 0)) AS avg_views_per_document,
    COUNT(DISTINCT dv.id) AS total_versions,
    AVG(d.version) AS avg_version_number,
    MIN(d.created_at) AS first_document_date,
    MAX(d.created_at) AS latest_document_date,
    MAX(d.updated_at) AS last_updated_date,
    COUNT(DISTINCT CASE WHEN d.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
                        THEN d.id END) AS documents_last_30_days,
    COUNT(DISTINCT CASE WHEN d.updated_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
                        THEN d.id END) AS updated_last_30_days
FROM 
    documents d
    LEFT JOIN document_versions dv ON d.id = dv.document_id
WHERE 
    d.deleted_at IS NULL
    AND d.category IS NOT NULL
GROUP BY 
    d.category, d.classification, d.status;

-- ============================================
-- 추가 통계 뷰 (선택)
-- ============================================

-- 팀별 문서 통계
CREATE OR REPLACE VIEW v_team_document_stats AS
SELECT 
    t.id AS team_id,
    t.name AS team_name,
    COUNT(DISTINCT u.id) AS total_members,
    COUNT(DISTINCT d.id) AS total_documents,
    SUM(COALESCE(d.view_count, 0)) AS total_views,
    COUNT(DISTINCT CASE WHEN d.status = 'published' THEN d.id END) AS published_docs,
    MAX(d.created_at) AS last_document_created
FROM 
    teams t
    LEFT JOIN users u ON t.id = u.team_id AND u.deleted_at IS NULL
    LEFT JOIN documents d ON u.id = d.author_id AND d.deleted_at IS NULL
WHERE 
    t.deleted_at IS NULL
GROUP BY 
    t.id, t.name;

-- 일별 활동 통계
CREATE OR REPLACE VIEW v_daily_activity_stats AS
SELECT 
    DATE(a.created_at) AS activity_date,
    COUNT(DISTINCT a.id) AS total_actions,
    COUNT(DISTINCT a.user_id) AS active_users,
    COUNT(DISTINCT CASE WHEN a.action LIKE 'document%' THEN a.id END) AS document_actions,
    COUNT(DISTINCT CASE WHEN a.action LIKE 'tool%' THEN a.id END) AS tool_actions,
    COUNT(DISTINCT CASE WHEN a.result = 'success' THEN a.id END) AS successful_actions,
    COUNT(DISTINCT CASE WHEN a.result = 'failure' THEN a.id END) AS failed_actions,
    ROUND(COUNT(DISTINCT CASE WHEN a.result = 'success' THEN a.id END) * 100.0 / 
          NULLIF(COUNT(DISTINCT a.id), 0), 2) AS success_rate
FROM 
    audit_logs a
WHERE 
    a.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
GROUP BY 
    DATE(a.created_at)
ORDER BY 
    activity_date DESC;

-- ============================================
-- 완료 메시지
-- ============================================

SELECT '✅ Database views created successfully!' AS Status;
SELECT 'Views created: v_user_document_stats, v_document_version_stats, v_category_stats, v_team_document_stats, v_daily_activity_stats' AS Summary;
