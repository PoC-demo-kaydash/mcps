"""
Elasticsearch 관리자
====================

Elasticsearch 연결, 인덱싱, 검색 기능을 제공합니다.

특징:
- Nori 분석기 (한국어 형태소 분석)
- 권한 기반 검색 필터링
- 하이라이팅 지원
- 벌크 인덱싱

사용 예:
    from shared.elasticsearch import ElasticsearchManager
    
    es = ElasticsearchManager()
    
    # 문서 인덱싱
    es.index_document("DOC001", {...})
    
    # 검색
    results = es.search_documents(
        query="보고서",
        user_classification=3,
        filters={"status": "published"}
    )
    
    # 감사 로그 인덱싱
    es.index_audit_log("LOG001", {...})
"""

from typing import Any, Optional, Dict, List, Union
from datetime import datetime
import logging
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import NotFoundError, ConnectionError

logger = logging.getLogger(__name__)


# ===========================================
# 인덱스 설정
# ===========================================

# 문서 인덱스 설정
DOCUMENTS_INDEX_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "korean": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer",
                    "filter": [
                        "nori_readingform",
                        "lowercase",
                        "nori_part_of_speech_basic"
                    ]
                },
                "korean_search": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer",
                    "filter": [
                        "nori_readingform",
                        "lowercase",
                        "synonym_filter"
                    ]
                }
            },
            "filter": {
                "nori_part_of_speech_basic": {
                    "type": "nori_part_of_speech",
                    "stoptags": [
                        "E", "IC", "J", "MAG", "MAJ",
                        "MM", "SP", "SSC", "SSO", "SC",
                        "SE", "XPN", "XSA", "XSN", "XSV"
                    ]
                },
                "synonym_filter": {
                    "type": "synonym",
                    "lenient": True,
                    "synonyms": [
                        "문서, 서류, 파일",
                        "회의, 미팅",
                        "보고서, 리포트"
                    ]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "korean",
                "search_analyzer": "korean_search",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "content": {
                "type": "text",
                "analyzer": "korean",
                "search_analyzer": "korean_search"
            },
            "summary": {
                "type": "text",
                "analyzer": "korean"
            },
            "author_id": {"type": "keyword"},
            "author_name": {"type": "keyword"},
            "classification": {"type": "keyword"},
            "classification_level": {"type": "integer"},
            "doc_type": {"type": "keyword"},
            "status": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "department": {"type": "keyword"},
            "file_path": {"type": "keyword"},
            "file_size": {"type": "long"},
            "version": {"type": "integer"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
            "metadata": {"type": "object", "enabled": False}
        }
    }
}

# 감사 로그 인덱스 설정
AUDIT_LOGS_INDEX_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "log_id": {"type": "keyword"},
            "user_id": {"type": "keyword"},
            "username": {"type": "keyword"},
            "action": {"type": "keyword"},
            "resource_type": {"type": "keyword"},
            "resource_id": {"type": "keyword"},
            "status": {"type": "keyword"},
            "ip_address": {"type": "ip"},
            "user_agent": {"type": "text", "index": False},
            "details": {"type": "object", "enabled": False},
            "created_at": {"type": "date"}
        }
    }
}


# ===========================================
# 보안 등급 매핑
# ===========================================

CLASSIFICATION_LEVELS = {
    "public": 1,
    "internal": 2,
    "confidential": 3,
    "secret": 4,
    "top_secret": 5
}


# ===========================================
# Elasticsearch 관리자
# ===========================================

class ElasticsearchManager:
    """
    Elasticsearch 관리자
    
    문서 검색 및 인덱싱, 감사 로그 관리를 담당합니다.
    """
    
    def __init__(
        self,
        hosts: Union[str, List[str]] = "http://localhost:9200",
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = False,
        verify_certs: bool = True,
        timeout: int = 30,
        documents_index: str = "mcps_documents",
        audit_logs_index: str = "mcps_audit_logs",
        **kwargs
    ):
        """
        초기화
        
        Args:
            hosts: ES 호스트 (URL 또는 URL 리스트)
            username: 사용자명
            password: 비밀번호
            use_ssl: SSL 사용 여부
            verify_certs: 인증서 검증 여부
            timeout: 연결 타임아웃
            documents_index: 문서 인덱스명
            audit_logs_index: 감사 로그 인덱스명
        """
        # 호스트 정규화
        if isinstance(hosts, str):
            hosts = [hosts]
        
        # 클라이언트 설정
        client_config = {
            "hosts": hosts,
            "timeout": timeout,
            "retry_on_timeout": True,
            "max_retries": 3,
        }
        
        # 인증 설정
        if username and password:
            client_config["basic_auth"] = (username, password)
        
        # SSL 설정
        if use_ssl:
            client_config["use_ssl"] = True
            client_config["verify_certs"] = verify_certs
        
        # 추가 설정
        client_config.update(kwargs)
        
        # 클라이언트 생성
        self.client = Elasticsearch(**client_config)
        
        # 인덱스명
        self.documents_index = documents_index
        self.audit_logs_index = audit_logs_index
        
        logger.info(f"ElasticsearchManager initialized: {hosts}")
    
    # ===========================================
    # 인덱스 관리
    # ===========================================
    
    def create_indices(self, force: bool = False):
        """
        인덱스 생성
        
        Args:
            force: 기존 인덱스 삭제 후 재생성
        """
        # 문서 인덱스
        self._create_index(
            self.documents_index,
            DOCUMENTS_INDEX_SETTINGS,
            force
        )
        
        # 감사 로그 인덱스
        self._create_index(
            self.audit_logs_index,
            AUDIT_LOGS_INDEX_SETTINGS,
            force
        )
        
        logger.info("Elasticsearch indices created")
    
    def _create_index(
        self,
        index_name: str,
        settings: Dict,
        force: bool = False
    ):
        """인덱스 생성 헬퍼"""
        try:
            exists = self.client.indices.exists(index=index_name)
            
            if exists:
                if force:
                    self.client.indices.delete(index=index_name)
                    logger.info(f"Index deleted: {index_name}")
                else:
                    logger.debug(f"Index already exists: {index_name}")
                    return
            
            self.client.indices.create(index=index_name, body=settings)
            logger.info(f"Index created: {index_name}")
        
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            raise
    
    def delete_indices(self):
        """인덱스 삭제"""
        try:
            if self.client.indices.exists(index=self.documents_index):
                self.client.indices.delete(index=self.documents_index)
            
            if self.client.indices.exists(index=self.audit_logs_index):
                self.client.indices.delete(index=self.audit_logs_index)
            
            logger.info("Elasticsearch indices deleted")
        
        except Exception as e:
            logger.error(f"Failed to delete indices: {e}")
            raise
    
    # ===========================================
    # 문서 인덱싱
    # ===========================================
    
    def index_document(
        self,
        doc_id: str,
        document: Dict[str, Any],
        refresh: bool = False
    ) -> bool:
        """
        문서 인덱싱
        
        Args:
            doc_id: 문서 ID
            document: 문서 데이터
            refresh: 즉시 검색 가능하게 할지
        
        Returns:
            성공 여부
        """
        try:
            # 보안 등급 숫자 추가
            if "classification" in document:
                document["classification_level"] = CLASSIFICATION_LEVELS.get(
                    document["classification"], 1
                )
            
            self.client.index(
                index=self.documents_index,
                id=doc_id,
                document=document,
                refresh=refresh
            )
            
            logger.debug(f"Document indexed: {doc_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            return False
    
    def bulk_index_documents(
        self,
        documents: List[Dict[str, Any]],
        refresh: bool = True
    ) -> Dict[str, Any]:
        """
        문서 벌크 인덱싱
        
        Args:
            documents: 문서 리스트 (각 문서에 doc_id 필수)
            refresh: 즉시 검색 가능하게 할지
        
        Returns:
            {
                "success": 성공 수,
                "failed": 실패 수,
                "errors": 에러 리스트
            }
        """
        actions = []
        
        for doc in documents:
            doc_id = doc.get("doc_id")
            if not doc_id:
                continue
            
            # 보안 등급 숫자 추가
            if "classification" in doc:
                doc["classification_level"] = CLASSIFICATION_LEVELS.get(
                    doc["classification"], 1
                )
            
            actions.append({
                "_index": self.documents_index,
                "_id": doc_id,
                "_source": doc
            })
        
        try:
            success, failed = helpers.bulk(
                self.client,
                actions,
                refresh=refresh,
                raise_on_error=False
            )
            
            errors = []
            if isinstance(failed, list):
                errors = [str(f) for f in failed]
            
            logger.info(f"Bulk indexed: success={success}, failed={len(errors)}")
            
            return {
                "success": success,
                "failed": len(errors),
                "errors": errors
            }
        
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return {
                "success": 0,
                "failed": len(documents),
                "errors": [str(e)]
            }
    
    def delete_document(self, doc_id: str, refresh: bool = False) -> bool:
        """
        문서 삭제
        
        Args:
            doc_id: 문서 ID
            refresh: 즉시 반영
        
        Returns:
            성공 여부
        """
        try:
            self.client.delete(
                index=self.documents_index,
                id=doc_id,
                refresh=refresh
            )
            logger.debug(f"Document deleted: {doc_id}")
            return True
        
        except NotFoundError:
            logger.warning(f"Document not found for delete: {doc_id}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        문서 조회
        
        Returns:
            문서 데이터 또는 None
        """
        try:
            result = self.client.get(
                index=self.documents_index,
                id=doc_id
            )
            return result["_source"]
        
        except NotFoundError:
            return None
        
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None
    
    # ===========================================
    # 문서 검색
    # ===========================================
    
    def search_documents(
        self,
        query: str,
        user_classification_level: int = 1,
        filters: Optional[Dict[str, Any]] = None,
        from_: int = 0,
        size: int = 20,
        highlight: bool = True,
        sort: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        문서 검색 (권한 기반 필터링 포함)
        
        Args:
            query: 검색어
            user_classification_level: 사용자 보안 등급 (1-5)
            filters: 추가 필터 {"status": "published", "doc_type": "report", ...}
            from_: 시작 위치
            size: 결과 수
            highlight: 하이라이팅 여부
            sort: 정렬 [{"created_at": "desc"}]
        
        Returns:
            {
                "total": 전체 결과 수,
                "hits": 검색 결과 리스트,
                "took": 소요 시간 (ms)
            }
        """
        # 기본 쿼리 구성
        must_queries = []
        filter_queries = []
        
        # 텍스트 검색
        if query:
            must_queries.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content", "summary^2", "tags"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        else:
            must_queries.append({"match_all": {}})
        
        # 보안 등급 필터 (사용자 등급 이하만 검색)
        filter_queries.append({
            "range": {
                "classification_level": {
                    "lte": user_classification_level
                }
            }
        })
        
        # 추가 필터
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    filter_queries.append({
                        "terms": {field: value}
                    })
                else:
                    filter_queries.append({
                        "term": {field: value}
                    })
        
        # 검색 쿼리 구성
        search_query = {
            "query": {
                "bool": {
                    "must": must_queries,
                    "filter": filter_queries
                }
            },
            "from": from_,
            "size": size
        }
        
        # 하이라이팅
        if highlight:
            search_query["highlight"] = {
                "fields": {
                    "title": {
                        "number_of_fragments": 1,
                        "fragment_size": 100
                    },
                    "content": {
                        "number_of_fragments": 3,
                        "fragment_size": 150
                    }
                },
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"]
            }
        
        # 정렬
        if sort:
            search_query["sort"] = sort
        else:
            search_query["sort"] = [
                "_score",
                {"created_at": "desc"}
            ]
        
        try:
            result = self.client.search(
                index=self.documents_index,
                body=search_query
            )
            
            hits = []
            for hit in result["hits"]["hits"]:
                doc = hit["_source"]
                doc["_score"] = hit["_score"]
                
                if "highlight" in hit:
                    doc["_highlight"] = hit["highlight"]
                
                hits.append(doc)
            
            return {
                "total": result["hits"]["total"]["value"],
                "hits": hits,
                "took": result["took"]
            }
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "total": 0,
                "hits": [],
                "took": 0,
                "error": str(e)
            }
    
    def suggest(
        self,
        query: str,
        user_classification_level: int = 1,
        size: int = 5
    ) -> List[str]:
        """
        검색어 자동완성
        
        Args:
            query: 검색어
            user_classification_level: 사용자 보안 등급
            size: 제안 수
        
        Returns:
            제안 리스트
        """
        search_query = {
            "query": {
                "bool": {
                    "must": {
                        "match_phrase_prefix": {
                            "title": {
                                "query": query,
                                "max_expansions": 10
                            }
                        }
                    },
                    "filter": {
                        "range": {
                            "classification_level": {
                                "lte": user_classification_level
                            }
                        }
                    }
                }
            },
            "size": size,
            "_source": ["title"]
        }
        
        try:
            result = self.client.search(
                index=self.documents_index,
                body=search_query
            )
            
            return [hit["_source"]["title"] for hit in result["hits"]["hits"]]
        
        except Exception as e:
            logger.error(f"Suggest failed: {e}")
            return []
    
    def get_aggregations(
        self,
        user_classification_level: int = 1
    ) -> Dict[str, Any]:
        """
        문서 집계 (대시보드용)
        
        Returns:
            {
                "by_classification": [...],
                "by_doc_type": [...],
                "by_status": [...],
                "by_department": [...]
            }
        """
        search_query = {
            "query": {
                "range": {
                    "classification_level": {
                        "lte": user_classification_level
                    }
                }
            },
            "size": 0,
            "aggs": {
                "by_classification": {
                    "terms": {"field": "classification"}
                },
                "by_doc_type": {
                    "terms": {"field": "doc_type"}
                },
                "by_status": {
                    "terms": {"field": "status"}
                },
                "by_department": {
                    "terms": {"field": "department"}
                }
            }
        }
        
        try:
            result = self.client.search(
                index=self.documents_index,
                body=search_query
            )
            
            aggs = result.get("aggregations", {})
            
            return {
                "by_classification": aggs.get("by_classification", {}).get("buckets", []),
                "by_doc_type": aggs.get("by_doc_type", {}).get("buckets", []),
                "by_status": aggs.get("by_status", {}).get("buckets", []),
                "by_department": aggs.get("by_department", {}).get("buckets", [])
            }
        
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            return {}
    
    # ===========================================
    # 감사 로그
    # ===========================================
    
    def index_audit_log(
        self,
        log_id: str,
        log_data: Dict[str, Any],
        refresh: bool = False
    ) -> bool:
        """
        감사 로그 인덱싱
        
        Args:
            log_id: 로그 ID
            log_data: 로그 데이터
            refresh: 즉시 반영
        
        Returns:
            성공 여부
        """
        try:
            self.client.index(
                index=self.audit_logs_index,
                id=log_id,
                document=log_data,
                refresh=refresh
            )
            
            logger.debug(f"Audit log indexed: {log_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to index audit log {log_id}: {e}")
            return False
    
    def search_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        from_: int = 0,
        size: int = 50
    ) -> Dict[str, Any]:
        """
        감사 로그 검색
        
        Returns:
            {
                "total": 전체 결과 수,
                "hits": 검색 결과 리스트,
                "took": 소요 시간 (ms)
            }
        """
        filter_queries = []
        
        if user_id:
            filter_queries.append({"term": {"user_id": user_id}})
        
        if action:
            filter_queries.append({"term": {"action": action}})
        
        if resource_type:
            filter_queries.append({"term": {"resource_type": resource_type}})
        
        if resource_id:
            filter_queries.append({"term": {"resource_id": resource_id}})
        
        if status:
            filter_queries.append({"term": {"status": status}})
        
        if from_date or to_date:
            range_query = {}
            if from_date:
                range_query["gte"] = from_date.isoformat()
            if to_date:
                range_query["lte"] = to_date.isoformat()
            filter_queries.append({"range": {"created_at": range_query}})
        
        search_query = {
            "query": {
                "bool": {
                    "filter": filter_queries if filter_queries else [{"match_all": {}}]
                }
            },
            "from": from_,
            "size": size,
            "sort": [{"created_at": "desc"}]
        }
        
        try:
            result = self.client.search(
                index=self.audit_logs_index,
                body=search_query
            )
            
            hits = [hit["_source"] for hit in result["hits"]["hits"]]
            
            return {
                "total": result["hits"]["total"]["value"],
                "hits": hits,
                "took": result["took"]
            }
        
        except Exception as e:
            logger.error(f"Audit log search failed: {e}")
            return {
                "total": 0,
                "hits": [],
                "took": 0,
                "error": str(e)
            }
    
    # ===========================================
    # 헬스 체크
    # ===========================================
    
    def ping(self) -> bool:
        """연결 상태 확인"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"ES ping failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        상세 헬스 체크
        
        Returns:
            {
                "status": "healthy" | "unhealthy",
                "cluster_name": 클러스터명,
                "cluster_status": "green" | "yellow" | "red",
                "indices": {...}
            }
        """
        try:
            cluster_health = self.client.cluster.health()
            
            indices_info = {}
            
            for index_name in [self.documents_index, self.audit_logs_index]:
                try:
                    if self.client.indices.exists(index=index_name):
                        stats = self.client.indices.stats(index=index_name)
                        indices_info[index_name] = {
                            "docs": stats["indices"][index_name]["primaries"]["docs"]["count"],
                            "size": stats["indices"][index_name]["primaries"]["store"]["size_in_bytes"]
                        }
                    else:
                        indices_info[index_name] = {"exists": False}
                except:
                    indices_info[index_name] = {"error": "Failed to get stats"}
            
            return {
                "status": "healthy",
                "cluster_name": cluster_health["cluster_name"],
                "cluster_status": cluster_health["status"],
                "number_of_nodes": cluster_health["number_of_nodes"],
                "indices": indices_info
            }
        
        except Exception as e:
            logger.error(f"ES health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # ===========================================
    # 리소스 정리
    # ===========================================
    
    def close(self):
        """클라이언트 종료"""
        if self.client:
            self.client.close()
            logger.info("ElasticsearchManager closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ===========================================
# Public API
# ===========================================

__all__ = [
    "ElasticsearchManager",
    "CLASSIFICATION_LEVELS",
    "DOCUMENTS_INDEX_SETTINGS",
    "AUDIT_LOGS_INDEX_SETTINGS",
]
