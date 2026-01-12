#!/bin/bash
# Frontend 배포 스크립트
# Reflex 애플리케이션 배포 자동화

set -e

echo "=== Frontend 배포 시작 ==="

# 1. 환경 변수 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하세요."
    cp .env.example .env
    echo "✅ .env 파일 생성 완료. 설정을 확인하세요."
fi

# 2. 의존성 설치
echo "📦 의존성 설치 중..."
pip install -r requirements.txt

# 3. Reflex 초기화
echo "🔧 Reflex 초기화 중..."
reflex init

# 4. 프로덕션 빌드
echo "🏗️  프로덕션 빌드 중..."
reflex export --frontend-only

# 5. Docker 이미지 빌드 (선택)
if command -v docker &> /dev/null; then
    echo "🐳 Docker 이미지 빌드 중..."
    docker build -t mcp-frontend:latest .
    echo "✅ Docker 이미지 빌드 완료"
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   ✅ Frontend 배포 완료              ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "📌 실행 방법:"
echo "   1. 로컬 실행: ./run.sh"
echo "   2. Docker 실행: docker-compose up -d"
echo ""
echo "🌐 접속 URL:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo ""
