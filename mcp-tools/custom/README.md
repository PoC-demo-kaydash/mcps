# Custom Tools

부서별 커스텀 Tool을 관리하는 디렉토리입니다.

## 개요

각 부서는 자체적으로 필요한 Tool을 개발하여 이 디렉토리에 추가할 수 있습니다.
Core Tools와 동일한 구조와 인터페이스를 따라야 합니다.

## 디렉토리 구조

```
custom/
├── README.md           # 이 파일
├── finance/            # 재무팀 커스텀 Tool
│   ├── __init__.py
│   ├── README.md
│   ├── budget_tool.py
│   └── expense_tool.py
└── hr/                 # 인사팀 커스텀 Tool
    ├── __init__.py
    ├── README.md
    ├── employee_tool.py
    └── attendance_tool.py
```

## Tool 개발 가이드

### 1. 기본 구조

모든 커스텀 Tool은 `BaseTool`을 상속받아야 합니다.

```python
from mcp_tools.base import BaseTool

class MyCustomTool(BaseTool):
    """
    커스텀 Tool 설명
    """
    
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="Tool 설명",
            category="custom",
            department="finance"  # 부서명
        )
    
    async def execute(self, params: dict, context: dict) -> dict:
        """Tool 실행 로직"""
        # 구현
        return {"success": True, "data": {}}
    
    def validate_params(self, params: dict) -> bool:
        """파라미터 검증"""
        # 구현
        return True
```

### 2. Tool 메타데이터 (tool.yaml)

각 Tool은 YAML 메타데이터를 포함해야 합니다.

```yaml
name: my_custom_tool
version: 1.0.0
description: 커스텀 Tool 설명

category: custom
department: finance
owner: finance_team@company.com

parameters:
  - name: param1
    type: string
    required: true
    description: 파라미터 설명

returns:
  type: object
  properties:
    success:
      type: boolean
    data:
      type: object

dependencies:
  - shared.database
  - shared.permissions

permissions:
  required_role: staff
  department_only: true
```

### 3. Tool 등록

Tool을 개발한 후 MCP Host에 등록해야 합니다.

#### 자동 등록 (권장)

```bash
# Tool 등록 스크립트 실행
python scripts/register_custom_tool.py \
  --department finance \
  --tool budget_tool
```

#### 수동 등록

`config/registry.json`에 추가:

```json
{
  "tool_id": "custom_finance_budget",
  "name": "budget_tool",
  "category": "custom",
  "department": "finance",
  "module": "mcp_tools.custom.finance.budget_tool",
  "class": "BudgetTool",
  "enabled": true
}
```

### 4. 테스트 작성

커스텀 Tool도 테스트를 작성해야 합니다.

```python
# tests/unit/custom/test_budget_tool.py
import pytest
from mcp_tools.custom.finance.budget_tool import BudgetTool

@pytest.mark.asyncio
async def test_budget_tool_execute():
    tool = BudgetTool()
    params = {"budget_id": "B001", "year": 2026}
    result = await tool.execute(params, context={})
    
    assert result["success"] is True
    assert "budget" in result["data"]
```

## 부서별 Tool 목록

### Finance (재무팀)

| Tool | 설명 | 상태 |
|------|------|------|
| budget_tool | 예산 조회/관리 | 예제 |
| expense_tool | 지출 내역 관리 | 예제 |

### HR (인사팀)

| Tool | 설명 | 상태 |
|------|------|------|
| employee_tool | 직원 정보 조회 | 예제 |
| attendance_tool | 근태 관리 | 예제 |

## 개발 절차

1. **기획**: Tool 요구사항 정의
2. **설계**: 인터페이스 및 메타데이터 작성
3. **개발**: Tool 구현
4. **테스트**: 단위 테스트 작성 및 실행
5. **등록**: MCP Host에 Tool 등록
6. **배포**: 운영 환경에 배포
7. **문서화**: README 및 사용 가이드 작성

## 권한 관리

커스텀 Tool은 부서별 권한을 설정할 수 있습니다.

```python
# Tool 실행 시 권한 체크
from shared.permissions import PermissionEngine

perm_engine = PermissionEngine()
has_permission = perm_engine.check_permission(
    user_id=context["user_id"],
    resource_type="tool",
    resource_id="custom_finance_budget",
    action="execute"
)
```

## 보안 주의사항

1. **입력 검증**: 모든 파라미터를 철저히 검증
2. **SQL Injection 방지**: Parameterized Query 사용
3. **권한 체크**: Tool 실행 전 권한 확인
4. **민감 정보 처리**: 로그에 민감 정보 노출 금지
5. **에러 처리**: 상세한 에러 메시지 반환 금지

## 성능 가이드라인

- **응답 시간**: < 2초 (목표)
- **메모리 사용**: < 100MB
- **DB 쿼리**: 최소화, 인덱스 활용
- **캐싱**: 자주 조회되는 데이터는 캐싱

## 문의

커스텀 Tool 개발 관련 문의:
- Tech Lead: tech-lead@company.com
- Slack: #mcp-custom-tools

---

**Last Updated**: 2026-01-12  
**Version**: 1.0.0
