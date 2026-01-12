"""
API 라우트

REST API 엔드포인트 정의
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from models.session import SessionCreate, SessionResponse, SessionInfo
from models.server import ServerInfo, ServerListResponse, ServerActionRequest, ServerActionResponse
from models.request import ToolExecuteRequest, ToolExecuteResponse, ToolListResponse, ToolInfo
from api.schemas import SuccessResponse, ErrorResponse, ErrorDetail, HealthCheckResponse

router = APIRouter(prefix="/api")

# 전역 의존성 (main.py에서 주입)
_server_manager = None
_session_manager = None
_router = None
_executor = None
_metrics = None


def setup_dependencies(server_manager, session_manager, tool_router, executor, metrics):
    """의존성 주입"""
    global _server_manager, _session_manager, _router, _executor, _metrics
    _server_manager = server_manager
    _session_manager = session_manager
    _router = tool_router
    _executor = executor
    _metrics = metrics


async def get_session(session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """세션 검증 의존성"""
    if not session_id:
        raise HTTPException(status_code=401, detail="Session ID required")
    
    session = _session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return session


# ==================== 세션 API ====================

@router.post("/sessions", response_model=SuccessResponse)
async def create_session(request: SessionCreate):
    """
    세션 생성 (로그인)
    
    - **username**: 사용자 ID
    - **password**: 비밀번호
    """
    session = await _session_manager.create_session(request.username, request.password)
    
    if not session:
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    _metrics.record_session_created()
    
    response = SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        user_role=session.user_role,
        user_team=session.user_team,
        expires_at=session.expires_at
    )
    
    return SuccessResponse(data=response)


@router.get("/sessions/{session_id}", response_model=SuccessResponse)
async def get_session_info(session_id: str):
    """
    세션 정보 조회
    
    - **session_id**: 세션 ID
    """
    session = _session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    info = SessionInfo(
        session_id=session.session_id,
        user_id=session.user_id,
        user_role=session.user_role,
        user_team=session.user_team,
        created_at=session.created_at,
        expires_at=session.expires_at,
        last_activity=session.last_activity
    )
    
    return SuccessResponse(data=info)


@router.delete("/sessions/{session_id}", response_model=SuccessResponse)
async def delete_session(session_id: str):
    """
    세션 삭제 (로그아웃)
    
    - **session_id**: 세션 ID
    """
    success = _session_manager.delete_session(session_id)
    
    if success:
        _metrics.record_session_deleted()
    
    return SuccessResponse(data={"deleted": success})


# ==================== Tool API ====================

@router.post("/tools/execute", response_model=SuccessResponse)
async def execute_tool(request: ToolExecuteRequest, session = Depends(get_session)):
    """
    Tool 실행
    
    - **tool_name**: Tool 이름
    - **arguments**: Tool 인자
    - **session_id**: 세션 ID (헤더: X-Session-ID)
    """
    # 사용자 컨텍스트
    user_context = {
        "user_id": session.user_id,
        "user_role": session.user_role,
        "user_team": session.user_team
    }
    
    # Tool 실행
    result = await _executor.execute_tool(
        tool_name=request.tool_name,
        arguments=request.arguments,
        user_context=user_context
    )
    
    # 메트릭 기록
    server_name = _router.get_server_for_tool(request.tool_name)
    if server_name:
        _metrics.record_tool_call(
            tool_name=request.tool_name,
            server_name=server_name,
            execution_time=result.get("execution_time", 0.0),
            is_error=(result.get("status") == "error")
        )
    
    # 응답
    response = ToolExecuteResponse(
        tool_name=request.tool_name,
        status=result.get("status", "error"),
        result=result.get("result"),
        error=result.get("error"),
        execution_time=result.get("execution_time", 0.0)
    )
    
    return SuccessResponse(data=response)


@router.get("/tools/list", response_model=SuccessResponse)
async def list_tools():
    """
    Tool 목록 조회
    
    전체 Tool 목록 반환
    """
    tools_data = _router.list_all_tools()
    
    tools = []
    for tool_data in tools_data:
        server_name = tool_data.get("server")
        is_running = _server_manager.is_running(server_name) if server_name else False
        
        tool_info = ToolInfo(
            name=tool_data.get("name"),
            server=server_name,
            category=tool_data.get("category", "unknown"),
            description=tool_data.get("description", ""),
            input_schema=tool_data.get("inputSchema", {}),
            required_permissions=tool_data.get("requiredPermissions", []),
            available=is_running
        )
        tools.append(tool_info)
    
    response = ToolListResponse(
        tools=tools,
        total=len(tools),
        available=sum(1 for t in tools if t.available)
    )
    
    return SuccessResponse(data=response)


@router.get("/tools/{tool_name}", response_model=SuccessResponse)
async def get_tool_info(tool_name: str):
    """
    Tool 상세 정보 조회
    
    - **tool_name**: Tool 이름
    """
    tool_data = _router.get_tool_metadata(tool_name)
    
    if not tool_data:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    server_name = tool_data.get("server")
    is_running = _server_manager.is_running(server_name) if server_name else False
    
    tool_info = ToolInfo(
        name=tool_data.get("name"),
        server=server_name,
        category=tool_data.get("category", "unknown"),
        description=tool_data.get("description", ""),
        input_schema=tool_data.get("inputSchema", {}),
        required_permissions=tool_data.get("requiredPermissions", []),
        available=is_running
    )
    
    return SuccessResponse(data=tool_info)


# ==================== Server API ====================

@router.get("/servers", response_model=SuccessResponse)
async def list_servers():
    """
    Server 목록 조회
    
    전체 Server 상태 반환
    """
    servers_data = _server_manager.list_servers()
    
    servers = [ServerInfo(**data) for data in servers_data]
    
    response = ServerListResponse(
        servers=servers,
        total=len(servers),
        running=sum(1 for s in servers if s.status == "running")
    )
    
    return SuccessResponse(data=response)


@router.get("/servers/{server_name}", response_model=SuccessResponse)
async def get_server_info(server_name: str):
    """
    Server 정보 조회
    
    - **server_name**: Server 이름
    """
    info = _server_manager.get_server_info(server_name)
    
    if not info:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server_info = ServerInfo(**info)
    
    return SuccessResponse(data=server_info)


@router.post("/servers/action", response_model=SuccessResponse)
async def server_action(request: ServerActionRequest):
    """
    Server 액션 실행
    
    - **server_name**: Server 이름
    - **action**: 액션 (start, stop, restart)
    """
    action = request.action.lower()
    server_name = request.server_name
    
    success = False
    message = ""
    
    if action == "start":
        success = _server_manager.start_server(server_name)
        message = f"Server started: {server_name}" if success else f"Failed to start server: {server_name}"
    
    elif action == "stop":
        success = _server_manager.stop_server(server_name)
        message = f"Server stopped: {server_name}" if success else f"Failed to stop server: {server_name}"
    
    elif action == "restart":
        success = _server_manager.restart_server(server_name)
        message = f"Server restarted: {server_name}" if success else f"Failed to restart server: {server_name}"
    
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
    
    response = ServerActionResponse(
        server_name=server_name,
        action=action,
        status="success" if success else "error",
        message=message,
        timestamp=datetime.utcnow()
    )
    
    return SuccessResponse(data=response)


# ==================== 헬스 체크 ====================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    헬스 체크
    
    시스템 전체 상태 확인
    """
    server_health = _server_manager.health_check()
    
    status = "healthy" if server_health["healthy"] else "degraded"
    
    response = HealthCheckResponse(
        status=status,
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        servers=server_health
    )
    
    return response


# ==================== 메트릭 API ====================

@router.get("/metrics", response_model=SuccessResponse)
async def get_metrics():
    """
    메트릭 조회
    
    Tool 및 Server 실행 통계
    """
    stats = _metrics.get_all_stats()
    
    return SuccessResponse(data=stats)
