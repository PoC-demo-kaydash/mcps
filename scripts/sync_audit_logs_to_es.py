#!/usr/bin/env python3
"""
감사 로그 동기화 스크립트
MariaDB의 감사 로그 데이터를 Elasticsearch로 동기화합니다.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# shared 모듈 import를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.logging_config import setup_logging
from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from shared import CONFIG

logger = setup_logging("sync_audit_logs")


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("Starting Audit Log Synchronization (MariaDB → Elasticsearch)")
    logger.info("=" * 60)
    
    # DB 연결 설정
    db_config = {
        "host": CONFIG["database"]["host"],
        "port": CONFIG["database"]["port"],
        "user": CONFIG["database"]["user"],
        "password": CONFIG["database"]["password"],
        "database": CONFIG["database"]["database"],
        "charset": CONFIG["database"]["charset"],
        "pool_size": {"min": 1, "max": 5}
    }
    
    db = DatabaseManager(db_config)
    
    # ES 연결 설정
    es_config = {
        "hosts": [CONFIG["elasticsearch"]["url"]],
        "http_auth": (
            CONFIG["elasticsearch"]["user"],
            CONFIG["elasticsearch"]["password"]
        ),
        "verify_certs": False,
        "ssl_show_warn": False,
        "timeout": 30
    }
    
    es = ElasticsearchManager(es_config)
    
    try:
        # audit_logs 인덱스 확인
        if not es.index_exists("audit_logs"):
            logger.error("❌ Index 'audit_logs' does not exist. Run init_elasticsearch.py first.")
            sys.exit(1)
        
        logger.info("Fetching audit logs from MariaDB...")
        
        # 최근 30일 로그만 동기화 (옵션)
        # start_date = datetime.now() - timedelta(days=30)
        
        # 전체 감사 로그 조회 (JOIN으로 사용자 이름 포함)
        logs = db.fetch_all(
            """
            SELECT 
                a.id, a.user_id, a.action, a.resource_type, a.resource_id,
                a.details, a.result, a.ip_address, a.user_agent, a.created_at,
                u.name AS user_name
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at
            """
        )
        
        logger.info(f"Found {len(logs)} audit logs")
        
        if not logs:
            logger.info("No audit logs to sync")
            return
        
        # Elasticsearch에 색인
        indexed = 0
        failed = 0
        es_docs = []
        
        for log in logs:
            try:
                # ES 문서 생성
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
                
                # 1000개씩 배치 처리
                if len(es_docs) >= 1000:
                    result = es.bulk_index("audit_logs", es_docs)
                    indexed += result["success"]
                    failed += result["failed"]
                    logger.info(f"Indexed {indexed} logs...")
                    es_docs = []
            
            except Exception as e:
                logger.error(f"Failed to prepare log {log['id']}: {e}")
                failed += 1
        
        # 남은 로그 색인
        if es_docs:
            result = es.bulk_index("audit_logs", es_docs)
            indexed += result["success"]
            failed += result["failed"]
        
        # 결과 요약
        logger.info("")
        logger.info("=" * 60)
        logger.info("Synchronization Summary")
        logger.info("=" * 60)
        logger.info(f"Total logs in MariaDB: {len(logs)}")
        logger.info(f"Successfully indexed: {indexed}")
        logger.info(f"Failed: {failed}")
        
        # ES에서 로그 수 확인
        log_count = es.count("audit_logs")
        logger.info(f"Total logs in Elasticsearch: {log_count}")
        logger.info("")
        logger.info("✅ Audit log synchronization completed!")
        
    except Exception as e:
        logger.error(f"❌ Audit log synchronization failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        db.close()
        es.close()


if __name__ == "__main__":
    main()
