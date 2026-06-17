# RAST MVP-0 Project Summary

## 1. 30-second Summary

RAST MVP-0는 로봇이나 embodied agent가 장면을 볼 때, 모든 raw observation을 planner에 그대로 넘기는 대신 planner가 바로 쓸 수 있는 structured token으로 정리하는 연구형 prototype입니다. 현재 버전은 실제 로봇이나 실제 카메라 입력이 아니라 `WindowsMetadataSim`이라는 deterministic metadata simulator에서 동작합니다. 이 프로젝트는 위험, 관계, 이벤트, 불확실성, 근거, 행동 가능성을 token으로 기록하고, 여러 baseline planner가 같은 조건에서 어떤 action과 reason을 남기는지 비교합니다. 결과는 real-world 성능 주장이 아니라, representation과 evaluation infrastructure가 작동하는지 보여주는 controlled prototype 결과입니다.

## 2. Technical Summary

RAST는 `ObservationSnapshot`에서 `EntityToken`, `RiskToken`, `RelationToken`, `EventToken`, `UncertaintyToken`, `EvidenceToken`, `AffordanceToken`을 생성하고, Object List, Flat Feature Table, Scene Graph, RAST 계열 planner를 같은 logging/summary/report contract로 비교합니다. Event-aware, Uncertainty-aware, Affordance-aware planner는 기존 RAST planner를 대체하지 않는 별도 experimental planner입니다. sampled extended evaluation은 전체 8,294,400개 extended grid를 모두 실행하지 않고 deterministic stratified sampling으로 대표 subset을 평가합니다. Seed stability와 sample-size convergence report는 sampled result의 reliability를 점검하기 위한 보조 artifact입니다.

## 3. System Components

| Component | Role |
|---|---|
| Simulator | `WindowsMetadataSim` metadata-only controlled scenario suite |
| Tokenizers | Entity/Risk/Relation/Event/Uncertainty/Evidence/Affordance token generation |
| Baselines | Object List, Flat Feature Table, Scene Graph representation |
| Planners | Object List, Flat Feature, Scene Graph, RAST, Event-aware RAST, Uncertainty-aware RAST, Affordance-aware RAST |
| Evaluation | step JSONL, episode summary, aggregate CSV/JSON, latency and disagreement metrics |
| Reports | result report, technical report, eval comparison, coverage/stability/convergence reports |
| Replay | metadata/action/evidence trace markdown/json export |

## 4. Key Results Snapshot

| Artifact | Snapshot |
|---|---|
| Default baseline | 900 runs, failed 0 |
| Sampled extended | 500 runs, failed 0, sample seed 42 |
| Seed sweep | seeds 7/13/42, sample-size 500 |
| Sample-size convergence | sample sizes 100/200/500 |
| Core token set | Entity, Risk, Relation, Event, Uncertainty, Evidence, Affordance implemented |
| Replay artifact | Available for sampled extended run through replay index |

## 5. Why It Matters

- RAST explores a planner-facing abstraction between raw observation and action planning.
- The token set makes risk, event, uncertainty, evidence, and navigation affordance traceable in a structured log.
- The evaluation harness separates Object List, Flat Feature Table, Scene Graph, and token-contract representations under shared logging and aggregation.
- Replay artifacts make important decision steps easier to audit as metadata/action/evidence traces.

This does not show that RAST is generally superior. It shows that the project now has a reproducible harness for asking that question more carefully.

## 6. Current Limitations

- This is not a real-world performance claim.
- This is not a real robot safety claim.
- This is not a real RGB-D perception or detector robustness claim.
- This is not real perception uncertainty calibration.
- Replay artifacts are not visual replay; they are metadata/action/evidence traces.
- The sampled extended result is not an exhaustive extended grid result.
- Current planner explanations are rule-based traces, not learned model interpretability.
