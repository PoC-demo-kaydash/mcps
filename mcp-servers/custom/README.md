# Custom MCP Servers

부서별 커스텀 MCP Server를 관리하는 디렉토리입니다.

## 개요

각 부서는 자체적으로 필요한 MCP Server를 개발하여 이 디렉토리에 추가할 수 있습니다.
Core MCP Servers와 동일한 구조와 프로토콜을 따라야 합니다.

## 디렉토리 구조

```
custom/
├── README.md           # 이 파일
├── finance_server/     # 재무팀 커스텀 Server (예제)
│   ├── main.py
│   ├── server.yaml
│   └── requirements.txt
└── hr_server/          # 인사팀 커스텀 Server (예제)
    ├── main.py
    ├── server.yaml
    └── requirements.txt
```

## Server 개발 가이드

### 1. 기본 구조

모든 커스텀 Server는 MCP Protocol을 따라야 합니다.

```python
"""
Custom MCP Server Template
"""

import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.mcp_protocol import MCPProtocol
from shared.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("custom_server")


class CustomServer:
    """커스텀 MCP Server"""
    
    def __init__(self):
        self.protocol = MCPProtocol()
        self.tools = {}
    
    async def initialize(self):
        """리소스 초기화"""
        logger.info("CustomServer initializing...")
        # Tool 등록
        await self._register_tools()
    
    async def _register_tools(self):
        """Tool 등록"""
        from mcp_tools.custom.department.my_tool import MyTool
        
        tool = MyTool()
        await tool.initialize(config)
        self.tools[tool.name] = tool
    
    async def handle_request(self, request: dict) -> dict:
        """요청 처리"""
        method = request.get("method")
        
        if method == "tools/list":
            return self._list_tools()
        elif method == "tools/call":
            return await self._call_tool(request)
        else:
            return self.protocol.error_response(
                request.get("id"),
                -32601,
                f"Method not found: {method}"
            )
    
    def _list_tools(self) -> dict:
        """Tool 목록 반환"""
        tools = [
            {
                "name": name,
                "description": tool.description,
                "category": tool.category
            }
            for name, tool in self.tools.items()
        ]
        return {"tools": tools}
    
    async def _call_tool(self, request: dict) -> dict:
        """Tool 실행"""
        params = request.get("params", {})
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return self.protocol.error_response(
                request.get("id"),
                -32602,
                f"Tool not found: {tool_name}"
            )
        
        tool = self.tools[tool_name]
        result = await tool.execute(tool_params, context={})
        
        return self.protocol.success_response(
            request.get("id"),
            result
        )
    
    async def run(self):
        """Server 실행"""
        logger.info("CustomServer started")
        await self.protocol.run(self.handle_request)
    
    async def cleanup(self):
        """리소스 정리"""
        for tool in self.tools.values():
            await tool.cleanup()


if __name__ == "__main__":
    import asyncio
    server = CustomServer()
    asyncio.run(server.run())
```

### 2. Server 메타데이터 (server.yaml)

각 Server는 YAML 메타데이터를 포함해야 합니다.

```yaml
name: custom_department_server
version: 1.0.0
description: 부서별 커스텀 MCP Server

server:
  type: mcp
  protocol: stdio
  language: python
  main_file: main.py
  class_name: CustomServer

tools:
  - name: custom_tool_1
    description: Tool 설명
    category: custom
    department: department_name

dependencies:
  python: ">=3.10"
  packages:
    - pymysql==1.1.0
    - pydantic==2.5.3

shared_modules:
  - shared.database
  - shared.mcp_protocol
  - mcp_tools.custom.department

environment:
  - MARIADB_HOST
  - MARIADB_PORT

logging:
  level: INFO
  file: data/logs/mcp-servers/custom_server.log
```

### 3. Server 등록

Server를 개발한 후 MCP Host에 등록해야 합니다.

#### config/services.json에 추가

```json
{
  "server_id": "custom_department_server",
  "name": "Custom Department Server",
  "command": "python",
  "args": [
    "/app/poc/mcps/mcp-servers/custom/department_server/main.py"
  ],
  "env": {
    "PYTHONPATH": "/app/poc/mcps"
  },
  "restart_on_failure": true,
  "max_restarts": 3,
  "enabled": true
}
```

### 4. 시작 스크립트에 추가

`mcp-servers/scripts/start_servers.sh`에 추가:

```bash
# Custom Servers
CUSTOM_SERVERS=(
  "custom_department_server"
)

for SERVER_NAME in "${CUSTOM_SERVERS[@]}"; do
  start_server "$SERVER_NAME"
done
```

## 개발 절차

1. **기획**: Server 요구사항 및 제공할 Tool 정의
2. **설계**: Server 구조 및 Tool 인터페이스 설계
3. **개발**: Server 및 Tool 구현
4. **테스트**: 단위/통합 테스트 작성 및 실행
5. **등록**: MCP Host에 Server 등록
6. **배포**: 운영 환경에 배포
7. **문서화**: README 및 사용 가이드 작성

## 테스트

### 단위 테스트

```python
# tests/unit/custom/test_custom_server.py
import pytest
from mcp_servers.custom.department_server.main import CustomServer

@pytest.mark.asyncio
async def test_server_initialization():
    server = CustomServer()
    await server.initialize()
    assert len(server.tools) > 0

@pytest.mark.asyncio
async def test_list_tools():
    server = CustomServer()
    await server.initialize()
    result = server._list_tools()
    assert "tools" in result
```

### 통합 테스트

```bash
# Server 시작
python mcp-servers/custom/department_server/main.py &
SERVER_PID=$!

# Tool 호출 테스트
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python -

# Server 종료
kill $SERVER_PID
```

## 디버깅

### 로그 확인

```bash
# Server 로그 실시간 확인
tail -f data/logs/mcp-servers/custom_server.log
```

### STDIO 디버깅

```python
# stderr로 디버그 메시지 출력 (stdout은 MCP 통신용)
import sys
print(f"DEBUG: {message}", file=sys.stderr)
```

## 성능 가이드라인

- **시작 시간**: < 1초
- **응답 시간**: < 2초 (평균)
- **메모리 사용**: < 512MB
- **동시 요청**: 10개 이상 처리 가능

## 보안 주의사항

1. **입력 검증**: 모든 Tool 파라미터 검증
2. **권한 체크**: Tool 실행 전 권한 확인
3. **에러 처리**: 민감 정보 노출 방지
4. **로깅**: 개인정보 로그 기록 금지
5. **리소스 관리**: 메모리 누수 방지

## 모니터링

### 헬스체크

```bash
# Server 상태 확인
./scripts/manage/status.sh | grep custom_server
```

### 메모리/CPU 모니터링

```bash
# 리소스 사용량 확인
ps aux | grep custom_server
```

## 문의

커스텀 Server 개발 관련 문의:
- Tech Lead: tech-lead@company.com
- Slack: #mcp-custom-servers

## 참고 문서

- [MCP Protocol Specification](../docs/MCP_Protocol.md)
- [Core MCP Servers](../auth_server/README.md)
- [Tool Development Guide](../../mcp-tools/custom/README.md)

---

**Last Updated**: 2026-01-12  
**Version**: 1.0.0
