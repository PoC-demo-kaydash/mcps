#!/usr/bin/env python3
"""
MCP Servers 통합 테스트

테스트 시나리오:
1. 인증 플로우
2. 문서 CRUD
3. 검색 연동
4. 버전 관리
5. 감사 로그
"""

import sys
import os
import json
import asyncio
from typing import Dict, Any, List

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.database import DatabaseManager
from shared.elasticsearch import ElasticsearchManager
from mcp_tools.core.auth_tools import AuthenticateTool, GetMyPermissionsTool
from mcp_tools.core.document_tools import (
    CreateDocumentTool, GetDocumentTool, UpdateDocumentTool, 
    DeleteDocumentTool, ListDocumentsTool
)
from mcp_tools.core.search_tools import SearchDocumentsTool
from mcp_tools.core.version_tools import GetDocumentVersionsTool
from mcp_tools.core.audit_tools import GetAuditLogsTool


class MCPServersIntegrationTest:
    """MCP 서버 통합 테스트"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.es = ElasticsearchManager()
        self.test_results: List[Dict[str, Any]] = []
        
        # 테스트용 컨텍스트
        self.context = {
            "user_id": "TEST_USER",
            "user_role": "admin",
            "user_team": "test_team",
            "session_id": "test_session"
        }
    
    def log_test(self, scenario: str, status: str, message: str, details: Any = None):
        """테스트 결과 로깅"""
        result = {
            "scenario": scenario,
            "status": status,
            "message": message,
            "details": details
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
        print(f"{status_icon} [{scenario}] {message}")
        if details:
            print(f"   상세: {json.dumps(details, ensure_ascii=False, indent=2)}")
    
    async def test_01_authentication_flow(self):
        """시나리오 1: 인증 플로우"""
        print("\n" + "="*60)
        print("시나리오 1: 인증 플로우")
        print("="*60)
        
        try:
            # 1-1. 사용자 인증
            auth_tool = AuthenticateTool(self.db)
            auth_result = await auth_tool.execute(
                username="admin",
                password="admin123",
                _context=self.context
            )
            
            if auth_result.get("success"):
                self.log_test("인증 플로우", "success", "사용자 인증 성공", auth_result)
            else:
                self.log_test("인증 플로우", "error", "사용자 인증 실패", auth_result)
                return
            
            # 1-2. 권한 조회
            perm_tool = GetMyPermissionsTool(self.db)
            perm_result = await perm_tool.execute(_context=self.context)
            
            if perm_result.get("success"):
                self.log_test("인증 플로우", "success", "권한 조회 성공", perm_result)
            else:
                self.log_test("인증 플로우", "warning", "권한 조회 실패", perm_result)
                
        except Exception as e:
            self.log_test("인증 플로우", "error", f"예외 발생: {str(e)}")
    
    async def test_02_document_crud(self):
        """시나리오 2: 문서 CRUD"""
        print("\n" + "="*60)
        print("시나리오 2: 문서 CRUD")
        print("="*60)
        
        doc_id = None
        
        try:
            # 2-1. 문서 생성
            create_tool = CreateDocumentTool(self.db, self.es)
            create_result = await create_tool.execute(
                title="통합 테스트 문서",
                content="이것은 통합 테스트를 위한 샘플 문서입니다.",
                classification="public",
                category="test",
                tags=["test", "integration"],
                _context=self.context
            )
            
            if create_result.get("success"):
                doc_id = create_result.get("document_id")
                self.log_test("문서 CRUD", "success", f"문서 생성 성공 (ID: {doc_id})", create_result)
            else:
                self.log_test("문서 CRUD", "error", "문서 생성 실패", create_result)
                return
            
            # 2-2. 문서 조회
            get_tool = GetDocumentTool(self.db)
            get_result = await get_tool.execute(
                doc_id=doc_id,
                _context=self.context
            )
            
            if get_result.get("success"):
                self.log_test("문서 CRUD", "success", "문서 조회 성공", get_result)
            else:
                self.log_test("문서 CRUD", "error", "문서 조회 실패", get_result)
            
            # 2-3. 문서 수정
            update_tool = UpdateDocumentTool(self.db, self.es)
            update_result = await update_tool.execute(
                doc_id=doc_id,
                title="통합 테스트 문서 (수정됨)",
                content="문서 내용이 수정되었습니다.",
                _context=self.context
            )
            
            if update_result.get("success"):
                self.log_test("문서 CRUD", "success", "문서 수정 성공", update_result)
            else:
                self.log_test("문서 CRUD", "error", "문서 수정 실패", update_result)
            
            # 2-4. 문서 목록
            list_tool = ListDocumentsTool(self.db)
            list_result = await list_tool.execute(
                limit=10,
                _context=self.context
            )
            
            if list_result.get("success"):
                self.log_test("문서 CRUD", "success", f"문서 목록 조회 성공 ({list_result.get('total', 0)}건)")
            else:
                self.log_test("문서 CRUD", "error", "문서 목록 조회 실패", list_result)
            
            # 2-5. 문서 삭제
            delete_tool = DeleteDocumentTool(self.db, self.es)
            delete_result = await delete_tool.execute(
                doc_id=doc_id,
                _context=self.context
            )
            
            if delete_result.get("success"):
                self.log_test("문서 CRUD", "success", "문서 삭제 성공", delete_result)
            else:
                self.log_test("문서 CRUD", "error", "문서 삭제 실패", delete_result)
                
        except Exception as e:
            self.log_test("문서 CRUD", "error", f"예외 발생: {str(e)}")
    
    async def test_03_search_integration(self):
        """시나리오 3: 검색 연동"""
        print("\n" + "="*60)
        print("시나리오 3: 검색 연동")
        print("="*60)
        
        try:
            # 3-1. 검색 테스트
            search_tool = SearchDocumentsTool(self.db, self.es)
            search_result = await search_tool.execute(
                query="테스트",
                limit=10,
                _context=self.context
            )
            
            if search_result.get("success"):
                total = search_result.get("total", 0)
                self.log_test("검색 연동", "success", f"검색 성공 ({total}건 발견)")
            else:
                self.log_test("검색 연동", "error", "검색 실패", search_result)
                
        except Exception as e:
            self.log_test("검색 연동", "error", f"예외 발생: {str(e)}")
    
    async def test_04_version_management(self):
        """시나리오 4: 버전 관리"""
        print("\n" + "="*60)
        print("시나리오 4: 버전 관리")
        print("="*60)
        
        try:
            # 버전 관리 테스트를 위해 문서 ID가 필요
            # 실제 테스트에서는 존재하는 문서 ID 사용
            version_tool = GetDocumentVersionsTool(self.db)
            
            # 테스트용 문서 ID (실제로는 존재하지 않을 수 있음)
            test_doc_id = "DOC-001"
            
            version_result = await version_tool.execute(
                doc_id=test_doc_id,
                _context=self.context
            )
            
            if version_result.get("success"):
                versions = version_result.get("versions", [])
                self.log_test("버전 관리", "success", f"버전 히스토리 조회 성공 ({len(versions)}개)")
            else:
                self.log_test("버전 관리", "warning", "버전 히스토리 없음 또는 문서 없음", version_result)
                
        except Exception as e:
            self.log_test("버전 관리", "error", f"예외 발생: {str(e)}")
    
    async def test_05_audit_logs(self):
        """시나리오 5: 감사 로그"""
        print("\n" + "="*60)
        print("시나리오 5: 감사 로그")
        print("="*60)
        
        try:
            # 5-1. 감사 로그 조회
            audit_tool = GetAuditLogsTool(self.db, self.es)
            audit_result = await audit_tool.execute(
                limit=10,
                _context=self.context
            )
            
            if audit_result.get("success"):
                total = audit_result.get("total", 0)
                self.log_test("감사 로그", "success", f"감사 로그 조회 성공 ({total}건)")
            else:
                self.log_test("감사 로그", "error", "감사 로그 조회 실패", audit_result)
                
        except Exception as e:
            self.log_test("감사 로그", "error", f"예외 발생: {str(e)}")
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "="*80)
        print(" "*20 + "MCP Servers 통합 테스트 시작")
        print("="*80)
        
        # DB/ES 연결 확인
        try:
            await self.db.initialize()
            await self.es.initialize()
            print("✅ DB/ES 연결 성공\n")
        except Exception as e:
            print(f"❌ DB/ES 연결 실패: {str(e)}\n")
            return
        
        # 각 테스트 시나리오 실행
        await self.test_01_authentication_flow()
        await self.test_02_document_crud()
        await self.test_03_search_integration()
        await self.test_04_version_management()
        await self.test_05_audit_logs()
        
        # 결과 요약
        self.print_summary()
        
        # 정리
        await self.db.close()
        await self.es.close()
    
    def print_summary(self):
        """테스트 결과 요약"""
        print("\n" + "="*80)
        print(" "*30 + "테스트 결과 요약")
        print("="*80)
        
        total = len(self.test_results)
        success = sum(1 for r in self.test_results if r["status"] == "success")
        error = sum(1 for r in self.test_results if r["status"] == "error")
        warning = sum(1 for r in self.test_results if r["status"] == "warning")
        
        print(f"\n총 테스트: {total}개")
        print(f"✅ 성공: {success}개")
        print(f"❌ 실패: {error}개")
        print(f"⚠️  경고: {warning}개")
        
        success_rate = (success / total * 100) if total > 0 else 0
        print(f"\n성공률: {success_rate:.1f}%")
        
        if error == 0:
            print("\n" + "="*80)
            print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("⚠️  일부 테스트가 실패했습니다. 로그를 확인해주세요.")
            print("="*80)


async def main():
    """메인 함수"""
    test = MCPServersIntegrationTest()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
