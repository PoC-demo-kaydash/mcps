"""
Tool 입력 검증

JSON Schema 기반 검증 및 다양한 유틸리티 검증 함수 제공
"""

import re
import json
from typing import Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """검증 에러 예외"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)
    
    def __str__(self):
        if self.field:
            return f"Validation error in '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


class ToolValidator:
    """
    Tool 입력 검증기
    
    JSON Schema 기반 검증 및 다양한 유틸리티 검증 함수 제공
    """
    
    @staticmethod
    def validate(arguments: dict, schema: dict) -> tuple[bool, Optional[str]]:
        """
        JSON Schema 검증
        
        Args:
            arguments: 입력 인자
            schema: JSON Schema
        
        Returns:
            (valid: bool, error_message: Optional[str])
        
        Example:
            schema = {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100}
                },
                "required": ["query"]
            }
            
            valid, error = ToolValidator.validate(args, schema)
        """
        try:
            # jsonschema 라이브러리 사용 (설치된 경우)
            try:
                import jsonschema
                jsonschema.validate(instance=arguments, schema=schema)
                return True, None
            except ImportError:
                # jsonschema 없으면 기본 검증
                return ToolValidator._basic_validate(arguments, schema)
            except jsonschema.ValidationError as e:
                error_message = f"Validation error: {e.message}"
                logger.warning(error_message)
                return False, error_message
        
        except Exception as e:
            error_message = f"Validation failed: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    @staticmethod
    def _basic_validate(arguments: dict, schema: dict) -> tuple[bool, Optional[str]]:
        """기본 검증 (jsonschema 없을 때)"""
        if schema.get("type") != "object":
            return True, None
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # 필수 필드 확인
        for field in required:
            if field not in arguments:
                return False, f"Missing required field: {field}"
        
        # 각 필드 검증
        for field, value in arguments.items():
            if field not in properties:
                continue
            
            prop_schema = properties[field]
            prop_type = prop_schema.get("type")
            
            # 타입 검증
            if prop_type == "string" and not isinstance(value, str):
                return False, f"Field '{field}' must be a string"
            elif prop_type == "integer" and not isinstance(value, int):
                return False, f"Field '{field}' must be an integer"
            elif prop_type == "number" and not isinstance(value, (int, float)):
                return False, f"Field '{field}' must be a number"
            elif prop_type == "boolean" and not isinstance(value, bool):
                return False, f"Field '{field}' must be a boolean"
            elif prop_type == "array" and not isinstance(value, list):
                return False, f"Field '{field}' must be an array"
            elif prop_type == "object" and not isinstance(value, dict):
                return False, f"Field '{field}' must be an object"
            
            # 문자열 길이 검증
            if prop_type == "string" and isinstance(value, str):
                min_len = prop_schema.get("minLength")
                max_len = prop_schema.get("maxLength")
                
                if min_len is not None and len(value) < min_len:
                    return False, f"Field '{field}' must be at least {min_len} characters"
                if max_len is not None and len(value) > max_len:
                    return False, f"Field '{field}' must be at most {max_len} characters"
            
            # 숫자 범위 검증
            if prop_type in ["integer", "number"] and isinstance(value, (int, float)):
                minimum = prop_schema.get("minimum")
                maximum = prop_schema.get("maximum")
                
                if minimum is not None and value < minimum:
                    return False, f"Field '{field}' must be at least {minimum}"
                if maximum is not None and value > maximum:
                    return False, f"Field '{field}' must be at most {maximum}"
            
            # enum 검증
            if "enum" in prop_schema:
                if value not in prop_schema["enum"]:
                    valid_values = ", ".join(str(v) for v in prop_schema["enum"])
                    return False, f"Field '{field}' must be one of: {valid_values}"
        
        return True, None
    
    @staticmethod
    def validate_doc_id(doc_id: str) -> bool:
        """
        문서 ID 형식 검증
        
        Args:
            doc_id: 문서 ID (예: "DOC_12345678")
        
        Returns:
            bool: 유효 여부
        """
        pattern = r'^DOC_[A-Z0-9]{8}$'
        return bool(re.match(pattern, doc_id))
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """
        사용자 ID 형식 검증
        
        Args:
            user_id: 사용자 ID (예: "U001")
        
        Returns:
            bool: 유효 여부
        """
        pattern = r'^U\d{3}$'
        return bool(re.match(pattern, user_id))
    
    @staticmethod
    def validate_classification(classification: str) -> bool:
        """
        문서 등급 검증
        
        Args:
            classification: 문서 등급
        
        Returns:
            bool: 유효 여부
        """
        valid_classifications = ["public", "team", "confidential"]
        return classification in valid_classifications
    
    @staticmethod
    def validate_pagination(limit: int, offset: int) -> tuple[bool, Optional[str]]:
        """
        페이지네이션 검증
        
        Args:
            limit: 페이지 크기
            offset: 오프셋
        
        Returns:
            (valid: bool, error_message: Optional[str])
        """
        if limit < 1 or limit > 100:
            return False, "limit must be between 1 and 100"
        
        if offset < 0:
            return False, "offset must be non-negative"
        
        return True, None
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """
        문자열 정제
        
        Args:
            text: 입력 텍스트
            max_length: 최대 길이
        
        Returns:
            정제된 문자열
        """
        if not isinstance(text, str):
            return str(text)
        
        # 공백 정규화
        text = " ".join(text.split())
        
        # 최대 길이 제한
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> tuple[bool, Optional[str]]:
        """
        날짜 범위 검증
        
        Args:
            start_date: 시작일 (ISO 8601)
            end_date: 종료일 (ISO 8601)
        
        Returns:
            (valid: bool, error_message: Optional[str])
        """
        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            
            if start > end:
                return False, "start_date must be before end_date"
            
            # 최대 1년 범위
            delta = end - start
            if delta.days > 365:
                return False, "Date range cannot exceed 1 year"
            
            return True, None
        
        except ValueError as e:
            return False, f"Invalid date format: {e}"
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        이메일 형식 검증
        
        Args:
            email: 이메일 주소
        
        Returns:
            bool: 유효 여부
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_json_string(json_str: str) -> tuple[bool, Optional[str]]:
        """
        JSON 문자열 검증
        
        Args:
            json_str: JSON 문자열
        
        Returns:
            (valid: bool, error_message: Optional[str])
        """
        try:
            json.loads(json_str)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        URL 형식 검증
        
        Args:
            url: URL 문자열
        
        Returns:
            bool: 유효 여부
        """
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url, re.IGNORECASE))
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
        """
        파일 확장자 검증
        
        Args:
            filename: 파일명
            allowed_extensions: 허용된 확장자 목록 (예: ['.pdf', '.docx'])
        
        Returns:
            bool: 유효 여부
        """
        if not filename:
            return False
        
        ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
        
        # 확장자에 .이 없으면 추가
        normalized_exts = [e if e.startswith('.') else f'.{e}' for e in allowed_extensions]
        
        return f'.{ext}' in normalized_exts
    
    @staticmethod
    def validate_non_empty(value: Any, field_name: str = "value") -> tuple[bool, Optional[str]]:
        """
        빈 값 검증
        
        Args:
            value: 검증할 값
            field_name: 필드 이름
        
        Returns:
            (valid: bool, error_message: Optional[str])
        """
        if value is None:
            return False, f"{field_name} cannot be None"
        
        if isinstance(value, str) and not value.strip():
            return False, f"{field_name} cannot be empty"
        
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False, f"{field_name} cannot be empty"
        
        return True, None
