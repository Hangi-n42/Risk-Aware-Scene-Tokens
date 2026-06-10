# RAST: Risk-Aware Scene Tokens

RAST는 Physical AI / Embodied AI / Robotics 환경에서 raw sensory data와 planner 사이에 둘 수 있는 planning-facing scene token representation을 검증하기 위한 연구형 MVP입니다. 현재 구현은 실제 3D 렌더링 simulator가 아니라 `WindowsMetadataSim` 기반 deterministic metadata simulator에서 동작합니다.

이 저장소의 현재 목표는 RAST가 Object List, Flat Feature Table baseline과 같은 information-bound 조건에서 어떤 로그, metric, decision trace를 남길 수 있는지 검증하는 것입니다. 아직 실제 perception latency, RGB-D detector error, real robot deployment, 상용 수준 safety guarantee를 검증하지 않습니다.

## 현재 진행 상태

현재 MVP-0는 Batch 10까지 구현되어 있습니다.

- `ObservationSnapshot`, `EntityToken`, `RiskToken`, `EventToken`, `LatencyRecord` schema
- fixture metadata 및 `WindowsMetadataSim` 기반 deterministic metadata simulation
- Object List baseline
- Flat Feature Table baseline
- RAST token planner
- Object List planner
- Flat Feature planner
- semantic event diff 기반 EventToken logging
- full recompute vs incremental update latency protocol
- multi-run evaluation suite
- aggregate 결과 생성
- Markdown result report 생성
- `PlannerDecision` 기반 action trace 및 decision explainability logging

## 핵심 구조

```text
WindowsMetadataSim
-> ObservationSnapshot
-> EntityToken / RiskToken / EventToken
-> Object List / Flat Feature Table / RAST representation
-> 각 baseline planner
-> PlannerDecision
-> Step JSONL log
-> Episode summary
-> Aggregate result
-> docs/result_report.md
```

## 주요 모듈

```text
rast/
  baselines/       Object List, Flat Feature Table, information-bound audit
  evaluation/      latency, JSONL logging, metrics, aggregate, report generation
  planner/         Action set, RAST/Object List/Flat Feature planners
  schemas/         observation, token, latency, metric, decision schemas
  simulator/       WindowsMetadataSim 및 controlled scenario suite
  token_memory/    TokenMemory, semantic diff, incremental update protocol
  tokenizer/       entity/risk/event tokenization pipeline

experiments/
  run_windows_metadata_sim.py
  run_windows_eval_suite.py
  generate_result_report.py

configs/
  windows_metadata_sim.yaml
  windows_eval_suite.yaml

docs/
  result_report.md
```

## Baselines

- Object List: object id, category, position, visibility, distance 중심의 baseline입니다.
- Flat Feature Table: RAST와 유사한 scalar feature를 받지만 token contract field를 제거한 baseline입니다.
- RAST: EntityToken, RiskToken, EventToken, PlannerDecision trace를 포함한 planner-facing token path입니다.

## Decision Explainability

Batch 10부터 planner는 단순 action 대신 `PlannerDecision`을 반환합니다.

주요 필드:

- `planner_name`
- `action`
- `reason_code`
- `reason_text`
- `trigger_object_ids`
- `trigger_token_ids`
- `trigger_features`
- `confidence`

현재 decision trace는 rule-based planner의 내부 규칙 로그입니다. learned model interpretability를 의미하지 않습니다.

## 실행 방법

개발 환경과 dependency 버전은 구현 시점의 공식 문서를 확인해야 합니다. 현재 로컬 검증은 Python 3.11 환경에서 수행했습니다.

```powershell
python -m pytest
python experiments\run_windows_metadata_sim.py --scenario planner_disagreement --max-steps 5 --update-mode incremental
python experiments\run_windows_eval_suite.py --config configs\windows_eval_suite.yaml
python experiments\generate_result_report.py --results runs\windows_eval_suite\<RUN_ID>\aggregate_results.csv --summary runs\windows_eval_suite\<RUN_ID>\aggregate_summary.csv --output docs\result_report.md
```

## 현재 검증 결과

최신 로컬 검증 기준:

- `python -m pytest`: 71 passed
- WindowsMetadataSim evaluation suite: 60 planned runs, 0 failed
- `docs/result_report.md`에 EventToken Summary, Incremental Update Summary, Decision Trace Summary 포함

`runs/` 디렉터리는 재생성 가능한 로컬 실험 산출물이므로 git tracking에서 제외합니다. 현재 연구 결과 요약은 `docs/result_report.md`를 source artifact로 둡니다.

## 명시적 한계

- WindowsMetadataSim은 deterministic metadata simulator입니다.
- 실제 AI2-THOR, Webots, CoppeliaSim, real robot 결과가 아닙니다.
- 실제 RGB-D perception latency나 detector error를 반영하지 않습니다.
- EventToken은 현재 planner action에 영향을 주지 않고 logging/summary에만 사용됩니다.
- incremental update는 최적화 완료가 아니라 full recompute와 비교하기 위한 latency protocol입니다.
- Decision trace는 rule-based 설명 로그이며 learned planner explanation이 아닙니다.
- Scene Graph baseline, RelationToken, UncertaintyToken은 아직 포함하지 않았습니다.

## 관련 문서

- `prd.md`: 연구형 PRD
- `stack.md`: 기술 스택 설계
- `tasks.md`: MVP-0 vertical slice 작업 계획
- `docs/result_report.md`: WindowsMetadataSim 기반 최신 결과 보고서
