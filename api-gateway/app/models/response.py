"""
Response models for API endpoints
"""
from typing import Optional, Dict, Any, List, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional error details")


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = Field(default="error", description="Response status")
    error: ErrorDetail = Field(..., description="Error details")


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response model"""
    status: str = Field(default="success", description="Response status")
    data: T = Field(..., description="Response data")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
    version: str = Field(default="1.0.0", description="API version")
    mcp_host_status: Optional[str] = Field(None, description="MCP Host status")
    redis_status: Optional[str] = Field(None, description="Redis status")


class SessionResponse(BaseModel):
    """Session response model"""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    token: Optional[str] = Field(None, description="JWT token for this session")
    created_at: datetime = Field(..., description="Session creation time")
    expires_at: datetime = Field(..., description="Session expiration time")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session metadata")


class ToolInfo(BaseModel):
    """Tool information model"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    server: str = Field(..., description="Server name")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tool parameters schema")


class ToolListResponse(BaseModel):
    """Tool list response"""
    tools: List[ToolInfo] = Field(..., description="List of available tools")
    total: int = Field(..., description="Total number of tools")


class ToolExecutionResponse(BaseModel):
    """Tool execution response"""
    tool_name: str = Field(..., description="Executed tool name")
    result: Any = Field(..., description="Execution result")
    execution_time: float = Field(..., description="Execution time in seconds")
    success: bool = Field(..., description="Execution success status")
    error: Optional[str] = Field(None, description="Error message if failed")


class DocumentResponse(BaseModel):
    """Document response model"""
    id: int = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    category_id: Optional[int] = Field(None, description="Category ID")
    category_name: Optional[str] = Field(None, description="Category name")
    author_id: str = Field(..., description="Author user ID")
    author_name: Optional[str] = Field(None, description="Author name")
    status: str = Field(..., description="Document status")
    version: int = Field(..., description="Document version")
    view_count: int = Field(default=0, description="View count")
    tags: Optional[List[str]] = Field(default_factory=list, description="Document tags")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")


class DocumentListResponse(BaseModel):
    """Document list response"""
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=20, description="Page size")


class DocumentVersionResponse(BaseModel):
    """Document version response"""
    version_id: int = Field(..., description="Version ID")
    document_id: int = Field(..., description="Document ID")
    version: int = Field(..., description="Version number")
    content: str = Field(..., description="Version content")
    changed_by: str = Field(..., description="User who made the change")
    change_summary: Optional[str] = Field(None, description="Change summary")
    created_at: datetime = Field(..., description="Version creation time")


class UserResponse(BaseModel):
    """User response model"""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email")
    role: str = Field(..., description="User role")
    team_id: Optional[str] = Field(None, description="Team ID")
    team_name: Optional[str] = Field(None, description="Team name")
    created_at: datetime = Field(..., description="Account creation time")
    last_login_at: Optional[datetime] = Field(None, description="Last login time")


class PermissionResponse(BaseModel):
    """Permission response model"""
    permission_id: int = Field(..., description="Permission ID")
    user_id: str = Field(..., description="User ID")
    resource_type: str = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource ID")
    permission_level: str = Field(..., description="Permission level")
    granted_by: str = Field(..., description="User who granted the permission")
    granted_at: datetime = Field(..., description="Grant time")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


class SystemStatsResponse(BaseModel):
    """System statistics response"""
    total_users: int = Field(..., description="Total number of users")
    active_sessions: int = Field(..., description="Active sessions count")
    total_documents: int = Field(..., description="Total documents count")
    total_tools: int = Field(..., description="Total tools count")
    total_audit_logs: int = Field(..., description="Total audit logs count")
    uptime_seconds: float = Field(..., description="System uptime in seconds")


class AuditLogResponse(BaseModel):
    """Audit log response model"""
    log_id: int = Field(..., description="Log ID")
    user_id: str = Field(..., description="User ID")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional details")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    created_at: datetime = Field(..., description="Log creation time")


class AuditLogListResponse(BaseModel):
    """Audit log list response"""
    logs: List[AuditLogResponse] = Field(..., description="List of audit logs")
    total: int = Field(..., description="Total number of logs")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=50, description="Page size")
