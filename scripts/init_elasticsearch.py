#!/usr/bin/env python3
"""
Elasticsearch 인덱스 초기화 스크립트
documents와 audit_logs 인덱스를 생성합니다.
"""

import sys
import json
from pathlib import Path

# shared 모듈 import를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.logging_config import setup_logging
from shared.elasticsearch import ElasticsearchManager
from shared import CONFIG

logger = setup_logging("init_elasticsearch")


def load_mapping(mapping_file: Path) -> dict:
    """매핑 파일 로드"""
    with open(mapping_file, "r", encoding="utf-8") as f:
        return json.load(f)


def create_index(es: ElasticsearchManager, index_name: str, mapping_data: dict, force: bool = False):
    """인덱스 생성"""
    logger.info(f"Creating index: {index_name}")
    
    # 기존 인덱스 확인
    if es.index_exists(index_name):
        if force:
            logger.warning(f"Index already exists: {index_name}, deleting...")
            es.delete_index(index_name)
            logger.info(f"Deleted index: {index_name}")
        else:
            logger.warning(f"Index already exists: {index_name}, skipping...")
            return False
    
    # 인덱스 생성
    try:
        es.create_index(
            index=index_name,
            mappings=mapping_data.get("mappings", {}),
            settings=mapping_data.get("settings", {})
        )
        logger.info(f"✅ Index created: {index_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create index {index_name}: {e}")
        raise


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("Starting Elasticsearch Initialization")
    logger.info("=" * 60)
    
    # Elasticsearch 연결 설정
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
        # 헬스 체크
        health = es.health_check()
        logger.info(f"Elasticsearch health: {health}")
        
        # 매핑 파일 경로
        base_dir = Path(__file__).parent.parent
        mappings_dir = base_dir / "data" / "elasticsearch" / "mappings"
        
        # 인덱스 목록
        indexes = [
            {
                "name": "documents",
                "mapping_file": mappings_dir / "documents.json",
                "description": "문서 인덱스 (Nori 분석기)"
            },
            {
                "name": "audit_logs",
                "mapping_file": mappings_dir / "audit_logs.json",
                "description": "감사 로그 인덱스"
            }
        ]
        
        # 사용자에게 확인
        logger.info("")
        logger.info("The following indexes will be created:")
        for index_info in indexes:
            logger.info(f"  - {index_info['name']}: {index_info['description']}")
        
        # force 모드 여부 확인 (기존 인덱스 삭제)
        force = False
        if len(sys.argv) > 1 and sys.argv[1] == "--force":
            force = True
            logger.warning("⚠️  --force mode: Existing indexes will be deleted!")
        
        logger.info("")
        
        # 인덱스 생성
        created_count = 0
        skipped_count = 0
        
        for index_info in indexes:
            index_name = index_info["name"]
            mapping_file = index_info["mapping_file"]
            
            if not mapping_file.exists():
                logger.error(f"❌ Mapping file not found: {mapping_file}")
                continue
            
            # 매핑 로드
            mapping_data = load_mapping(mapping_file)
            
            # 인덱스 생성
            if create_index(es, index_name, mapping_data, force):
                created_count += 1
            else:
                skipped_count += 1
        
        # 결과 확인
        logger.info("")
        logger.info("=" * 60)
        logger.info("Elasticsearch Initialization Summary")
        logger.info("=" * 60)
        
        # 인덱스 목록 조회
        for index_info in indexes:
            index_name = index_info["name"]
            if es.index_exists(index_name):
                doc_count = es.count(index_name)
                logger.info(f"  - {index_name}: {doc_count} documents")
            else:
                logger.info(f"  - {index_name}: Not created")
        
        logger.info("")
        logger.info(f"✅ Elasticsearch initialization completed!")
        logger.info(f"   Created: {created_count}, Skipped: {skipped_count}")
        
    except Exception as e:
        logger.error(f"❌ Elasticsearch initialization failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        es.close()


if __name__ == "__main__":
    main()
