"""
공통 유틸리티 함수
==================

모든 컴포넌트에서 사용하는 범용 유틸리티 함수를 제공합니다.

기능:
- ID 생성
- 파일 처리 (JSON, YAML, Markdown)
- 날짜/시간 처리
- 문자열 처리
- 검증 함수
- 데이터 변환
- 보안 유틸리티
- 재시도 로직

사용 예:
    from shared.utils import generate_id, read_json, now_iso
    
    doc_id = generate_id("DOC", 8)
    config = read_json("config/settings.json")
    timestamp = now_iso()
"""

import os
import hashlib
import uuid
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Callable
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


# ===========================================
# ID 생성
# ===========================================

def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    고유 ID 생성
    
    Args:
        prefix: 접두사 (예: "DOC", "USER")
        length: ID 길이 (최대 32)
    
    Returns:
        str: "DOC_A1B2C3D4" 또는 "A1B2C3D4"
    
    Example:
        doc_id = generate_id("DOC", 8)   # "DOC_A1B2C3D4"
        user_id = generate_id("U", 3)    # "U_A1B"
        simple_id = generate_id()        # "A1B2C3D4"
    """
    random_part = uuid.uuid4().hex[:min(length, 32)].upper()
    
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


def generate_uuid() -> str:
    """UUID4 생성"""
    return str(uuid.uuid4())


# ===========================================
# 파일 처리
# ===========================================

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    디렉토리 생성 (없으면)
    
    Args:
        path: 디렉토리 경로
    
    Returns:
        Path: 생성된 경로
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
    """파일 읽기"""
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()


def write_file(
    file_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8"
):
    """파일 쓰기"""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)


def read_json(file_path: Union[str, Path]) -> Any:
    """JSON 파일 읽기"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(
    file_path: Union[str, Path],
    data: Any,
    indent: int = 2
):
    """JSON 파일 쓰기"""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def read_yaml(file_path: Union[str, Path]) -> dict:
    """YAML 파일 읽기"""
    try:
        import yaml
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed. Install with: pip install PyYAML")
        raise


def write_yaml(file_path: Union[str, Path], data: dict):
    """YAML 파일 쓰기"""
    try:
        import yaml
        file_path = Path(file_path)
        ensure_dir(file_path.parent)
        
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    except ImportError:
        logger.warning("PyYAML not installed. Install with: pip install PyYAML")
        raise


def read_markdown(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Markdown 파일 읽기 (frontmatter 포함)
    
    Returns:
        {
            "metadata": {...},
            "content": "..."
        }
    """
    try:
        import frontmatter
        post = frontmatter.load(file_path)
        return {
            "metadata": post.metadata,
            "content": post.content
        }
    except ImportError:
        logger.warning("python-frontmatter not installed")
        # fallback: 단순 읽기
        content = read_file(file_path)
        return {"metadata": {}, "content": content}


def write_markdown(
    file_path: Union[str, Path],
    content: str,
    metadata: Optional[dict] = None
):
    """Markdown 파일 쓰기 (frontmatter 포함)"""
    try:
        import frontmatter
        file_path = Path(file_path)
        ensure_dir(file_path.parent)
        
        post = frontmatter.Post(content, **(metadata or {}))
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
    except ImportError:
        # fallback: frontmatter 없이 쓰기
        write_file(file_path, content)


def get_file_size(file_path: Union[str, Path]) -> int:
    """파일 크기 (bytes)"""
    return os.path.getsize(file_path)


def get_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """파일 해시"""
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def list_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    디렉토리 내 파일 목록
    
    Args:
        directory: 디렉토리 경로
        pattern: 파일 패턴 (예: "*.md", "*.json")
        recursive: 하위 디렉토리 포함
    """
    directory = Path(directory)
    
    if recursive:
        return list(directory.rglob(pattern))
    else:
        return list(directory.glob(pattern))


# ===========================================
# 날짜/시간 처리
# ===========================================

def now_iso() -> str:
    """현재 시간 (ISO 8601 형식)"""
    return datetime.utcnow().isoformat() + "Z"


def now_timestamp() -> int:
    """현재 시간 (Unix timestamp)"""
    return int(datetime.now().timestamp())


def now_datetime() -> datetime:
    """현재 시간 (datetime 객체)"""
    return datetime.now()


def parse_datetime(date_str: str) -> datetime:
    """
    날짜 문자열 파싱
    
    지원 형식:
    - "2026-01-08T10:00:00Z"
    - "2026-01-08T10:00:00"
    - "2026-01-08"
    """
    # ISO 8601
    if "T" in date_str:
        date_str = date_str.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            # Python 3.10 이하 호환
            date_str = date_str.replace("+00:00", "")
            return datetime.fromisoformat(date_str)
    else:
        return datetime.strptime(date_str, "%Y-%m-%d")


def format_datetime(dt: datetime, format: str = "iso") -> str:
    """
    날짜 포맷팅
    
    Args:
        dt: datetime 객체
        format: "iso" | "date" | "datetime" | "timestamp" | 커스텀 포맷
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
        return dt.strftime(format)


def time_ago(dt: datetime) -> str:
    """
    상대 시간 표현 (한글)
    
    Returns:
        "방금 전", "5분 전", "2시간 전", "3일 전", "1개월 전", "2년 전"
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


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """날짜에 분 더하기"""
    return dt + timedelta(minutes=minutes)


# ===========================================
# 문자열 처리
# ===========================================

def truncate(text: str, length: int = 100, suffix: str = "...") -> str:
    """문자열 자르기"""
    if len(text) <= length:
        return text
    else:
        return text[:length] + suffix


def slugify(text: str) -> str:
    """
    URL/파일명 안전한 문자열로 변환
    
    "2026년 예산 계획" -> "2026-년-예산-계획"
    """
    text = text.lower()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-가-힣]', '', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text


def sanitize_filename(filename: str) -> str:
    """
    파일명 정리 (안전한 문자만)
    
    "문서/제목?.txt" -> "문서_제목.txt"
    """
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    키워드 추출 (간단한 버전)
    
    Args:
        text: 텍스트
        max_keywords: 최대 키워드 수
    """
    # 단어 추출 (한글 2자 이상, 영문 3자 이상)
    words = re.findall(r'[가-힣]{2,}|[a-zA-Z]{3,}|\d+', text.lower())
    
    # 불용어 제거
    stopwords = {'그리고', '그러나', '하지만', '또한', '및', '와', '과', '이', '그', '저'}
    words = [w for w in words if w not in stopwords]
    
    # 빈도 계산
    from collections import Counter
    word_freq = Counter(words)
    
    return [word for word, _ in word_freq.most_common(max_keywords)]


def highlight_text(text: str, keywords: List[str], tag: str = "mark") -> str:
    """
    텍스트에서 키워드 하이라이트
    
    Args:
        text: 원본 텍스트
        keywords: 하이라이트할 키워드 목록
        tag: HTML 태그
    """
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        text = pattern.sub(f"<{tag}>\\g<0></{tag}>", text)
    
    return text


def remove_html_tags(text: str) -> str:
    """HTML 태그 제거"""
    return re.sub(r'<[^>]+>', '', text)


def normalize_whitespace(text: str) -> str:
    """공백 정규화 (연속 공백을 단일 공백으로)"""
    return re.sub(r'\s+', ' ', text).strip()


# ===========================================
# 검증
# ===========================================

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


def is_safe_path(path: str, base_dir: str) -> bool:
    """
    경로 안전성 검증 (Path Traversal 방지)
    
    Args:
        path: 검증할 경로
        base_dir: 기준 디렉토리
    """
    base = Path(base_dir).resolve()
    target = (base / path).resolve()
    return str(target).startswith(str(base))


# ===========================================
# 데이터 변환
# ===========================================

def bytes_to_human(bytes_size: int) -> str:
    """
    바이트를 사람이 읽기 쉬운 형식으로
    
    "1.46 MB", "2.30 GB"
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    
    size = float(bytes_size)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def dict_to_query_string(params: dict) -> str:
    """딕셔너리를 쿼리 스트링으로"""
    from urllib.parse import urlencode
    return urlencode(params)


def merge_dicts(*dicts: dict) -> dict:
    """여러 딕셔너리 병합"""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """
    중첩 딕셔너리 평탄화
    
    {"user": {"name": "홍길동"}} -> {"user.name": "홍길동"}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def deep_get(d: dict, path: str, default=None):
    """
    중첩 딕셔너리에서 안전하게 값 가져오기
    
    deep_get({"user": {"name": "홍길동"}}, "user.name") -> "홍길동"
    """
    keys = path.split('.')
    value = d
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def deep_set(d: dict, path: str, value: Any):
    """
    중첩 딕셔너리에 값 설정
    
    deep_set({}, "user.name", "홍길동") -> {"user": {"name": "홍길동"}}
    """
    keys = path.split('.')
    current = d
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    return d


# ===========================================
# 보안
# ===========================================

def hash_string(text: str, algorithm: str = "sha256") -> str:
    """문자열 해시"""
    return hashlib.new(algorithm, text.encode()).hexdigest()


def hash_password(password: str) -> str:
    """
    비밀번호 해시 (SHA256 + salt)
    
    주의: 실제 운영환경에서는 bcrypt 사용 권장
    """
    salt = uuid.uuid4().hex
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, hashed: str) -> bool:
    """비밀번호 검증"""
    try:
        salt, hash_value = hashed.split('$')
        computed = hashlib.sha256((password + salt).encode()).hexdigest()
        return computed == hash_value
    except:
        return False


def mask_sensitive_data(text: str, mask_char: str = "*") -> str:
    """
    민감 정보 마스킹
    
    "홍길동" -> "홍*동"
    "hong@email.com" -> "ho**@email.com"
    """
    if len(text) <= 2:
        return mask_char * len(text)
    else:
        return text[0] + mask_char * (len(text) - 2) + text[-1]


def mask_email(email: str) -> str:
    """이메일 마스킹"""
    if '@' in email:
        local, domain = email.split('@')
        masked_local = mask_sensitive_data(local)
        return f"{masked_local}@{domain}"
    return mask_sensitive_data(email)


# ===========================================
# 기타 유틸리티
# ===========================================

def retry(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    함수 재시도
    
    Args:
        func: 실행할 함수
        max_attempts: 최대 시도 횟수
        delay: 재시도 간격 (초)
        exceptions: 재시도할 예외 타입
        on_retry: 재시도 시 호출할 콜백
    
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
            
            if on_retry:
                on_retry(attempt, e)
            
            if attempt < max_attempts - 1:
                time.sleep(delay)
    
    raise last_exception


def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """
    리스트를 청크로 분할
    
    [1, 2, 3, 4, 5] with chunk_size=2 -> [[1, 2], [3, 4], [5]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def unique_list(lst: list) -> list:
    """리스트 중복 제거 (순서 유지)"""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def safe_int(value: Any, default: int = 0) -> int:
    """안전한 정수 변환"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """안전한 실수 변환"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def coalesce(*values):
    """첫 번째 None이 아닌 값 반환"""
    for value in values:
        if value is not None:
            return value
    return None


# ===========================================
# Public API
# ===========================================

__all__ = [
    # ID 생성
    "generate_id",
    "generate_request_id",
    "generate_uuid",
    
    # 파일 처리
    "ensure_dir",
    "read_file",
    "write_file",
    "read_json",
    "write_json",
    "read_yaml",
    "write_yaml",
    "read_markdown",
    "write_markdown",
    "get_file_size",
    "get_file_hash",
    "list_files",
    
    # 날짜/시간
    "now_iso",
    "now_timestamp",
    "now_datetime",
    "parse_datetime",
    "format_datetime",
    "time_ago",
    "add_days",
    "add_hours",
    "add_minutes",
    
    # 문자열
    "truncate",
    "slugify",
    "sanitize_filename",
    "extract_keywords",
    "highlight_text",
    "remove_html_tags",
    "normalize_whitespace",
    
    # 검증
    "is_valid_email",
    "is_valid_url",
    "is_valid_json",
    "validate_classification",
    "validate_role",
    "is_safe_path",
    
    # 변환
    "bytes_to_human",
    "dict_to_query_string",
    "merge_dicts",
    "flatten_dict",
    "deep_get",
    "deep_set",
    
    # 보안
    "hash_string",
    "hash_password",
    "verify_password",
    "mask_sensitive_data",
    "mask_email",
    
    # 기타
    "retry",
    "chunk_list",
    "unique_list",
    "safe_int",
    "safe_float",
    "coalesce",
]
