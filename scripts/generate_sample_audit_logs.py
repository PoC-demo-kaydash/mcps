#!/usr/bin/env python3
"""
샘플 감사 로그 생성 스크립트
30일간의 사용자 활동을 시뮬레이션하여 감사 로그를 생성합니다
"""

import sys
from pathlib import Path
import random
from datetime import datetime, timedelta

# shared 모듈 import를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.logging_config import setup_logging
from shared.database import DatabaseManager
from shared.utils import generate_id
from shared import CONFIG

logger = setup_logging("generate_audit_logs")

# 액션 타입별 가중치 (빈도 반영)
ACTIONS = {
    "search_documents": 30,      # 가장 빈번
    "get_document": 25,
    "list_documents": 20,
    "authenticate": 15,
    "create_document": 5,
    "update_document": 3,
    "get_document_versions": 1,
    "request_access": 0.5,
    "get_audit_logs": 0.3,
    "delete_document": 0.2
}

# 리소스 타입별 ID 샘플
RESOURCE_SAMPLES = {
    "document": ["DOC-001", "DOC-002", "DOC-003", "DOC-004", "DOC-005"],
    "tool": ["search_documents", "get_document", "create_document"],
    "user": ["U001", "U002", "U003", "U004", "U005", "U006"],
    "audit_log": ["AUD-001", "AUD-002"]
}

# 검색어 샘플
SEARCH_QUERIES = [
    "개발 가이드",
    "보안 정책",
    "API 문서",
    "사업 계획",
    "회의록",
    "프로젝트 계획",
    "기술 스펙",
    "사용자 매뉴얼",
    "운영 절차",
    "품질 관리"
]

# 결과 타입 (성공 95%, 실패 5%)
RESULTS = ["success"] * 95 + ["failure"] * 5


def generate_action_details(action: str) -> dict:
    """액션 타입에 맞는 상세 정보 생성"""
    details = {}
    
    if action == "search_documents":
        details["query"] = random.choice(SEARCH_QUERIES)
        details["results_count"] = random.randint(0, 50)
    
    elif action in ["get_document", "update_document", "delete_document"]:
        details["document_id"] = random.choice(RESOURCE_SAMPLES["document"])
    
    elif action == "create_document":
        details["title"] = f"새 문서 {random.randint(1, 1000)}"
        details["classification"] = random.choice(["public", "team", "confidential"])
    
    elif action == "get_document_versions":
        details["document_id"] = random.choice(RESOURCE_SAMPLES["document"])
        details["version_count"] = random.randint(1, 10)
    
    elif action == "request_access":
        details["resource_type"] = "document"
        details["resource_id"] = random.choice(RESOURCE_SAMPLES["document"])
    
    elif action == "get_audit_logs":
        details["date_range"] = "last_30_days"
        details["log_count"] = random.randint(10, 500)
    
    return details


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("Starting Sample Audit Log Generation")
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
        # 사용자 목록
        users = ["U000", "U001", "U002", "U003", "U004", "U005", "U006"]
        
        # 30일간 로그 생성
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 가중치를 기반으로 액션 목록 생성
        weighted_actions = []
        for action, weight in ACTIONS.items():
            count = int(weight * 10)
            weighted_actions.extend([action] * count)
        
        created_count = 0
        
        logger.info(f"Generating logs from {start_date.date()} to {end_date.date()}...")
        logger.info("")
        
        # 날짜별 로그 생성
        current_date = start_date
        while current_date <= end_date:
            # 하루에 10~50개 로그 생성 (주말은 적게)
            is_weekend = current_date.weekday() >= 5
            daily_logs = random.randint(5, 20) if is_weekend else random.randint(20, 50)
            
            for _ in range(daily_logs):
                # 랜덤 시간 (업무 시간 9시~18시에 집중)
                hour = random.choices(
                    range(24),
                    weights=[1]*9 + [10]*9 + [5]*6,  # 9-18시 가중치
                    k=1
                )[0]
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                timestamp = current_date.replace(hour=hour, minute=minute, second=second)
                
                # 랜덤 액션 및 사용자
                action = random.choice(weighted_actions)
                user_id = random.choice(users)
                result = random.choice(RESULTS)
                
                # 리소스 타입 결정
                if action in ["get_document", "update_document", "delete_document", "create_document"]:
                    resource_type = "document"
                    resource_id = random.choice(RESOURCE_SAMPLES["document"])
                elif action == "search_documents":
                    resource_type = "tool"
                    resource_id = "search_documents"
                elif action == "authenticate":
                    resource_type = "user"
                    resource_id = user_id
                else:
                    resource_type = "tool"
                    resource_id = action
                
                # 상세 정보 생성
                details = generate_action_details(action)
                details_str = str(details) if details else None
                
                # IP 주소 생성
                ip_address = f"192.168.{random.randint(1, 10)}.{random.randint(1, 254)}"
                
                # 로그 삽입
                log_id = generate_id("AUD", 12)
                
                db.execute(
                    """
                    INSERT INTO audit_logs (
                        id, user_id, action, resource_type, resource_id,
                        result, ip_address, details, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        log_id, user_id, action, resource_type, resource_id,
                        result, ip_address, details_str, timestamp
                    )
                )
                
                created_count += 1
            
            # 날짜별 진행 상황 출력
            if current_date.day % 5 == 0:
                logger.info(f"  {current_date.date()}: {created_count} logs created so far...")
            
            current_date += timedelta(days=1)
        
        # 결과 확인
        result = db.fetch_one("SELECT COUNT(*) AS total FROM audit_logs")
        total = result["total"] if result else 0
        
        # 통계 조회
        stats = db.fetch_all(
            """
            SELECT action, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= %s
            GROUP BY action
            ORDER BY count DESC
            """,
            (start_date,)
        )
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Sample Audit Log Generation Summary")
        logger.info("=" * 60)
        logger.info(f"Created logs: {created_count}")
        logger.info(f"Date range: {start_date.date()} ~ {end_date.date()}")
        logger.info(f"Total audit logs in database: {total}")
        logger.info("")
        logger.info("Top actions:")
        for stat in stats[:5]:
            logger.info(f"  - {stat['action']}: {stat['count']}")
        logger.info("")
        logger.info("✅ Sample audit log generation completed!")
        
    except Exception as e:
        logger.error(f"❌ Audit log generation failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
