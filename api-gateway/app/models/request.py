"""
Request models for API endpoints
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """Request model for creating a new session"""
    user_id: str = Field(..., description="User ID")
    password: Optional[str] = Field(None, description="User password (if required)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional session metadata")


class ExecuteToolRequest(BaseModel):
    """Request model for executing a tool"""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    session_id: Optional[str] = Field(None, description="Session ID (if not using current user session)")


class CreateDocumentRequest(BaseModel):
    """Request model for creating a document"""
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(..., description="Document content")
    category_id: Optional[int] = Field(None, description="Category ID")
    tags: Optional[List[str]] = Field(default_factory=list, description="Document tags")
    status: Optional[str] = Field(default="draft", description="Document status (draft, published, archived)")


class UpdateDocumentRequest(BaseModel):
    """Request model for updating a document"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Document title")
    content: Optional[str] = Field(None, description="Document content")
    category_id: Optional[int] = Field(None, description="Category ID")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    status: Optional[str] = Field(None, description="Document status (draft, published, archived)")


class GrantPermissionRequest(BaseModel):
    """Request model for granting permission"""
    user_id: str = Field(..., description="User ID to grant permission to")
    resource_type: str = Field(..., description="Resource type (document, category, etc.)")
    resource_id: str = Field(..., description="Resource ID")
    permission_level: str = Field(..., description="Permission level (read, write, manage)")
    expires_at: Optional[str] = Field(None, description="Expiration datetime (ISO format)")


class RevokePermissionRequest(BaseModel):
    """Request model for revoking permission"""
    user_id: str = Field(..., description="User ID to revoke permission from")
    resource_type: str = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource ID")


class LoginRequest(BaseModel):
    """Request model for user login"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
