# RAST MVP-0 Runbook

## Local API 실행

```powershell
python -m pip install -e ".[dev]"
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

또는:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_api.ps1
```

## Docker 실행

```powershell
docker build -t rast-mvp0 .
docker run --rm -p 8000:8000 rast-mvp0
```

## Healthcheck

```powershell
curl.exe http://localhost:8000/health
```

기대 응답:

```json
{"status":"ok","service":"rast-api","version":"1.0.0"}
```

## Metrics

```powershell
curl.exe http://localhost:8000/metrics
```

노출 metric:

- `total_api_requests`
- `scenario_runs_total`
- `last_run_latency_ms`
- `app_uptime_seconds`

## Smoke Test

서버가 실행 중일 때:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke_api.ps1
```

## Common Failure

| 증상 | 가능한 원인 | 대응 |
|---|---|---|
| `ModuleNotFoundError: fastapi` | editable install을 하지 않음 | `python -m pip install -e ".[dev]"` 실행 |
| `/health` 연결 실패 | API 서버가 실행 중이 아님 | `scripts/run_api.ps1` 또는 uvicorn 명령 실행 |
| smoke script 실행 정책 오류 | PowerShell execution policy | `powershell -ExecutionPolicy Bypass -File scripts\smoke_api.ps1` 사용 |
| Docker image가 너무 큼 | `runs/` 포함 | `.dockerignore`가 적용되는지 확인 |

## Rollback Plan

- GitHub release tag 기준 이전 tag로 checkout합니다.
- Docker 배포 시 previous image tag로 되돌립니다.
- Render/Railway/Fly 같은 호스팅을 사용할 경우 previous deployment로 rollback합니다.
- rollback 후 `/health`, `/metrics`, `POST /api/run-scenario` smoke를 다시 확인합니다.

## Scope Warning

이 API는 `WindowsMetadataSim` metadata-only prototype입니다. real robot, real perception model, real-world safety, visual replay를 검증하지 않습니다.
