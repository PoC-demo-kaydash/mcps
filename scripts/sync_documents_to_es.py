#!/usr/bin/env python3
"""
문서 동기화 스크립트
MariaDB의 문서 데이터를 Elasticsearch로 동기화합니다.
"""

import sys
from pathlib import Path
from datetime import datetime

# shared 모듈 import를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.logging_config import setup_logging
from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from shared import CONFIG

logger = setup_logging("sync_documents")


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("Starting Document Synchronization (MariaDB → Elasticsearch)")
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
        # documents 인덱스 확인
        if not es.index_exists("documents"):
            logger.error("❌ Index 'documents' does not exist. Run init_elasticsearch.py first.")
            sys.exit(1)
        
        logger.info("Fetching documents from MariaDB...")
        
        # 전체 문서 조회 (JOIN으로 작성자 이름 포함)
        documents = db.fetch_all(
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
        
        if not documents:
            logger.info("No documents to sync")
            return
        
        # Elasticsearch에 색인
        indexed = 0
        failed = 0
        es_docs = []
        
        for doc in documents:
            try:
                # ES 문서 생성
                es_doc = {
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
                }
                
                es_docs.append(es_doc)
                
                # 100개씩 배치 처리
                if len(es_docs) >= 100:
                    result = es.bulk_index("documents", es_docs)
                    indexed += result["success"]
                    failed += result["failed"]
                    logger.info(f"Indexed {indexed} documents...")
                    es_docs = []
            
            except Exception as e:
                logger.error(f"Failed to prepare document {doc['id']}: {e}")
                failed += 1
        
        # 남은 문서 색인
        if es_docs:
            result = es.bulk_index("documents", es_docs)
            indexed += result["success"]
            failed += result["failed"]
        
        # 결과 요약
        logger.info("")
        logger.info("=" * 60)
        logger.info("Synchronization Summary")
        logger.info("=" * 60)
        logger.info(f"Total documents in MariaDB: {len(documents)}")
        logger.info(f"Successfully indexed: {indexed}")
        logger.info(f"Failed: {failed}")
        
        # ES에서 문서 수 확인
        doc_count = es.count("documents")
        logger.info(f"Total documents in Elasticsearch: {doc_count}")
        logger.info("")
        logger.info("✅ Document synchronization completed!")
        
    except Exception as e:
        logger.error(f"❌ Document synchronization failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        db.close()
        es.close()


if __name__ == "__main__":
    main()
