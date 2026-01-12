# Frontend Assets

정적 파일을 저장하는 디렉토리입니다.

## 파일 구조

```
assets/
├── favicon.ico         # 파비콘
├── logo.png            # 로고 이미지
├── images/             # 이미지 파일
│   ├── banner.png
│   └── icons/
└── fonts/              # 폰트 파일 (선택)
```

## 사용 방법

### Reflex에서 정적 파일 사용

```python
import reflex as rx

def navbar():
    return rx.hstack(
        rx.image(src="/logo.png", width="40px", height="40px"),
        rx.heading("MCP Ecosystem", size="lg"),
        # ...
    )
```

### 파일 경로
- 정적 파일은 `/assets/` 경로로 접근
- 예: `http://localhost:8501/logo.png`

## 파비콘 설정

`rxconfig.py`에서 파비콘 설정:

```python
config = rx.Config(
    app_name="mcp_docs",
    favicon="favicon.ico",  # assets/ 폴더 내 파일
)
```

## 이미지 추가

1. 이미지 파일을 `assets/` 폴더에 복사
2. Reflex 앱에서 `/파일명`으로 참조

```python
rx.image(src="/banner.png")
```

## 주의사항

- 파일명은 소문자 권장
- 공백 대신 하이픈(-) 또는 언더스코어(_) 사용
- 이미지는 최적화하여 크기 최소화

---

**Note**: 현재 이 폴더에는 플레이스홀더 파일만 있습니다. 
실제 로고, 파비콘 등은 디자인 팀에서 제공받아 추가하세요.
