"""
Security utilities for JWT tokens and password hashing
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from .config import settings
from .exceptions import AuthenticationError

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_session_token(user_id: str, session_id: str) -> str:
    """
    Create a session token for API Gateway
    
    Args:
        user_id: User ID
        session_id: Session ID from MCP Host
        
    Returns:
        JWT token string
    """
    data = {
        "sub": user_id,
        "session_id": session_id,
        "type": "session"
    }
    return create_access_token(data)


def verify_session_token(token: str) -> tuple[str, str]:
    """
    Verify session token and extract user_id and session_id
    
    Args:
        token: JWT token string
        
    Returns:
        Tuple of (user_id, session_id)
        
    Raises:
        AuthenticationError: If token is invalid or missing required fields
    """
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    token_type = payload.get("type")
    
    if not user_id or not session_id:
        raise AuthenticationError("Invalid token: missing user_id or session_id")
    
    if token_type != "session":
        raise AuthenticationError("Invalid token type")
    
    return user_id, session_id
