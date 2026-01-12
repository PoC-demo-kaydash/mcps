# MCP Ecosystem 설계 문서

본 디렉토리는 MCP 에코시스템의 전체 설계 문서를 포함합니다.

## 📚 문서 구조

### 00. 시스템 아키텍처
- **[00_System_Architecture.md](00_System_Architecture.md)** - 전체 시스템 아키텍처 및 기술 스택

### 01. 공유 모듈
- **01_Shared_Module.md** - shared/ 폴더 설계 (database, elasticsearch, permissions 등)

### 02. MCP Tools
- **02_MCP_Tools.md** - mcp-tools/ 폴더 설계 (Tool 구현체)

### 03. MCP Servers
- **03_MCP_Servers.md** - mcp-servers/ 폴더 설계 (Server 구현체)

### 04. MCP Host
- **04_MCP_Host.md** - mcp-host/ 폴더 설계 (핵심 백엔드)

### 05. API Gateway
- **05_API_Gateway.md** - api-gateway/ 폴더 설계 (API Gateway)

### 06. Frontend
- **06_Frontend.md** - frontend/ 폴더 설계 (Reflex 프론트엔드)

### 07. Scripts
- **07_Scripts.md** - scripts/ 폴더 설계 (운영 스크립트)

### 08. Data
- **08_Data.md** - data/ 폴더 설계 (DB, ES, 문서, 로그)

### 09. Configuration
- **09_Configuration.md** - config/ 폴더 설계 (전역 설정)

### 10. Tests
- **10_Tests.md** - tests/ 폴더 설계 (unit, integration, e2e)

## 📖 문서 읽는 순서

### 초보자 (처음 시작하는 경우)
1. **00_System_Architecture.md** - 전체 구조 파악
2. **01_Shared_Module.md** - 공유 모듈 이해
3. **04_MCP_Host.md** - 핵심 로직 이해
4. **05_API_Gateway.md** - API 구조 이해
5. **06_Frontend.md** - UI 구조 이해

### 개발자 (구현 시작하는 경우)
1. **00_System_Architecture.md** - 아키텍처 확인
2. 구현할 모듈의 설계서 읽기
3. **01_Shared_Module.md** - 공유 모듈 활용법
4. **10_Tests.md** - 테스트 작성법

### 운영자 (시스템 운영하는 경우)
1. **07_Scripts.md** - 운영 스크립트
2. **08_Data.md** - 데이터 백업/복구
3. **00_System_Architecture.md** - 아키텍처 이해

## 🔗 관련 문서

### 매뉴얼
- [manual/installation_guide.md](../manual/installation_guide.md) - 설치 가이드
- [manual/deploy_guide.md](../manual/deploy_guide.md) - 배포 가이드
- [manual/operation_guide.md](../manual/operation_guide.md) - 운영 가이드

### 개별 폴더 설계서
- [shared/SR.md](../shared/SR.md) - shared 모듈 상세 설계
- [mcp-servers/SR.md](../mcp-servers/SR.md) - MCP Servers 상세 설계
- [mcp-host/SR.md](../mcp-host/SR.md) - MCP Host 상세 설계
- [api-gateway/SR.md](../api-gateway/SR.md) - API Gateway 상세 설계
- [frontend/SR.md](../frontend/SR.md) - Frontend 상세 설계
- [mcp-tools/SR.md](../mcp-tools/SR.md) - MCP Tools 상세 설계
- [scripts/SR.md](../scripts/SR.md) - Scripts 상세 설계

## 📝 문서 작성 규칙

### 파일명
- `<번호>_<모듈명>.md` 형식
- 예: `01_Shared_Module.md`
- 숫자는 2자리 (00-99)

### 문서 구조
```markdown
# 모듈명

## 1. 개요
- 목적
- 주요 기능
- 제약 사항

## 2. 아키텍처
- 구조도
- 디렉토리 구조
- 의존성

## 3. 구현 상세
- 클래스 설계
- 함수 설계
- 인터페이스

## 4. 사용 예제
- 코드 예제
- API 호출 예제

## 5. 테스트
- 단위 테스트
- 통합 테스트

## 6. 배포
- 배포 방법
- 설정 관리

## 7. 운영
- 모니터링
- 장애 대응
```

### 마크다운 규칙
- 헤더는 `#`, `##`, `###` 사용
- 코드 블록은 ` ```python ` 사용
- 링크는 상대 경로 사용
- 이미지는 `docs/images/` 폴더에 저장

## 🔄 문서 업데이트

### 변경 이력
모든 문서는 상단에 변경 이력을 기록합니다.

```markdown
**변경 이력**
- 2026-01-12: 초안 작성
- 2026-01-15: 섹션 3 추가
- 2026-01-20: 예제 코드 업데이트
```

### 리뷰 프로세스
1. 문서 작성/수정
2. PR 생성
3. 리뷰어 검토
4. 승인 후 병합

## 📞 문의

문서 관련 문의는 아래로 연락주세요:
- Email: admin@mcps.local
- Slack: #mcps-docs

---

**Last Updated**: 2026-01-12  
**Version**: 1.0.0
