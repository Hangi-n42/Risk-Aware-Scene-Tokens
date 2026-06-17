# RAST MVP-0: Risk-Aware Scene Tokens

## One-paragraph Summary

RAST는 raw observation과 planner 사이에 planner-facing token contract를 두는 연구형 prototype입니다. 현재 MVP-0는 실제 3D simulator가 아니라 `WindowsMetadataSim` 기반 deterministic metadata simulator에서 동작합니다. 구현된 core token set은 `EntityToken`, `RiskToken`, `RelationToken`, `EventToken`, `UncertaintyToken`, `EvidenceToken`, `AffordanceToken`입니다. 비교군은 Object List, Flat Feature Table, Scene Graph, RAST, Event-aware RAST, Uncertainty-aware RAST, Affordance-aware RAST입니다. 실험 harness는 token generation, planner decision trace, evidence pointer, replay artifact, sampled extended evaluation report를 생성합니다. 이 프로젝트는 real-world performance claim이나 real robot safety claim을 하지 않으며, 현재 결과는 metadata-only controlled evaluation infrastructure의 관찰 결과로 해석해야 합니다.

## What This Project Demonstrates

- WindowsMetadataSim에서 controlled scenario suite를 반복 실행할 수 있습니다.
- 여러 representation/planner를 같은 step log, episode summary, aggregate report contract로 비교할 수 있습니다.
- token generation, decision trace, evidence pointer, replay artifact를 기록할 수 있습니다.
- sampled extended evaluation, seed stability, sample-size convergence를 통해 sampling reliability를 점검할 수 있습니다.
- Object List, Flat Feature Table, Scene Graph와 RAST 계열 planner의 action/reason boundary 차이를 같은 ObservationSnapshot source에서 관찰할 수 있습니다.

## What This Project Does Not Claim

- real-world performance claim이 아닙니다.
- real robot safety claim이 아닙니다.
- real RGB-D perception 또는 detector robustness claim이 아닙니다.
- real perception uncertainty calibration이 아닙니다.
- visual replay가 아닙니다. Replay는 metadata/action/evidence trace 재구성입니다.
- exhaustive extended grid result가 아닙니다. Sampled extended result는 seed와 sample size에 의존합니다.
- learned model interpretability가 아닙니다. 현재 planner 설명은 deterministic rule-based decision trace입니다.

## Key Documents

| Document | Purpose | When to read |
|---|---|---|
| [Artifact Manifest](docs/artifact_manifest.md) | canonical report, run directory, config, replay artifact 목록 | 어떤 산출물이 기준인지 빠르게 확인할 때 |
| [Reproducibility Guide](docs/reproducibility_guide.md) | report 재생성 명령과 실행 경고 | 로컬에서 검증 또는 report를 재생성할 때 |
| [Technical Report](docs/technical_report.md) | MVP-0 방법론, architecture, token/baseline/planner 설명 | 연구형 설명과 한계를 깊게 읽을 때 |
| [Latest Result Report](docs/result_report.md) | 최신 sampled extended result와 replay/coverage/stability artifact 연결 | 현재 관찰 결과를 볼 때 |
| [Evaluation Comparison Report](docs/eval_comparison_report.md) | default suite와 sampled extended suite 비교 | evaluation profile 차이를 볼 때 |
| [Sampling Coverage Report](docs/sampling_coverage_report.md) | sampled run의 axis coverage 점검 | sampled result 대표성을 확인할 때 |
| [Seed Stability Report](docs/seed_stability_report.md) | seed 7/13/42 기준 sampled stability 점검 | seed-to-seed variation을 볼 때 |
| [Sample-size Convergence Report](docs/sample_size_convergence_report.md) | sample-size 100/200/500 convergence와 sampling quality score | sample-size reliability를 볼 때 |

## Quick Start

빠른 검증은 unit/regression test로 시작합니다.

```powershell
python -m pytest
```

default evaluation suite를 재생성하려면 다음을 실행합니다.

```powershell
python experiments\run_windows_eval_suite.py --config configs\windows_eval_suite.yaml
```

주의: `configs/windows_eval_suite_extended.yaml`의 전체 extended grid는 매우 큽니다. 전체 조합을 실행하지 말고 `--dry-run`, `--sample-size`, 또는 `--limit`를 사용하십시오.

## Reproducibility

상세 재현 절차는 [Reproducibility Guide](docs/reproducibility_guide.md)를 보십시오. 이 guide에는 default report, sampled extended report, comparison report, sampling coverage, seed stability, sample-size convergence, replay artifact를 재생성하는 명령이 정리되어 있습니다.

## Current Canonical Artifacts

canonical report와 run directory 목록은 [Artifact Manifest](docs/artifact_manifest.md)를 기준으로 관리합니다. README에는 긴 run directory 목록을 반복하지 않습니다.

## Limitations

- `WindowsMetadataSim`은 deterministic metadata simulator입니다.
- 실제 AI2-THOR, Webots, CoppeliaSim, real robot 결과가 아닙니다.
- 실제 RGB-D perception latency, detector error, sensor fusion, uncertainty calibration을 반영하지 않습니다.
- EvidenceToken은 metadata pointer 기반이며 real sensor evidence나 image crop을 저장하지 않습니다.
- Replay artifact는 visual replay가 아니라 metadata/action/evidence trace입니다.
- sampled extended result는 exhaustive extended grid result가 아닙니다.
- 모든 planner는 deterministic rule-based experimental policy입니다.
- 현재 결과는 RAST가 다른 representation보다 일반적으로 우수하다는 결론을 지원하지 않습니다.
