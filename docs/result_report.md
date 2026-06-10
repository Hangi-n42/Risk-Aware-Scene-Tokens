# RAST MVP-0 Result Report

이 문서는 WindowsMetadataSim 기반 RAST MVP-0 evaluation suite 결과를 자동 요약한 보고서입니다.

## Experiment Context

- Results source: `runs\windows_eval_suite\windows_eval_suite_20260610_164047\aggregate_results.csv`
- Summary source: `runs\windows_eval_suite\windows_eval_suite_20260610_164047\aggregate_summary.csv`
- Total runs: 60
- Successful runs: 60
- Failed runs: 0
- Current report purpose: evaluation infrastructure 검증과 관찰 결과 정리입니다.

## Simulator and Scope

- 이 결과는 WindowsMetadataSim 기반 deterministic metadata simulator 결과입니다.
- 실제 AI2-THOR / Webots / CoppeliaSim / real robot 결과가 아닙니다.
- 실제 RGB-D perception latency나 perception error를 반영하지 않습니다.
- collision, near-miss, goal reaching은 simple geometry rule 기반입니다.
- 현재 seed는 metadata에 기록되지만 stochastic variation은 아직 제한적입니다.
- 현재 결과는 연구 주장이라기보다 evaluation infrastructure 검증입니다.

## Scenarios

- `clear_path`
- `far_obstacle`
- `near_obstacle`
- `object_appears`
- `object_disappears`
- `object_moves`
- `planner_disagreement`
- `risk_increases`
- `target_reachable`
- `unknown_near_path`

## Baselines

- Object List: object id, category, position, visible, distance, confidence 중심의 baseline입니다.
- Flat Feature Table: RAST와 유사한 scalar feature를 받지만 token contract field를 제거한 baseline입니다.
- RAST: EntityToken, RiskToken, EventToken logging을 포함한 planner-facing token contract 경로입니다.
- 이번 Batch에서 EventToken은 planner input으로 action을 바꾸지 않고, semantic event logging과 summary에만 사용됩니다.

## Metrics

- success / goal_reached
- completed_steps
- collision_count / near_miss_count
- RAST vs Object List disagreement
- RAST vs Flat Feature disagreement
- Object List vs Flat Feature disagreement
- token_count_avg / object_count_avg / flat_feature_row_count_avg
- event_token_count_total / event_token_count_avg / event_type_counts
- update_mode / changed_object_count_avg / affected_token_count_avg
- full_recompute_latency_avg_ms / incremental_update_latency_avg_ms / incremental_update_benefit_avg
- rast_reason_code_counts / object_list_reason_code_counts / flat_feature_reason_code_counts
- rast_trigger_token_count_total / decision_trace_coverage
- latency_avg_ms / latency_p50_ms / latency_p95_ms
- token_generation_latency_avg_ms / planning_latency_avg_ms / total_latency_avg_ms

## Before/After Context

- 이전 report는 EventToken 추가 전 Object List / Flat Feature / RAST baseline comparison 결과였습니다.
- 현재 report는 EventToken이 step log와 episode summary, aggregate result에 포함된 이후의 결과입니다.
- EventToken은 semantic event 감지와 기록을 위한 token이며, 현재 planner action에는 영향을 주지 않습니다.
- TokenMemory는 현재 semantic diff와 incremental latency protocol에 사용됩니다. incremental update optimization is experimental.
- 따라서 현재 결과는 EventToken의 감지와 기록 검증이지, EventToken이 planning 성능을 개선했다는 증거가 아닙니다.

## EventToken Summary

- EventToken included in this report: yes
- Total EventToken count across successful runs: 78
- Average EventToken count per episode: 1.300
- Average EventToken count per step: 0.130
- EventToken does not affect planner action in this batch; it is used only for logging and summary.
- EventToken은 현재 semantic event diff 기반으로 생성되며 실제 perception event detection 결과가 아닙니다.

| Event Type | Occurred | Count |
|---|---:|---:|
| `object_appeared` | yes | 6 |
| `object_moved` | yes | 24 |
| `risk_changed` | yes | 42 |
| `object_disappeared` | yes | 6 |

| Scenario | Runs | Avg Event Tokens / Episode | Avg Event Tokens / Step | Event Type Counts |
|---|---:|---:|---:|---|
| `clear_path` | 6 | 0.000 | 0.000 | `{}` |
| `far_obstacle` | 6 | 1.667 | 0.167 | `{"risk_changed":10}` |
| `near_obstacle` | 6 | 0.000 | 0.000 | `{}` |
| `object_appears` | 6 | 2.000 | 0.200 | `{"object_appeared":6,"risk_changed":6}` |
| `object_disappears` | 6 | 2.000 | 0.200 | `{"object_disappeared":6,"risk_changed":6}` |
| `object_moves` | 6 | 5.000 | 0.500 | `{"object_moved":18,"risk_changed":12}` |
| `planner_disagreement` | 6 | 0.333 | 0.033 | `{"risk_changed":2}` |
| `risk_increases` | 6 | 2.000 | 0.200 | `{"object_moved":6,"risk_changed":6}` |
| `target_reachable` | 6 | 0.000 | 0.000 | `{}` |
| `unknown_near_path` | 6 | 0.000 | 0.000 | `{}` |

## Aggregate Results

- Total runs: 60
- Failed runs: 0
- Overall success rate: 1.000
- Overall average near-miss count: 4.933
- Overall latency avg / p50 / p95 ms: 0.398 / 0.366 / 0.586

## Scenario-level Observations

| Scenario | Runs | Success Rate | Avg Near-miss | Avg RAST vs Object | Avg RAST vs Flat | Avg Object vs Flat |
|---|---:|---:|---:|---:|---:|---:|
| `clear_path` | 6 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `far_obstacle` | 6 | 1.000 | 1.333 | 4.667 | 0.000 | 4.667 |
| `near_obstacle` | 6 | 1.000 | 10.000 | 0.000 | 0.000 | 0.000 |
| `object_appears` | 6 | 1.000 | 9.000 | 0.000 | 0.000 | 0.000 |
| `object_disappears` | 6 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `object_moves` | 6 | 1.000 | 7.000 | 5.667 | 0.000 | 5.667 |
| `planner_disagreement` | 6 | 1.000 | 3.000 | 7.000 | 0.000 | 7.000 |
| `risk_increases` | 6 | 1.000 | 9.000 | 0.000 | 0.000 | 0.000 |
| `target_reachable` | 6 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `unknown_near_path` | 6 | 1.000 | 10.000 | 0.000 | 0.000 | 0.000 |

## Baseline Disagreement Analysis

- Average RAST vs Object List disagreement: 1.733
- Average RAST vs Flat Feature disagreement: 0.000
- Average Object List vs Flat Feature disagreement: 1.733
- Flat Feature가 RAST와 자주 일치한다면, 현재 toy setup에서는 scalar risk feature가 두 planner의 action을 크게 좌우한다는 뜻으로 해석해야 합니다.
- Object List와 RAST가 달라지는 경우는 distance-only object view와 risk-aware scalar/token view가 서로 다른 action boundary를 만들 수 있음을 보여줍니다.
- 이 차이는 아직 RAST의 우수성을 뜻하지 않으며, 같은 information bound에서 구조화 효과를 더 분리해 검증해야 합니다.

## Decision Trace Summary

- PlannerDecision trace is included in this report when planner reason_code fields are present in aggregate results.
- Average decision_trace_coverage: 1.000
- Total RAST trigger token references: 378
- Average RAST trigger token references per episode: 6.300
- RAST, Object List, and Flat Feature planners can choose the same action for different reasons.
- These traces are rule-based planner explanations, not learned model interpretability results.
- EventToken is still not used by planner policy in this batch.

| Planner | Reason Code Counts |
|---|---|
| RAST | `{"no_risk_move_ahead":180,"risk_token_present":378}` |
| Object List | `{"near_object_distance":274,"no_near_object_move_ahead":284}` |
| Flat Feature | `{"no_risk_scalar_move_ahead":180,"within_risk_threshold":378}` |

| Scenario | Runs | Decision Trace Coverage | RAST Reason Codes |
|---|---:|---:|---|
| `clear_path` | 6 | 1.000 | `{"no_risk_move_ahead":60}` |
| `far_obstacle` | 6 | 1.000 | `{"no_risk_move_ahead":24,"risk_token_present":36}` |
| `near_obstacle` | 6 | 1.000 | `{"risk_token_present":60}` |
| `object_appears` | 6 | 1.000 | `{"no_risk_move_ahead":6,"risk_token_present":54}` |
| `object_disappears` | 6 | 1.000 | `{"no_risk_move_ahead":54,"risk_token_present":6}` |
| `object_moves` | 6 | 1.000 | `{"no_risk_move_ahead":12,"risk_token_present":48}` |
| `planner_disagreement` | 6 | 1.000 | `{"risk_token_present":60}` |
| `risk_increases` | 6 | 1.000 | `{"no_risk_move_ahead":6,"risk_token_present":54}` |
| `target_reachable` | 6 | 1.000 | `{"no_risk_move_ahead":18}` |
| `unknown_near_path` | 6 | 1.000 | `{"risk_token_present":60}` |

## Latency Summary

- Average latency: 0.398 ms
- Average p50 latency: 0.366 ms
- Average p95 latency: 0.586 ms
- Average token generation latency: 0.132 ms
- Average planning latency: 0.091 ms
- 이 latency는 Python metadata simulator 경로에서 측정된 값이며, real rendering이나 perception model overhead를 포함하지 않습니다.

| Apply Policy | Runs | Avg Latency ms | Avg Planning ms |
|---|---:|---:|---:|
| `flat_feature` | 20 | 0.361 | 0.083 |
| `object_list` | 20 | 0.423 | 0.095 |
| `rast` | 20 | 0.411 | 0.096 |

## Incremental Update Summary

- 이 섹션은 full token recomputation과 TokenMemory 기반 event-aware incremental update의 latency protocol을 비교합니다.
- incremental update optimization is experimental; 현재 결과는 최적화 완료나 planner 성능 개선을 의미하지 않습니다.
- WindowsMetadataSim은 metadata-only toy simulator이므로 absolute latency value는 매우 작고 실제 perception/model cost를 포함하지 않습니다.
- 이번 runner는 같은 snapshot에서 full_recompute와 incremental 후보를 모두 측정하고, 선택된 update_mode의 token generation latency를 step latency에 기록합니다.
- Overall changed object count avg: 0.243
- Overall affected token count avg: 1.312
- Overall full recompute latency avg: 0.155 ms
- Overall incremental update latency avg: 0.116 ms
- Overall incremental update benefit avg: 0.285

| Update Mode | Runs | Changed Objects Avg | Affected Tokens Avg | Full ms | Incremental ms | Benefit |
|---|---:|---:|---:|---:|---:|---:|
| `full_recompute` | 30 | 0.243 | 2.160 | 0.154 | 0.121 | 0.253 |
| `incremental` | 30 | 0.243 | 0.463 | 0.155 | 0.110 | 0.317 |

| Scenario | Runs | Changed Objects Avg | Affected Tokens Avg | Incremental Benefit Avg |
|---|---:|---:|---:|---:|
| `clear_path` | 6 | 0.200 | 1.100 | 0.286 |
| `far_obstacle` | 6 | 0.267 | 1.183 | 0.274 |
| `near_obstacle` | 6 | 0.100 | 1.100 | 0.146 |
| `object_appears` | 6 | 0.200 | 1.750 | 0.273 |
| `object_disappears` | 6 | 0.300 | 0.950 | 0.378 |
| `object_moves` | 6 | 0.500 | 2.250 | 0.287 |
| `planner_disagreement` | 6 | 0.133 | 1.167 | 0.321 |
| `risk_increases` | 6 | 0.300 | 1.850 | 0.244 |
| `target_reachable` | 6 | 0.333 | 0.667 | 0.382 |
| `unknown_near_path` | 6 | 0.100 | 1.100 | 0.258 |

## What This Result Supports

- WindowsMetadataSim 기반 scenario suite를 반복 실행할 수 있음을 보여줍니다.
- Object List / Flat Feature Table / RAST 세 representation과 planner action을 같은 log/summary contract로 기록할 수 있음을 보여줍니다.
- scenario별 disagreement, near-miss, success, latency를 aggregate table로 모을 수 있음을 보여줍니다.
- Flat Feature baseline을 통해 정보량 효과와 token contract 효과를 분리해서 보기 위한 실험 인프라가 준비되었음을 보여줍니다.
- EventToken이 semantic event를 감지하고 step log, episode summary, aggregate result에 기록될 수 있음을 보여줍니다.
- 세 planner의 action 선택 사유를 PlannerDecision trace로 기록하고 집계할 수 있음을 보여줍니다.

## What This Result Does Not Support

- This result does not support real-world performance claims.
- RAST가 Object List나 Flat Feature보다 일반적으로 우수하다는 결론을 지원하지 않습니다.
- EventToken이 planning 성능, success, near-miss, disagreement를 개선했다는 결론을 지원하지 않습니다.
- Decision trace는 rule-based planner 로그이며 learned model explanation 품질을 검증하지 않습니다.
- 실제 RGB-D perception, detector error, occlusion error, sim-to-real 성능을 검증하지 않습니다.
- 상용 자율주행 또는 real robot safety guarantee를 제공하지 않습니다.
- AI2-THOR / Webots / CoppeliaSim / real robot 환경에서의 성능을 대변하지 않습니다.

## Limitations

- deterministic metadata simulator이므로 물리, 렌더링, 센서 노이즈가 제한적입니다.
- collision, near-miss, goal reaching은 simple geometry rule 기반입니다.
- seed가 기록되지만 현재 stochastic variation은 제한적입니다.
- token generation latency는 metadata 기반 Python 경로의 비용이며, perception-bound extractor 비용이 아닙니다.
- EventToken은 semantic diff 기반으로 생성되며, 실제 perception event detection이 아닙니다.
- TokenMemory는 현재 semantic diff와 incremental latency protocol에 사용되지만, incremental update optimization is experimental입니다.
- Batch 9의 incremental update는 measurement protocol 단계이며, 일부 token 계산은 correctness를 위해 여전히 재계산됩니다.
- full_recompute와 incremental 후보를 같은 step에서 모두 측정하므로 report의 selected token_generation latency와 실제 Python wall-clock은 다를 수 있습니다.
- EventToken은 planner action에 영향을 주지 않으므로, success/near-miss/disagreement 변화는 EventToken 효과로 해석하면 안 됩니다.
- PlannerDecision은 현재 deterministic rule-based policy의 내부 규칙을 기록한 것이며, learned model interpretability는 아닙니다.
- 동일 action이라도 planner별 reason_code와 trigger feature가 다를 수 있으므로 action count만으로 의사결정 근거를 해석하면 안 됩니다.
- RelationToken, UncertaintyToken, Scene Graph baseline은 아직 포함하지 않습니다.
- Flat Feature와 RAST가 동일한 scalar risk rule에 강하게 묶여 있어 token contract 효과는 아직 제한적으로만 관찰됩니다.

## Next Steps

- scenario별 failure case와 action trace를 함께 저장해 decision explainability 분석을 강화합니다.
- threshold sensitivity sweep을 넓혀 RAST/Object List/Flat Feature disagreement boundary를 더 명확히 봅니다.
- noise injection과 unknown/occlusion scenario를 추가해 metadata-only 결과의 한계를 점진적으로 줄입니다.
- 이후 단계에서 EventToken을 planner policy 또는 실제 incremental cache 재사용 최적화에 연결할지 별도 Batch에서 검토합니다.
- Scene Graph baseline, RelationToken, UncertaintyToken, perception-bound adapter는 별도 Batch로 추가합니다.
- AI2-THOR나 다른 simulator로 확장할 때도 같은 aggregate/report contract를 유지합니다.
