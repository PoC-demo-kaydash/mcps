# Frontend Dockerfile
# Reflex 애플리케이션 Docker 이미지

FROM python:3.11-slim

# Node.js 설치 (Reflex 필요)
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리
WORKDIR /app

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# Reflex 초기화
RUN reflex init

# 포트 노출
EXPOSE 3000 8000

# 실행
CMD ["reflex", "run", "--env", "prod", "--loglevel", "info"]
