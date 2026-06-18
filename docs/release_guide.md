# RAST MVP-0 Release Guide

이 문서는 캡스톤 최종 제출을 위한 release tag와 GitHub Release 작성 절차입니다. 이 문서는 절차만 기록하며, tag 생성이나 PR merge를 자동으로 수행하지 않습니다.

## 1. PR 확인

1. PR #4의 CI가 통과했는지 확인합니다.
2. Draft PR을 Ready for review로 전환합니다.
3. review 후 `main`에 merge합니다.

## 2. Local main 갱신

```powershell
git checkout main
git pull origin main
```

## 3. Release tag 생성

최종 확인 후 수동으로 실행합니다.

```powershell
git tag v1.0.0
git push origin v1.0.0
```

## 4. GitHub Release 생성

- Release title: `v1.0.0 - RAST MVP-0 Capstone Submission`
- Target: `v1.0.0`

Release notes에 포함할 내용:

- FastAPI API/UI
- Docker support
- CI/security docs
- reports/reproducibility artifacts
- known limitations and non-claims

## 5. Release Notes Template

```markdown
## v1.0.0 - RAST MVP-0 Capstone Submission

### Included
- FastAPI API and minimal HTML UI
- Dockerfile and local run/smoke scripts
- GitHub Actions CI, Dependabot, informative security workflow
- RAST MVP-0 reports, artifact manifest, reproducibility guide
- Runbook, model/data card, retrospective, submission checklist

### Limitations
- WindowsMetadataSim metadata-only prototype
- Not a real robot or real-world safety result
- Not real RGB-D perception or detector robustness
- Replay is metadata/action/evidence trace, not visual replay
```
