# Contributing to RAST MVP-0

RAST MVP-0는 `WindowsMetadataSim` 기반 metadata-only 연구 prototype입니다. 기여자는 새 기능을 추가하기 전에 현재 범위가 실제 로봇, 실제 perception model, real-world safety claim을 포함하지 않는다는 점을 유지해야 합니다.

## 개발 환경

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

## 작업 원칙

- 기존 planner policy를 바꾸는 변경은 별도 issue 또는 PR에서 명확히 설명합니다.
- full extended grid는 기본 실행하지 않습니다.
- 새 token, 새 planner, 새 simulator adapter는 제출 hardening PR과 분리합니다.
- 보고서와 README에는 real-world performance claim을 쓰지 않습니다.

## PR 전 확인

```powershell
python -m pytest
python experiments\check_docs_consistency.py
```

API 변경이 있으면 로컬에서 다음도 확인합니다.

```powershell
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
powershell -ExecutionPolicy Bypass -File scripts\smoke_api.ps1
```
