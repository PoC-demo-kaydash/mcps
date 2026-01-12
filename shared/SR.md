# shared 공유모듈 설계서

***

# 01. MCP 에코시스템 - shared 공유모듈 설계서

**문서 버전**: 1.0.0  
**작성일**: 2026-01-08  
**대상 경로**: `/app/poc/mcps/shared/`  
**목적**: 모든 컴포넌트가 공유하는 핵심 모듈의 상세 설계

***

## 목차

1. [개요](#1-개요)
2. [database.py - 데이터베이스 연결 관리](#2-databasepy)
3. [queries.py - SQL 쿼리 모음](#3-queriespy)
4. [elasticsearch.py - Elasticsearch 클라이언트](#4-elasticsearchpy)
5. [permissions.py - 권한 시스템](#5-permissionspy)
6. [logging_config.py - 로깅 설정](#6-logging_configpy)
7. [mcp_protocol.py - MCP 프로토콜](#7-mcp_protocolpy)
8. [utils.py - 유틸리티 함수](#8-utilspy)
9. [cache.py - 캐싱 시스템](#9-cachepy)
10. [테스트 전략](#10-테스트-전략)

***

## 1. 개요

### 1.1 목적

**shared 모듈**은 MCP 에코시스템의 모든 컴포넌트(MCP Host, MCP Servers, API Gateway, Frontend)가 공통으로 사용하는 핵심 기능을 제공합니다.

### 1.2 폴더 구조

```
/app/poc/mcps/shared/
├── __init__.py
├── database.py           # MariaDB 연결 관리
├── queries.py            # SQL 쿼리 모음
├── elasticsearch.py      # Elasticsearch 클라이언트
├── permissions.py        # 권한 시스템 (RBAC)
├── logging_config.py     # 로깅 설정
├── mcp_protocol.py       # MCP 프로토콜 구현
├── utils.py              # 유틸리티 함수
├── cache.py              # 캐싱 시스템
└── requirements.txt      # 의존성
```

### 1.3 의존성

```txt
# shared/requirements.txt

# Database
pymysql==1.1.0
DBUtils==3.0.3

# Search
elasticsearch==8.11.1

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0

# Configuration
python-dotenv==1.0.0

# Parsing
PyYAML==6.0.1
python-frontmatter==1.1.0

# Utilities
python-dateutil==2.8.2
```

### 1.4 임포트 패턴

```python
# 다른 컴포넌트에서 shared 모듈 사용

# 방법 1: 직접 임포트
from shared.database import DatabaseManager
from shared.queries import GET_USER_BY_ID
from shared.permissions import PermissionEngine

# 방법 2: __init__.py를 통한 임포트
from shared import db_manager, permission_engine

# 방법 3: 모든 쿼리 임포트
from shared import queries
result = db_manager.execute_query(queries.GET_USER_BY_ID, (user_id,))
```

### 1.5 공통 설정

```python
# shared/__init__.py
"""
MCP 에코시스템 공유 모듈
"""

import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 전역 설정
CONFIG = {
    "database": {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME", "mcps_db"),
        "user": os.getenv("DB_USER", "mcps_user"),
        "password": os.getenv("DB_PASSWORD", ""),
        "charset": "utf8mb4",
        "pool_size": {
            "min": int(os.getenv("DB_POOL_MIN", "5")),
            "max": int(os.getenv("DB_POOL_MAX", "20"))
        }
    },
    "elasticsearch": {
        "hosts": os.getenv("ES_HOSTS", "localhost:9200").split(","),
        "timeout": int(os.getenv("ES_TIMEOUT", "30"))
    },
    "logging": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": os.getenv("LOG_FORMAT", "json"),
        "file_max_bytes": int(os.getenv("LOG_MAX_BYTES", "10485760")),
        "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "10"))
    },
    "cache": {
        "max_size": int(os.getenv("CACHE_MAX_SIZE", "1000")),
        "default_ttl": int(os.getenv("CACHE_DEFAULT_TTL", "300"))
    }
}

# 싱글톤 인스턴스 (필요 시 초기화)
db_manager = None
es_manager = None
permission_engine = None

def initialize():
    """공유 모듈 초기화"""
    global db_manager, es_manager, permission_engine
    
    from .database import DatabaseManager
    from .elasticsearch import ElasticsearchManager
    from .permissions import PermissionEngine
    
    db_manager = DatabaseManager(CONFIG["database"])
    es_manager = ElasticsearchManager(CONFIG["elasticsearch"])
    permission_engine = PermissionEngine()
    
    return {
        "db": db_manager,
        "es": es_manager,
        "permissions": permission_engine
    }

def cleanup():
    """리소스 정리"""
    global db_manager, es_manager
    
    if db_manager:
        db_manager.close()
    
    if es_manager:
        es_manager.close()
```

***

## 2. database.py

### 2.1 개요

**역할**: MariaDB 연결 관리, Connection Pool, 트랜잭션, 쿼리 실행

**주요 기능**:
- Connection Pool 관리 (DBUtils)
- 쿼리 실행 (SELECT, INSERT, UPDATE, DELETE)
- 트랜잭션 관리 (BEGIN, COMMIT, ROLLBACK)
- 에러 처리 및 재시도
- 연결 헬스 체크

### 2.2 전체 코드

```python
# shared/database.py
"""
MariaDB 데이터베이스 연결 관리
ORM 미사용 - 순수 SQL 쿼리 실행
"""

import pymysql
from pymysql.cursors import DictCursor
from DBUtils.PooledDB import PooledDB
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """데이터베이스 에러 기본 클래스"""
    pass


class ConnectionError(DatabaseError):
    """연결 에러"""
    pass


class QueryError(DatabaseError):
    """쿼리 실행 에러"""
    pass


class TransactionError(DatabaseError):
    """트랜잭션 에러"""
    pass


class DatabaseManager:
    """
    MariaDB 연결 관리자
    
    특징:
    - Connection Pool 사용 (DBUtils.PooledDB)
    - 자동 재연결
    - 트랜잭션 지원
    - Parameterized Query (SQL Injection 방지)
    """
    
    def __init__(self, config: dict):
        """
        초기화
        
        Args:
            config: {
                "host": "localhost",
                "port": 3306,
                "database": "mcps_db",
                "user": "mcps_user",
                "password": "password",
                "charset": "utf8mb4",
                "pool_size": {
                    "min": 5,
                    "max": 20
                }
            }
        """
        self.config = config
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Connection Pool 초기화"""
        try:
            self.pool = PooledDB(
                creator=pymysql,
                maxconnections=self.config["pool_size"]["max"],
                mincached=self.config["pool_size"]["min"],
                maxcached=self.config["pool_size"]["max"],
                blocking=True,
                maxusage=None,
                setsession=[],
                ping=1,  # 연결 사용 전 ping
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                charset=self.config["charset"],
                cursorclass=DictCursor,
                autocommit=False
            )
            
            logger.info(
                f"Database connection pool initialized: "
                f"host={self.config['host']}, "
                f"db={self.config['database']}, "
                f"pool_size={self.config['pool_size']['min']}-{self.config['pool_size']['max']}"
            )
        
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise ConnectionError(f"Connection pool initialization failed: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        연결 획득 (Context Manager)
        
        사용 예:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
        
        Yields:
            pymysql.Connection
        """
        conn = None
        try:
            conn = self.pool.connection()
            yield conn
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Failed to get connection: {e}")
        finally:
            if conn:
                conn.close()
    
    def execute_query(
        self, 
        sql: str, 
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """
        SELECT 쿼리 실행
        
        Args:
            sql: SQL 쿼리 (Parameterized)
            params: 쿼리 파라미터 (tuple)
            fetch: 결과 fetch 여부
        
        Returns:
            List[Dict]: 쿼리 결과 (DictCursor)
        
        Example:
            result = db.execute_query(
                "SELECT * FROM users WHERE id = %s",
                (user_id,)
            )
        """
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    start_time = datetime.now()
                    
                    cursor.execute(sql, params or ())
                    
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    if fetch:
                        result = cursor.fetchall()
                        logger.debug(
                            f"Query executed: {sql[:100]}... "
                            f"[params={params}] "
                            f"[rows={len(result)}] "
                            f"[time={execution_time:.2f}ms]"
                        )
                        return result
                    else:
                        logger.debug(
                            f"Query executed: {sql[:100]}... "
                            f"[params={params}] "
                            f"[time={execution_time:.2f}ms]"
                        )
                        return []
                
            except pymysql.Error as e:
                logger.error(f"Query error: {sql[:100]}... - {e}")
                raise QueryError(f"Query execution failed: {e}")
    
    def execute_insert(
        self, 
        sql: str, 
        params: Optional[Tuple] = None
    ) -> int:
        """
        INSERT 쿼리 실행
        
        Args:
            sql: INSERT 쿼리
            params: 쿼리 파라미터
        
        Returns:
            int: 삽입된 행의 ID (LAST_INSERT_ID)
        
        Example:
            doc_id = db.execute_insert(
                "INSERT INTO documents (title, content) VALUES (%s, %s)",
                ("제목", "내용")
            )
        """
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params or ())
                    conn.commit()
                    
                    last_id = cursor.lastrowid
                    
                    logger.info(
                        f"Insert executed: {sql[:100]}... "
                        f"[affected={cursor.rowcount}] "
                        f"[last_id={last_id}]"
                    )
                    
                    return last_id
                
            except pymysql.Error as e:
                conn.rollback()
                logger.error(f"Insert error: {sql[:100]}... - {e}")
                raise QueryError(f"Insert failed: {e}")
    
    def execute_update(
        self, 
        sql: str, 
        params: Optional[Tuple] = None
    ) -> int:
        """
        UPDATE/DELETE 쿼리 실행
        
        Args:
            sql: UPDATE/DELETE 쿼리
            params: 쿼리 파라미터
        
        Returns:
            int: 영향받은 행 수
        
        Example:
            affected = db.execute_update(
                "UPDATE documents SET title = %s WHERE id = %s",
                ("새 제목", "DOC001")
            )
        """
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params or ())
                    conn.commit()
                    
                    affected = cursor.rowcount
                    
                    logger.info(
                        f"Update executed: {sql[:100]}... "
                        f"[affected={affected}]"
                    )
                    
                    return affected
                
            except pymysql.Error as e:
                conn.rollback()
                logger.error(f"Update error: {sql[:100]}... - {e}")
                raise QueryError(f"Update failed: {e}")
    
    def execute_many(
        self, 
        sql: str, 
        params_list: List[Tuple]
    ) -> int:
        """
        Batch INSERT/UPDATE 실행
        
        Args:
            sql: SQL 쿼리
            params_list: 파라미터 리스트
        
        Returns:
            int: 영향받은 총 행 수
        
        Example:
            affected = db.execute_many(
                "INSERT INTO audit_logs (user_id, action) VALUES (%s, %s)",
                [
                    ("U001", "login"),
                    ("U002", "search"),
                    ("U003", "logout")
                ]
            )
        """
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.executemany(sql, params_list)
                    conn.commit()
                    
                    affected = cursor.rowcount
                    
                    logger.info(
                        f"Batch executed: {sql[:100]}... "
                        f"[batches={len(params_list)}] "
                        f"[affected={affected}]"
                    )
                    
                    return affected
                
            except pymysql.Error as e:
                conn.rollback()
                logger.error(f"Batch error: {sql[:100]}... - {e}")
                raise QueryError(f"Batch execution failed: {e}")
    
    @contextmanager
    def transaction(self):
        """
        트랜잭션 Context Manager
        
        사용 예:
            with db.transaction() as tx:
                tx.execute("INSERT INTO users ...")
                tx.execute("INSERT INTO permissions ...")
                # 자동 COMMIT (에러 시 ROLLBACK)
        
        Yields:
            Transaction
        """
        conn = self.pool.connection()
        
        try:
            tx = Transaction(conn)
            yield tx
            conn.commit()
            logger.debug("Transaction committed")
        
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise TransactionError(f"Transaction failed: {e}")
        
        finally:
            conn.close()
    
    def execute_script(self, script: str):
        """
        SQL 스크립트 실행 (여러 쿼리)
        
        Args:
            script: SQL 스크립트 (';'로 구분된 여러 쿼리)
        
        Example:
            with open("schema.sql") as f:
                db.execute_script(f.read())
        """
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    # 여러 쿼리 분리
                    statements = [
                        stmt.strip() 
                        for stmt in script.split(';') 
                        if stmt.strip()
                    ]
                    
                    for stmt in statements:
                        cursor.execute(stmt)
                    
                    conn.commit()
                    
                    logger.info(f"Script executed: {len(statements)} statements")
                
            except pymysql.Error as e:
                conn.rollback()
                logger.error(f"Script error: {e}")
                raise QueryError(f"Script execution failed: {e}")
    
    def health_check(self) -> bool:
        """
        데이터베이스 연결 상태 확인
        
        Returns:
            bool: 연결 정상 여부
        """
        try:
            result = self.execute_query("SELECT 1 AS health")
            return len(result) > 0 and result[0]["health"] == 1
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_pool_status(self) -> Dict[str, Any]:
        """
        Connection Pool 상태 조회
        
        Returns:
            Dict: {
                "total": 전체 연결 수,
                "active": 사용 중인 연결,
                "idle": 유휴 연결
            }
        """
        # DBUtils는 상세 통계 제공하지 않음
        # MariaDB에서 직접 조회
        try:
            result = self.execute_query(
                "SHOW STATUS WHERE Variable_name IN ('Threads_connected', 'Threads_running')"
            )
            
            stats = {row["Variable_name"]: int(row["Value"]) for row in result}
            
            return {
                "total": stats.get("Threads_connected", 0),
                "active": stats.get("Threads_running", 0),
                "idle": stats.get("Threads_connected", 0) - stats.get("Threads_running", 0)
            }
        
        except Exception as e:
            logger.error(f"Failed to get pool status: {e}")
            return {"total": 0, "active": 0, "idle": 0}
    
    def close(self):
        """Connection Pool 종료"""
        if self.pool:
            self.pool.close()
            logger.info("Database connection pool closed")


class Transaction:
    """
    트랜잭션 헬퍼 클래스
    """
    
    def __init__(self, connection):
        self.conn = connection
        self.cursor = connection.cursor()
    
    def execute(self, sql: str, params: Optional[Tuple] = None) -> List[Dict]:
        """쿼리 실행 (트랜잭션 내)"""
        self.cursor.execute(sql, params or ())
        
        if sql.strip().upper().startswith("SELECT"):
            return self.cursor.fetchall()
        else:
            return []
    
    def execute_many(self, sql: str, params_list: List[Tuple]) -> int:
        """Batch 실행 (트랜잭션 내)"""
        self.cursor.executemany(sql, params_list)
        return self.cursor.rowcount


# 편의 함수
def dict_to_params(data: Dict[str, Any], columns: List[str]) -> Tuple:
    """
    딕셔너리를 SQL 파라미터 튜플로 변환
    
    Args:
        data: {"name": "홍길동", "age": 30}
        columns: ["name", "age"]
    
    Returns:
        ("홍길동", 30)
    """
    return tuple(data.get(col) for col in columns)


def build_insert_query(table: str, columns: List[str]) -> str:
    """
    INSERT 쿼리 생성
    
    Args:
        table: 테이블명
        columns: 컬럼 리스트
    
    Returns:
        "INSERT INTO table (col1, col2) VALUES (%s, %s)"
    """
    cols = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    return f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"


def build_update_query(table: str, columns: List[str], where: str) -> str:
    """
    UPDATE 쿼리 생성
    
    Args:
        table: 테이블명
        columns: 업데이트할 컬럼 리스트
        where: WHERE 절 (예: "id = %s")
    
    Returns:
        "UPDATE table SET col1 = %s, col2 = %s WHERE id = %s"
    """
    set_clause = ", ".join([f"{col} = %s" for col in columns])
    return f"UPDATE {table} SET {set_clause} WHERE {where}"
```

### 2.3 사용 예제

```python
# 예제 1: 기본 쿼리
from shared.database import DatabaseManager
from shared.queries import GET_USER_BY_ID

db = DatabaseManager(config)

# SELECT
user = db.execute_query(GET_USER_BY_ID, ("U001",))
print(user[0]["name"])  # "김신입"

# INSERT
doc_id = db.execute_insert(
    "INSERT INTO documents (id, title, content, author_id) VALUES (%s, %s, %s, %s)",
    ("DOC001", "제목", "내용", "U001")
)

# UPDATE
affected = db.execute_update(
    "UPDATE documents SET title = %s WHERE id = %s",
    ("새 제목", "DOC001")
)

# DELETE
affected = db.execute_update(
    "DELETE FROM documents WHERE id = %s",
    ("DOC001",)
)

# 예제 2: 트랜잭션
with db.transaction() as tx:
    # 문서 생성
    tx.execute(
        "INSERT INTO documents (id, title, content) VALUES (%s, %s, %s)",
        ("DOC002", "제목", "내용")
    )
    
    # 감사 로그 기록
    tx.execute(
        "INSERT INTO audit_logs (user_id, action, resource_id) VALUES (%s, %s, %s)",
        ("U001", "document_create", "DOC002")
    )
    
    # 자동 COMMIT (에러 시 ROLLBACK)

# 예제 3: Batch INSERT
logs = [
    ("U001", "login", "2026-01-08 10:00:00"),
    ("U002", "search", "2026-01-08 10:01:00"),
    ("U003", "logout", "2026-01-08 10:02:00")
]

affected = db.execute_many(
    "INSERT INTO audit_logs (user_id, action, created_at) VALUES (%s, %s, %s)",
    logs
)

# 예제 4: 헬스 체크
if db.health_check():
    print("✅ Database is healthy")
else:
    print("❌ Database is down")

# Pool 상태
status = db.get_pool_status()
print(f"Connections: {status['active']}/{status['total']}")
```

### 2.4 에러 처리

```python
from shared.database import DatabaseManager, QueryError, ConnectionError

db = DatabaseManager(config)

try:
    result = db.execute_query(
        "SELECT * FROM users WHERE id = %s",
        (user_id,)
    )
except ConnectionError as e:
    # 연결 실패 - 재시도 또는 알림
    logger.error(f"DB connection failed: {e}")
    # 재시도 로직...
    
except QueryError as e:
    # 쿼리 실패 - SQL 오류
    logger.error(f"Query failed: {e}")
    # 에러 응답 반환...
    
except Exception as e:
    # 기타 에러
    logger.error(f"Unexpected error: {e}")
```

***

## 3. queries.py

### 3.1 개요

**역할**: 모든 SQL 쿼리를 중앙 집중 관리

**장점**:
- SQL Injection 방지 (Parameterized Query)
- 쿼리 재사용
- 유지보수 용이
- 테스트 용이

### 3.2 전체 코드

```python
# shared/queries.py
"""
SQL 쿼리 모음
모든 쿼리는 Parameterized Query 형식 (Placeholder: %s)
"""

# ============================================
# 사용자 (users)
# ============================================

GET_USER_BY_ID = """
    SELECT 
        id, name, role, team, 
        created_at, updated_at
    FROM users
    WHERE id = %s
"""

GET_ALL_USERS = """
    SELECT 
        id, name, role, team, 
        created_at, updated_at
    FROM users
    ORDER BY created_at DESC
"""

GET_USERS_BY_ROLE = """
    SELECT 
        id, name, role, team, 
        created_at, updated_at
    FROM users
    WHERE role = %s
    ORDER BY created_at DESC
"""

GET_USERS_BY_TEAM = """
    SELECT 
        id, name, role, team, 
        created_at, updated_at
    FROM users
    WHERE team = %s
    ORDER BY created_at DESC
"""

CREATE_USER = """
    INSERT INTO users (id, name, role, team)
    VALUES (%s, %s, %s, %s)
"""

UPDATE_USER = """
    UPDATE users
    SET name = %s, role = %s, team = %s
    WHERE id = %s
"""

DELETE_USER = """
    DELETE FROM users
    WHERE id = %s
"""

COUNT_USERS = """
    SELECT COUNT(*) AS total
    FROM users
"""

COUNT_USERS_BY_ROLE = """
    SELECT role, COUNT(*) AS count
    FROM users
    GROUP BY role
"""

# ============================================
# 문서 (documents)
# ============================================

GET_DOCUMENT_BY_ID = """
    SELECT 
        d.id, d.title, d.content, d.classification, 
        d.category, d.author_id, d.team, d.file_path,
        d.version, d.created_at, d.updated_at,
        u.name AS author_name
    FROM documents d
    LEFT JOIN users u ON d.author_id = u.id
    WHERE d.id = %s
"""

GET_ALL_DOCUMENTS = """
    SELECT 
        d.id, d.title, d.classification, d.category,
        d.author_id, d.team, d.version,
        d.created_at, d.updated_at,
        u.name AS author_name
    FROM documents d
    LEFT JOIN users u ON d.author_id = u.id
    ORDER BY d.updated_at DESC
    LIMIT %s OFFSET %s
"""

GET_DOCUMENTS_BY_AUTHOR = """
    SELECT 
        d.id, d.title, d.classification, d.category,
        d.author_id, d.team, d.version,
        d.created_at, d.updated_at
    FROM documents d
    WHERE d.author_id = %s
    ORDER BY d.updated_at DESC
"""

GET_DOCUMENTS_BY_CLASSIFICATION = """
    SELECT 
        d.id, d.title, d.classification, d.category,
        d.author_id, d.team, d.version,
        d.created_at, d.updated_at,
        u.name AS author_name
    FROM documents d
    LEFT JOIN users u ON d.author_id = u.id
    WHERE d.classification = %s
    ORDER BY d.updated_at DESC
    LIMIT %s OFFSET %s
"""

GET_DOCUMENTS_BY_TEAM = """
    SELECT 
        d.id, d.title, d.classification, d.category,
        d.author_id, d.team, d.version,
        d.created_at, d.updated_at,
        u.name AS author_name
    FROM documents d
    LEFT JOIN users u ON d.author_id = u.id
    WHERE d.team = %s
    ORDER BY d.updated_at DESC
    LIMIT %s OFFSET %s
"""

GET_PUBLIC_DOCUMENTS = """
    SELECT 
        d.id, d.title, d.classification, d.category,
        d.author_id, d.version,
        d.created_at, d.updated_at,
        u.name AS author_name
    FROM documents d
    LEFT JOIN users u ON d.author_id = u.id
    WHERE d.classification = 'public'
    ORDER BY d.updated_at DESC
    LIMIT %s OFFSET %s
"""

CREATE_DOCUMENT = """
    INSERT INTO documents (
        id, title, content, classification, 
        category, author_id, team, file_path, version
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

UPDATE_DOCUMENT = """
    UPDATE documents
    SET 
        title = %s,
        content = %s,
        classification = %s,
        category = %s,
        file_path = %s,
        version = version + 1
    WHERE id = %s
"""

DELETE_DOCUMENT = """
    DELETE FROM documents
    WHERE id = %s
"""

COUNT_DOCUMENTS = """
    SELECT COUNT(*) AS total
    FROM documents
"""

COUNT_DOCUMENTS_BY_CLASSIFICATION = """
    SELECT classification, COUNT(*) AS count
    FROM documents
    GROUP BY classification
"""

SEARCH_DOCUMENTS_FULLTEXT = """
    SELECT 
        d.id, d.title, d.classification, d.category,
        d.author_id, d.team,
        MATCH(d.title, d.content) AGAINST(%s IN NATURAL LANGUAGE MODE) AS relevance
    FROM documents d
    WHERE MATCH(d.title, d.content) AGAINST(%s IN NATURAL LANGUAGE MODE)
    ORDER BY relevance DESC
    LIMIT %s
"""

# ============================================
# 권한 (permissions)
# ============================================

GET_PERMISSIONS_BY_USER = """
    SELECT 
        id, user_id, role, resource_type, 
        resource_id, actions, created_at
    FROM permissions
    WHERE user_id = %s
"""

GET_PERMISSIONS_BY_ROLE = """
    SELECT 
        id, user_id, role, resource_type, 
        resource_id, actions, created_at
    FROM permissions
    WHERE role = %s
"""

GET_PERMISSIONS_BY_RESOURCE = """
    SELECT 
        id, user_id, role, resource_type, 
        resource_id, actions, created_at
    FROM permissions
    WHERE resource_type = %s AND resource_id = %s
"""

CREATE_PERMISSION = """
    INSERT INTO permissions (
        user_id, role, resource_type, resource_id, actions
    )
    VALUES (%s, %s, %s, %s, %s)
"""

DELETE_PERMISSION = """
    DELETE FROM permissions
    WHERE id = %s
"""

DELETE_PERMISSIONS_BY_USER = """
    DELETE FROM permissions
    WHERE user_id = %s
"""

# ============================================
# Tool 레지스트리 (tools)
# ============================================

GET_TOOL_BY_NAME = """
    SELECT 
        id, name, description, category, 
        department, version, server_name,
        metadata, usage_count, registered_at
    FROM tools
    WHERE name = %s
"""

GET_ALL_TOOLS = """
    SELECT 
        id, name, description, category, 
        department, version, server_name,
        usage_count, registered_at
    FROM tools
    ORDER BY registered_at DESC
"""

GET_TOOLS_BY_CATEGORY = """
    SELECT 
        id, name, description, category, 
        department, version, server_name,
        usage_count, registered_at
    FROM tools
    WHERE category = %s
    ORDER BY registered_at DESC
"""

GET_TOOLS_BY_DEPARTMENT = """
    SELECT 
        id, name, description, category, 
        department, version, server_name,
        usage_count, registered_at
    FROM tools
    WHERE department = %s
    ORDER BY registered_at DESC
"""

CREATE_TOOL = """
    INSERT INTO tools (
        name, description, category, department,
        version, server_name, metadata
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

UPDATE_TOOL = """
    UPDATE tools
    SET 
        description = %s,
        category = %s,
        department = %s,
        version = %s,
        server_name = %s,
        metadata = %s
    WHERE name = %s
"""

DELETE_TOOL = """
    DELETE FROM tools
    WHERE name = %s
"""

INCREMENT_TOOL_USAGE = """
    UPDATE tools
    SET usage_count = usage_count + 1
    WHERE name = %s
"""

COUNT_TOOLS = """
    SELECT COUNT(*) AS total
    FROM tools
"""

# ============================================
# MCP Server (servers)
# ============================================

GET_SERVER_BY_NAME = """
    SELECT 
        id, name, description, status,
        host, port, pid, started_at, updated_at
    FROM servers
    WHERE name = %s
"""

GET_ALL_SERVERS = """
    SELECT 
        id, name, description, status,
        host, port, pid, started_at, updated_at
    FROM servers
    ORDER BY started_at DESC
"""

GET_ACTIVE_SERVERS = """
    SELECT 
        id, name, description, status,
        host, port, pid, started_at, updated_at
    FROM servers
    WHERE status = 'running'
"""

CREATE_SERVER = """
    INSERT INTO servers (
        name, description, status, host, port, pid
    )
    VALUES (%s, %s, %s, %s, %s, %s)
"""

UPDATE_SERVER_STATUS = """
    UPDATE servers
    SET status = %s, updated_at = CURRENT_TIMESTAMP
    WHERE name = %s
"""

UPDATE_SERVER_PID = """
    UPDATE servers
    SET pid = %s, updated_at = CURRENT_TIMESTAMP
    WHERE name = %s
"""

DELETE_SERVER = """
    DELETE FROM servers
    WHERE name = %s
"""

COUNT_SERVERS = """
    SELECT COUNT(*) AS total
    FROM servers
"""

COUNT_SERVERS_BY_STATUS = """
    SELECT status, COUNT(*) AS count
    FROM servers
    GROUP BY status
```



### 3.2 전체 코드 (계속)

```python
# shared/queries.py (계속)

"""

# ============================================
# 감사 로그 (audit_logs)
# ============================================

GET_AUDIT_LOG_BY_ID = """
    SELECT 
        id, user_id, action, resource_type, resource_id,
        details, result, ip_address, user_agent,
        created_at
    FROM audit_logs
    WHERE id = %s
"""

GET_AUDIT_LOGS_BY_USER = """
    SELECT 
        id, user_id, action, resource_type, resource_id,
        details, result, ip_address,
        created_at
    FROM audit_logs
    WHERE user_id = %s
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s
"""

GET_AUDIT_LOGS_BY_ACTION = """
    SELECT 
        id, user_id, action, resource_type, resource_id,
        details, result, created_at
    FROM audit_logs
    WHERE action = %s
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s
"""

GET_AUDIT_LOGS_BY_RESOURCE = """
    SELECT 
        id, user_id, action, resource_type, resource_id,
        details, result, created_at
    FROM audit_logs
    WHERE resource_type = %s AND resource_id = %s
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s
"""

GET_AUDIT_LOGS_BY_DATE_RANGE = """
    SELECT 
        id, user_id, action, resource_type, resource_id,
        details, result, created_at
    FROM audit_logs
    WHERE created_at BETWEEN %s AND %s
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s
"""

GET_RECENT_AUDIT_LOGS = """
    SELECT 
        a.id, a.user_id, a.action, a.resource_type, a.resource_id,
        a.result, a.created_at,
        u.name AS user_name
    FROM audit_logs a
    LEFT JOIN users u ON a.user_id = u.id
    ORDER BY a.created_at DESC
    LIMIT %s
"""

CREATE_AUDIT_LOG = """
    INSERT INTO audit_logs (
        user_id, action, resource_type, resource_id,
        details, result, ip_address, user_agent
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

COUNT_AUDIT_LOGS = """
    SELECT COUNT(*) AS total
    FROM audit_logs
"""

COUNT_AUDIT_LOGS_BY_USER = """
    SELECT user_id, COUNT(*) AS count
    FROM audit_logs
    GROUP BY user_id
    ORDER BY count DESC
    LIMIT %s
"""

COUNT_AUDIT_LOGS_BY_ACTION = """
    SELECT action, COUNT(*) AS count
    FROM audit_logs
    GROUP BY action
    ORDER BY count DESC
"""

GET_FAILED_ACTIONS = """
    SELECT 
        id, user_id, action, resource_type, resource_id,
        details, created_at
    FROM audit_logs
    WHERE result = 'failure'
    ORDER BY created_at DESC
    LIMIT %s
"""

DELETE_OLD_AUDIT_LOGS = """
    DELETE FROM audit_logs
    WHERE created_at < %s
"""

# ============================================
# 문서 버전 (document_versions)
# ============================================

GET_DOCUMENT_VERSIONS = """
    SELECT 
        id, document_id, version, title, content,
        changed_by, change_summary, created_at
    FROM document_versions
    WHERE document_id = %s
    ORDER BY version DESC
"""

GET_DOCUMENT_VERSION = """
    SELECT 
        id, document_id, version, title, content,
        changed_by, change_summary, created_at
    FROM document_versions
    WHERE document_id = %s AND version = %s
"""

GET_LATEST_VERSION = """
    SELECT 
        id, document_id, version, title, content,
        changed_by, change_summary, created_at
    FROM document_versions
    WHERE document_id = %s
    ORDER BY version DESC
    LIMIT 1
"""

CREATE_DOCUMENT_VERSION = """
    INSERT INTO document_versions (
        document_id, version, title, content,
        changed_by, change_summary
    )
    VALUES (%s, %s, %s, %s, %s, %s)
"""

COUNT_DOCUMENT_VERSIONS = """
    SELECT COUNT(*) AS total
    FROM document_versions
    WHERE document_id = %s
"""

DELETE_DOCUMENT_VERSIONS = """
    DELETE FROM document_versions
    WHERE document_id = %s
"""

# ============================================
# 접근 요청 (access_requests)
# ============================================

GET_ACCESS_REQUEST_BY_ID = """
    SELECT 
        id, user_id, resource_type, resource_id,
        reason, status, requested_at, reviewed_at,
        reviewed_by, review_comment
    FROM access_requests
    WHERE id = %s
"""

GET_ACCESS_REQUESTS_BY_USER = """
    SELECT 
        id, user_id, resource_type, resource_id,
        reason, status, requested_at, reviewed_at
    FROM access_requests
    WHERE user_id = %s
    ORDER BY requested_at DESC
"""

GET_PENDING_ACCESS_REQUESTS = """
    SELECT 
        ar.id, ar.user_id, ar.resource_type, ar.resource_id,
        ar.reason, ar.requested_at,
        u.name AS user_name, u.role AS user_role
    FROM access_requests ar
    LEFT JOIN users u ON ar.user_id = u.id
    WHERE ar.status = 'pending'
    ORDER BY ar.requested_at ASC
"""

GET_ACCESS_REQUESTS_BY_STATUS = """
    SELECT 
        id, user_id, resource_type, resource_id,
        reason, status, requested_at, reviewed_at
    FROM access_requests
    WHERE status = %s
    ORDER BY requested_at DESC
    LIMIT %s OFFSET %s
"""

CREATE_ACCESS_REQUEST = """
    INSERT INTO access_requests (
        user_id, resource_type, resource_id, reason
    )
    VALUES (%s, %s, %s, %s)
"""

UPDATE_ACCESS_REQUEST = """
    UPDATE access_requests
    SET 
        status = %s,
        reviewed_at = CURRENT_TIMESTAMP,
        reviewed_by = %s,
        review_comment = %s
    WHERE id = %s
"""

DELETE_ACCESS_REQUEST = """
    DELETE FROM access_requests
    WHERE id = %s
"""

COUNT_ACCESS_REQUESTS_BY_STATUS = """
    SELECT status, COUNT(*) AS count
    FROM access_requests
    GROUP BY status
"""

# ============================================
# 통계 쿼리
# ============================================

GET_SYSTEM_STATS = """
    SELECT 
        (SELECT COUNT(*) FROM users) AS total_users,
        (SELECT COUNT(*) FROM documents) AS total_documents,
        (SELECT COUNT(*) FROM tools) AS total_tools,
        (SELECT COUNT(*) FROM servers WHERE status = 'running') AS active_servers,
        (SELECT COUNT(*) FROM audit_logs WHERE DATE(created_at) = CURDATE()) AS today_actions
"""

GET_USER_ACTIVITY_STATS = """
    SELECT 
        DATE(created_at) AS date,
        COUNT(DISTINCT user_id) AS active_users,
        COUNT(*) AS total_actions
    FROM audit_logs
    WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
    GROUP BY DATE(created_at)
    ORDER BY date DESC
"""

GET_DOCUMENT_STATS_BY_CLASSIFICATION = """
    SELECT 
        classification,
        COUNT(*) AS count,
        AVG(version) AS avg_version
    FROM documents
    GROUP BY classification
"""

GET_TOP_USED_TOOLS = """
    SELECT 
        name, description, category,
        usage_count
    FROM tools
    ORDER BY usage_count DESC
    LIMIT %s
"""

GET_MOST_ACTIVE_USERS = """
    SELECT 
        u.id, u.name, u.role,
        COUNT(a.id) AS action_count
    FROM users u
    LEFT JOIN audit_logs a ON u.id = a.user_id
    WHERE a.created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
    GROUP BY u.id, u.name, u.role
    ORDER BY action_count DESC
    LIMIT %s
"""

GET_POPULAR_DOCUMENTS = """
    SELECT 
        d.id, d.title, d.classification,
        COUNT(a.id) AS view_count
    FROM documents d
    LEFT JOIN audit_logs a ON d.id = a.resource_id 
        AND a.resource_type = 'document' 
        AND a.action = 'document_view'
    WHERE a.created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
    GROUP BY d.id, d.title, d.classification
    ORDER BY view_count DESC
    LIMIT %s
"""

# ============================================
# 검색 쿼리
# ============================================

SEARCH_USERS = """
    SELECT 
        id, name, role, team, created_at
    FROM users
    WHERE 
        name LIKE %s 
        OR id LIKE %s
    ORDER BY name
    LIMIT %s
"""

SEARCH_DOCUMENTS_BY_TITLE = """
    SELECT 
        d.id, d.title, d.classification, d.category,
        d.author_id, d.team,
        u.name AS author_name
    FROM documents d
    LEFT JOIN users u ON d.author_id = u.id
    WHERE d.title LIKE %s
    ORDER BY d.updated_at DESC
    LIMIT %s
"""

SEARCH_TOOLS = """
    SELECT 
        name, description, category, department
    FROM tools
    WHERE 
        name LIKE %s 
        OR description LIKE %s
    ORDER BY usage_count DESC
    LIMIT %s
"""

# ============================================
# 유틸리티 쿼리
# ============================================

CHECK_USER_EXISTS = """
    SELECT COUNT(*) AS count
    FROM users
    WHERE id = %s
"""

CHECK_DOCUMENT_EXISTS = """
    SELECT COUNT(*) AS count
    FROM documents
    WHERE id = %s
"""

CHECK_TOOL_EXISTS = """
    SELECT COUNT(*) AS count
    FROM tools
    WHERE name = %s
"""

GET_TABLE_ROW_COUNT = """
    SELECT 
        table_name,
        table_rows
    FROM information_schema.tables
    WHERE table_schema = %s
    ORDER BY table_name
"""

GET_DATABASE_SIZE = """
    SELECT 
        table_schema AS database_name,
        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
    FROM information_schema.tables
    WHERE table_schema = %s
    GROUP BY table_schema
"""

# ============================================
# 인덱스 최적화 쿼리
# ============================================

ANALYZE_TABLE = """
    ANALYZE TABLE %s
"""

OPTIMIZE_TABLE = """
    OPTIMIZE TABLE %s
"""

# ============================================
# 쿼리 헬퍼 함수
# ============================================

def build_in_clause(values: list) -> tuple:
    """
    IN 절 생성 헬퍼
    
    Args:
        values: ["A", "B", "C"]
    
    Returns:
        ("(%s, %s, %s)", ["A", "B", "C"])
    
    Example:
        in_clause, params = build_in_clause(["public", "team"])
        sql = f"SELECT * FROM documents WHERE classification IN {in_clause}"
        result = db.execute_query(sql, tuple(params))
    """
    placeholders = ", ".join(["%s"] * len(values))
    return f"({placeholders})", values


def build_like_pattern(text: str, position: str = "both") -> str:
    """
    LIKE 패턴 생성
    
    Args:
        text: 검색어
        position: "both" | "start" | "end"
    
    Returns:
        "%검색어%" | "검색어%" | "%검색어"
    """
    if position == "both":
        return f"%{text}%"
    elif position == "start":
        return f"{text}%"
    elif position == "end":
        return f"%{text}"
    else:
        return f"%{text}%"


def paginate(limit: int = 20, page: int = 1) -> tuple:
    """
    페이지네이션 계산
    
    Args:
        limit: 페이지당 개수
        page: 페이지 번호 (1부터 시작)
    
    Returns:
        (limit, offset)
    
    Example:
        limit, offset = paginate(20, 3)
        result = db.execute_query(
            "SELECT * FROM documents LIMIT %s OFFSET %s",
            (limit, offset)
        )
    """
    offset = (page - 1) * limit
    return limit, offset
```

### 3.3 사용 예제

```python
# 예제 1: 기본 쿼리 사용
from shared.database import DatabaseManager
from shared import queries

db = DatabaseManager(config)

# 사용자 조회
user = db.execute_query(queries.GET_USER_BY_ID, ("U001",))
print(user[0]["name"])

# 문서 조회 (페이지네이션)
limit, offset = queries.paginate(limit=20, page=2)
docs = db.execute_query(queries.GET_ALL_DOCUMENTS, (limit, offset))

# 예제 2: 검색 (LIKE)
search_text = "예산"
pattern = queries.build_like_pattern(search_text)
docs = db.execute_query(
    queries.SEARCH_DOCUMENTS_BY_TITLE,
    (pattern, 10)
)

# 예제 3: IN 절
classifications = ["public", "team"]
in_clause, params = queries.build_in_clause(classifications)

sql = f"""
    SELECT * FROM documents 
    WHERE classification IN {in_clause}
    ORDER BY updated_at DESC
"""
result = db.execute_query(sql, tuple(params))

# 예제 4: 통계 조회
stats = db.execute_query(queries.GET_SYSTEM_STATS)
print(f"Total users: {stats[0]['total_users']}")
print(f"Total documents: {stats[0]['total_documents']}")

# 예제 5: 감사 로그 기록
db.execute_insert(
    queries.CREATE_AUDIT_LOG,
    (
        "U001",                    # user_id
        "document_view",           # action
        "document",                # resource_type
        "DOC001",                  # resource_id
        '{"duration_ms": 245}',   # details (JSON)
        "success",                 # result
        "192.168.1.100",          # ip_address
        "Mozilla/5.0..."          # user_agent
    )
)

# 예제 6: 트랜잭션 (문서 생성 + 버전 기록)
with db.transaction() as tx:
    # 문서 생성
    tx.execute(
        queries.CREATE_DOCUMENT,
        ("DOC999", "제목", "내용", "public", "general", "U001", None, None, 1)
    )
    
    # 버전 기록
    tx.execute(
        queries.CREATE_DOCUMENT_VERSION,
        ("DOC999", 1, "제목", "내용", "U001", "Initial version")
    )
    
    # 감사 로그
    tx.execute(
        queries.CREATE_AUDIT_LOG,
        ("U001", "document_create", "document", "DOC999", None, "success", None, None)
    )
```

***

## 4. elasticsearch.py

### 4.1 개요

**역할**: Elasticsearch 클라이언트 래퍼, 문서 색인/검색

**주요 기능**:
- 인덱스 생성/삭제
- 문서 색인 (단건/배치)
- 검색 (전문 검색, 필터링, 하이라이트)
- 한글 분석기 (nori tokenizer)
- 권한 기반 필터링

### 4.2 전체 코드

```python
# shared/elasticsearch.py
"""
Elasticsearch 클라이언트 래퍼
한글 전문 검색 지원 (nori analyzer)
"""

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import (
    ConnectionError, 
    NotFoundError, 
    RequestError
)
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ElasticsearchError(Exception):
    """Elasticsearch 에러 기본 클래스"""
    pass


class IndexError(ElasticsearchError):
    """인덱스 에러"""
    pass


class SearchError(ElasticsearchError):
    """검색 에러"""
    pass


class ElasticsearchManager:
    """
    Elasticsearch 관리자
    
    특징:
    - 한글 분석기 (nori)
    - Bulk 색인
    - 권한 기반 필터링
    - 하이라이트
    """
    
    def __init__(self, config: dict):
        """
        초기화
        
        Args:
            config: {
                "hosts": ["localhost:9200"],
                "timeout": 30
            }
        """
        self.config = config
        self.client = None
        self._connect()
    
    def _connect(self):
        """Elasticsearch 연결"""
        try:
            self.client = Elasticsearch(
                hosts=self.config["hosts"],
                timeout=self.config.get("timeout", 30),
                max_retries=3,
                retry_on_timeout=True
            )
            
            # 연결 확인
            if self.client.ping():
                logger.info(f"Elasticsearch connected: {self.config['hosts']}")
            else:
                raise ConnectionError("Elasticsearch ping failed")
        
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise ElasticsearchError(f"Connection failed: {e}")
    
    def create_index(
        self, 
        index: str, 
        mappings: dict,
        settings: Optional[dict] = None
    ):
        """
        인덱스 생성
        
        Args:
            index: 인덱스 이름
            mappings: 필드 매핑
            settings: 인덱스 설정
        
        Example:
            es.create_index(
                "documents",
                mappings={
                    "properties": {
                        "title": {"type": "text", "analyzer": "nori"}
                    }
                }
            )
        """
        try:
            # 기본 설정 (한글 분석기)
            default_settings = {
                "analysis": {
                    "analyzer": {
                        "nori": {
                            "type": "custom",
                            "tokenizer": "nori_tokenizer",
                            "filter": ["lowercase"]
                        }
                    }
                },
                "number_of_shards": 1,
                "number_of_replicas": 1
            }
            
            if settings:
                default_settings.update(settings)
            
            body = {
                "settings": default_settings,
                "mappings": mappings
            }
            
            self.client.indices.create(index=index, body=body)
            
            logger.info(f"Index created: {index}")
        
        except RequestError as e:
            if "resource_already_exists_exception" in str(e):
                logger.warning(f"Index already exists: {index}")
            else:
                logger.error(f"Failed to create index {index}: {e}")
                raise IndexError(f"Index creation failed: {e}")
    
    def delete_index(self, index: str):
        """인덱스 삭제"""
        try:
            self.client.indices.delete(index=index)
            logger.info(f"Index deleted: {index}")
        
        except NotFoundError:
            logger.warning(f"Index not found: {index}")
        
        except Exception as e:
            logger.error(f"Failed to delete index {index}: {e}")
            raise IndexError(f"Index deletion failed: {e}")
    
    def index_exists(self, index: str) -> bool:
        """인덱스 존재 확인"""
        return self.client.indices.exists(index=index)
    
    def index_document(
        self, 
        index: str, 
        doc_id: str, 
        body: dict
    ):
        """
        문서 색인 (단건)
        
        Args:
            index: 인덱스 이름
            doc_id: 문서 ID
            body: 문서 내용
        
        Example:
            es.index_document(
                "documents",
                "DOC001",
                {
                    "title": "예산 계획",
                    "content": "2026년 예산...",
                    "classification": "public"
                }
            )
        """
        try:
            self.client.index(
                index=index,
                id=doc_id,
                body=body
            )
            
            logger.debug(f"Document indexed: {index}/{doc_id}")
        
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            raise ElasticsearchError(f"Indexing failed: {e}")
    
    def bulk_index(
        self, 
        index: str, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        문서 배치 색인
        
        Args:
            index: 인덱스 이름
            documents: [
                {"_id": "DOC001", "title": "...", "content": "..."},
                {"_id": "DOC002", "title": "...", "content": "..."}
            ]
        
        Returns:
            {"success": 2, "failed": 0}
        
        Example:
            result = es.bulk_index("documents", docs)
            print(f"Indexed: {result['success']}")
        """
        try:
            actions = [
                {
                    "_index": index,
                    "_id": doc.pop("_id"),
                    "_source": doc
                }
                for doc in documents
            ]
            
            success, failed = helpers.bulk(
                self.client,
                actions,
                stats_only=False,
                raise_on_error=False
            )
            
            logger.info(
                f"Bulk index completed: {index} "
                f"[success={success}, failed={len(failed)}]"
            )
            
            return {"success": success, "failed": len(failed)}
        
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            raise ElasticsearchError(f"Bulk indexing failed: {e}")
    
    def search(
        self, 
        index: str, 
        query: dict,
        size: int = 10,
        from_: int = 0,
        sort: Optional[List[dict]] = None,
        highlight: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        문서 검색
        
        Args:
            index: 인덱스 이름
            query: Elasticsearch 쿼리 DSL
            size: 결과 개수
            from_: 시작 오프셋
            sort: 정렬 (예: [{"_score": "desc"}])
            highlight: 하이라이트 설정
        
        Returns:
            {
                "total": 5,
                "hits": [
                    {
                        "_id": "DOC001",
                        "_score": 8.5,
                        "_source": {...},
                        "highlight": {...}
                    }
                ]
            }
        
        Example:
            result = es.search(
                "documents",
                query={"match": {"content": "예산"}},
                size=10,
                highlight={"fields": {"content": {}}}
            )
        """
        try:
            body = {
                "query": query,
                "size": size,
                "from": from_
            }
            
            if sort:
                body["sort"] = sort
            
            if highlight:
                body["highlight"] = highlight
            
            response = self.client.search(
                index=index,
                body=body
            )
            
            total = response["hits"]["total"]["value"]
            hits = response["hits"]["hits"]
            
            logger.debug(
                f"Search executed: {index} "
                f"[total={total}, returned={len(hits)}]"
            )
            
            return {
                "total": total,
                "hits": hits
            }
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(f"Search failed: {e}")
    
    def search_documents(
        self,
        query_text: str,
        classification: List[str],
        team: Optional[str] = None,
        category: Optional[str] = None,
        size: int = 10,
        from_: int = 0
    ) -> Dict[str, Any]:
        """
        문서 검색 (권한 필터링 포함)
        
        Args:
            query_text: 검색어
            classification: 접근 가능한 등급 (예: ["public", "team"])
            team: 팀 (team 등급 문서 필터링)
            category: 카테고리 필터
            size: 결과 개수
            from_: 시작 오프셋
        
        Returns:
            {
                "total": 5,
                "results": [
                    {
                        "doc_id": "DOC001",
                        "title": "예산 계획",
                        "snippet": "...예산...",
                        "classification": "public",
                        "score": 8.5
                    }
                ]
            }
        """
        # 쿼리 빌드
        must = [
            {
                "multi_match": {
                    "query": query_text,
                    "fields": ["title^3", "content"],
                    "type": "best_fields",
                    "operator": "or"
                }
            }
        ]
        
        filters = [
            {"terms": {"classification": classification}}
        ]
        
        # team 등급 문서는 같은 팀만
        if "team" in classification and team:
            filters.append(
                {
                    "bool": {
                        "should": [
                            {"term": {"classification": "public"}},
                            {
                                "bool": {
                                    "must": [
                                        {"term": {"classification": "team"}},
                                        {"term": {"team": team}}
                                    ]
                                }
                            },
                            {"term": {"classification": "confidential"}}
                        ]
                    }
                }
            )
        
        if category:
            filters.append({"term": {"category": category}})
        
        query = {
            "bool": {
                "must": must,
                "filter": filters
            }
        }
        
        # 하이라이트
        highlight = {
            "fields": {
                "title": {
                    "number_of_fragments": 0
                },
                "content": {
                    "fragment_size": 150,
                    "number_of_fragments": 3
                }
            },
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"]
        }
        
        # 검색 실행
        result = self.search(
            index="documents",
            query=query,
            size=size,
            from_=from_,
            highlight=highlight
        )
        
        # 결과 파싱
        results = []
        for hit in result["hits"]:
            source = hit["_source"]
            highlight_content = hit.get("highlight", {})
            
            # 스니펫 생성
            if "content" in highlight_content:
                snippet = " ... ".join(highlight_content["content"])
            else:
                snippet = source.get("content", "")[:200] + "..."
            
            results.append({
                "doc_id": hit["_id"],
                "title": source.get("title", ""),
                "snippet": snippet,
                "classification": source.get("classification", ""),
                "category": source.get("category", ""),
                "author_id": source.get("author_id", ""),
                "team": source.get("team", ""),
                "created_at": source.get("created_at", ""),
                "score": hit["_score"]
            })
        
        return {
            "total": result["total"],
            "results": results
        }
    
    def get_document(self, index: str, doc_id: str) -> Optional[dict]:
        """문서 조회"""
        try:
            response = self.client.get(index=index, id=doc_id)
            return response["_source"]
        
        except NotFoundError:
            return None
        
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise ElasticsearchError(f"Get document failed: {e}")
    
    def delete_document(self, index: str, doc_id: str):
        """문서 삭제"""
        try:
            self.client.delete(index=index, id=doc_id)
            logger.debug(f"Document deleted: {index}/{doc_id}")
        
        except NotFoundError:
            logger.warning(f"Document not found: {index}/{doc_id}")
        
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise ElasticsearchError(f"Delete failed: {e}")
    
    def update_document(
        self, 
        index: str, 
        doc_id: str, 
        body: dict
    ):
        """문서 업데이트 (부분 업데이트)"""
        try:
            self.client.update(
                index=index,
                id=doc_id,
                body={"doc": body}
            )
            
            logger.debug(f"Document updated: {index}/{doc_id}")
        
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise ElasticsearchError(f"Update failed: {e}")
    
    def count(self, index: str, query: Optional[dict] = None) -> int:
        """문서 개수 조회"""
        try:
            body = {"query": query} if query else None
            response = self.client.count(index=index, body=body)
            return response["count"]
        
        except Exception as e:
            logger.error(f"Count failed: {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """
        Elasticsearch 상태 확인
        
        Returns:
            {
                "status": "green",
                "cluster_name": "mcps-cluster",
                "nodes": 1
            }
        """
        try:
            health = self.client.cluster.health()
            
            return {
                "status": health["status"],
                "cluster_name": health["cluster_name"],
                "nodes": health["number_of_nodes"],
                "active_shards": health["active_shards"]
            }
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unknown", "error": str(e)}
    
    def close(self):
        """연결 종료"""
        if self.client:
            self.client.close()
            logger.info("Elasticsearch connection closed")


# 인덱스 매핑 정의
DOCUMENTS_INDEX_MAPPING = {
    "properties": {
        "doc_id": {
            "type": "keyword"
        },
        "title": {
            "type": "text",
            "analyzer": "nori",
            "fields": {
                "keyword": {
                    "type": "keyword"
                }
            }
        },
        "content": {
            "type": "text",
            "analyzer": "nori"
        },
        "classification": {
            "type": "keyword"
        },
        "category": {
            "type": "keyword"
        },
        "author_id": {
            "type": "keyword"
        },
        "team": {
            "type": "keyword"
        },
        "created_at": {
            "type": "date"
        },
        "updated_at": {
            "type": "date"
        }
    }
}

AUDIT_LOGS_INDEX_MAPPING = {
    "properties": {
        "user_id": {
            "type": "keyword"
        },
        "action": {
            "type": "keyword"
        },
        "resource_type": {
            "type": "keyword"
        },
        "resource_id": {
            "type": "keyword"
        },
        "details": {
            "type": "text"
        },
        "result": {
            "type": "keyword"
        },
        "ip_address": {
            "type": "ip"
        },
        "timestamp": {
            "type": "date"
        }
    }
}
```

### 4.3 사용 예제

```python
# 예제 1: 인덱스 생성
from shared.elasticsearch import ElasticsearchManager, DOCUMENTS_INDEX_MAPPING

es = ElasticsearchManager(config)

es.create_index("documents", DOCUMENTS_INDEX_MAPPING)

# 예제 2: 문서 색인
es.index_document(
    "documents",
    "DOC001",
    {
        "doc_id": "DOC001",
        "title": "2026년 예산 계획",
        "content": "2026년 예산은 전년 대비 10% 증가...",
        "classification": "public",
        "category": "finance",
        "author_id": "U001",
        "team": None,
        "created_at": "2026-01-08T10:00:00Z"
    }
)

# 예제 3: 검색 (권한 필터링)
result = es.search_documents(
    query_text="예산",
    classification=["public", "team"],
    team="dev_team",
    size=10
)

print(f"검색 결과: {result['total']}건")
for doc in result['results']:
    print(f"  - {doc['title']} ({doc['score']:.2f})")
    print(f"    {doc['snippet']}")

# 예제 4: 배치 색인
documents = [
    {"_id": "DOC001", "title": "문서1", "content": "내용1"},
    {"_id": "DOC002", "title": "문서2", "content": "내용2"},
    {"_id": "DOC003", "title": "문서3", "content": "내용3"}
]

result = es.bulk_index("documents", documents)
print(f"색인 완료: {result['success']}건")

# 예제 5: 고급 검색 (직접 쿼리)
query = {
    "bool": {
        "must": [
            {"match": {"content": "예산"}}
        ],
        "filter": [
            {"term": {"classification": "public"}},
            {"range": {"created_at": {"gte": "2026-01-01"}}}
        ]
    }
}

result = es.search(
    "documents",
    query=query,
    size=20,
    sort=[{"_score": "desc"}, {"created_at": "desc"}],
    highlight={"fields": {"content": {}}}
)
```


## 5. permissions.py

### 5.1 개요

**역할**: 역할 기반 접근 제어 (RBAC) 구현

**주요 기능**:
- 사용자 권한 확인
- 문서 접근 권한
- Tool 실행 권한
- Server 관리 권한
- 권한 캐싱

### 5.2 전체 코드

```python
# shared/permissions.py
"""
RBAC (Role-Based Access Control) 구현
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """사용자 역할"""
    JUNIOR = "junior"
    STAFF = "staff"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    ADMIN = "admin"


class Classification(str, Enum):
    """문서 등급"""
    PUBLIC = "public"
    TEAM = "team"
    CONFIDENTIAL = "confidential"


class Action(str, Enum):
    """액션 타입"""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    MANAGE = "manage"


class PermissionDeniedError(Exception):
    """권한 거부 에러"""
    pass


class PermissionEngine:
    """
    권한 엔진
    
    특징:
    - 역할 기반 접근 제어
    - 문서 등급별 접근 제어
    - Tool 실행 권한
    - 권한 캐싱
    """
    
    def __init__(self):
        """초기화"""
        self.cache = {}
        self._load_permission_matrix()
    
    def _load_permission_matrix(self):
        """권한 매트릭스 로드"""
        self.permission_matrix = {
            Role.JUNIOR: {
                "document": {
                    Classification.PUBLIC: [Action.READ],
                    Classification.TEAM: [],
                    Classification.CONFIDENTIAL: []
                },
                "tool": {
                    "search_documents": [Action.EXECUTE],
                    "get_document": [Action.EXECUTE],
                    "list_documents": [Action.EXECUTE]
                },
                "server": [],
                "admin": []
            },
            Role.STAFF: {
                "document": {
                    Classification.PUBLIC: [Action.READ, Action.CREATE, Action.UPDATE],
                    Classification.TEAM: [Action.READ, Action.CREATE, Action.UPDATE],
                    Classification.CONFIDENTIAL: []
                },
                "tool": {
                    "search_documents": [Action.EXECUTE],
                    "get_document": [Action.EXECUTE],
                    "list_documents": [Action.EXECUTE],
                    "create_document": [Action.EXECUTE],
                    "update_document": [Action.EXECUTE]
                },
                "server": [],
                "admin": []
            },
            Role.MANAGER: {
                "document": {
                    Classification.PUBLIC: [Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE],
                    Classification.TEAM: [Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE],
                    Classification.CONFIDENTIAL: []
                },
                "tool": {
                    "*": [Action.EXECUTE]  # 모든 Tool
                },
                "server": [],
                "admin": [Action.APPROVE]  # 팀원 승인만
            },
            Role.EXECUTIVE: {
                "document": {
                    Classification.PUBLIC: [Action.READ],
                    Classification.TEAM: [Action.READ],
                    Classification.CONFIDENTIAL: [Action.READ]
                },
                "tool": {
                    "*": [Action.EXECUTE]
                },
                "server": [],
                "admin": []
            },
            Role.ADMIN: {
                "document": {
                    "*": [Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE]
                },
                "tool": {
                    "*": [Action.EXECUTE, Action.MANAGE]
                },
                "server": {
                    "*": [Action.MANAGE]
                },
                "admin": {
                    "*": [Action.MANAGE]
                }
            }
        }
    
    def check_document_permission(
        self,
        user_id: str,
        user_role: str,
        user_team: Optional[str],
        document: Dict[str, Any],
        action: str
    ) -> bool:
        """
        문서 접근 권한 확인
        
        Args:
            user_id: 사용자 ID
            user_role: 사용자 역할
            user_team: 사용자 팀
            document: 문서 정보 {
                "id": "DOC001",
                "classification": "team",
                "team": "dev_team",
                "author_id": "U001"
            }
            action: 액션 (read, create, update, delete)
        
        Returns:
            bool: 권한 있음 여부
        """
        role = Role(user_role)
        classification = Classification(document["classification"])
        action_enum = Action(action)
        
        # 캐시 키
        cache_key = f"{user_id}:{document['id']}:{action}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Admin은 모든 권한
        if role == Role.ADMIN:
            self.cache[cache_key] = True
            return True
        
        # 본인이 작성한 문서는 항상 접근 가능 (삭제 제외)
        if document.get("author_id") == user_id and action_enum != Action.DELETE:
            self.cache[cache_key] = True
            return True
        
        # Executive는 모든 문서 읽기 가능
        if role == Role.EXECUTIVE and action_enum == Action.READ:
            self.cache[cache_key] = True
            return True
        
        # 권한 매트릭스에서 확인
        doc_permissions = self.permission_matrix.get(role, {}).get("document", {})
        
        # Wildcard 확인
        if "*" in doc_permissions:
            allowed_actions = doc_permissions["*"]
            if action_enum in allowed_actions:
                self.cache[cache_key] = True
                return True
        
        # 등급별 권한 확인
        allowed_actions = doc_permissions.get(classification, [])
        
        if action_enum not in allowed_actions:
            self.cache[cache_key] = False
            return False
        
        # team 등급은 같은 팀만 접근
        if classification == Classification.TEAM:
            if document.get("team") != user_team:
                self.cache[cache_key] = False
                return False
        
        self.cache[cache_key] = True
        return True
    
    def check_tool_permission(
        self,
        user_role: str,
        tool_name: str,
        action: str = "execute"
    ) -> bool:
        """
        Tool 실행 권한 확인
        
        Args:
            user_role: 사용자 역할
            tool_name: Tool 이름
            action: 액션 (execute, manage)
        
        Returns:
            bool: 권한 있음 여부
        """
        role = Role(user_role)
        action_enum = Action(action)
        
        # Admin은 모든 권한
        if role == Role.ADMIN:
            return True
        
        tool_permissions = self.permission_matrix.get(role, {}).get("tool", {})
        
        # Wildcard 확인
        if "*" in tool_permissions:
            return action_enum in tool_permissions["*"]
        
        # 특정 Tool 권한 확인
        if tool_name in tool_permissions:
            return action_enum in tool_permissions[tool_name]
        
        return False
    
    def check_server_permission(
        self,
        user_role: str,
        server_name: str,
        action: str = "manage"
    ) -> bool:
        """
        Server 관리 권한 확인
        
        Args:
            user_role: 사용자 역할
            server_name: Server 이름
            action: 액션 (manage)
        
        Returns:
            bool: 권한 있음 여부
        """
        role = Role(user_role)
        
        # Admin만 Server 관리 가능
        return role == Role.ADMIN
    
    def check_admin_permission(
        self,
        user_role: str,
        action: str
    ) -> bool:
        """
        관리 기능 권한 확인
        
        Args:
            user_role: 사용자 역할
            action: 액션 (approve, manage)
        
        Returns:
            bool: 권한 있음 여부
        """
        role = Role(user_role)
        action_enum = Action(action)
        
        admin_permissions = self.permission_matrix.get(role, {}).get("admin", [])
        
        # Wildcard 확인
        if "*" in admin_permissions:
            return True
        
        return action_enum in admin_permissions
    
    def get_accessible_classifications(
        self,
        user_role: str,
        action: str = "read"
    ) -> List[str]:
        """
        접근 가능한 문서 등급 목록
        
        Args:
            user_role: 사용자 역할
            action: 액션
        
        Returns:
            List[str]: ["public", "team", "confidential"]
        """
        role = Role(user_role)
        action_enum = Action(action)
        
        doc_permissions = self.permission_matrix.get(role, {}).get("document", {})
        
        # Wildcard
        if "*" in doc_permissions:
            return ["public", "team", "confidential"]
        
        accessible = []
        for classification, actions in doc_permissions.items():
            if action_enum in actions:
                accessible.append(classification.value)
        
        return accessible
    
    def get_allowed_tools(
        self,
        user_role: str
    ) -> List[str]:
        """
        실행 가능한 Tool 목록
        
        Args:
            user_role: 사용자 역할
        
        Returns:
            List[str]: Tool 이름 목록 (["*"] 이면 전체)
        """
        role = Role(user_role)
        
        tool_permissions = self.permission_matrix.get(role, {}).get("tool", {})
        
        if "*" in tool_permissions:
            return ["*"]
        
        return list(tool_permissions.keys())
    
    def can_approve_request(
        self,
        approver_role: str,
        approver_team: Optional[str],
        requester_team: Optional[str]
    ) -> bool:
        """
        접근 요청 승인 권한
        
        Args:
            approver_role: 승인자 역할
            approver_team: 승인자 팀
            requester_team: 요청자 팀
        
        Returns:
            bool: 승인 가능 여부
        """
        role = Role(approver_role)
        
        # Admin은 모든 요청 승인 가능
        if role == Role.ADMIN:
            return True
        
        # Manager는 같은 팀 요청만 승인 가능
        if role == Role.MANAGER:
            return approver_team == requester_team
        
        return False
    
    def filter_documents_by_permission(
        self,
        documents: List[Dict[str, Any]],
        user_id: str,
        user_role: str,
        user_team: Optional[str],
        action: str = "read"
    ) -> List[Dict[str, Any]]:
        """
        권한이 있는 문서만 필터링
        
        Args:
            documents: 문서 목록
            user_id: 사용자 ID
            user_role: 사용자 역할
            user_team: 사용자 팀
            action: 액션
        
        Returns:
            List[Dict]: 접근 가능한 문서 목록
        """
        filtered = []
        
        for doc in documents:
            if self.check_document_permission(
                user_id, user_role, user_team, doc, action
            ):
                filtered.append(doc)
        
        return filtered
    
    def require_permission(
        self,
        user_id: str,
        user_role: str,
        user_team: Optional[str],
        resource_type: str,
        resource: Any,
        action: str
    ):
        """
        권한 확인 (없으면 예외 발생)
        
        Args:
            user_id: 사용자 ID
            user_role: 사용자 역할
            user_team: 사용자 팀
            resource_type: 리소스 타입 (document, tool, server)
            resource: 리소스 객체 또는 이름
            action: 액션
        
        Raises:
            PermissionDeniedError: 권한 없음
        """
        has_permission = False
        
        if resource_type == "document":
            has_permission = self.check_document_permission(
                user_id, user_role, user_team, resource, action
            )
        elif resource_type == "tool":
            has_permission = self.check_tool_permission(
                user_role, resource, action
            )
        elif resource_type == "server":
            has_permission = self.check_server_permission(
                user_role, resource, action
            )
        
        if not has_permission:
            raise PermissionDeniedError(
                f"Permission denied: {user_role} cannot {action} {resource_type}"
            )
    
    def clear_cache(self):
        """권한 캐시 초기화"""
        self.cache.clear()
        logger.info("Permission cache cleared")
    
    def get_permission_summary(
        self,
        user_role: str
    ) -> Dict[str, Any]:
        """
        역할별 권한 요약
        
        Args:
            user_role: 사용자 역할
        
        Returns:
            {
                "documents": {
                    "public": ["read", "create", "update"],
                    "team": ["read", "create"],
                    "confidential": []
                },
                "tools": ["*"] or ["tool1", "tool2"],
                "servers": [],
                "admin": ["approve"]
            }
        """
        role = Role(user_role)
        permissions = self.permission_matrix.get(role, {})
        
        summary = {
            "documents": {},
            "tools": [],
            "servers": [],
            "admin": []
        }
        
        # 문서 권한
        for classification, actions in permissions.get("document", {}).items():
            if classification == "*":
                summary["documents"]["all"] = [a.value for a in actions]
            else:
                summary["documents"][classification.value] = [a.value for a in actions]
        
        # Tool 권한
        tool_perms = permissions.get("tool", {})
        if "*" in tool_perms:
            summary["tools"] = ["*"]
        else:
            summary["tools"] = list(tool_perms.keys())
        
        # Server 권한
        server_perms = permissions.get("server", {})
        if "*" in server_perms:
            summary["servers"] = ["*"]
        else:
            summary["servers"] = list(server_perms.keys())
        
        # 관리 권한
        admin_perms = permissions.get("admin", [])
        if "*" in admin_perms:
            summary["admin"] = ["*"]
        else:
            summary["admin"] = [a.value for a in admin_perms]
        
        return summary


# 데코레이터
def require_role(allowed_roles: List[str]):
    """
    역할 확인 데코레이터
    
    Example:
        @require_role(["admin", "manager"])
        def delete_document(user_role, doc_id):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_role = kwargs.get("user_role")
            if user_role not in allowed_roles:
                raise PermissionDeniedError(
                    f"Role {user_role} not allowed. Required: {allowed_roles}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### 5.3 사용 예제

```python
# 예제 1: 문서 접근 권한 확인
from shared.permissions import PermissionEngine, PermissionDeniedError

perm_engine = PermissionEngine()

user = {
    "id": "U001",
    "role": "staff",
    "team": "dev_team"
}

document = {
    "id": "DOC001",
    "classification": "team",
    "team": "dev_team",
    "author_id": "U002"
}

# 읽기 권한 확인
can_read = perm_engine.check_document_permission(
    user["id"], user["role"], user["team"],
    document, "read"
)
print(f"읽기 권한: {can_read}")  # True

# 삭제 권한 확인
can_delete = perm_engine.check_document_permission(
    user["id"], user["role"], user["team"],
    document, "delete"
)
print(f"삭제 권한: {can_delete}")  # False


# 예제 2: Tool 실행 권한
can_execute = perm_engine.check_tool_permission(
    user_role="staff",
    tool_name="search_documents",
    action="execute"
)
print(f"Tool 실행 권한: {can_execute}")  # True


# 예제 3: 권한 강제 (없으면 예외)
try:
    perm_engine.require_permission(
        user["id"], user["role"], user["team"],
        resource_type="document",
        resource=document,
        action="delete"
    )
except PermissionDeniedError as e:
    print(f"권한 거부: {e}")


# 예제 4: 접근 가능한 문서 등급 조회
classifications = perm_engine.get_accessible_classifications(
    user_role="staff",
    action="read"
)
print(f"접근 가능 등급: {classifications}")  # ["public", "team"]


# 예제 5: 문서 목록 필터링
documents = [
    {"id": "DOC001", "classification": "public", "team": None},
    {"id": "DOC002", "classification": "team", "team": "dev_team"},
    {"id": "DOC003", "classification": "team", "team": "hr_team"},
    {"id": "DOC004", "classification": "confidential", "team": None}
]

filtered = perm_engine.filter_documents_by_permission(
    documents,
    user["id"], user["role"], user["team"],
    action="read"
)
print(f"접근 가능 문서: {len(filtered)}개")  # 2개 (DOC001, DOC002)


# 예제 6: 역할별 권한 요약
summary = perm_engine.get_permission_summary("manager")
print(json.dumps(summary, indent=2))
# {
#   "documents": {
#     "public": ["read", "create", "update", "delete"],
#     "team": ["read", "create", "update", "delete"]
#   },
#   "tools": ["*"],
#   "servers": [],
#   "admin": ["approve"]
# }


# 예제 7: 데코레이터 사용
from shared.permissions import require_role

@require_role(["admin", "manager"])
def delete_document(user_role, doc_id):
    print(f"문서 {doc_id} 삭제")

try:
    delete_document(user_role="staff", doc_id="DOC001")
except PermissionDeniedError as e:
    print(f"에러: {e}")
```

***

## 6. logging_config.py

### 6.1 개요

**역할**: 통합 로깅 설정

**주요 기능**:
- 표준 로거 설정
- 파일 로테이션
- JSON 포맷 지원
- 컴포넌트별 로거

### 6.2 전체 코드

```python
# shared/logging_config.py
"""
통합 로깅 설정
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class JSONFormatter(logging.Formatter):
    """JSON 포맷 로거"""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그를 JSON으로 포맷팅"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 추가 필드
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        # 예외 정보
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """텍스트 포맷 로거"""
    
    def __init__(self):
        fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        super().__init__(fmt=fmt, datefmt=datefmt)


def setup_logging(
    component: str,
    log_dir: Optional[Path] = None,
    level: str = "INFO",
    format_type: str = "text",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 10
) -> logging.Logger:
    """
    로거 설정
    
    Args:
        component: 컴포넌트 이름 (mcp-host, api-gateway, frontend 등)
        log_dir: 로그 디렉토리
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 포맷 타입 ("text" | "json")
        max_bytes: 파일 최대 크기
        backup_count: 백업 파일 개수
    
    Returns:
        logging.Logger
    
    Example:
        logger = setup_logging("mcp-host", Path("/app/poc/mcps/data/logs"))
        logger.info("Application started")
    """
    logger = logging.getLogger(component)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 기존 핸들러 제거
    logger.handlers.clear()
    
    # 포맷터 선택
    if format_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 일반 로그
        app_log_file = log_dir / f"{component}.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        app_handler.setFormatter(formatter)
        logger.addHandler(app_handler)
        
        # 에러 로그 (ERROR 이상만)
        error_log_file = log_dir / f"{component}_error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    logger.info(f"Logger initialized: {component} (level={level}, format={format_type})")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    로거 가져오기
    
    Args:
        name: 로거 이름 (보통 __name__)
    
    Returns:
        logging.Logger
    
    Example:
        logger = get_logger(__name__)
        logger.info("Processing document")
    """
    return logging.getLogger(name)


class LogContext:
    """
    로그 컨텍스트 (추가 필드)
    
    Example:
        with LogContext(user_id="U001", request_id="req_123"):
            logger.info("User action")
            # 로그에 user_id, request_id 자동 포함
    """
    
    def __init__(self, **fields):
        self.fields = fields
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.fields.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


# 미리 정의된 로거 (선택)
def get_mcp_host_logger() -> logging.Logger:
    """MCP Host 로거"""
    return get_logger("mcp-host")


def get_api_gateway_logger() -> logging.Logger:
    """API Gateway 로거"""
    return get_logger("api-gateway")


def get_frontend_logger() -> logging.Logger:
    """Frontend 로거"""
    return get_logger("frontend")


def get_mcp_server_logger(server_name: str) -> logging.Logger:
    """MCP Server 로거"""
    return get_logger(f"mcp-server.{server_name}")


# 로그 레벨 변경 유틸리티
def set_log_level(logger_name: str, level: str):
    """
    로그 레벨 동적 변경
    
    Args:
        logger_name: 로거 이름
        level: 새 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.info(f"Log level changed to {level}")


# 전역 로깅 설정
def configure_global_logging(
    level: str = "INFO",
    format_type: str = "text"
):
    """
    전역 로깅 설정
    
    Args:
        level: 기본 로그 레벨
        format_type: 포맷 타입
    """
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 기존 핸들러 제거
    root_logger.handlers.clear()
    
    # 포맷터
    if format_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("pymysql").setLevel(logging.WARNING)


# 예외 로깅 데코레이터
def log_exceptions(logger: Optional[logging.Logger] = None):
    """
    예외 로깅 데코레이터
    
    Example:
        @log_exceptions()
        def risky_function():
            raise ValueError("Something went wrong")
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger(func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _logger.exception(
                    f"Exception in {func.__name__}: {e}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


# 실행 시간 로깅 데코레이터
def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    실행 시간 로깅 데코레이터
    
    Example:
        @log_execution_time()
        def slow_function():
            time.sleep(2)
    """
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger(func.__module__)
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000
            _logger.info(
                f"{func.__name__} executed in {execution_time:.2f}ms"
            )
            
            return result
        return wrapper
    return decorator
```

### 6.3 사용 예제

```python
# 예제 1: 기본 로거 설정
from shared.logging_config import setup_logging, get_logger
from pathlib import Path

# 컴포넌트 로거 설정
logger = setup_logging(
    component="mcp-host",
    log_dir=Path("/app/poc/mcps/data/logs/mcp-host"),
    level="INFO",
    format_type="text"
)

logger.info("Application started")
logger.warning("Connection pool nearly full")
logger.error("Database connection failed")


# 예제 2: 모듈별 로거
# module1.py
from shared.logging_config import get_logger

logger = get_logger(__name__)

def process_document():
    logger.info("Processing document")
    try:
        # 작업 수행
        pass
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)


# 예제 3: 로그 컨텍스트 (추가 필드)
from shared.logging_config import LogContext

logger = get_logger(__name__)

with LogContext(user_id="U001", request_id="req_abc123"):
    logger.info("User logged in")
    logger.info("Document accessed")
    # 모든 로그에 user_id, request_id 자동 포함


# 예제 4: JSON 포맷
logger = setup_logging(
    component="api-gateway",
    log_dir=Path("/app/poc/mcps/data/logs/api-gateway"),
    level="INFO",
    format_type="json"
)

logger.info("API request received")
# 출력: {"timestamp": "2026-01-08T10:00:00Z", "level": "INFO", ...}


# 예제 5: 데코레이터
from shared.logging_config import log_exceptions, log_execution_time

logger = get_logger(__name__)

@log_exceptions(logger)
@log_execution_time(logger)
def search_documents(query):
    # 검색 로직
    return results


# 예제 6: 동적 로그 레벨 변경
from shared.logging_config import set_log_level

# 디버깅 필요 시
set_log_level("mcp-host", "DEBUG")

# 정상 운영 시
set_log_level("mcp-host", "INFO")
```

***

## 7. mcp_protocol.py

### 7.1 개요

**역할**: MCP (Model Context Protocol) JSON-RPC 구현

**주요 기능**:
- JSON-RPC 2.0 메시지 파싱
- STDIO 통신
- 요청/응답 처리
- 에러 코드 정의

### 7.2 전체 코드

```python
# shared/mcp_protocol.py
"""
MCP (Model Context Protocol) 구현
JSON-RPC 2.0 over STDIO
"""

import json
import sys
from typing import Dict, Any, Optional, Callable
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)


class JSONRPCError(IntEnum):
    """JSON-RPC 2.0 에러 코드"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # 커스텀 에러
    PERMISSION_DENIED = 1001
    RESOURCE_NOT_FOUND = 1002
    DATABASE_ERROR = 1003
    ELASTICSEARCH_ERROR = 1004
    TIMEOUT_ERROR = 1005


class MCPMessage:
    """MCP 메시지 기본 클래스"""
    
    def __init__(self, jsonrpc: str = "2.0"):
        self.jsonrpc = jsonrpc
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        raise NotImplementedError
    
    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class MCPRequest(MCPMessage):
    """
    MCP 요청 메시지
    
    Example:
        {
            "jsonrpc": "2.0",
            "id": "req_123",
            "method": "tools/call",
            "params": {
                "name": "search_documents",
                "arguments": {"query": "예산"}
            }
        }
    """
    
    def __init__(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None
    ):
        super().__init__()
        self.method = method
        self.params = params or {}
        self.id = id
    
    def to_dict(self) -> dict:
        data = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params
        }
        
        if self.id is not None:
            data["id"] = self.id
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MCPRequest':
        """딕셔너리에서 생성"""
        return cls(
            method=data["method"],
            params=data.get("params"),
            id=data.get("id")
        )


class MCPResponse(MCPMessage):
    """
    MCP 응답 메시지 (성공)
    
    Example:
        {
            "jsonrpc": "2.0",
            "id": "req_123",
            "result": {
                "total": 5,
                "results": [...]
            }
        }
    """
    
    def __init__(self, result: Any, id: Optional[str] = None):
        super().__init__()
        self.result = result
        self.id = id
    
    def to_dict(self) -> dict:
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "result": self.result
        }


class MCPError(MCPMessage):
    """
    MCP 에러 응답
    
    Example:
        {
            "jsonrpc": "2.0",
            "id": "req_123",
            "error": {
                "code": -32601,
                "message": "Method not found",
                "data": {"method": "unknown_tool"}
            }
        }
    """
    
    def __init__(
        self,
        code: int,
        message: str,
        data: Optional[Any] = None,
        id: Optional[str] = None
    ):
        super().__init__()
        self.code = code
        self.message = message
        self.data = data
        self.id = id
    
    def to_dict(self) -> dict:
        error = {
            "code": self.code,
            "message": self.message
        }
        
        if self.data is not None:
            error["data"] = self.data
        
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "error": error
        }


class MCPProtocol:
    """
    MCP 프로토콜 핸들러
    
    STDIO 기반 JSON-RPC 통신
    """
    
    def __init__(self):
        self.handlers = {}
    
    def register_handler(
        self,
        method: str,
        handler: Callable
    ):
        """
        메서드 핸들러 등록
        
        Args:
            method: 메서드 이름 (예: "tools/call")
            handler: 핸들러 함수 (params를 받아 result 반환)
        
        Example:
            def handle_tool_call(params):
                return {"result": "success"}
            
            protocol.register_handler("tools/call", handle_tool_call)
        """
        self.handlers[method] = handler
        logger.debug(f"Handler registered: {method}")
    
    def handle_request(self, request: MCPRequest) -> MCPMessage:
        """
        요청 처리
        
        Args:
            request: MCP 요청
        
        Returns:
            MCPResponse 또는 MCPError
        """
        method = request.method
        
        # 핸들러 확인
        if method not in self.handlers:
            return MCPError(
                code=JSONRPCError.METHOD_NOT_FOUND,
                message=f"Method not found: {method}",
                data={"method": method},
                id=request.id
            )
        
        # 핸들러 실행
        try:
            handler = self.handlers[method]
            result = handler(request.params)
            
            return MCPResponse(result=result, id=request.id)
        
        except Exception as e:
            logger.error(f"Handler error: {method} - {e}", exc_info=True)
            
            return MCPError(
                code=JSONRPCError.INTERNAL_ERROR,
                message=str(e),
                data={"exception": type(e).__name__},
                id=request.id
            )
    
    def send_message(self, message: MCPMessage):
        """
        메시지 전송 (STDIO)
        
        Args:
            message: MCP 메시지
        """
        json_str = message.to_json()
        sys.stdout.write(json_str + "\n")
        sys.stdout.flush()
        logger.debug(f"Message sent: {json_str[:100]}...")
    
    def receive_message(self) -> Optional[MCPRequest]:
        """
        메시지 수신 (STDIO)
        
        Returns:
            MCPRequest 또는 None (EOF)
        """
        try:
            line = sys.stdin.readline()
            
            if not line:
                return None
            
            data = json.loads(line)
            request = MCPRequest.from_dict(data)
            
            logger.debug(f"Message received: {request.method}")
            
            return request
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            
            error = MCPError(
                code=JSONRPCError.PARSE_ERROR,
                message="Parse error",
                data={"error": str(e)}
            )
            self.send_message(error)
            
            return None
        
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None
    
    def run(self):
        """
        메시지 처리 루프
        
        STDIO에서 메시지를 받아 처리하고 응답 전송
        """
        logger.info("MCP protocol started")
        
        while True:
            request = self.receive_message()
            
            if request is None:
                break
            
            response = self.handle_request(request)
            self.send_message(response)
        
        logger.info("MCP protocol stopped")


# 유틸리티 함수
def create_tool_call_request(
    tool_name: str,
    arguments: dict,
    request_id: Optional[str] = None
) -> MCPRequest:
    """
    Tool 호출 요청 생성
    
    Args:
        tool_name: Tool 이름
        arguments: Tool 인자
        request_id: 요청 ID
    
    Returns:
        MCPRequest
    """
    return MCPRequest(
        method="tools/call",
        params={
            "name": tool_name,
            "arguments": arguments
        },
        id=request_id
    )


def create_tools_list_request(request_id: Optional[str] = None) -> MCPRequest:
    """
    Tool 목록 요청 생성
    
    Returns:
        MCPRequest
    """
    return MCPRequest(
        method="tools/list",
        params={},
        id=request_id
    )


def parse_mcp_message(json_str: str) -> MCPMessage:
    """
    JSON 문자열을 MCP 메시지로 파싱
    
    Args:
        json_str: JSON 문자열
    
    Returns:
        MCPRequest, MCPResponse, 또는 MCPError
    """
    data = json.loads(json_str)
    
    if "method" in data:
        return MCPRequest.from_dict(data)
    elif "result" in data:
        return MCPResponse(result=data["result"], id=data.get("id"))
    elif "error" in data:
        error = data["error"]
        return MCPError(
            code=error["code"],
            message=error["message"],
            data=error.get("data"),
            id=data.get("id")
        )
    else:
        raise ValueError("Invalid MCP message")
```

### 7.3 사용 예제

```python
# 예제 1: MCP Server 구현
from shared.mcp_protocol import MCPProtocol

protocol = MCPProtocol()

# 핸들러 등록
def handle_tool_call(params):
    tool_name = params["name"]
    arguments = params["arguments"]
    
    # Tool 실행 로직
    if tool_name == "search_documents":
        query = arguments["query"]
        results = search(query)
        return {"total": len(results), "results": results}
    
    raise ValueError(f"Unknown tool: {tool_name}")

protocol.register_handler("tools/call", handle_tool_call)

# 메시지 처리 루프
protocol.run()


# 예제 2: MCP Client (Tool 호출)
import subprocess
import json

def call_mcp_tool(server_path, tool_name, arguments):
    """MCP Server에 Tool 호출"""
    
    process = subprocess.Popen(
        ["python", f"{server_path}/main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 요청 생성
    request = create_tool_call_request(
        tool_name=tool_name,
        arguments=arguments,
        request_id="req_001"
    )
    
    # 전송
    process.stdin.write((request.to_json() + "\n").encode())
    process.stdin.flush()
    
    # 응답 수신
    response_line = process.stdout.readline().decode()
    response = parse_mcp_message(response_line)
    
    process.terminate()
    
    if isinstance(response, MCPResponse):
        return response.result
    elif isinstance(response, MCPError):
        raise Exception(f"Error {response.code}: {response.message}")


# 예제 3: 에러 처리
from shared.mcp_protocol import MCPError, JSONRPCError

def handle_tool_call_with_error(params):
    try:
        # Tool 실행
        result = execute_tool(params)
        return result
    
    except PermissionError:
        # 권한 에러를 MCPError로 변환
        raise MCPError(
            code=JSONRPCError.PERMISSION_DENIED,
            message="Permission denied",
            data={"required_role": "staff"}
        )
    
    except Exception as e:
        # 일반 에러
        raise MCPError(
            code=JSONRPCError.INTERNAL_ERROR,
            message=str(e)
        )
```




## 8. utils.py

### 8.1 개요

**역할**: 공통 유틸리티 함수

**주요 기능**:
- 파일 처리
- 날짜/시간 처리
- 문자열 처리
- ID 생성
- 검증 함수

### 8.2 전체 코드

```python
# shared/utils.py
"""
공통 유틸리티 함수
"""

import os
import hashlib
import uuid
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import json
import yaml
import frontmatter
import logging

logger = logging.getLogger(__name__)


# ============================================
# ID 생성
# ============================================

def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    고유 ID 생성
    
    Args:
        prefix: 접두사 (예: "DOC", "USER")
        length: ID 길이
    
    Returns:
        str: "DOC_a1b2c3d4"
    
    Example:
        doc_id = generate_id("DOC", 8)
        user_id = generate_id("U", 3)
    """
    random_part = uuid.uuid4().hex[:length].upper()
    
    if prefix:
        return f"{prefix}_{random_part}"
    else:
        return random_part


def generate_request_id() -> str:
    """
    요청 ID 생성
    
    Returns:
        str: "req_1704700800_a1b2c3d4"
    """
    timestamp = int(datetime.now().timestamp())
    random_part = uuid.uuid4().hex[:8]
    return f"req_{timestamp}_{random_part}"


# ============================================
# 파일 처리
# ============================================

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    디렉토리 생성 (없으면)
    
    Args:
        path: 디렉토리 경로
    
    Returns:
        Path: 생성된 경로
    
    Example:
        doc_dir = ensure_dir("/app/poc/mcps/data/documents/team")
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
    """
    파일 읽기
    
    Args:
        file_path: 파일 경로
        encoding: 인코딩
    
    Returns:
        str: 파일 내용
    """
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()


def write_file(
    file_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8"
):
    """
    파일 쓰기
    
    Args:
        file_path: 파일 경로
        content: 내용
        encoding: 인코딩
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)


def read_json(file_path: Union[str, Path]) -> Any:
    """
    JSON 파일 읽기
    
    Args:
        file_path: JSON 파일 경로
    
    Returns:
        dict 또는 list
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(
    file_path: Union[str, Path],
    data: Any,
    indent: int = 2
):
    """
    JSON 파일 쓰기
    
    Args:
        file_path: 파일 경로
        data: 데이터
        indent: 들여쓰기
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def read_yaml(file_path: Union[str, Path]) -> dict:
    """
    YAML 파일 읽기
    
    Args:
        file_path: YAML 파일 경로
    
    Returns:
        dict
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_yaml(file_path: Union[str, Path], data: dict):
    """
    YAML 파일 쓰기
    
    Args:
        file_path: 파일 경로
        data: 데이터
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def read_markdown(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Markdown 파일 읽기 (frontmatter 포함)
    
    Args:
        file_path: Markdown 파일 경로
    
    Returns:
        {
            "metadata": {...},
            "content": "..."
        }
    
    Example:
        ---
        title: 문서 제목
        author: 홍길동
        ---
        
        # 본문
        내용...
    """
    post = frontmatter.load(file_path)
    
    return {
        "metadata": post.metadata,
        "content": post.content
    }


def write_markdown(
    file_path: Union[str, Path],
    content: str,
    metadata: Optional[dict] = None
):
    """
    Markdown 파일 쓰기 (frontmatter 포함)
    
    Args:
        file_path: 파일 경로
        content: 본문
        metadata: 메타데이터
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    post = frontmatter.Post(content, **(metadata or {}))
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    파일 크기 (bytes)
    
    Args:
        file_path: 파일 경로
    
    Returns:
        int: 파일 크기 (bytes)
    """
    return os.path.getsize(file_path)


def get_file_hash(file_path: Union[str, Path]) -> str:
    """
    파일 해시 (SHA256)
    
    Args:
        file_path: 파일 경로
    
    Returns:
        str: 해시값
    """
    sha256 = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def list_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    디렉토리 내 파일 목록
    
    Args:
        directory: 디렉토리 경로
        pattern: 파일 패턴 (예: "*.md")
        recursive: 하위 디렉토리 포함
    
    Returns:
        List[Path]: 파일 경로 목록
    """
    directory = Path(directory)
    
    if recursive:
        return list(directory.rglob(pattern))
    else:
        return list(directory.glob(pattern))


# ============================================
# 날짜/시간 처리
# ============================================

def now_iso() -> str:
    """
    현재 시간 (ISO 8601 형식)
    
    Returns:
        str: "2026-01-08T10:00:00Z"
    """
    return datetime.utcnow().isoformat() + "Z"


def now_timestamp() -> int:
    """
    현재 시간 (Unix timestamp)
    
    Returns:
        int: 1704700800
    """
    return int(datetime.now().timestamp())


def parse_datetime(date_str: str) -> datetime:
    """
    날짜 문자열 파싱
    
    Args:
        date_str: "2026-01-08T10:00:00Z" 또는 "2026-01-08"
    
    Returns:
        datetime
    """
    # ISO 8601
    if "T" in date_str:
        date_str = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(date_str)
    else:
        return datetime.strptime(date_str, "%Y-%m-%d")


def format_datetime(dt: datetime, format: str = "iso") -> str:
    """
    날짜 포맷팅
    
    Args:
        dt: datetime 객체
        format: "iso" | "date" | "datetime" | "timestamp"
    
    Returns:
        str
    """
    if format == "iso":
        return dt.isoformat() + "Z"
    elif format == "date":
        return dt.strftime("%Y-%m-%d")
    elif format == "datetime":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    elif format == "timestamp":
        return str(int(dt.timestamp()))
    else:
        return dt.isoformat()


def time_ago(dt: datetime) -> str:
    """
    상대 시간 표현
    
    Args:
        dt: datetime 객체
    
    Returns:
        str: "2시간 전", "3일 전", "1개월 전"
    """
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "방금 전"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}분 전"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}시간 전"
    elif seconds < 2592000:  # 30일
        days = int(seconds / 86400)
        return f"{days}일 전"
    elif seconds < 31536000:  # 365일
        months = int(seconds / 2592000)
        return f"{months}개월 전"
    else:
        years = int(seconds / 31536000)
        return f"{years}년 전"


def add_days(dt: datetime, days: int) -> datetime:
    """날짜에 일수 더하기"""
    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """날짜에 시간 더하기"""
    return dt + timedelta(hours=hours)


# ============================================
# 문자열 처리
# ============================================

def truncate(text: str, length: int = 100, suffix: str = "...") -> str:
    """
    문자열 자르기
    
    Args:
        text: 원본 텍스트
        length: 최대 길이
        suffix: 접미사
    
    Returns:
        str: 잘린 텍스트
    """
    if len(text) <= length:
        return text
    else:
        return text[:length] + suffix


def slugify(text: str) -> str:
    """
    URL/파일명 안전한 문자열로 변환
    
    Args:
        text: "2026년 예산 계획"
    
    Returns:
        str: "2026-년-예산-계획"
    """
    # 소문자 변환
    text = text.lower()
    
    # 공백을 하이픈으로
    text = re.sub(r'\s+', '-', text)
    
    # 특수문자 제거
    text = re.sub(r'[^\w\-가-힣]', '', text)
    
    # 연속 하이픈 제거
    text = re.sub(r'-+', '-', text)
    
    # 앞뒤 하이픈 제거
    text = text.strip('-')
    
    return text


def sanitize_filename(filename: str) -> str:
    """
    파일명 정리 (안전한 문자만)
    
    Args:
        filename: "문서/제목?.txt"
    
    Returns:
        str: "문서_제목.txt"
    """
    # 파일명에 사용 불가한 문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 공백을 언더스코어로
    filename = re.sub(r'\s+', '_', filename)
    
    return filename


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    키워드 추출 (간단한 버전)
    
    Args:
        text: 텍스트
        max_keywords: 최대 키워드 수
    
    Returns:
        List[str]: 키워드 목록
    """
    # 단어 추출 (한글, 영문, 숫자)
    words = re.findall(r'[가-힣]{2,}|[a-zA-Z]{3,}|\d+', text.lower())
    
    # 불용어 제거 (간단한 예시)
    stopwords = {'그리고', '그러나', '하지만', '또한', '및', '와', '과'}
    words = [w for w in words if w not in stopwords]
    
    # 빈도 계산
    from collections import Counter
    word_freq = Counter(words)
    
    # 상위 키워드 반환
    return [word for word, _ in word_freq.most_common(max_keywords)]


def highlight_text(text: str, keywords: List[str], tag: str = "mark") -> str:
    """
    텍스트에서 키워드 하이라이트
    
    Args:
        text: 원본 텍스트
        keywords: 하이라이트할 키워드 목록
        tag: HTML 태그
    
    Returns:
        str: 하이라이트된 텍스트
    """
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        text = pattern.sub(f"<{tag}>\\g<0></{tag}>", text)
    
    return text


# ============================================
# 검증
# ============================================

def is_valid_email(email: str) -> bool:
    """이메일 형식 검증"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_url(url: str) -> bool:
    """URL 형식 검증"""
    pattern = r'^https?://[^\s]+$'
    return re.match(pattern, url) is not None


def is_valid_json(json_str: str) -> bool:
    """JSON 형식 검증"""
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False


def validate_classification(classification: str) -> bool:
    """문서 등급 검증"""
    valid_classifications = ["public", "team", "confidential"]
    return classification in valid_classifications


def validate_role(role: str) -> bool:
    """역할 검증"""
    valid_roles = ["junior", "staff", "manager", "executive", "admin"]
    return role in valid_roles


# ============================================
# 데이터 변환
# ============================================

def bytes_to_human(bytes: int) -> str:
    """
    바이트를 사람이 읽기 쉬운 형식으로
    
    Args:
        bytes: 바이트 수
    
    Returns:
        str: "1.5 MB", "2.3 GB"
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    
    size = float(bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def dict_to_query_string(params: dict) -> str:
    """
    딕셔너리를 쿼리 스트링으로
    
    Args:
        params: {"page": 1, "limit": 20}
    
    Returns:
        str: "page=1&limit=20"
    """
    from urllib.parse import urlencode
    return urlencode(params)


def merge_dicts(*dicts: dict) -> dict:
    """
    여러 딕셔너리 병합
    
    Args:
        *dicts: 딕셔너리 목록
    
    Returns:
        dict: 병합된 딕셔너리
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """
    중첩 딕셔너리 평탄화
    
    Args:
        d: {"user": {"name": "홍길동", "age": 30}}
    
    Returns:
        {"user.name": "홍길동", "user.age": 30}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# ============================================
# 보안
# ============================================

def hash_password(password: str) -> str:
    """
    비밀번호 해시 (SHA256 + salt)
    
    Args:
        password: 평문 비밀번호
    
    Returns:
        str: 해시값
    """
    salt = uuid.uuid4().hex
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, hashed: str) -> bool:
    """
    비밀번호 검증
    
    Args:
        password: 평문 비밀번호
        hashed: 해시값 (salt$hash)
    
    Returns:
        bool: 일치 여부
    """
    try:
        salt, hash_value = hashed.split('$')
        computed = hashlib.sha256((password + salt).encode()).hexdigest()
        return computed == hash_value
    except:
        return False


def mask_sensitive_data(text: str, mask_char: str = "*") -> str:
    """
    민감 정보 마스킹
    
    Args:
        text: "홍길동"
    
    Returns:
        str: "홍*동"
    """
    if len(text) <= 2:
        return mask_char * len(text)
    else:
        return text[0] + mask_char * (len(text) - 2) + text[-1]


# ============================================
# 기타
# ============================================

def retry(
    func,
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    함수 재시도
    
    Args:
        func: 실행할 함수
        max_attempts: 최대 시도 횟수
        delay: 재시도 간격 (초)
        exceptions: 재시도할 예외 타입
    
    Returns:
        함수 실행 결과
    
    Example:
        result = retry(
            lambda: db.connect(),
            max_attempts=3,
            delay=2.0
        )
    """
    import time
    
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            logger.warning(
                f"Retry attempt {attempt + 1}/{max_attempts} failed: {e}"
            )
            
            if attempt < max_attempts - 1:
                time.sleep(delay)
    
    raise last_exception


def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """
    리스트를 청크로 분할
    
    Args:
        lst: [1, 2, 3, 4, 5, 6, 7]
        chunk_size: 3
    
    Returns:
        [[1, 2, 3], [4, 5, 6], [7]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deep_get(d: dict, path: str, default=None):
    """
    중첩 딕셔너리에서 안전하게 값 가져오기
    
    Args:
        d: {"user": {"profile": {"name": "홍길동"}}}
        path: "user.profile.name"
    
    Returns:
        "홍길동" 또는 default
    """
    keys = path.split('.')
    value = d
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def measure_time(func):
    """
    함수 실행 시간 측정 데코레이터
    
    Example:
        @measure_time
        def slow_function():
            time.sleep(1)
    """
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        
        logger.info(f"{func.__name__} took {elapsed:.2f}ms")
        
        return result
    
    return wrapper
```

### 8.3 사용 예제

```python
# 예제 1: ID 생성
from shared.utils import generate_id, generate_request_id

doc_id = generate_id("DOC", 8)  # "DOC_A1B2C3D4"
user_id = generate_id("U", 3)   # "U_A1B"
request_id = generate_request_id()  # "req_1704700800_a1b2c3d4"


# 예제 2: 파일 처리
from shared.utils import read_json, write_json, read_markdown, write_markdown

# JSON
config = read_json("config/settings.json")
write_json("output.json", {"key": "value"})

# Markdown
doc = read_markdown("documents/DOC001.md")
print(doc["metadata"]["title"])
print(doc["content"])

write_markdown(
    "documents/DOC002.md",
    "# 제목\n\n내용...",
    metadata={"title": "문서 제목", "author": "홍길동"}
)


# 예제 3: 날짜/시간
from shared.utils import now_iso, time_ago, parse_datetime

# 현재 시간
now = now_iso()  # "2026-01-08T10:00:00Z"

# 상대 시간
created_at = parse_datetime("2026-01-07T10:00:00Z")
print(time_ago(created_at))  # "1일 전"


# 예제 4: 문자열 처리
from shared.utils import truncate, slugify, extract_keywords

# 자르기
text = "매우 긴 텍스트입니다..."
print(truncate(text, 20))  # "매우 긴 텍스트입니다..."

# Slug
title = "2026년 예산 계획"
slug = slugify(title)  # "2026-년-예산-계획"

# 키워드 추출
content = "예산 계획 예산 실행 예산 분석"
keywords = extract_keywords(content, max_keywords=3)  # ["예산", "계획", "실행"]


# 예제 5: 검증
from shared.utils import validate_classification, validate_role

if not validate_classification(doc["classification"]):
    raise ValueError("Invalid classification")

if not validate_role(user["role"]):
    raise ValueError("Invalid role")


# 예제 6: 데이터 변환
from shared.utils import bytes_to_human, flatten_dict

# 파일 크기
size = bytes_to_human(1536000)  # "1.46 MB"

# 딕셔너리 평탄화
nested = {"user": {"profile": {"name": "홍길동"}}}
flat = flatten_dict(nested)  # {"user.profile.name": "홍길동"}


# 예제 7: 재시도
from shared.utils import retry

def unreliable_function():
    # 가끔 실패하는 함수
    import random
    if random.random() < 0.7:
        raise ConnectionError("Network error")
    return "success"

result = retry(
    unreliable_function,
    max_attempts=5,
    delay=1.0,
    exceptions=(ConnectionError,)
)


# 예제 8: 데코레이터
from shared.utils import measure_time

@measure_time
def slow_function():
    import time
    time.sleep(1)
    return "done"

result = slow_function()
# 로그: slow_function took 1000.00ms
```

***

## 9. cache.py

### 9.1 개요

**역할**: 메모리 기반 캐시 시스템

**주요 기능**:
- TTL (Time To Live) 지원
- LRU (Least Recently Used) 정책
- 캐시 무효화
- 통계

### 9.2 전체 코드

```python
# shared/cache.py
"""
메모리 기반 캐시 시스템
"""

from typing import Any, Optional, Dict, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging
import threading

logger = logging.getLogger(__name__)


class CacheEntry:
    """캐시 항목"""
    
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl)
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """만료 여부"""
        return datetime.now() > self.expires_at
    
    def access(self):
        """접근 기록"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class Cache:
    """
    메모리 캐시
    
    특징:
    - TTL 지원
    - LRU 정책
    - 스레드 안전
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        초기화
        
        Args:
            max_size: 최대 캐시 항목 수
            default_ttl: 기본 TTL (초)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = threading.Lock()
        
        # 통계
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시 조회
        
        Args:
            key: 캐시 키
        
        Returns:
            값 또는 None (미스)
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            # 만료 확인
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                logger.debug(f"Cache expired: {key}")
                return None
            
            # 접근 기록
            entry.access()
            self.hits += 1
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        캐시 저장
        
        Args:
            key: 캐시 키
            value: 값
            ttl: TTL (초), None이면 default_ttl
        """
        with self.lock:
            # TTL 설정
            if ttl is None:
                ttl = self.default_ttl
            
            # 크기 초과 시 LRU 제거
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            # 캐시 저장
            self.cache[key] = CacheEntry(value, ttl)
            
            logger.debug(f"Cache set: {key} (ttl={ttl}s)")
    
    def delete(self, key: str):
        """캐시 삭제"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache deleted: {key}")
    
    def clear(self):
        """전체 캐시 삭제"""
        with self.lock:
            self.cache.clear()
            logger.info("Cache cleared")
    
    def exists(self, key: str) -> bool:
        """캐시 존재 여부"""
        with self.lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            
            if entry.is_expired():
                del self.cache[key]
                return False
            
            return True
    
    def _evict_lru(self):
        """LRU 항목 제거"""
        if not self.cache:
            return
        
        # 가장 오래전에 접근한 항목 찾기
        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed
        )
        
        del self.cache[lru_key]
        self.evictions += 1
        
        logger.debug(f"Cache evicted (LRU): {lru_key}")
    
    def cleanup_expired(self):
        """만료된 항목 정리"""
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계
        
        Returns:
            {
                "size": 100,
                "max_size": 1000,
                "hits": 500,
                "misses": 50,
                "hit_rate": 0.91,
                "evictions": 10
            }
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(hit_rate, 2),
                "evictions": self.evictions
            }
    
    def reset_stats(self):
        """통계 초기화"""
        with self.lock:
            self.hits = 0
            self.misses = 0
            self.evictions = 0


# 전역 캐시 인스턴스
_default_cache = Cache()


def get_cache() -> Cache:
    """기본 캐시 인스턴스 가져오기"""
    return _default_cache


# 캐시 데코레이터
def cached(ttl: int = 300, key_func: Optional[Callable] = None):
    """
    함수 결과 캐싱 데코레이터
    
    Args:
        ttl: TTL (초)
        key_func: 캐시 키 생성 함수 (args, kwargs를 받아 문자열 반환)
    
    Example:
        @cached(ttl=600)
        def get_user(user_id):
            return db.query("SELECT * FROM users WHERE id = ?", user_id)
        
        # 커스텀 키
        @cached(ttl=300, key_func=lambda args, kwargs: f"user:{args[0]}")
        def get_user(user_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # 캐시 키 생성
            if key_func:
                cache_key = key_func(args, kwargs)
            else:
                # 기본 키: 함수명 + 인자
                import pickle
                args_key = pickle.dumps((args, kwargs))
                cache_key = f"{func.__module__}.{func.__name__}:{args_key.hex()}"
            
            # 캐시 조회
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result
            
            # 캐시 미스 - 함수 실행
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # 캐시 저장
            cache.set(cache_key, result, ttl)
            
            return result
        
        # 캐시 무효화 함수 추가
        def invalidate(*args, **kwargs):
            cache = get_cache()
            if key_func:
                cache_key = key_func(args, kwargs)
            else:
                import pickle
                args_key = pickle.dumps((args, kwargs))
                cache_key = f"{func.__module__}.{func.__name__}:{args_key.hex()}"
            
            cache.delete(cache_key)
            logger.debug(f"Cache invalidated: {cache_key}")
        
        wrapper.invalidate = invalidate
        
        return wrapper
    
    return decorator


# 특화된 캐시
class PermissionCache(Cache):
    """권한 캐시 (짧은 TTL)"""
    
    def __init__(self):
        super().__init__(max_size=500, default_ttl=60)


class UserCache(Cache):
    """사용자 캐시"""
    
    def __init__(self):
        super().__init__(max_size=1000, default_ttl=300)


class ToolCache(Cache):
    """Tool 메타데이터 캐시 (긴 TTL)"""
    
    def __init__(self):
        super().__init__(max_size=200, default_ttl=3600)
```

### 9.3 사용 예제

```python
# 예제 1: 기본 사용
from shared.cache import Cache

cache = Cache(max_size=100, default_ttl=300)

# 저장
cache.set("user:U001", {"name": "홍길동", "role": "staff"})

# 조회
user = cache.get("user:U001")
print(user["name"])  # "홍길동"

# 삭제
cache.delete("user:U001")

# 전체 삭제
cache.clear()


# 예제 2: 데코레이터
from shared.cache import cached
from shared.database import DatabaseManager

db = DatabaseManager(config)

@cached(ttl=600)
def get_user(user_id):
    """사용자 조회 (10분 캐싱)"""
    result = db.execute_query(
        "SELECT * FROM users WHERE id = %s",
        (user_id,)
    )
    return result[0] if result else None

# 첫 호출 - DB 조회
user = get_user("U001")

# 두 번째 호출 - 캐시에서 반환 (빠름)
user = get_user("U001")

# 캐시 무효화
get_user.invalidate("U001")


# 예제 3: 커스텀 키 함수
@cached(
    ttl=300,
    key_func=lambda args, kwargs: f"doc:{args[0]}:{kwargs.get('version', 1)}"
)
def get_document(doc_id, version=1):
    return db.execute_query(
        "SELECT * FROM documents WHERE id = %s AND version = %s",
        (doc_id, version)
    )


# 예제 4: 캐시 통계
from shared.cache import get_cache

cache = get_cache()

stats = cache.get_stats()
print(f"캐시 크기: {stats['size']}/{stats['max_size']}")
print(f"히트율: {stats['hit_rate'] * 100:.1f}%")
print(f"히트: {stats['hits']}, 미스: {stats['misses']}")


# 예제 5: 만료된 항목 정리
cache.cleanup_expired()


# 예제 6: 특화된 캐시
from shared.cache import PermissionCache, UserCache, ToolCache

permission_cache = PermissionCache()
user_cache = UserCache()
tool_cache = ToolCache()

# 권한 캐싱 (짧은 TTL: 60초)
permission_cache.set(
    f"perm:{user_id}:{doc_id}",
    {"can_read": True, "can_write": False}
)

# 사용자 캐싱 (중간 TTL: 300초)
user_cache.set(f"user:{user_id}", user_data)

# Tool 메타데이터 캐싱 (긴 TTL: 3600초)
tool_cache.set(f"tool:{tool_name}", tool_metadata)
```

***

## 10. 테스트 전략

### 10.1 단위 테스트

```python
# tests/unit/test_database.py
"""
database.py 단위 테스트
"""

import pytest
from shared.database import DatabaseManager, QueryError

@pytest.fixture
def db():
    """테스트용 DB 연결"""
    config = {
        "host": "localhost",
        "port": 3306,
        "database": "test_mcps_db",
        "user": "test_user",
        "password": "test_password",
        "charset": "utf8mb4",
        "pool_size": {"min": 1, "max": 5}
    }
    
    db = DatabaseManager(config)
    yield db
    db.close()


def test_execute_query(db):
    """쿼리 실행 테스트"""
    result = db.execute_query("SELECT 1 AS num")
    assert result[0]["num"] == 1


def test_execute_insert(db):
    """INSERT 테스트"""
    doc_id = db.execute_insert(
        "INSERT INTO documents (id, title) VALUES (%s, %s)",
        ("DOC999", "테스트 문서")
    )
    assert doc_id > 0


def test_transaction(db):
    """트랜잭션 테스트"""
    with db.transaction() as tx:
        tx.execute(
            "INSERT INTO users (id, name) VALUES (%s, %s)",
            ("U999", "테스트")
        )
        
        result = tx.execute("SELECT * FROM users WHERE id = %s", ("U999",))
        assert len(result) == 1


def test_health_check(db):
    """헬스 체크 테스트"""
    assert db.health_check() == True
```

```python
# tests/unit/test_permissions.py
"""
permissions.py 단위 테스트
"""

import pytest
from shared.permissions import PermissionEngine, PermissionDeniedError

@pytest.fixture
def perm_engine():
    return PermissionEngine()


def test_check_document_permission_public(perm_engine):
    """Public 문서 접근 테스트"""
    doc = {
        "id": "DOC001",
        "classification": "public",
        "team": None
    }
    
    # Junior도 읽기 가능
    assert perm_engine.check_document_permission(
        "U001", "junior", None, doc, "read"
    ) == True
    
    # Junior는 쓰기 불가
    assert perm_engine.check_document_permission(
        "U001", "junior", None, doc, "update"
    ) == False


def test_check_document_permission_team(perm_engine):
    """Team 문서 접근 테스트"""
    doc = {
        "id": "DOC002",
        "classification": "team",
        "team": "dev_team"
    }
    
    # 같은 팀 - 읽기 가능
    assert perm_engine.check_document_permission(
        "U002", "staff", "dev_team", doc, "read"
    ) == True
    
    # 다른 팀 - 읽기 불가
    assert perm_engine.check_document_permission(
        "U003", "staff", "hr_team", doc, "read"
    ) == False


def test_check_tool_permission(perm_engine):
    """Tool 실행 권한 테스트"""
    # Staff는 search_documents 실행 가능
    assert perm_engine.check_tool_permission(
        "staff", "search_documents", "execute"
    ) == True
    
    # Manager는 모든 Tool 실행 가능
    assert perm_engine.check_tool_permission(
        "manager", "any_tool", "execute"
    ) == True


def test_require_permission(perm_engine):
    """권한 강제 테스트"""
    doc = {
        "id": "DOC003",
        "classification": "confidential",
        "team": None
    }
    
    # Staff는 confidential 접근 불가 - 예외 발생
    with pytest.raises(PermissionDeniedError):
        perm_engine.require_permission(
            "U004", "staff", "dev_team",
            "document", doc, "read"
        )
```

### 10.2 통합 테스트

```python
# tests/integration/test_document_workflow.py
"""
문서 워크플로우 통합 테스트
"""

import pytest
from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from shared.permissions import PermissionEngine

@pytest.fixture
def components():
    """테스트용 컴포넌트"""
    db = DatabaseManager(test_db_config)
    es = ElasticsearchManager(test_es_config)
    perm = PermissionEngine()
    
    yield {"db": db, "es": es, "perm": perm}
    
    db.close()
    es.close()


def test_create_and_search_document(components):
    """문서 생성 및 검색 통합 테스트"""
    db = components["db"]
    es = components["es"]
    
    # 1. 문서 생성 (DB)
    doc_id = generate_id("DOC", 8)
    db.execute_insert(
        queries.CREATE_DOCUMENT,
        (doc_id, "테스트 문서", "내용...", "public", "general", "U001", None, None, 1)
    )
    
    # 2. 문서 색인 (ES)
    es.index_document(
        "documents",
        doc_id,
        {
            "doc_id": doc_id,
            "title": "테스트 문서",
            "content": "내용...",
            "classification": "public"
        }
    )
    
    # 3. 검색
    result = es.search_documents(
        query_text="테스트",
        classification=["public"],
        size=10
    )
    
    assert result["total"] >= 1
    assert any(r["doc_id"] == doc_id for r in result["results"])
```

### 10.3 성능 테스트

```python
# tests/performance/test_cache_performance.py
"""
캐시 성능 테스트
"""

import time
from shared.cache import Cache, cached

def test_cache_hit_performance():
    """캐시 히트 성능"""
    cache = Cache()
    
    # 캐시 저장
    for i in range(1000):
        cache.set(f"key:{i}", {"value": i})
    
    # 조회 성능 측정
    start = time.time()
    
    for i in range(1000):
        value = cache.get(f"key:{i}")
        assert value is not None
    
    elapsed = time.time() - start
    
    print(f"1000 cache hits: {elapsed:.3f}s")
    assert elapsed < 0.1  # 100ms 이내


def test_function_cache_performance():
    """함수 캐싱 성능"""
    call_count = 0
    
    @cached(ttl=60)
    def expensive_function(x):
        nonlocal call_count
        call_count += 1
        time.sleep(0.1)  # 비용이 큰 작업 시뮬레이션
        return x * 2
    
    # 첫 호출 - 느림
    start = time.time()
    result = expensive_function(5)
    first_call_time = time.time() - start
    
    # 두 번째 호출 - 빠름 (캐시)
    start = time.time()
    result = expensive_function(5)
    second_call_time = time.time() - start
    
    assert call_count == 1  # 함수는 한 번만 실행
    assert second_call_time < first_call_time / 10  # 10배 이상 빠름
```

***

## 11. 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-08 | AI Assistant | 초안 작성 |

***

## 12. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **작성자** | | | |
| **검토자** | | | |
| **승인자** | | | |

***

