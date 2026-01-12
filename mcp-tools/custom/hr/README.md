# HR Team Custom Tools

인사팀 전용 커스텀 Tool 모음입니다.

## Tool 목록

### 1. Employee Tool (직원 정보 관리)
- **파일**: `employee_tool.py`
- **기능**: 직원 정보 조회, 수정, 이력 관리
- **권한**: staff 이상 (본인 정보는 junior도 조회 가능)

### 2. Attendance Tool (근태 관리)
- **파일**: `attendance_tool.py`
- **기능**: 근태 기록, 휴가 신청, 승인
- **권한**: staff 이상

## 사용 예제

### Employee Tool

```python
from mcp_tools.custom.hr.employee_tool import EmployeeTool

# Tool 초기화
tool = EmployeeTool()

# 직원 정보 조회
result = await tool.execute({
    "employee_id": "E001",
    "action": "get"
}, context={"user_id": "H001"})

# 결과
{
    "success": True,
    "data": {
        "employee_id": "E001",
        "name": "김직원",
        "department": "IT",
        "position": "Staff",
        "email": "kim@company.com",
        "hire_date": "2020-01-01",
        "status": "active"
    }
}
```

### Attendance Tool

```python
from mcp_tools.custom.hr.attendance_tool import AttendanceTool

# Tool 초기화
tool = AttendanceTool()

# 휴가 신청
result = await tool.execute({
    "employee_id": "E001",
    "leave_type": "annual",
    "start_date": "2026-01-20",
    "end_date": "2026-01-21",
    "reason": "개인 사유",
    "action": "request_leave"
}, context={"user_id": "E001"})

# 결과
{
    "success": True,
    "data": {
        "leave_request_id": "L2026001",
        "status": "pending",
        "days": 2
    }
}
```

## 개발 가이드

### 새 Tool 추가

1. `<tool_name>_tool.py` 파일 생성
2. `BaseTool` 상속받아 구현
3. `tool.yaml` 메타데이터 작성
4. 테스트 코드 작성
5. Tool 등록

### Tool 템플릿

```python
"""
HR Custom Tool Template
"""

from mcp_tools.base import BaseTool
from shared.database import DatabaseManager
from shared.permissions import PermissionEngine

class MyHRTool(BaseTool):
    """인사팀 커스텀 Tool"""
    
    def __init__(self):
        super().__init__(
            name="my_hr_tool",
            description="Tool 설명",
            category="custom",
            department="hr"
        )
        self.db = None
        self.perm_engine = PermissionEngine()
    
    async def execute(self, params: dict, context: dict) -> dict:
        """Tool 실행"""
        # 1. 권한 체크
        user_id = context.get("user_id")
        if not self._check_permission(user_id, params):
            return {"success": False, "error": "Permission denied"}
        
        # 2. 파라미터 검증
        if not self.validate_params(params):
            return {"success": False, "error": "Invalid parameters"}
        
        # 3. 비즈니스 로직
        try:
            result = await self._execute_logic(params)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_params(self, params: dict) -> bool:
        """파라미터 검증"""
        required = ["param1", "param2"]
        return all(k in params for k in required)
    
    def _check_permission(self, user_id: str, params: dict) -> bool:
        """권한 확인"""
        user_info = self.perm_engine.get_user_info(user_id)
        
        # 인사팀 또는 본인 정보 조회
        is_hr = user_info.get("department") == "hr"
        is_self = user_id == params.get("employee_id")
        
        return is_hr or is_self
    
    async def _execute_logic(self, params: dict) -> dict:
        """비즈니스 로직 구현"""
        # TODO: 구현
        return {}
```

## 데이터베이스 스키마

인사팀 Tool에서 사용하는 테이블:

```sql
-- 직원 테이블
CREATE TABLE employees (
    employee_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(50),
    position VARCHAR(50),
    email VARCHAR(100),
    hire_date DATE,
    status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 근태 테이블
CREATE TABLE attendance (
    attendance_id VARCHAR(20) PRIMARY KEY,
    employee_id VARCHAR(20),
    date DATE,
    check_in TIME,
    check_out TIME,
    status VARCHAR(20),
    created_at TIMESTAMP
);

-- 휴가 테이블
CREATE TABLE leave_requests (
    leave_request_id VARCHAR(20) PRIMARY KEY,
    employee_id VARCHAR(20),
    leave_type VARCHAR(20),
    start_date DATE,
    end_date DATE,
    days INT,
    reason TEXT,
    status VARCHAR(20),
    approved_by VARCHAR(20),
    approved_at TIMESTAMP,
    created_at TIMESTAMP
);
```

## 개인정보 보호

인사 정보는 민감한 개인정보이므로 특별한 주의가 필요합니다.

### 보안 규칙

1. **접근 제한**: 인사팀 또는 본인만 조회 가능
2. **로그 마스킹**: 주민번호, 계좌번호 등 로그에 기록 금지
3. **암호화**: 민감 정보는 DB에 암호화 저장
4. **감사 로그**: 모든 접근 이력 기록

### 예제: 마스킹 처리

```python
def mask_sensitive_data(data: dict) -> dict:
    """민감 정보 마스킹"""
    if "ssn" in data:
        data["ssn"] = data["ssn"][:6] + "******"
    if "account_number" in data:
        data["account_number"] = "****" + data["account_number"][-4:]
    return data
```

## 테스트

```bash
# 단위 테스트 실행
pytest tests/unit/custom/hr/

# 통합 테스트 실행
pytest tests/integration/custom/hr/
```

## 배포

```bash
# Tool 등록
python scripts/register_custom_tool.py --department hr --tool employee_tool

# 서비스 재시작
./scripts/control/restart_service.sh mcp-host
```

## 문의

인사팀 Tool 관련 문의:
- 담당자: hr-team@company.com
- Slack: #hr-mcp-tools

---

**Owner**: HR Team  
**Last Updated**: 2026-01-12
