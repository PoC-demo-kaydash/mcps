#!/usr/bin/env python3
"""
DB 스키마 초기화 스크립트
MariaDB 스키마, 인덱스, 트리거, 초기 데이터를 생성합니다.
"""

import sys
import os
from pathlib import Path

# shared 모듈 import를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.logging_config import setup_logging
from shared.database import DatabaseManager
from shared import CONFIG

logger = setup_logging("init_database")


def read_sql_file(file_path: Path) -> str:
    """SQL 파일 읽기"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def execute_sql_file(db: DatabaseManager, sql_content: str, description: str):
    """SQL 파일 실행"""
    logger.info(f"Executing: {description}")
    
    # SQL 문을 세미콜론으로 분리하여 실행
    statements = []
    current_statement = []
    in_delimiter = False
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # 주석 제거
        if line.startswith('--') or not line:
            continue
        
        # DELIMITER 처리
        if line.upper().startswith('DELIMITER'):
            in_delimiter = not in_delimiter
            continue
        
        current_statement.append(line)
        
        # 세미콜론으로 끝나면 statement 완료
        if not in_delimiter and line.endswith(';'):
            statement = ' '.join(current_statement)
            if statement.strip() and not statement.strip().startswith('--'):
                statements.append(statement)
            current_statement = []
    
    # 마지막 statement 추가
    if current_statement:
        statement = ' '.join(current_statement)
        if statement.strip():
            statements.append(statement)
    
    # 각 statement 실행
    success_count = 0
    error_count = 0
    
    for statement in statements:
        try:
            db.execute(statement)
            success_count += 1
        except Exception as e:
            error_count += 1
            logger.warning(f"Statement execution warning: {str(e)[:100]}")
    
    logger.info(f"✅ {description} completed: {success_count} statements executed, {error_count} warnings")


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("Starting Database Initialization")
    logger.info("=" * 60)
    
    # 데이터베이스 연결 설정
    db_config = {
        "host": CONFIG["database"]["host"],
        "port": CONFIG["database"]["port"],
        "user": CONFIG["database"]["user"],
        "password": CONFIG["database"]["password"],
        "database": "mysql",  # 초기 연결은 mysql DB로
        "charset": CONFIG["database"]["charset"],
        "pool_size": {"min": 1, "max": 3}
    }
    
    db = DatabaseManager(db_config)
    
    try:
        # SQL 파일 경로
        base_dir = Path(__file__).parent.parent
        data_dir = base_dir / "data" / "database"
        
        sql_files = [
            (data_dir / "schema.sql", "Schema (Tables)"),
            (data_dir / "indexes.sql", "Additional Indexes"),
            (data_dir / "triggers.sql", "Triggers"),
            (data_dir / "seed_data.sql", "Seed Data")
        ]
        
        # 각 SQL 파일 실행
        for sql_file, description in sql_files:
            if not sql_file.exists():
                logger.error(f"❌ File not found: {sql_file}")
                continue
            
            sql_content = read_sql_file(sql_file)
            execute_sql_file(db, sql_content, description)
        
        # 결과 확인
        logger.info("")
        logger.info("=" * 60)
        logger.info("Database Initialization Summary")
        logger.info("=" * 60)
        
        # mcps_db로 연결 변경
        db.close()
        db_config["database"] = "mcps_db"
        db = DatabaseManager(db_config)
        
        # 테이블 목록 조회
        tables = db.fetch_all("SHOW TABLES")
        logger.info(f"Total tables created: {len(tables)}")
        for table in tables:
            table_name = list(table.values())[0]
            count_result = db.fetch_one(f"SELECT COUNT(*) as cnt FROM {table_name}")
            count = count_result['cnt'] if count_result else 0
            logger.info(f"  - {table_name}: {count} rows")
        
        logger.info("")
        logger.info("✅ Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
