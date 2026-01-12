"""
텍스트 처리 Tool

텍스트 요약, 키워드 추출 기능 제공
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_tools.base import BaseTool, ToolMetadata
from shared.logging_config import get_logger

logger = get_logger(__name__)


class SummarizeTextTool(BaseTool):
    """
    텍스트 요약 Tool
    
    간단한 추출 요약 방식
    """
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="summarize_text",
            description="텍스트 요약 (추출 방식)",
            category="utils",
            department="text",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "minLength": 10,
                        "description": "요약할 텍스트"
                    },
                    "max_sentences": {
                        "type": "integer",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10,
                        "description": "최대 문장 수"
                    }
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "original_length": {"type": "integer"},
                    "summary_length": {"type": "integer"}
                }
            },
            examples=[
                {
                    "input": {
                        "text": "긴 텍스트...",
                        "max_sentences": 3
                    },
                    "output": {
                        "summary": "요약된 텍스트...",
                        "original_length": 1000,
                        "summary_length": 150
                    }
                }
            ]
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """텍스트 요약"""
        try:
            text = arguments["text"]
            max_sentences = arguments.get("max_sentences", 3)
            
            # 간단한 추출 요약 (문장 기반)
            import re
            
            # 문장 분리
            sentences = re.split(r'[.!?]+\s+', text.strip())
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) <= max_sentences:
                summary = text
            else:
                # 첫 문장 + 중간 문장 + 마지막 문장
                if max_sentences == 1:
                    summary = sentences[0]
                elif max_sentences == 2:
                    summary = f"{sentences[0]}. {sentences[-1]}."
                else:
                    # 균등하게 분배
                    step = len(sentences) // max_sentences
                    selected = [sentences[i * step] for i in range(max_sentences)]
                    summary = ". ".join(selected) + "."
            
            return self.create_success_response({
                "summary": summary,
                "original_length": len(text),
                "summary_length": len(summary)
            })
        
        except Exception as e:
            logger.error(f"Summarize failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "SUMMARIZE_ERROR")


class ExtractKeywordsTool(BaseTool):
    """
    키워드 추출 Tool
    
    빈도 기반 키워드 추출
    """
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="extract_keywords",
            description="텍스트에서 키워드 추출",
            category="utils",
            department="text",
            version="1.0.0",
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "minLength": 10,
                        "description": "분석할 텍스트"
                    },
                    "max_keywords": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "keywords": {"type": "array"}
                }
            }
        )
    
    def execute(self, arguments: dict, context: dict = None) -> dict:
        """키워드 추출"""
        try:
            text = arguments["text"]
            max_keywords = arguments.get("max_keywords", 10)
            
            # 간단한 빈도 기반 키워드 추출
            import re
            from collections import Counter
            
            # 단어 추출 (영문/한글)
            words = re.findall(r'\b[a-zA-Z가-힣]{2,}\b', text.lower())
            
            # 불용어 제거 (간단한 영문/한글 불용어)
            stopwords = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                '이', '그', '저', '것', '수', '등', '및', '에', '를', '을', '이다',
                '있다', '하다', '되다', '않다'
            }
            
            words = [w for w in words if w not in stopwords and len(w) >= 2]
            
            # 빈도 계산
            word_freq = Counter(words)
            
            # 상위 키워드 추출
            keywords = [
                {"word": word, "frequency": freq}
                for word, freq in word_freq.most_common(max_keywords)
            ]
            
            return self.create_success_response({
                "keywords": keywords
            })
        
        except Exception as e:
            logger.error(f"Extract keywords failed: {e}", exc_info=True)
            return self.create_error_response(str(e), "KEYWORD_ERROR")
