# RAST MVP-0 3-minute Demo Script

## 0:00-0:20 Problem

로봇이나 embodied agent는 raw observation 전체를 planner에 바로 넘기기보다, action과 safety decision에 필요한 구조화된 정보를 필요로 합니다. RAST는 raw observation과 planner 사이에 planner-facing token contract를 두는 연구형 prototype입니다.

## 0:20-0:50 Project Overview

RAST MVP-0는 Entity, Risk, Relation, Event, Uncertainty, Evidence, Affordance token을 구현합니다. 비교군으로 Object List, Flat Feature Table, Scene Graph, RAST, Event-aware RAST, Uncertainty-aware RAST, Affordance-aware RAST를 둡니다. 현재 demo는 실제 3D simulator가 아니라 `WindowsMetadataSim` 기반 metadata prototype입니다.

## 0:50-1:40 Live Demo

1. API를 실행합니다.

```powershell
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```

2. healthcheck를 확인합니다.

```powershell
curl.exe http://localhost:8000/health
```

3. UI에 접속합니다.

```text
http://localhost:8000/
```

4. scenario는 `inspect_required_uncertain_path` 또는 `uncertainty_without_high_risk`를 선택합니다.
5. policy는 `uncertainty_aware_rast` 또는 `affordance_aware_rast`를 선택합니다.
6. 결과에서 selected action, reason_code, token counts, replay trace preview를 설명합니다.

## 1:40-2:20 Reports/Reproducibility

주요 보고서:

- `docs/result_report.md`
- `docs/artifact_manifest.md`
- `docs/reproducibility_guide.md`

Replay artifact는 visual replay가 아니라 metadata/action/evidence trace 재구성입니다. 어떤 token과 planner reason이 action에 연결되었는지 audit할 수 있게 합니다.

## 2:20-2:50 OSS/Engineering

이 repository는 CI, Docker, Dependabot/security workflow, RUNBOOK, MODEL_CARD, RETROSPECTIVE, submission checklist를 포함합니다. 외부 평가자는 `python -m pytest`, Docker 실행, API smoke script로 핵심 기능을 검증할 수 있습니다.

## 2:50-3:00 Limitations

현재 결과는 real robot 또는 real perception 성능 주장이 아닙니다. WindowsMetadataSim metadata simulator prototype이며, future work는 real simulator adapter와 perception-bound adapter입니다.
