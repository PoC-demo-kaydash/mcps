"""
검증 함수

입력 유효성 검증
"""

import re
from typing import Tuple


def validate_required(value: str, field_name: str) -> bool:
    """
    필수 필드 검증
    
    Args:
        value: 검증할 값
        field_name: 필드 이름
        
    Returns:
        유효성 여부
    """
    if not value or value.strip() == "":
        return False
    return True


def validate_email(email: str) -> bool:
    """
    이메일 형식 검증
    
    Args:
        email: 이메일 주소
        
    Returns:
        유효성 여부
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_document_form(title: str, content: str) -> Tuple[bool, str]:
    """
    문서 폼 검증
    
    Args:
        title: 제목
        content: 내용
        
    Returns:
        (유효성 여부, 에러 메시지)
    """
    if not validate_required(title, "제목"):
        return False, "제목을 입력하세요"
    
    if not validate_required(content, "내용"):
        return False, "내용을 입력하세요"
    
    if len(title) > 200:
        return False, "제목은 200자 이내로 입력하세요"
    
    return True, ""
