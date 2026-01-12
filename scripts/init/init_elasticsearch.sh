#!/bin/bash
# scripts/init/init_elasticsearch.sh
# Elasticsearch 초기화 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

log_info "Elasticsearch 초기화 시작..."

# ==============================================
# Elasticsearch 실행 대기
# ==============================================

log_info "Elasticsearch 준비 대기 중..."

if ! systemctl is-active --quiet elasticsearch; then
    log_warning "Elasticsearch가 실행 중이 아닙니다"
    log_info "Elasticsearch 시작 중..."
    systemctl start elasticsearch
fi

# Elasticsearch가 준비될 때까지 대기
if wait_for_url "${ES_URL}" ${ES_START_TIMEOUT}; then
    log_success "Elasticsearch 준비 완료"
else
    log_error "Elasticsearch가 시작되지 않았습니다 (타임아웃: ${ES_START_TIMEOUT}초)"
    exit 1
fi

# ==============================================
# Python 스크립트로 인덱스 생성
# ==============================================

log_info "Python 스크립트로 인덱스 생성 중..."

# 가상환경 활성화
if [ -f "${VENV_DIR}/bin/activate" ]; then
    source "${VENV_DIR}/bin/activate"
else
    log_error "가상환경을 찾을 수 없습니다: ${VENV_DIR}"
    exit 1
fi

# init_elasticsearch.py 실행
if [ -f "${SCRIPTS_DIR}/init_elasticsearch.py" ]; then
    cd "${SCRIPTS_DIR}"
    
    if python init_elasticsearch.py; then
        log_success "인덱스 생성 완료"
    else
        log_error "init_elasticsearch.py 실행 실패"
        exit 1
    fi
else
    log_warning "init_elasticsearch.py를 찾을 수 없습니다"
    log_info "수동으로 인덱스 생성을 진행합니다..."
    
    # 대체 방법: curl로 직접 인덱스 생성
    create_documents_index
    create_audit_logs_index
fi

# ==============================================
# 인덱스 직접 생성 함수
# ==============================================

create_documents_index() {
    log_info "documents 인덱스 생성 중..."
    
    curl -X PUT "${ES_URL}/documents" \
        -H 'Content-Type: application/json' \
        -d '{
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
          "analyzer": {
            "korean": {
              "type": "custom",
              "tokenizer": "standard",
              "filter": ["lowercase"]
            }
          }
        }
      },
      "mappings": {
        "properties": {
          "doc_id": {"type": "keyword"},
          "title": {
            "type": "text",
            "analyzer": "korean",
            "fields": {
              "keyword": {"type": "keyword"}
            }
          },
          "content": {
            "type": "text",
            "analyzer": "korean"
          },
          "classification": {"type": "keyword"},
          "category": {"type": "keyword"},
          "tags": {"type": "keyword"},
          "author_id": {"type": "keyword"},
          "team": {"type": "keyword"},
          "department": {"type": "keyword"},
          "created_at": {"type": "date"},
          "updated_at": {"type": "date"}
        }
      }
    }' 2>/dev/null
    
    log_success "documents 인덱스 생성 완료"
}

create_audit_logs_index() {
    log_info "audit_logs 인덱스 생성 중..."
    
    curl -X PUT "${ES_URL}/audit_logs" \
        -H 'Content-Type: application/json' \
        -d '{
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
      },
      "mappings": {
        "properties": {
          "log_id": {"type": "keyword"},
          "timestamp": {"type": "date"},
          "user_id": {"type": "keyword"},
          "action": {"type": "keyword"},
          "resource_type": {"type": "keyword"},
          "resource_id": {"type": "keyword"},
          "details": {"type": "text"},
          "ip_address": {"type": "ip"},
          "user_agent": {"type": "text"}
        }
      }
    }' 2>/dev/null
    
    log_success "audit_logs 인덱스 생성 완료"
}

# ==============================================
# 인덱스 확인
# ==============================================

log_info "생성된 인덱스 확인 중..."

INDICES=$(curl -s "${ES_URL}/_cat/indices?h=index" | grep -E "^(documents|audit_logs)" || echo "")

if [ -n "$INDICES" ]; then
    log_success "생성된 인덱스:"
    echo "$INDICES" | while read INDEX; do
        log_info "  - $INDEX"
    done
else
    log_warning "생성된 인덱스를 찾을 수 없습니다"
fi

log_success "======================================"
log_success "  Elasticsearch 초기화 완료"
log_success "======================================"
log_info "Cluster: ${ES_CLUSTER_NAME}"
log_info "URL: ${ES_URL}"
log_info ""
log_info "인덱스 확인:"
log_info "  curl ${ES_URL}/_cat/indices?v"
