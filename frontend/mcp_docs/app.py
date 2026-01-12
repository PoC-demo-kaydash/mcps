"""
Reflex 애플리케이션

메인 앱 엔트리포인트 및 라우팅
"""

import reflex as rx
from frontend.styles.theme import theme

# Pages
from frontend.pages.index import index
from frontend.pages.login import login
from frontend.pages.dashboard import dashboard
from frontend.pages.documents.list import documents_list
from frontend.pages.documents.detail import document_detail
from frontend.pages.documents.create import document_create
from frontend.pages.documents.edit import document_edit
from frontend.pages.search import search
from frontend.pages.admin.users import admin_users
from frontend.pages.admin.stats import admin_stats

# 앱 생성
app = rx.App(theme=theme)

# 라우트 등록
app.add_page(index, route="/", title="홈 | MCP Docs")
app.add_page(login, route="/login", title="로그인 | MCP Docs")
app.add_page(dashboard, route="/dashboard", title="대시보드 | MCP Docs")

# 문서 라우트
app.add_page(documents_list, route="/documents", title="문서 목록 | MCP Docs")
app.add_page(document_detail, route="/documents/[doc_id]", title="문서 상세 | MCP Docs")
app.add_page(document_create, route="/documents/create", title="문서 생성 | MCP Docs")
app.add_page(document_edit, route="/documents/[doc_id]/edit", title="문서 수정 | MCP Docs")

# 검색
app.add_page(search, route="/search", title="검색 | MCP Docs")

# 관리자
app.add_page(admin_users, route="/admin/users", title="사용자 관리 | MCP Docs")
app.add_page(admin_stats, route="/admin/stats", title="통계 | MCP Docs")
