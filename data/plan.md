# Data 폴더 구현 계획서

> 작성일: 2026-01-08  
> 기준 문서: [SR.md](SR.md)  
> 상태: 🔴 미완료 | 🟡 진행중 | 🟢 완료

---

## 1. 개요

SR.md 설계서와 현재 구현 상태 비교 결과, 아래 항목들의 추가 구현이 필요합니다.

| 카테고리 | 설계서 | 현재 구현 | 일치율 |
|---------|--------|----------|--------|
| 테이블 | 9개 | 9개 (일부 다름) | ~78% |
| 뷰 | 3개 | 0개 | 0% |
| 저장 프로시저 | 6개 | 0개 | 0% |
| 운영 스크립트 | 4개 | 0개 | 0% |

### 현재 구현 상태

**구현 완료:**
- `database/schema.sql` - 9개 테이블 (users, documents, document_versions, permissions, tools, servers, audit_logs, access_requests, system_settings)
- `database/indexes.sql` - 복합 인덱스
- `database/triggers.sql` - 문서 버전 자동 생성 트리거
- `database/seed_data.sql` - 초기 데이터 (7명 사용자, 샘플 문서)
- `elasticsearch/mappings/documents.json` - nori 분석기 포함
- `elasticsearch/mappings/audit_logs.json` - 감사 로그 매핑

**누락 항목:**
- teams, sessions, migration_history 테이블
- 통계 뷰 3개
- 저장 프로시저 6개
- 운영 스크립트 (backup, cron, ES 초기화)

---

## 2. To-Do List

### 2.1 🔴 High Priority (필수)

#### 2.1.1 신규 테이블 생성

- [ ] **teams 테이블** 생성 (`database/schema.sql`)
  - [ ] id, name, description, parent_team_id, manager_id
  - [ ] created_at, updated_at, deleted_at
  - [ ] 외래키: manager_id → users.id

- [ ] **sessions 테이블** 생성 (`database/schema.sql`)
  - [ ] id, user_id, token, ip_address, user_agent
  - [ ] expires_at, created_at, last_accessed_at
  - [ ] 외래키: user_id → users.id

- [ ] **migration_history 테이블** 생성 (`database/schema.sql`)
  - [ ] id, version, description, executed_at, checksum

#### 2.1.2 기존 테이블 컬럼 추가

- [ ] **users 테이블** 컬럼 추가
  - [ ] `deleted_at` DATETIME (Soft Delete)
  - [ ] `password_hash` VARCHAR(255)
  - [ ] `last_login_at` DATETIME
  - [ ] `team_id` VARCHAR(50) (외래키 → teams.id)

- [ ] **documents 테이블** 컬럼 추가
  - [ ] `status` ENUM('draft', 'published', 'archived') DEFAULT 'draft'
  - [ ] `deleted_at` DATETIME (Soft Delete)
  - [ ] `view_count` INT DEFAULT 0
  - [ ] `tags` JSON

- [ ] **permissions 테이블** 컬럼 추가
  - [ ] `status` ENUM('active', 'revoked') DEFAULT 'active'

- [ ] **access_requests 테이블** 수정
  - [ ] `status` ENUM에 'cancelled' 추가

#### 2.1.3 저장 프로시저 생성

- [ ] `database/procedures.sql` 파일 생성
  - [ ] `sp_cleanup_expired_sessions()` - 만료된 세션 정리
  - [ ] `sp_archive_old_audit_logs()` - 오래된 감사 로그 아카이브
  - [ ] `sp_cleanup_old_document_versions()` - 오래된 문서 버전 정리
  - [ ] `sp_purge_deleted_documents()` - 삭제된 문서 영구 제거
  - [ ] `sp_get_system_stats()` - 시스템 통계 조회
  - [ ] `sp_get_user_activity_stats()` - 사용자 활동 통계 조회

---

### 2.2 🟡 Medium Priority (권장)

#### 2.2.1 뷰 생성

- [ ] `database/views.sql` 파일 생성
  - [ ] `v_user_document_stats` - 사용자별 문서 통계
  - [ ] `v_document_version_stats` - 문서별 버전 통계
  - [ ] `v_category_stats` - 카테고리별 문서 통계

#### 2.2.2 인덱스 추가

- [ ] `database/indexes.sql` 보완
  - [ ] teams 테이블 인덱스
  - [ ] sessions 테이블 인덱스 (token, expires_at)
  - [ ] documents.status 인덱스
  - [ ] documents.deleted_at 인덱스

#### 2.2.3 초기 데이터 보완

- [ ] `database/seed_data.sql` 보완
  - [ ] 샘플 teams 데이터 추가
  - [ ] users.team_id 업데이트

---

### 2.3 🟢 Low Priority (선택)

#### 2.3.1 운영 스크립트

- [ ] `database/backup/` 폴더 생성
  - [ ] `backup_database.sh` - DB 백업 스크립트

- [ ] `database/cron/` 폴더 생성
  - [ ] `daily_cleanup.sh` - 일일 정리 작업 스크립트

- [ ] `database/migrations/` 폴더 생성
  - [ ] `001_initial_schema.sql`
  - [ ] `002_add_teams_sessions.sql`
  - [ ] `README.md` - 마이그레이션 가이드

#### 2.3.2 Elasticsearch

- [ ] `elasticsearch/create_index.py` 생성
  - [ ] documents 인덱스 생성 로직
  - [ ] audit_logs 인덱스 생성 로직
  - [ ] 기존 매핑 파일 활용

- [ ] `elasticsearch/mappings/documents.json` 수정 (선택)
  - [ ] english_analyzer 추가
  - [ ] department 필드 추가
  - [ ] status 필드 추가

---

## 3. 파일 변경 계획

### 3.1 수정 대상 파일

| 파일 | 변경 내용 |
|------|----------|
| `database/schema.sql` | teams, sessions, migration_history 테이블 추가, 기존 테이블 컬럼 추가 |
| `database/indexes.sql` | 신규 테이블 인덱스 추가 |
| `database/seed_data.sql` | teams 샘플 데이터, users.team_id 업데이트 |

### 3.2 신규 생성 파일

| 파일 | 설명 |
|------|------|
| `database/views.sql` | 통계 뷰 3개 |
| `database/procedures.sql` | 저장 프로시저 6개 |
| `database/backup/backup_database.sh` | DB 백업 스크립트 |
| `database/cron/daily_cleanup.sh` | 일일 정리 스크립트 |
| `database/migrations/README.md` | 마이그레이션 가이드 |
| `elasticsearch/create_index.py` | ES 인덱스 생성 스크립트 |

---

## 4. 작업 순서

```
1. schema.sql 수정 (테이블 추가/컬럼 추가)
   ↓
2. indexes.sql 수정 (신규 인덱스)
   ↓
3. views.sql 생성 (통계 뷰)
   ↓
4. procedures.sql 생성 (저장 프로시저)
   ↓
5. seed_data.sql 수정 (초기 데이터)
   ↓
6. 운영 스크립트 생성 (backup, cron)
   ↓
7. elasticsearch/create_index.py 생성
```

---

## 5. 진행 상태

| 단계 | 항목 | 상태 | 완료일 |
|-----|------|------|--------|
| 1 | schema.sql 수정 | � 완료 | 2026-01-08 |
| 2 | indexes.sql 수정 | 🟢 완료 | 2026-01-08 |
| 3 | views.sql 생성 | 🟢 완료 | 2026-01-08 |
| 4 | procedures.sql 생성 | 🟢 완료 | 2026-01-08 |
| 5 | seed_data.sql 수정 | 🟢 완료 | 2026-01-08 |
| 6 | 운영 스크립트 생성 | 🟢 완료 | 2026-01-08 |
| 7 | ES create_index.py | 🟢 완료 | 2026-01-08 |

---

## 6. 참고 사항

- 현재 구현에 추가된 `tools`, `servers`, `system_settings` 테이블은 MCP 시스템에 필요하므로 유지
- Elasticsearch shards/replicas는 개발 환경 설정(1/1) 유지, 프로덕션 배포 시 조정
- Soft Delete 적용 시 관련 쿼리에 `WHERE deleted_at IS NULL` 조건 추가 필요
- teams 테이블 생성 후 users 테이블에 team_id 외래키 추가 필요 (순서 주의)
