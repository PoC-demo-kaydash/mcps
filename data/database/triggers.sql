-- ============================================
-- Database Triggers
-- Database: mcps_db
-- ============================================

USE mcps_db;

-- ============================================
-- 1. 문서 버전 자동 생성
-- ============================================

DELIMITER //

-- 문서 생성 시 초기 버전 자동 생성
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

-- 문서 수정 시 새 버전 자동 생성
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
-- 2. 감사 로그 자동 기록
-- ============================================

DELIMITER //

-- 문서 삭제 시 감사 로그 자동 기록
-- Note: @current_user_id는 애플리케이션에서 SET @current_user_id = 'U001'; 형태로 설정 필요
CREATE TRIGGER trg_audit_document_delete
BEFORE DELETE ON documents
FOR EACH ROW
BEGIN
    -- current_user_id가 설정되어 있을 때만 로그 기록
    IF @current_user_id IS NOT NULL THEN
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
            JSON_OBJECT('title', OLD.title, 'classification', OLD.classification),
            'success'
        );
    END IF;
END//

DELIMITER ;

-- ============================================
-- Note: Tool 사용 횟수 증가는 애플리케이션 레벨에서 처리 권장
-- UPDATE tools SET usage_count = usage_count + 1 WHERE name = ?;
-- ============================================

-- ============================================
-- 완료 메시지
-- ============================================

SELECT '✅ Triggers created!' AS Status;
