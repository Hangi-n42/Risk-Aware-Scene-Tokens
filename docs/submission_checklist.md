# Capstone OSS Submission Checklist

| Item | Status | Note |
|---|---|---|
| Public GitHub repo | Manual | GitHub repository setting에서 확인 필요 |
| README | Done | API/UI/Docker/문서 링크 포함 |
| CONTRIBUTING | Done | `CONTRIBUTING.md` |
| CODE_OF_CONDUCT | Done | `CODE_OF_CONDUCT.md` |
| LICENSE | Done | MIT License |
| FastAPI API | Done | `apps/api/main.py` |
| Minimal UI | Done | `apps/api/static/index.html` |
| `/health` | Done | `GET /health` |
| `/metrics` | Done | `GET /metrics` |
| CI test | Done | `.github/workflows/ci.yml` |
| Mini eval | Done | CI에서 `clear_path` mini eval 실행 |
| Dependabot/security scan | Done | Dependabot + informative `security.yml` |
| Runbook | Done | `RUNBOOK.md` |
| Changelog | Done | `CHANGELOG.md` |
| Model/Data card | Done | `MODEL_CARD.md` |
| Retrospective | Done | `RETROSPECTIVE.md` |
| Release tag v1.0.0+ | Manual | maintainer가 GitHub release/tag 생성 |
| Deployment URL | Manual | Render/Railway/Fly 등 배포 후 기입 |
| 3-minute demo video | Manual | 제출 영상 URL 기입 |
| Rollback plan | Done | `RUNBOOK.md` |
| Logs/metrics/observability explanation | Done | `RUNBOOK.md`와 `/metrics` |

## Scope Warning

이 제출물은 `WindowsMetadataSim` metadata-only RAST MVP-0 prototype입니다. real robot 성능, real-world safety, real perception robustness, visual replay를 주장하지 않습니다.
