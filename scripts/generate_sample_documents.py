#!/usr/bin/env python3
"""
샘플 문서 생성 스크립트
다양한 등급의 샘플 문서를 생성합니다 (public 10개, team 20개, confidential 10개)
"""

import sys
from pathlib import Path
import random

# shared 모듈 import를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.logging_config import setup_logging
from shared.database import DatabaseManager
from shared.utils import generate_id
from shared import CONFIG

logger = setup_logging("generate_samples")

# 샘플 제목
SAMPLE_TITLES = {
    "public": [
        "회사 비전 2030",
        "직원 행동 강령",
        "보안 정책 안내",
        "출퇴근 관리 규정",
        "사무실 이용 안내",
        "재택근무 가이드",
        "휴가 사용 안내",
        "복지 포인트 사용법",
        "사내 동호회 소개",
        "신입사원 온보딩 가이드"
    ],
    "team_dev": [
        "개발 환경 설정",
        "Git 워크플로우",
        "코드 리뷰 가이드",
        "배포 프로세스",
        "API 설계 원칙",
        "데이터베이스 스키마",
        "테스트 전략",
        "성능 최적화 팁",
        "보안 체크리스트",
        "장애 대응 매뉴얼"
    ],
    "team_hr": [
        "채용 프로세스",
        "면접 가이드",
        "인사 평가 기준",
        "교육 계획",
        "복리후생 정책",
        "급여 체계",
        "승진 기준",
        "퇴직 절차",
        "근태 관리",
        "조직 문화"
    ],
    "confidential": [
        "2026년 사업 계획",
        "M&A 검토 보고서",
        "임원 회의록",
        "재무 실적 분석",
        "신제품 로드맵",
        "경쟁사 분석",
        "투자 유치 계획",
        "조직 개편안",
        "인력 계획",
        "예산 집행 현황"
    ]
}

SAMPLE_CONTENT = """
# {title}

## 개요
이 문서는 {title}에 관한 내용을 다룹니다.

## 상세 내용

### 1. 배경
{title}의 필요성과 배경을 설명합니다.

### 2. 목표
- 목표 1: 명확한 기준 수립
- 목표 2: 효율적인 프로세스 구축
- 목표 3: 지속적인 개선

### 3. 실행 계획
1. 1단계: 현황 분석
2. 2단계: 개선 방안 도출
3. 3단계: 실행 및 모니터링

## 결론
{title}를 통해 조직의 발전을 도모합니다.

---
작성일: 2026-01-08
"""


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("Starting Sample Document Generation")
    logger.info("=" * 60)
    
    # DB 연결 설정
    db_config = {
        "host": CONFIG["database"]["host"],
        "port": CONFIG["database"]["port"],
        "user": CONFIG["database"]["user"],
        "password": CONFIG["database"]["password"],
        "database": CONFIG["database"]["database"],
        "charset": CONFIG["database"]["charset"],
        "pool_size": {"min": 1, "max": 3}
    }
    
    db = DatabaseManager(db_config)
    
    try:
        users = {
            "admin": "U000",
            "junior": "U001",
            "staff_dev": "U002",
            "manager_dev": "U003",
            "executive": "U004",
            "staff_hr": "U005",
            "staff_finance": "U006"
        }
        
        created_count = 0
        
        # Public 문서 (10개)
        logger.info("Creating public documents...")
        for title in SAMPLE_TITLES["public"]:
            doc_id = generate_id("DOC", 8)
            content = SAMPLE_CONTENT.format(title=title)
            
            db.execute(
                """
                INSERT INTO documents (id, title, content, classification, category, author_id, team)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (doc_id, title, content, "public", "general", users["admin"], None)
            )
            
            created_count += 1
            logger.info(f"  Created: {doc_id} - {title}")
        
        # Team 문서 - dev_team (10개)
        logger.info("Creating team documents (dev_team)...")
        for title in SAMPLE_TITLES["team_dev"]:
            doc_id = generate_id("DOC", 8)
            content = SAMPLE_CONTENT.format(title=title)
            
            db.execute(
                """
                INSERT INTO documents (id, title, content, classification, category, author_id, team)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (doc_id, title, content, "team", "development", users["staff_dev"], "dev_team")
            )
            
            created_count += 1
            logger.info(f"  Created: {doc_id} - {title}")
        
        # Team 문서 - hr_team (10개)
        logger.info("Creating team documents (hr_team)...")
        for title in SAMPLE_TITLES["team_hr"]:
            doc_id = generate_id("DOC", 8)
            content = SAMPLE_CONTENT.format(title=title)
            
            db.execute(
                """
                INSERT INTO documents (id, title, content, classification, category, author_id, team)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (doc_id, title, content, "team", "hr", users["staff_hr"], "hr_team")
            )
            
            created_count += 1
            logger.info(f"  Created: {doc_id} - {title}")
        
        # Confidential 문서 (10개)
        logger.info("Creating confidential documents...")
        for title in SAMPLE_TITLES["confidential"]:
            doc_id = generate_id("DOC", 8)
            content = SAMPLE_CONTENT.format(title=title)
            
            db.execute(
                """
                INSERT INTO documents (id, title, content, classification, category, author_id, team)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (doc_id, title, content, "confidential", "management", users["executive"], None)
            )
            
            created_count += 1
            logger.info(f"  Created: {doc_id} - {title}")
        
        # 결과 확인
        result = db.fetch_one("SELECT COUNT(*) AS total FROM documents")
        total = result["total"] if result else 0
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Sample Generation Summary")
        logger.info("=" * 60)
        logger.info(f"Created documents: {created_count}")
        logger.info(f"  - Public: 10")
        logger.info(f"  - Team (dev_team): 10")
        logger.info(f"  - Team (hr_team): 10")
        logger.info(f"  - Confidential: 10")
        logger.info(f"Total documents in database: {total}")
        logger.info("")
        logger.info("✅ Sample document generation completed!")
        
    except Exception as e:
        logger.error(f"❌ Sample generation failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
