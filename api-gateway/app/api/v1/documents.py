"""
Document management API endpoints
"""
from fastapi import APIRouter, Depends, Query, Path
from typing import Dict, Any, Optional, List
from ...models.request import CreateDocumentRequest, UpdateDocumentRequest
from ...models.response import (
    SuccessResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentVersionResponse
)
from ...services.mcp_client import MCPClient
from ...core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.get("", response_model=SuccessResponse[DocumentListResponse])
async def list_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    category_id: Optional[int] = Query(default=None, description="Filter by category"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get list of documents
    
    Requires authentication.
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of documents per page
        status: Filter by document status (draft, published, archived)
        category_id: Filter by category ID
        
    Returns:
        Paginated list of documents
    """
    mcp_client = MCPClient()
    
    try:
        # Build query parameters
        params = {
            "page": page,
            "page_size": page_size
        }
        if status:
            params["status"] = status
        if category_id:
            params["category_id"] = category_id
        
        # Get documents from MCP Host
        response = await mcp_client.get(
            "/api/documents",
            params=params,
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        documents_data = response.get("data", {})
        
        # Convert to response model
        documents = [
            DocumentResponse(**doc)
            for doc in documents_data.get("documents", [])
        ]
        
        response_data = DocumentListResponse(
            documents=documents,
            total=documents_data.get("total", 0),
            page=page,
            page_size=page_size
        )
        
        return SuccessResponse(data=response_data)
        
    finally:
        await mcp_client.close()


@router.get("/{doc_id}", response_model=SuccessResponse[DocumentResponse])
async def get_document(
    doc_id: int = Path(..., description="Document ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get document by ID
    
    Requires authentication.
    
    Args:
        doc_id: Document ID
        
    Returns:
        Document details
    """
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.get(
            f"/api/documents/{doc_id}",
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        doc_data = response.get("data", {})
        document = DocumentResponse(**doc_data)
        
        return SuccessResponse(data=document)
        
    finally:
        await mcp_client.close()


@router.post("", response_model=SuccessResponse[DocumentResponse])
async def create_document(
    request: CreateDocumentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new document
    
    Requires authentication.
    
    Args:
        request: Document creation request
        
    Returns:
        Created document
    """
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.post(
            "/api/documents",
            json=request.dict(exclude_none=True),
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        doc_data = response.get("data", {})
        document = DocumentResponse(**doc_data)
        
        return SuccessResponse(data=document)
        
    finally:
        await mcp_client.close()


@router.put("/{doc_id}", response_model=SuccessResponse[DocumentResponse])
async def update_document(
    doc_id: int = Path(..., description="Document ID"),
    request: UpdateDocumentRequest = ...,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a document
    
    Requires authentication.
    
    Args:
        doc_id: Document ID
        request: Document update request
        
    Returns:
        Updated document
    """
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.put(
            f"/api/documents/{doc_id}",
            json=request.dict(exclude_none=True),
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        doc_data = response.get("data", {})
        document = DocumentResponse(**doc_data)
        
        return SuccessResponse(data=document)
        
    finally:
        await mcp_client.close()


@router.delete("/{doc_id}", response_model=SuccessResponse[Dict[str, str]])
async def delete_document(
    doc_id: int = Path(..., description="Document ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a document (soft delete)
    
    Requires authentication.
    
    Args:
        doc_id: Document ID
        
    Returns:
        Confirmation message
    """
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.delete(
            f"/api/documents/{doc_id}",
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        return SuccessResponse(data={"message": f"Document {doc_id} deleted successfully"})
        
    finally:
        await mcp_client.close()


@router.get("/{doc_id}/versions", response_model=SuccessResponse[List[DocumentVersionResponse]])
async def get_document_versions(
    doc_id: int = Path(..., description="Document ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get document version history
    
    Requires authentication.
    
    Args:
        doc_id: Document ID
        
    Returns:
        List of document versions
    """
    mcp_client = MCPClient()
    
    try:
        response = await mcp_client.get(
            f"/api/documents/{doc_id}/versions",
            headers={"X-Session-ID": current_user.get("session_id")}
        )
        
        versions_data = response.get("data", {}).get("versions", [])
        versions = [DocumentVersionResponse(**v) for v in versions_data]
        
        return SuccessResponse(data=versions)
        
    finally:
        await mcp_client.close()
