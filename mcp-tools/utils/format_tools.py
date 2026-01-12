"""
포맷 변환 Tool

JSON, CSV, Markdown 포맷 변환 기능 제공
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_tools.base import BaseTool, ToolMetadata
from shared.logging_config import get_logger
import json
import csv
from io import StringIO

logger = get_logger(__name__)


class ConvertToJsonTool(BaseTool):
    """
    JSON 변환 Tool
    """
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="convert_to_json",
            description="데이터를 JSON 형식으로 변환",
            category="utils",
            department="format",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "data": {
                        "description": "변환할 데이터"
                    },
                    "pretty": {
                        "type": "boolean",
                        "default": True,
                        "description": "보기 좋게 포맷팅"
                    }
                },
                "required": ["data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "json": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """JSON 변환"""
        try:
            data = arguments["data"]
            pretty = arguments.get("pretty", True)
            
            if pretty:
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
            else:
                json_str = json.dumps(data, ensure_ascii=False)
            
            return self.create_success_response({
                "json": json_str
            })
        
        except Exception as e:
            logger.error(f"Convert to JSON failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "JSON_ERROR")


class ConvertToCsvTool(BaseTool):
    """
    CSV 변환 Tool
    """
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="convert_to_csv",
            description="데이터를 CSV 형식으로 변환",
            category="utils",
            department="format",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "변환할 데이터 (dict 배열)"
                    },
                    "delimiter": {
                        "type": "string",
                        "default": ",",
                        "description": "구분자"
                    }
                },
                "required": ["data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "csv": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """CSV 변환"""
        try:
            data = arguments["data"]
            delimiter = arguments.get("delimiter", ",")
            
            if not data or not isinstance(data, list):
                return self.create_error_response(
                    "Data must be a non-empty list",
                    "INVALID_DATA"
                )
            
            # CSV 생성
            output = StringIO()
            
            # 첫 번째 행에서 헤더 추출
            if isinstance(data[0], dict):
                fieldnames = list(data[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.writer(output, delimiter=delimiter)
                writer.writerows(data)
            
            csv_str = output.getvalue()
            
            return self.create_success_response({
                "csv": csv_str
            })
        
        except Exception as e:
            logger.error(f"Convert to CSV failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "CSV_ERROR")


class ConvertToMarkdownTool(BaseTool):
    """
    Markdown 테이블 변환 Tool
    """
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="convert_to_markdown",
            description="데이터를 Markdown 테이블로 변환",
            category="utils",
            department="format",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "변환할 데이터 (dict 배열)"
                    }
                },
                "required": ["data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "markdown": {"type": "string"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """Markdown 테이블 변환"""
        try:
            data = arguments["data"]
            
            if not data or not isinstance(data, list) or not isinstance(data[0], dict):
                return self.create_error_response(
                    "Data must be a non-empty list of dicts",
                    "INVALID_DATA"
                )
            
            # 헤더
            headers = list(data[0].keys())
            header_row = "| " + " | ".join(headers) + " |"
            separator = "| " + " | ".join(["---"] * len(headers)) + " |"
            
            # 데이터 행
            rows = []
            for row in data:
                values = [str(row.get(h, "")) for h in headers]
                rows.append("| " + " | ".join(values) + " |")
            
            markdown = "\n".join([header_row, separator] + rows)
            
            return self.create_success_response({
                "markdown": markdown
            })
        
        except Exception as e:
            logger.error(f"Convert to Markdown failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "MARKDOWN_ERROR")
