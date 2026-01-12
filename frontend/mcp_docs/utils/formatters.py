"""
포맷터 함수

데이터 포맷팅
"""

from datetime import datetime
from typing import Optional


def format_date(date_str: Optional[str]) -> str:
    """
    날짜 포맷팅
    
    Args:
        date_str: ISO 형식 날짜 문자열
        
    Returns:
        포맷팅된 날짜 ("YYYY-MM-DD HH:MM")
    """
    if not date_str:
        return ""
    
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str


def format_file_size(bytes: int) -> str:
    """
    파일 크기 포맷팅
    
    Args:
        bytes: 바이트 크기
        
    Returns:
        포맷팅된 크기 ("1.2 MB")
    """
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f} KB"
    elif bytes < 1024 * 1024 * 1024:
        return f"{bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes / (1024 * 1024 * 1024):.1f} GB"


def format_time_ago(date_str: Optional[str]) -> str:
    """
    상대 시간 포맷팅
    
    Args:
        date_str: ISO 형식 날짜 문자열
        
    Returns:
        상대 시간 ("2시간 전")
    """
    if not date_str:
        return ""
    
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
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
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days}일 전"
        else:
            return format_date(date_str)
    except:
        return date_str
