"""
데이터베이스 관리자
===================

MariaDB 연결 풀 및 쿼리 실행을 담당합니다.

특징:
- DBUtils를 이용한 Connection Pooling
- 트랜잭션 지원 (컨텍스트 매니저)
- 자동 재연결
- SQL Injection 방지 (파라미터화된 쿼리)

사용 예:
    from shared.database import DatabaseManager
    
    db = DatabaseManager()
    
    # 조회
    rows = db.fetch_all("SELECT * FROM users WHERE status = %s", ["active"])
    row = db.fetch_one("SELECT * FROM users WHERE user_id = %s", ["U001"])
    
    # 삽입/수정/삭제
    affected = db.execute("UPDATE users SET name = %s WHERE user_id = %s", ["홍길동", "U001"])
    last_id = db.insert("INSERT INTO users (name) VALUES (%s)", ["홍길동"])
    
    # 트랜잭션
    with db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
        cursor.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
"""

from typing import Any, Optional, Dict, List, Tuple, Union, Generator
from contextlib import contextmanager
from datetime import datetime
import threading
import logging
import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB

logger = logging.getLogger(__name__)


# ===========================================
# 타입 정의
# ===========================================

Row = Dict[str, Any]
Rows = List[Row]
QueryParams = Union[List[Any], Tuple[Any, ...], Dict[str, Any], None]


# ===========================================
# 데이터베이스 관리자
# ===========================================

class DatabaseManager:
    """
    MariaDB 데이터베이스 관리자
    
    Connection Pool을 관리하고 쿼리 실행을 담당합니다.
    ORM을 사용하지 않고 직접 SQL을 실행합니다.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "",
        charset: str = "utf8mb4",
        ssl: bool = False,
        min_connections: int = 5,
        max_connections: int = 20,
        max_idle_time: int = 3600,
        connect_timeout: int = 10,
        **kwargs
    ):
        """
        초기화
        
        Args:
            host: DB 호스트
            port: DB 포트
            user: 사용자명
            password: 비밀번호
            database: 데이터베이스명
            charset: 문자셋
            ssl: SSL 사용 여부
            min_connections: 최소 연결 수
            max_connections: 최대 연결 수
            max_idle_time: 최대 유휴 시간 (초)
            connect_timeout: 연결 타임아웃 (초)
        """
        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "charset": charset,
            "connect_timeout": connect_timeout,
            "cursorclass": DictCursor,
            "autocommit": True,
        }
        
        # SSL 설정
        if ssl:
            self.config["ssl"] = {"ssl": True}
        
        # 추가 옵션
        self.config.update(kwargs)
        
        # Connection Pool 생성
        self.pool = PooledDB(
            creator=pymysql,
            mincached=min_connections,
            maxcached=max_connections,
            maxshared=0,  # 공유 안함 (스레드 안전)
            maxconnections=max_connections,
            blocking=True,
            maxusage=None,
            setsession=["SET NAMES utf8mb4"],
            ping=1,  # 연결 확인
            **self.config
        )
        
        # 통계
        self._lock = threading.Lock()
        self._query_count = 0
        self._error_count = 0
        
        logger.info(f"DatabaseManager initialized: {host}:{port}/{database}")
    
    # ===========================================
    # 연결 관리
    # ===========================================
    
    def get_connection(self):
        """
        Connection Pool에서 연결 가져오기
        
        Returns:
            pymysql.Connection
        """
        return self.pool.connection()
    
    @contextmanager
    def connection(self):
        """
        연결 컨텍스트 매니저
        
        Example:
            with db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
        """
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def transaction(self):
        """
        트랜잭션 컨텍스트 매니저
        
        자동 커밋을 비활성화하고, 성공 시 커밋, 실패 시 롤백합니다.
        
        Example:
            with db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users ...")
                cursor.execute("INSERT INTO logs ...")
        """
        conn = self.get_connection()
        conn.autocommit(False)
        
        try:
            yield conn
            conn.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            conn.rollback()
            logger.warning(f"Transaction rolled back: {e}")
            raise
        finally:
            conn.autocommit(True)
            conn.close()
    
    # ===========================================
    # 쿼리 실행
    # ===========================================
    
    def execute(
        self,
        query: str,
        params: QueryParams = None,
        conn=None
    ) -> int:
        """
        쿼리 실행 (INSERT, UPDATE, DELETE 등)
        
        Args:
            query: SQL 쿼리 (파라미터는 %s 또는 %(name)s)
            params: 쿼리 파라미터
            conn: 기존 연결 (트랜잭션용)
        
        Returns:
            영향받은 행 수
        """
        own_connection = conn is None
        
        if own_connection:
            conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            affected = cursor.rowcount
            
            with self._lock:
                self._query_count += 1
            
            logger.debug(f"Execute: affected={affected}, query={query[:100]}")
            
            return affected
        
        except Exception as e:
            with self._lock:
                self._error_count += 1
            logger.error(f"Execute error: {e}, query={query[:100]}")
            raise
        
        finally:
            if own_connection:
                conn.close()
    
    def execute_many(
        self,
        query: str,
        params_list: List[QueryParams],
        conn=None
    ) -> int:
        """
        다중 쿼리 실행 (배치)
        
        Args:
            query: SQL 쿼리
            params_list: 파라미터 리스트
            conn: 기존 연결
        
        Returns:
            영향받은 행 수
        """
        own_connection = conn is None
        
        if own_connection:
            conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            affected = cursor.rowcount
            
            with self._lock:
                self._query_count += 1
            
            logger.debug(f"ExecuteMany: affected={affected}, count={len(params_list)}")
            
            return affected
        
        except Exception as e:
            with self._lock:
                self._error_count += 1
            logger.error(f"ExecuteMany error: {e}")
            raise
        
        finally:
            if own_connection:
                conn.close()
    
    def insert(
        self,
        query: str,
        params: QueryParams = None,
        conn=None
    ) -> int:
        """
        INSERT 쿼리 실행
        
        Returns:
            마지막 삽입 ID (AUTO_INCREMENT)
        """
        own_connection = conn is None
        
        if own_connection:
            conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            last_id = cursor.lastrowid
            
            with self._lock:
                self._query_count += 1
            
            logger.debug(f"Insert: last_id={last_id}")
            
            return last_id
        
        except Exception as e:
            with self._lock:
                self._error_count += 1
            logger.error(f"Insert error: {e}")
            raise
        
        finally:
            if own_connection:
                conn.close()
    
    def fetch_one(
        self,
        query: str,
        params: QueryParams = None,
        conn=None
    ) -> Optional[Row]:
        """
        단일 행 조회
        
        Returns:
            결과 행 (딕셔너리) 또는 None
        """
        own_connection = conn is None
        
        if own_connection:
            conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            with self._lock:
                self._query_count += 1
            
            return row
        
        except Exception as e:
            with self._lock:
                self._error_count += 1
            logger.error(f"FetchOne error: {e}")
            raise
        
        finally:
            if own_connection:
                conn.close()
    
    def fetch_all(
        self,
        query: str,
        params: QueryParams = None,
        conn=None
    ) -> Rows:
        """
        전체 행 조회
        
        Returns:
            결과 행 리스트
        """
        own_connection = conn is None
        
        if own_connection:
            conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            with self._lock:
                self._query_count += 1
            
            logger.debug(f"FetchAll: rows={len(rows)}")
            
            return rows
        
        except Exception as e:
            with self._lock:
                self._error_count += 1
            logger.error(f"FetchAll error: {e}")
            raise
        
        finally:
            if own_connection:
                conn.close()
    
    def fetch_iter(
        self,
        query: str,
        params: QueryParams = None,
        batch_size: int = 1000
    ) -> Generator[Row, None, None]:
        """
        대용량 데이터 조회 (이터레이터)
        
        메모리 효율적으로 대량 데이터를 처리합니다.
        
        Args:
            query: SQL 쿼리
            params: 파라미터
            batch_size: 배치 크기
        
        Yields:
            결과 행
        
        Example:
            for row in db.fetch_iter("SELECT * FROM large_table"):
                process(row)
        """
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                for row in rows:
                    yield row
        
        except Exception as e:
            logger.error(f"FetchIter error: {e}")
            raise
        
        finally:
            conn.close()
    
    def fetch_value(
        self,
        query: str,
        params: QueryParams = None,
        default: Any = None
    ) -> Any:
        """
        단일 값 조회
        
        Returns:
            첫 번째 컬럼의 값 또는 default
        
        Example:
            count = db.fetch_value("SELECT COUNT(*) as cnt FROM users", default=0)
        """
        row = self.fetch_one(query, params)
        
        if row is None:
            return default
        
        # 첫 번째 값 반환
        return list(row.values())[0] if row else default
    
    def exists(self, query: str, params: QueryParams = None) -> bool:
        """
        존재 여부 확인
        
        Example:
            if db.exists("SELECT 1 FROM users WHERE email = %s", [email]):
                print("이미 존재합니다")
        """
        row = self.fetch_one(query, params)
        return row is not None
    
    def count(self, table: str, where: str = "", params: QueryParams = None) -> int:
        """
        테이블 행 수 조회
        
        Example:
            total = db.count("users")
            active = db.count("users", "status = %s", ["active"])
        """
        query = f"SELECT COUNT(*) as cnt FROM {table}"
        if where:
            query += f" WHERE {where}"
        
        return self.fetch_value(query, params, default=0)
    
    # ===========================================
    # 헬퍼 메서드
    # ===========================================
    
    def table_exists(self, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        query = """
            SELECT COUNT(*) as cnt 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """
        return self.fetch_value(query, [self.config["database"], table_name], 0) > 0
    
    def get_columns(self, table_name: str) -> List[str]:
        """테이블 컬럼 목록"""
        query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """
        rows = self.fetch_all(query, [self.config["database"], table_name])
        return [row["column_name"] for row in rows]
    
    # ===========================================
    # CRUD 헬퍼
    # ===========================================
    
    def insert_dict(
        self,
        table: str,
        data: Dict[str, Any],
        conn=None
    ) -> int:
        """
        딕셔너리 삽입
        
        Args:
            table: 테이블명
            data: 삽입할 데이터
            conn: 연결
        
        Returns:
            마지막 삽입 ID
        
        Example:
            user_id = db.insert_dict("users", {
                "name": "홍길동",
                "email": "hong@example.com",
                "status": "active"
            })
        """
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["%s"] * len(columns))
        
        query = f"""
            INSERT INTO {table} ({", ".join(columns)})
            VALUES ({placeholders})
        """
        
        return self.insert(query, values, conn)
    
    def update_dict(
        self,
        table: str,
        data: Dict[str, Any],
        where: str,
        where_params: QueryParams = None,
        conn=None
    ) -> int:
        """
        딕셔너리 업데이트
        
        Args:
            table: 테이블명
            data: 업데이트할 데이터
            where: WHERE 절
            where_params: WHERE 파라미터
            conn: 연결
        
        Returns:
            영향받은 행 수
        
        Example:
            affected = db.update_dict(
                "users",
                {"name": "홍길동", "updated_at": datetime.now()},
                "user_id = %s",
                ["U001"]
            )
        """
        set_clause = ", ".join([f"{col} = %s" for col in data.keys()])
        values = list(data.values())
        
        if where_params:
            if isinstance(where_params, (list, tuple)):
                values.extend(where_params)
            else:
                values.append(where_params)
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        return self.execute(query, values, conn)
    
    def delete(
        self,
        table: str,
        where: str,
        params: QueryParams = None,
        conn=None
    ) -> int:
        """
        삭제
        
        Example:
            affected = db.delete("users", "user_id = %s", ["U001"])
        """
        query = f"DELETE FROM {table} WHERE {where}"
        return self.execute(query, params, conn)
    
    def upsert(
        self,
        table: str,
        data: Dict[str, Any],
        update_columns: Optional[List[str]] = None,
        conn=None
    ) -> int:
        """
        Upsert (INSERT ... ON DUPLICATE KEY UPDATE)
        
        Args:
            table: 테이블명
            data: 삽입할 데이터
            update_columns: 업데이트할 컬럼 (None이면 모든 컬럼)
        
        Returns:
            영향받은 행 수
        """
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["%s"] * len(columns))
        
        if update_columns is None:
            update_columns = columns
        
        update_clause = ", ".join([f"{col} = VALUES({col})" for col in update_columns])
        
        query = f"""
            INSERT INTO {table} ({", ".join(columns)})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_clause}
        """
        
        return self.execute(query, values, conn)
    
    # ===========================================
    # 페이지네이션
    # ===========================================
    
    def fetch_page(
        self,
        query: str,
        params: QueryParams = None,
        page: int = 1,
        page_size: int = 20,
        count_query: Optional[str] = None,
        count_params: QueryParams = None
    ) -> Dict[str, Any]:
        """
        페이지네이션 조회
        
        Args:
            query: 기본 쿼리 (ORDER BY 필수)
            params: 쿼리 파라미터
            page: 페이지 번호 (1부터)
            page_size: 페이지당 항목 수
            count_query: 총 개수 쿼리 (None이면 자동 생성)
            count_params: 총 개수 쿼리 파라미터
        
        Returns:
            {
                "items": [...],
                "total": 전체 개수,
                "page": 현재 페이지,
                "page_size": 페이지 크기,
                "total_pages": 전체 페이지 수
            }
        """
        # 총 개수 조회
        if count_query is None:
            # 간단한 카운트 쿼리 생성 시도
            # SELECT 부분을 COUNT(*)로 대체
            count_query = f"SELECT COUNT(*) as cnt FROM ({query}) as subquery"
            count_params = params
        
        total = self.fetch_value(count_query, count_params, 0)
        
        # 페이지 계산
        offset = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        # 데이터 조회
        paginated_query = f"{query} LIMIT %s OFFSET %s"
        
        if params:
            if isinstance(params, (list, tuple)):
                paginated_params = list(params) + [page_size, offset]
            else:
                paginated_params = [params, page_size, offset]
        else:
            paginated_params = [page_size, offset]
        
        items = self.fetch_all(paginated_query, paginated_params)
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    
    # ===========================================
    # 통계
    # ===========================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        통계 조회
        
        Returns:
            {
                "query_count": 쿼리 실행 횟수,
                "error_count": 에러 횟수,
                "pool_size": 현재 풀 크기
            }
        """
        with self._lock:
            return {
                "query_count": self._query_count,
                "error_count": self._error_count,
                "pool_size": self.pool._connections,  # 근사값
            }
    
    def reset_stats(self):
        """통계 초기화"""
        with self._lock:
            self._query_count = 0
            self._error_count = 0
    
    # ===========================================
    # 리소스 정리
    # ===========================================
    
    def close(self):
        """연결 풀 종료"""
        if self.pool:
            self.pool.close()
            logger.info("DatabaseManager closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ===========================================
    # 헬스 체크
    # ===========================================
    
    def ping(self) -> bool:
        """연결 상태 확인"""
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        상세 헬스 체크
        
        Returns:
            {
                "status": "healthy" | "unhealthy",
                "database": 데이터베이스명,
                "version": MariaDB 버전,
                "uptime": 업타임 (초),
                "connections": 연결 정보
            }
        """
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                
                # 버전
                cursor.execute("SELECT VERSION() as version")
                version = cursor.fetchone()["version"]
                
                # 업타임
                cursor.execute("SHOW STATUS LIKE 'Uptime'")
                uptime = int(cursor.fetchone()["Value"])
                
                # 연결 정보
                cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                threads = int(cursor.fetchone()["Value"])
                
                return {
                    "status": "healthy",
                    "database": self.config["database"],
                    "version": version,
                    "uptime": uptime,
                    "connections": {
                        "active": threads,
                        "pool_min": self.pool._mincached,
                        "pool_max": self.pool._maxcached,
                    }
                }
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# ===========================================
# Public API
# ===========================================

__all__ = [
    "DatabaseManager",
    "Row",
    "Rows",
    "QueryParams",
]
