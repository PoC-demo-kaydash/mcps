# mcp-servers 구조 수정 계획서

**작성일**: 2026-01-08  
**목적**: SR.md 설계서 준수를 위한 폴더 구조 수정

---

## 1. 현재 문제점

### 1.1 구조 불일치

| 항목 | SR.md 설계 | 현재 구현 |
|------|-----------|----------|
| 서버 위치 | 최상위 독립 폴더 | `core/` 하위에 중첩 |
| 폴더명 | `core/`, `search/`, `analytics/` | `core/auth_server/` 등 |
| `core` 의미 | "Core MCP Server" (서버명) | 단순 컨테이너 폴더 |

### 1.2 네이밍 혼동

```
SR.md의 core/ = 서버 (문서 CRUD 담당)
현재의 core/ = 폴더 (5개 서버를 담는 컨테이너)
```

---

## 2. 수정 방안

### 방안 A: 폴더 구조만 수정 (권장)
- 5-서버 구조 유지
- `core/` 폴더 제거, 서버들을 최상위로 이동

### 방안 B: SR.md 3-서버로 회귀
- auth + document → `core/`
- search → `search/`
- audit + version + statistics → `analytics/`
- 코드 대폭 수정 필요

**선택: 방안 A** (최소 변경, 기존 코드 유지)

---

## 3. 수정 작업

### 3.1 폴더 이동

```bash
# 현재 구조
mcp-servers/
├── core/
│   ├── auth_server/
│   ├── document_server/
│   ├── search_server/
│   ├── version_server/
│   └── audit_server/
└── scripts/

# 수정 후 구조
mcp-servers/
├── auth_server/
├── document_server/
├── search_server/
├── version_server/
├── audit_server/
└── scripts/
```

### 3.2 실행 명령

```bash
cd /app/poc/mcps/mcp-servers

# 1. 서버 폴더들을 최상위로 이동
mv core/auth_server .
mv core/document_server .
mv core/search_server .
mv core/version_server .
mv core/audit_server .

# 2. 빈 core 폴더 삭제
rmdir core

# 3. 스크립트 경로 수정 (start_servers.sh)
```

### 3.3 스크립트 수정

| 파일 | 수정 내용 |
|------|----------|
| `scripts/start_servers.sh` | `CORE_DIR="${PROJECT_ROOT}/core"` → `SERVERS_DIR="${PROJECT_ROOT}"` |
| `scripts/stop_servers.sh` | 변경 없음 (PID 기반) |
| `scripts/status.sh` | 변경 없음 (PID 기반) |
| `scripts/integration_test.py` | 변경 없음 (import 경로 동일) |

### 3.4 plan.md 업데이트

- 섹션 5 "디렉토리 구조" 수정
- `core/` 하위 표기 제거

---

## 4. 수정 후 최종 구조

```
/app/poc/mcps/mcp-servers/
├── SR.md                    # 원본 설계서
├── plan.md                  # 구현 계획서 (수정)
├── fix_plan.md              # 본 문서
│
├── auth_server/             # Auth Server (4 Tools)
│   ├── main.py
│   └── requirements.txt
│
├── document_server/         # Document Server (5 Tools)
│   ├── main.py
│   └── requirements.txt
│
├── search_server/           # Search Server (2 Tools)
│   ├── main.py
│   └── requirements.txt
│
├── version_server/          # Version Server (3 Tools)
│   ├── main.py
│   └── requirements.txt
│
├── audit_server/            # Audit Server (3 Tools)
│   ├── main.py
│   └── requirements.txt
│
└── scripts/                 # 운영 스크립트
    ├── start_servers.sh
    ├── stop_servers.sh
    ├── status.sh
    └── integration_test.py
```

---

## 5. 상세 수정 내역

### 5.1 scripts/start_servers.sh 수정

**수정 전:**
```bash
CORE_DIR="${PROJECT_ROOT}/core"
# ...
SERVER_DIR="${CORE_DIR}/${SERVER_NAME}"
```

**수정 후:**
```bash
SERVERS_DIR="${PROJECT_ROOT}"
# ...
SERVER_DIR="${SERVERS_DIR}/${SERVER_NAME}"
```

### 5.2 plan.md 수정

**수정 전 (섹션 5):**
```
├── core/                           # 핵심 Servers
│   ├── auth_server/
│   │   ├── main.py
│   │   └── requirements.txt
│   └── ...
```

**수정 후:**
```
├── auth_server/                    # Auth Server
│   ├── main.py
│   └── requirements.txt
├── document_server/                # Document Server
│   ├── main.py
│   └── requirements.txt
└── ...
```

---

## 6. 체크리스트

- [ ] 5개 서버 폴더 이동 (`core/` → 최상위)
- [ ] `core/` 폴더 삭제
- [ ] `scripts/start_servers.sh` 경로 수정 (`CORE_DIR` → `SERVERS_DIR`)
- [ ] `plan.md` 섹션 5 업데이트
- [ ] 서버 시작 테스트 (`./scripts/start_servers.sh`)
- [ ] 서버 상태 확인 (`./scripts/status.sh`)

---

## 7. 예상 소요 시간

| 작업 | 시간 |
|------|------|
| 폴더 이동 (5개) | 1분 |
| 스크립트 수정 | 2분 |
| plan.md 수정 | 2분 |
| 테스트 | 5분 |
| **총계** | **10분** |

---

## 8. 롤백 계획

문제 발생 시:
```bash
cd /app/poc/mcps/mcp-servers

# 1. 원상복구
mkdir core
mv auth_server core/
mv document_server core/
mv search_server core/
mv version_server core/
mv audit_server core/

# 2. 스크립트 원복
git checkout scripts/start_servers.sh
```

---

**Note**: 방안 B (3-서버로 회귀)가 필요한 경우, 별도 계획서 작성 필요.
