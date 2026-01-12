"""
상수

애플리케이션 상수
"""

import os

# API Gateway URL
API_BASE_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8080")

# 역할
ROLES = ["junior", "staff", "manager", "executive", "admin"]

# 역할 레벨
ROLE_LEVELS = {
    "junior": 1,
    "staff": 2,
    "manager": 3,
    "executive": 4,
    "admin": 5,
}

# 공개 범위
CLASSIFICATIONS = ["public", "team", "department", "confidential"]

# 공개 범위 색상
CLASSIFICATION_COLORS = {
    "public": "blue",
    "team": "green",
    "department": "orange",
    "confidential": "red",
}

# 역할 색상
ROLE_COLORS = {
    "junior": "gray",
    "staff": "blue",
    "manager": "purple",
    "executive": "orange",
    "admin": "red",
}

# 상태 색상
STATUS_COLORS = {
    "draft": "gray",
    "published": "green",
    "archived": "orange",
}
