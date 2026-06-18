# RAST MVP-0 Deployment Guide

이 문서는 RAST MVP-0 FastAPI demo를 컨테이너 기반으로 배포하기 위한 일반 절차입니다. 현재 demo는 `WindowsMetadataSim` metadata-only prototype이며 real robot, real perception, real-world safety 성능을 주장하지 않습니다.

## Deployment URL

- Deployment URL: `https://risk-aware-scene-tokens.onrender.com`
- Healthcheck: `https://risk-aware-scene-tokens.onrender.com/health`
- Metrics: `https://risk-aware-scene-tokens.onrender.com/metrics`
- API docs: `https://risk-aware-scene-tokens.onrender.com/docs`
- UI: `https://risk-aware-scene-tokens.onrender.com/`
- Port: `8000`

## Local Docker 실행

```powershell
docker build -t rast-mvp0 .
docker run --rm -p 8000:8000 rast-mvp0
```

확인:

```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/metrics
```

## Container Start Command

```bash
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```

Dockerfile은 위 command를 기본 `CMD`로 포함합니다.

## Render / Railway / Fly.io 일반 절차

1. GitHub repository를 배포 서비스에 연결합니다.
2. deployment type은 Docker 또는 container 기반 배포로 선택합니다.
3. service port는 `8000`으로 설정합니다.
4. healthcheck path는 `/health`로 설정합니다.
5. 배포 후 `GET /health`, `GET /metrics`, `POST /api/run-scenario`를 smoke test합니다.

특정 서비스 계정, API key, secret은 이 문서에 포함하지 않습니다. 실제 URL과 서비스별 설정은 제출자가 수동으로 채웁니다.

## Rollback Plan

- 이전 GitHub release tag로 checkout합니다.
- 이전 Docker image tag로 rollback합니다.
- Render/Railway/Fly.io 같은 배포 서비스에서는 previous deployment로 rollback합니다.
- rollback 이후 `/health`, `/metrics`, `POST /api/run-scenario`를 다시 확인합니다.

## Scope Warning

이 배포는 API/UI demo surface를 제공하기 위한 것입니다. 실제 로봇 배포, 실제 perception model, real-world safety 검증이 아닙니다.
