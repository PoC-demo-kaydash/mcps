# Finance Team Custom Tools

재무팀 전용 커스텀 Tool 모음입니다.

## Tool 목록

### 1. Budget Tool (예산 관리)
- **파일**: `budget_tool.py`
- **기능**: 예산 조회, 집행 현황, 승인
- **권한**: staff 이상

### 2. Expense Tool (지출 관리)
- **파일**: `expense_tool.py`
- **기능**: 지출 내역 조회, 승인, 정산
- **권한**: staff 이상

## 사용 예제

### Budget Tool

```python
from mcp_tools.custom.finance.budget_tool import BudgetTool

# Tool 초기화
tool = BudgetTool()

# 예산 조회
result = await tool.execute({
    "budget_id": "B2026001",
    "year": 2026
}, context={"user_id": "F001"})

# 결과
{
    "success": True,
    "data": {
        "budget_id": "B2026001",
        "department": "IT",
        "total_amount": 100000000,
        "spent_amount": 45000000,
        "remaining": 55000000,
        "status": "active"
    }
}
```

### Expense Tool

```python
from mcp_tools.custom.finance.expense_tool import ExpenseTool

# Tool 초기화
tool = ExpenseTool()

# 지출 내역 조회
result = await tool.execute({
    "expense_id": "E2026001",
    "status": "pending"
}, context={"user_id": "F001"})

# 결과
{
    "success": True,
    "data": {
        "expense_id": "E2026001",
        "requester": "김직원",
        "amount": 500000,
        "category": "여비교통비",
        "status": "pending",
        "created_at": "2026-01-10"
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
Finance Custom Tool Template
"""

from mcp_tools.base import BaseTool
from shared.database import DatabaseManager
from shared.permissions import PermissionEngine

class MyFinanceTool(BaseTool):
    """재무팀 커스텀 Tool"""
    
    def __init__(self):
        super().__init__(
            name="my_finance_tool",
            description="Tool 설명",
            category="custom",
            department="finance"
        )
        self.db = None
        self.perm_engine = PermissionEngine()
    
    async def execute(self, params: dict, context: dict) -> dict:
        """Tool 실행"""
        # 1. 권한 체크
        user_id = context.get("user_id")
        if not self._check_permission(user_id):
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
    
    def _check_permission(self, user_id: str) -> bool:
        """권한 확인"""
        return self.perm_engine.check_permission(
            user_id=user_id,
            resource_type="tool",
            resource_id=f"custom_finance_{self.name}",
            action="execute"
        )
    
    async def _execute_logic(self, params: dict) -> dict:
        """비즈니스 로직 구현"""
        # TODO: 구현
        return {}
```

## 데이터베이스 스키마

재무팀 Tool에서 사용하는 테이블:

```sql
-- 예산 테이블
CREATE TABLE budgets (
    budget_id VARCHAR(20) PRIMARY KEY,
    department VARCHAR(50),
    year INT,
    total_amount DECIMAL(15,2),
    spent_amount DECIMAL(15,2),
    status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 지출 테이블
CREATE TABLE expenses (
    expense_id VARCHAR(20) PRIMARY KEY,
    budget_id VARCHAR(20),
    requester_id VARCHAR(20),
    amount DECIMAL(15,2),
    category VARCHAR(50),
    description TEXT,
    status VARCHAR(20),
    created_at TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by VARCHAR(20)
);
```

## 테스트

```bash
# 단위 테스트 실행
pytest tests/unit/custom/finance/

# 통합 테스트 실행
pytest tests/integration/custom/finance/
```

## 배포

```bash
# Tool 등록
python scripts/register_custom_tool.py --department finance --tool budget_tool

# 서비스 재시작
./scripts/control/restart_service.sh mcp-host
```

## 문의

재무팀 Tool 관련 문의:
- 담당자: finance-team@company.com
- Slack: #finance-mcp-tools

---

**Owner**: Finance Team  
**Last Updated**: 2026-01-12
