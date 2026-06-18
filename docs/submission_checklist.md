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
| Dockerfile | Done | `Dockerfile` |
| CI test | Done | `.github/workflows/ci.yml` |
| Tests | Done | `python -m pytest` 기준 |
| Mini eval | Done | CI에서 `clear_path` mini eval 실행 |
| Dependabot/security workflow | Done | Dependabot + informative `security.yml` |
| Runbook | Done | `RUNBOOK.md` |
| Changelog | Done | `CHANGELOG.md` |
| Model/Data card | Done | `MODEL_CARD.md` |
| Retrospective draft | Done | `RETROSPECTIVE.md` |
| Deployment guide | Done | `docs/deployment_guide.md` |
| Release guide | Done | `docs/release_guide.md` |
| 3-minute demo script | Done | `docs/demo_script_3min.md` |
| Final readiness checker | Done | `experiments/check_submission_readiness.py` |
| Rollback plan | Done | `RUNBOOK.md` |
| Logs/metrics/observability explanation | Done | `RUNBOOK.md`와 `/metrics` |
| GitHub public URL | Manual | repository public 설정 확인 후 제출 양식에 기입 |
| PR #4 merge | Manual/Pending | CI 확인 후 maintainer가 merge |
| deployment URL | Manual/Pending | Render/Railway/Fly 등 배포 후 기입 |
| release URL | Manual/Pending | `v1.0.0+` GitHub Release 생성 후 기입 |
| demo video URL | Manual/Pending | 3분 demo video 업로드 후 기입 |
| final submitted GitHub URL | Manual/Pending | 최종 제출 양식에 main branch 또는 release URL 기입 |

## Scope Warning

이 제출물은 `WindowsMetadataSim` metadata-only RAST MVP-0 prototype입니다. real robot 성능, real-world safety, real perception robustness, visual replay를 주장하지 않습니다.
