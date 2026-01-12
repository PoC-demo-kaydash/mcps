"""
파일 처리 Tool

파일 검증, 파일 정보 조회 기능 제공
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_tools.base import BaseTool, ToolMetadata
from shared.logging_config import get_logger
import os

logger = get_logger(__name__)


class ValidateFileTool(BaseTool):
    """
    파일 검증 Tool
    
    확장자, 크기, MIME 타입 검증
    """
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="validate_file",
            description="파일 검증 (확장자, 크기)",
            category="utils",
            department="file",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "allowed_extensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "허용된 확장자 목록"
                    },
                    "max_size_mb": {
                        "type": "number",
                        "description": "최대 파일 크기 (MB)"
                    },
                    "file_size": {
                        "type": "integer",
                        "description": "파일 크기 (bytes)"
                    }
                },
                "required": ["filename"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "valid": {"type": "boolean"},
                    "errors": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """파일 검증"""
        try:
            filename = arguments["filename"]
            allowed_extensions = arguments.get("allowed_extensions", [])
            max_size_mb = arguments.get("max_size_mb")
            file_size = arguments.get("file_size")
            
            errors = []
            
            # 확장자 검증
            if allowed_extensions:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in [f".{e.lower()}" if not e.startswith(".") else e.lower() 
                               for e in allowed_extensions]:
                    errors.append(f"Invalid extension. Allowed: {', '.join(allowed_extensions)}")
            
            # 파일명 검증
            if not filename or filename.startswith('.') or '/' in filename or '\\' in filename:
                errors.append("Invalid filename")
            
            # 크기 검증
            if max_size_mb and file_size:
                max_bytes = max_size_mb * 1024 * 1024
                if file_size > max_bytes:
                    errors.append(f"File too large. Max: {max_size_mb} MB")
            
            valid = len(errors) == 0
            
            return self.create_success_response({
                "valid": valid,
                "errors": errors,
                "filename": filename
            })
        
        except Exception as e:
            logger.error(f"Validate file failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "VALIDATION_ERROR")


class GetFileInfoTool(BaseTool):
    """
    파일 정보 조회 Tool
    """
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_file_info",
            description="파일 정보 조회",
            category="utils",
            department="file",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                },
                "required": ["filename"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "extension": {"type": "string"},
                    "base_name": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """파일 정보 조회"""
        try:
            filename = arguments["filename"]
            
            # 경로 분리
            base_name = os.path.basename(filename)
            name_without_ext, ext = os.path.splitext(base_name)
            
            # MIME 타입 추정 (간단한 매핑)
            mime_types = {
                '.txt': 'text/plain',
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.zip': 'application/zip',
                '.json': 'application/json',
                '.xml': 'application/xml'
            }
            
            mime_type = mime_types.get(ext.lower(), 'application/octet-stream')
            
            return self.create_success_response({
                "name": base_name,
                "base_name": name_without_ext,
                "extension": ext,
                "mime_type": mime_type
            })
        
        except Exception as e:
            logger.error(f"Get file info failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "FILE_INFO_ERROR")
