#!/bin/bash
# Frontend 실행 스크립트
# Reflex 애플리케이션 로컬 실행

set -e

echo "=== Frontend 실행 ==="

# 1. 환경 변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ 환경 변수 로드 완료"
else
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하세요."
    exit 1
fi

# 2. Reflex 실행
echo "🚀 Reflex 실행 중..."
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Frontend 서버 시작                 ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "🌐 접속 URL:"
echo "   - Frontend: http://localhost:${REFLEX_FRONTEND_PORT:-3000}"
echo "   - Backend API: http://localhost:${REFLEX_BACKEND_PORT:-8000}"
echo ""
echo "📝 로그를 확인하세요..."
echo ""

reflex run
