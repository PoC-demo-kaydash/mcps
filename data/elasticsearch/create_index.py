#!/usr/bin/env python3
"""
Elasticsearch Index Creation Script
Database: mcps_db
Elasticsearch Indexes: documents, audit_logs
"""

import json
import os
import sys
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError

# 설정
ES_HOST = os.getenv('ELASTICSEARCH_HOST', 'localhost')
ES_PORT = int(os.getenv('ELASTICSEARCH_PORT', 9200))
ES_USER = os.getenv('ELASTICSEARCH_USER', 'elastic')
ES_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD', 'your_password')

# 매핑 파일 경로
MAPPINGS_DIR = os.path.join(os.path.dirname(__file__), 'mappings')

# 색상 출력
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color

def log_info(message):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")

def log_warn(message):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")

def log_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def connect_elasticsearch():
    """Elasticsearch 연결"""
    log_info(f"Elasticsearch 연결 중... ({ES_HOST}:{ES_PORT})")
    
    try:
        es = Elasticsearch(
            [f"http://{ES_HOST}:{ES_PORT}"],
            basic_auth=(ES_USER, ES_PASSWORD),
            request_timeout=30
        )
        
        # 연결 확인
        if es.ping():
            info = es.info()
            log_info(f"Elasticsearch 연결 성공!")
            log_info(f"버전: {info['version']['number']}")
            log_info(f"클러스터 이름: {info['cluster_name']}")
            return es
        else:
            log_error("Elasticsearch 연결 실패!")
            return None
    except Exception as e:
        log_error(f"Elasticsearch 연결 오류: {e}")
        return None

def load_mapping(index_name):
    """매핑 파일 로드"""
    mapping_file = os.path.join(MAPPINGS_DIR, f"{index_name}.json")
    
    if not os.path.exists(mapping_file):
        log_error(f"매핑 파일을 찾을 수 없습니다: {mapping_file}")
        return None
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        log_info(f"매핑 파일 로드 성공: {mapping_file}")
        return mapping
    except Exception as e:
        log_error(f"매핑 파일 로드 오류: {e}")
        return None

def create_index(es, index_name, mapping, force=False):
    """인덱스 생성"""
    log_info(f"인덱스 생성 중: {index_name}")
    
    # 기존 인덱스 확인
    if es.indices.exists(index=index_name):
        if force:
            log_warn(f"기존 인덱스 삭제 중: {index_name}")
            es.indices.delete(index=index_name)
        else:
            log_warn(f"인덱스가 이미 존재합니다: {index_name}")
            response = input(f"기존 인덱스를 삭제하고 재생성하시겠습니까? (y/N): ")
            if response.lower() == 'y':
                log_warn(f"기존 인덱스 삭제 중: {index_name}")
                es.indices.delete(index=index_name)
            else:
                log_info(f"인덱스 생성 건너뛰기: {index_name}")
                return False
    
    # 인덱스 생성
    try:
        es.indices.create(
            index=index_name,
            body=mapping
        )
        log_info(f"✅ 인덱스 생성 완료: {index_name}")
        
        # 인덱스 정보 확인
        settings = es.indices.get_settings(index=index_name)
        mappings = es.indices.get_mapping(index=index_name)
        
        num_shards = settings[index_name]['settings']['index']['number_of_shards']
        num_replicas = settings[index_name]['settings']['index']['number_of_replicas']
        
        log_info(f"  - Shards: {num_shards}")
        log_info(f"  - Replicas: {num_replicas}")
        
        return True
    except RequestError as e:
        log_error(f"인덱스 생성 오류: {e.info}")
        return False
    except Exception as e:
        log_error(f"인덱스 생성 오류: {e}")
        return False

def verify_indices(es, index_names):
    """인덱스 확인"""
    log_info("인덱스 확인 중...")
    
    for index_name in index_names:
        if es.indices.exists(index=index_name):
            doc_count = es.count(index=index_name)['count']
            log_info(f"  ✅ {index_name}: {doc_count} documents")
        else:
            log_error(f"  ❌ {index_name}: 존재하지 않음")

def main():
    """메인 함수"""
    print("=" * 60)
    print("Elasticsearch Index Creation Script")
    print("=" * 60)
    print()
    
    # 명령행 인자 처리
    force_mode = '--force' in sys.argv or '-f' in sys.argv
    
    if force_mode:
        log_warn("강제 모드: 기존 인덱스를 자동으로 삭제합니다.")
    
    # Elasticsearch 연결
    es = connect_elasticsearch()
    if es is None:
        sys.exit(1)
    
    print()
    
    # 생성할 인덱스 목록
    indices = ['documents', 'audit_logs']
    created_indices = []
    
    # 각 인덱스 생성
    for index_name in indices:
        print("-" * 60)
        
        # 매핑 로드
        mapping = load_mapping(index_name)
        if mapping is None:
            log_error(f"인덱스 생성 실패: {index_name}")
            continue
        
        # 인덱스 생성
        if create_index(es, index_name, mapping, force=force_mode):
            created_indices.append(index_name)
        
        print()
    
    # 결과 확인
    print("=" * 60)
    log_info("인덱스 생성 완료!")
    print("=" * 60)
    
    if created_indices:
        log_info(f"생성된 인덱스: {', '.join(created_indices)}")
    else:
        log_warn("새로 생성된 인덱스가 없습니다.")
    
    print()
    
    # 모든 인덱스 확인
    verify_indices(es, indices)
    
    print()
    print("=" * 60)
    log_info("작업 완료!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        log_warn("사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        log_error(f"예기치 않은 오류: {e}")
        sys.exit(1)
