#!/bin/bash
# scripts/install/install_elasticsearch.sh
# Elasticsearch 설치 스크립트

set -e

# 공통 설정 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils/logger.sh"
source "${SCRIPT_DIR}/../utils/common.sh"

log_info "Elasticsearch 설치 시작..."

# ==============================================
# Elasticsearch 설치
# ==============================================

if systemctl is-active --quiet elasticsearch; then
    log_info "Elasticsearch 이미 실행 중"
    SKIP_INSTALL=true
elif is_package_installed "elasticsearch"; then
    log_info "Elasticsearch 이미 설치됨"
    SKIP_INSTALL=true
else
    SKIP_INSTALL=false
fi

if [ "$SKIP_INSTALL" = false ]; then
    log_info "Elasticsearch 저장소 추가 중..."
    
    # GPG 키 추가
    rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch
    
    # 저장소 추가 (Elasticsearch 8.x)
    cat > /etc/yum.repos.d/elasticsearch.repo << 'EOF'
[elasticsearch]
name=Elasticsearch repository for 8.x packages
baseurl=https://artifacts.elastic.co/packages/8.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
EOF
    
    log_info "Elasticsearch 설치 중..."
    dnf install -y elasticsearch
    
    log_success "Elasticsearch 설치 완료"
fi

# ==============================================
# 설정
# ==============================================

log_info "Elasticsearch 설정 중..."

# 기존 설정 백업
if [ -f /etc/elasticsearch/elasticsearch.yml ]; then
    backup_file /etc/elasticsearch/elasticsearch.yml
fi

# Elasticsearch 설정
cat > /etc/elasticsearch/elasticsearch.yml << EOF
# ==============================================
# 클러스터
# ==============================================
cluster.name: ${ES_CLUSTER_NAME}
node.name: ${ES_NODE_NAME}

# ==============================================
# 네트워크
# ==============================================
network.host: 0.0.0.0
http.port: ${ES_PORT}

# ==============================================
# 디스커버리 (단일 노드)
# ==============================================
discovery.type: single-node

# ==============================================
# 보안 (개발 환경)
# ==============================================
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false

# ==============================================
# 메모리
# ==============================================
bootstrap.memory_lock: true

# ==============================================
# 경로
# ==============================================
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
EOF

# JVM 힙 설정
cat > /etc/elasticsearch/jvm.options.d/heap.options << 'EOF'
# JVM 힙 크기 (시스템 메모리의 1/4 권장, 최대 2GB)
-Xms2g
-Xmx2g
EOF

# Systemd 서비스 설정 (메모리 락)
ensure_directory /etc/systemd/system/elasticsearch.service.d root:root 755

cat > /etc/systemd/system/elasticsearch.service.d/override.conf << 'EOF'
[Service]
LimitMEMLOCK=infinity
EOF

# Systemd 리로드
systemctl daemon-reload

# ==============================================
# 서비스 시작
# ==============================================

if ! systemctl is-enabled --quiet elasticsearch; then
    log_info "Elasticsearch 서비스 활성화 중..."
    systemctl enable elasticsearch
fi

if ! systemctl is-active --quiet elasticsearch; then
    log_info "Elasticsearch 시작 중... (최대 ${ES_START_TIMEOUT}초 대기)"
    systemctl start elasticsearch
    
    # Elasticsearch 시작 대기
    if wait_for_url "${ES_URL}" ${ES_START_TIMEOUT}; then
        log_success "Elasticsearch 실행 중"
    else
        log_error "Elasticsearch 시작 실패 또는 타임아웃"
        log_info "로그 확인: journalctl -u elasticsearch -n 50"
        exit 1
    fi
else
    log_info "Elasticsearch 이미 실행 중"
fi

# ==============================================
# 연결 테스트
# ==============================================

log_info "Elasticsearch 연결 테스트 중..."

if curl -s "${ES_URL}" > /dev/null; then
    log_success "Elasticsearch 연결 성공"
else
    log_error "Elasticsearch 연결 실패"
    exit 1
fi

# ==============================================
# 설치 정보 출력
# ==============================================

ES_VERSION=$(curl -s "${ES_URL}" | grep -o '"number" : "[^"]*"' | cut -d'"' -f4 || echo "Unknown")

log_success "======================================"
log_success "  Elasticsearch 설치 완료"
log_success "======================================"
log_info "버전: ${ES_VERSION}"
log_info "포트: ${ES_PORT}"
log_info "클러스터: ${ES_CLUSTER_NAME}"
log_info "상태: $(systemctl is-active elasticsearch)"
log_info ""
log_info "연결 테스트:"
log_info "  curl ${ES_URL}"
log_info ""
log_info "클러스터 상태:"
log_info "  curl ${ES_URL}/_cluster/health?pretty"
