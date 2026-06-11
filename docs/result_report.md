# RAST MVP-0 Result Report

이 문서는 WindowsMetadataSim 기반 RAST MVP-0 evaluation suite 결과를 자동 요약한 보고서입니다.

## Experiment Context

- Results source: `runs\windows_eval_suite\windows_eval_suite_20260611_021550\aggregate_results.csv`
- Summary source: `runs\windows_eval_suite\windows_eval_suite_20260611_021550\aggregate_summary.csv`
- Total runs: 280
- Successful runs: 280
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
- Event-aware RAST: 기존 RAST planner와 분리된 실험용 planner이며 EventToken을 decision reason에 반영합니다.
- 기존 RAST planner는 EventToken으로 action을 바꾸지 않으며, Event-aware RAST planner에서만 실험적으로 EventToken reason을 사용합니다.

## Metrics

- success / goal_reached
- completed_steps
- collision_count / near_miss_count
- RAST vs Object List disagreement
- RAST vs Flat Feature disagreement
- Object List vs Flat Feature disagreement
- RAST vs Event-aware RAST disagreement
- token_count_avg / object_count_avg / flat_feature_row_count_avg
- event_token_count_total / event_token_count_avg / event_type_counts
- update_mode / changed_object_count_avg / affected_token_count_avg
- full_recompute_latency_avg_ms / incremental_update_latency_avg_ms / incremental_update_benefit_avg
- rast_reason_code_counts / object_list_reason_code_counts / flat_feature_reason_code_counts
- event_aware_rast_reason_code_counts / event_triggered_action_count
- event_policy_variant / event_policy_variant_action_counts / event_policy_variant_reason_code_counts
- risk_threshold / near_miss_threshold
- position_noise_std / distance_noise_std / visibility_flip_prob
- rast_trigger_token_count_total / decision_trace_coverage
- event_aware_decision_trace_coverage
- latency_avg_ms / latency_p50_ms / latency_p95_ms
- token_generation_latency_avg_ms / planning_latency_avg_ms / total_latency_avg_ms

## Before/After Context

- 이전 report는 EventToken 추가 전 Object List / Flat Feature / RAST baseline comparison 결과였습니다.
- 현재 report는 EventToken이 step log와 episode summary, aggregate result에 포함된 이후의 결과입니다.
- EventToken은 semantic event 감지와 기록을 위한 token이며, 기존 RAST planner action에는 영향을 주지 않습니다.
- TokenMemory는 현재 semantic diff와 incremental latency protocol에 사용됩니다. incremental update optimization is experimental.
- 현재 report는 Event-aware RAST planner가 추가되어 EventToken을 action reason으로 사용할 수 있는 이후 결과입니다.
- Event-aware planner는 deterministic rule-based policy이며 성능 개선을 단정하기 위한 결과가 아닙니다.
- 따라서 현재 결과는 EventToken의 감지와 기록 검증이지, EventToken이 planning 성능을 개선했다는 증거가 아닙니다.

## EventToken Summary

- EventToken included in this report: yes
- Total EventToken count across successful runs: 398
- Average EventToken count per episode: 1.421
- Average EventToken count per step: 0.142
- EventToken affects only the separate Event-aware RAST experimental planner; the existing RAST planner remains unchanged.
- EventToken은 현재 semantic event diff 기반으로 생성되며 실제 perception event detection 결과가 아닙니다.

| Event Type | Occurred | Count |
|---|---:|---:|
| `object_appeared` | yes | 28 |
| `object_moved` | yes | 126 |
| `risk_changed` | yes | 216 |
| `object_disappeared` | yes | 28 |

| Scenario | Runs | Avg Event Tokens / Episode | Avg Event Tokens / Step | Event Type Counts |
|---|---:|---:|---:|---|
| `clear_path` | 28 | 0.500 | 0.050 | `{"object_moved":14}` |
| `far_obstacle` | 28 | 2.571 | 0.257 | `{"risk_changed":72}` |
| `near_obstacle` | 28 | 0.000 | 0.000 | `{}` |
| `object_appears` | 28 | 2.000 | 0.200 | `{"object_appeared":28,"risk_changed":28}` |
| `object_disappears` | 28 | 2.000 | 0.200 | `{"object_disappeared":28,"risk_changed":28}` |
| `object_moves` | 28 | 5.000 | 0.500 | `{"object_moved":84,"risk_changed":56}` |
| `planner_disagreement` | 28 | 0.143 | 0.014 | `{"risk_changed":4}` |
| `risk_increases` | 28 | 2.000 | 0.200 | `{"object_moved":28,"risk_changed":28}` |
| `target_reachable` | 28 | 0.000 | 0.000 | `{}` |
| `unknown_near_path` | 28 | 0.000 | 0.000 | `{}` |

## RelationToken Summary

- RelationToken included in this report: yes
- Total RelationToken count across successful runs: 2984
- Average RelationToken count per episode: 10.657
- Average RelationToken count per step: 1.136
- Relation type distribution: `{"blocking_path":532,"near_agent":1740,"near_path":628,"target_reachable":84}`
- RelationToken은 MVP에서 navigation relation만 다루며 learned relation extraction 결과가 아닙니다.
- Relation은 simple geometry rule 기반이므로 실제 perception relation 품질을 검증하지 않습니다.

| Scenario | Runs | Avg Relation Tokens / Episode | Avg Relation Tokens / Step | Relation Type Counts |
|---|---:|---:|---:|---|
| `clear_path` | 28 | 0.000 | 0.000 | `{}` |
| `far_obstacle` | 28 | 11.000 | 1.100 | `{"blocking_path":48,"near_agent":144,"near_path":116}` |
| `near_obstacle` | 28 | 16.000 | 1.600 | `{"blocking_path":84,"near_agent":280,"near_path":84}` |
| `object_appears` | 28 | 15.000 | 1.500 | `{"blocking_path":84,"near_agent":252,"near_path":84}` |
| `object_disappears` | 28 | 3.000 | 0.300 | `{"blocking_path":28,"near_agent":28,"near_path":28}` |
| `object_moves` | 28 | 11.286 | 1.129 | `{"blocking_path":32,"near_agent":224,"near_path":60}` |
| `planner_disagreement` | 28 | 16.286 | 1.629 | `{"blocking_path":88,"near_agent":280,"near_path":88}` |
| `risk_increases` | 28 | 15.000 | 1.500 | `{"blocking_path":84,"near_agent":252,"near_path":84}` |
| `target_reachable` | 28 | 3.000 | 1.000 | `{"target_reachable":84}` |
| `unknown_near_path` | 28 | 16.000 | 1.600 | `{"blocking_path":84,"near_agent":280,"near_path":84}` |

## Aggregate Results

- Total runs: 280
- Failed runs: 0
- Overall success rate: 1.000
- Overall average near-miss count: 4.664
- Overall latency avg / p50 / p95 ms: 0.371 / 0.368 / 0.437

## Scenario-level Observations

| Scenario | Runs | Success Rate | Avg Near-miss | Avg RAST vs Object | Avg RAST vs Flat | Avg Object vs Flat | Avg RAST vs Event-aware |
|---|---:|---:|---:|---:|---:|---:|---:|
| `clear_path` | 28 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `far_obstacle` | 28 | 1.000 | 0.357 | 4.786 | 0.000 | 4.786 | 0.071 |
| `near_obstacle` | 28 | 1.000 | 10.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `object_appears` | 28 | 1.000 | 9.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `object_disappears` | 28 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `object_moves` | 28 | 1.000 | 7.000 | 7.000 | 0.000 | 7.000 | 0.714 |
| `planner_disagreement` | 28 | 1.000 | 1.286 | 8.714 | 0.000 | 8.714 | 0.143 |
| `risk_increases` | 28 | 1.000 | 9.000 | 0.000 | 0.000 | 0.000 | 0.714 |
| `target_reachable` | 28 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `unknown_near_path` | 28 | 1.000 | 10.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Baseline Disagreement Analysis

- Average RAST vs Object List disagreement: 2.050
- Average RAST vs Flat Feature disagreement: 0.000
- Average Object List vs Flat Feature disagreement: 2.050
- Average RAST vs Event-aware RAST disagreement: 0.164
- Flat Feature가 RAST와 자주 일치한다면, 현재 toy setup에서는 scalar risk feature가 두 planner의 action을 크게 좌우한다는 뜻으로 해석해야 합니다.
- Object List와 RAST가 달라지는 경우는 distance-only object view와 risk-aware scalar/token view가 서로 다른 action boundary를 만들 수 있음을 보여줍니다.
- 이 차이는 아직 RAST의 우수성을 뜻하지 않으며, 같은 information bound에서 구조화 효과를 더 분리해 검증해야 합니다.

## Decision Trace Summary

- PlannerDecision trace is included in this report when planner reason_code fields are present in aggregate results.
- Average decision_trace_coverage: 1.000
- Total RAST trigger token references: 1740
- Average RAST trigger token references per episode: 6.214
- RAST, Object List, and Flat Feature planners can choose the same action for different reasons.
- These traces are rule-based planner explanations, not learned model interpretability results.
- EventToken is used only by the separate Event-aware RAST experimental planner; the existing RAST planner remains unchanged.

| Planner | Reason Code Counts |
|---|---|
| RAST | `{"no_risk_move_ahead":864,"risk_token_present":1740}` |
| Object List | `{"near_object_distance":1166,"no_near_object_move_ahead":1438}` |
| Flat Feature | `{"no_risk_scalar_move_ahead":864,"within_risk_threshold":1740}` |
| Event-aware RAST | `{"event_object_appeared_near_path":24,"event_object_disappeared_clear_path":24,"event_object_moved":12,"event_risk_increased":100,"fallback_no_risk_move_ahead":840,"fallback_risk_token_present":1604}` |

| Scenario | Runs | Decision Trace Coverage | RAST Reason Codes |
|---|---:|---:|---|
| `clear_path` | 28 | 1.000 | `{"no_risk_move_ahead":280}` |
| `far_obstacle` | 28 | 1.000 | `{"no_risk_move_ahead":136,"risk_token_present":144}` |
| `near_obstacle` | 28 | 1.000 | `{"risk_token_present":280}` |
| `object_appears` | 28 | 1.000 | `{"no_risk_move_ahead":28,"risk_token_present":252}` |
| `object_disappears` | 28 | 1.000 | `{"no_risk_move_ahead":252,"risk_token_present":28}` |
| `object_moves` | 28 | 1.000 | `{"no_risk_move_ahead":56,"risk_token_present":224}` |
| `planner_disagreement` | 28 | 1.000 | `{"risk_token_present":280}` |
| `risk_increases` | 28 | 1.000 | `{"no_risk_move_ahead":28,"risk_token_present":252}` |
| `target_reachable` | 28 | 1.000 | `{"no_risk_move_ahead":84}` |
| `unknown_near_path` | 28 | 1.000 | `{"risk_token_present":280}` |

## Scene Graph Baseline Summary

- Scene Graph baseline은 MVP용 simplified graph입니다.
- Graph node는 agent/object/optional goal이며 edge는 near_agent, near_path, blocking_path, target_reachable relation입니다.
- Scene Graph planner는 RiskToken의 severity, risk_type, recommended_policy 같은 RAST-only contract field를 사용하지 않습니다.
- Average Scene Graph node count: 2.500
- Average Scene Graph edge count: 1.136
- Average RAST vs Scene Graph disagreement: 0.000
- Average Scene Graph vs Flat Feature disagreement: 0.000
- Average Scene Graph decision trace coverage: 1.000
- Scene Graph reason code distribution: `{"graph_blocking_path":532,"graph_near_object":1208,"graph_no_blocking_move_ahead":780,"graph_target_reachable":84}`
- RAST와 Scene Graph의 차이는 representation 차이를 관찰하기 위한 것이며 RAST 우수성을 의미하지 않습니다.

| Scenario | Runs | Avg Nodes | Avg Edges | Avg RAST vs Scene Graph | Scene Graph Reason Codes |
|---|---:|---:|---:|---:|---|
| `clear_path` | 28 | 3.000 | 0.000 | 0.000 | `{"graph_no_blocking_move_ahead":280}` |
| `far_obstacle` | 28 | 2.000 | 1.100 | 0.000 | `{"graph_blocking_path":48,"graph_near_object":96,"graph_no_blocking_move_ahead":136}` |
| `near_obstacle` | 28 | 2.000 | 1.600 | 0.000 | `{"graph_blocking_path":84,"graph_near_object":196}` |
| `object_appears` | 28 | 2.900 | 1.500 | 0.000 | `{"graph_blocking_path":84,"graph_near_object":168,"graph_no_blocking_move_ahead":28}` |
| `object_disappears` | 28 | 2.100 | 0.300 | 0.000 | `{"graph_blocking_path":28,"graph_no_blocking_move_ahead":252}` |
| `object_moves` | 28 | 3.000 | 1.129 | 0.000 | `{"graph_blocking_path":32,"graph_near_object":192,"graph_no_blocking_move_ahead":56}` |
| `planner_disagreement` | 28 | 2.000 | 1.629 | 0.000 | `{"graph_blocking_path":88,"graph_near_object":192}` |
| `risk_increases` | 28 | 3.000 | 1.500 | 0.000 | `{"graph_blocking_path":84,"graph_near_object":168,"graph_no_blocking_move_ahead":28}` |
| `target_reachable` | 28 | 3.000 | 1.000 | 0.000 | `{"graph_target_reachable":84}` |
| `unknown_near_path` | 28 | 2.000 | 1.600 | 0.000 | `{"graph_blocking_path":84,"graph_near_object":196}` |

## Event-aware Planner Summary

- Event-aware RAST planner included in this report: yes
- Average RAST vs Event-aware RAST disagreement: 0.164
- Total event-triggered Event-aware actions: 160
- Average event-triggered Event-aware actions per episode: 0.571
- Average Event-aware decision trace coverage: 1.000
- Event-aware reason code distribution: `{"event_object_appeared_near_path":24,"event_object_disappeared_clear_path":24,"event_object_moved":12,"event_risk_increased":100,"fallback_no_risk_move_ahead":840,"fallback_risk_token_present":1604}`
- Scenarios with observed RAST vs Event-aware disagreement: `far_obstacle, object_moves, planner_disagreement, risk_increases`
- 같은 action이 선택되더라도 기존 RAST와 Event-aware RAST의 reason_code는 다를 수 있습니다.
- Event-aware planner는 deterministic rule-based experimental policy이며 성능 개선을 단정하는 근거가 아닙니다.

| Scenario | Runs | Avg RAST vs Event-aware Disagreement | Avg Event-triggered Actions | Event-aware Reason Codes |
|---|---:|---:|---:|---|
| `clear_path` | 28 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":280}` |
| `far_obstacle` | 28 | 0.071 | 1.286 | `{"event_risk_increased":36,"fallback_no_risk_move_ahead":136,"fallback_risk_token_present":108}` |
| `near_obstacle` | 28 | 0.000 | 0.000 | `{"fallback_risk_token_present":280}` |
| `object_appears` | 28 | 0.000 | 0.857 | `{"event_object_appeared_near_path":24,"fallback_no_risk_move_ahead":28,"fallback_risk_token_present":228}` |
| `object_disappears` | 28 | 0.000 | 0.857 | `{"event_object_disappeared_clear_path":24,"fallback_no_risk_move_ahead":228,"fallback_risk_token_present":28}` |
| `object_moves` | 28 | 0.714 | 1.714 | `{"event_object_moved":8,"event_risk_increased":40,"fallback_no_risk_move_ahead":56,"fallback_risk_token_present":176}` |
| `planner_disagreement` | 28 | 0.143 | 0.143 | `{"event_risk_increased":4,"fallback_risk_token_present":276}` |
| `risk_increases` | 28 | 0.714 | 0.857 | `{"event_object_moved":4,"event_risk_increased":20,"fallback_no_risk_move_ahead":28,"fallback_risk_token_present":228}` |
| `target_reachable` | 28 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":84}` |
| `unknown_near_path` | 28 | 0.000 | 0.000 | `{"fallback_risk_token_present":280}` |

## Event-aware Ablation Summary

- Event-aware policy variant가 aggregate row에 기록되어 variant별 비교가 가능합니다.
- `logging_only` variant는 EventToken을 입력으로 받지만 action에는 사용하지 않는 비교 조건입니다.
- 이 표는 어떤 event rule이 action change와 함께 관찰되는지 분리하기 위한 infrastructure이며, 성능 개선 주장으로 해석하면 안 됩니다.

| Event Policy Variant | Runs | Avg RAST vs Event-aware Disagreement | Avg Event-triggered Actions | Reason Codes |
|---|---:|---:|---:|---|
| `full` | 40 | 0.200 | 0.650 | `{"event_object_appeared_near_path":4,"event_object_disappeared_clear_path":4,"event_risk_increased":18,"fallback_no_risk_move_ahead":120,"fallback_risk_token_present":226}` |
| `logging_only` | 40 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":124,"fallback_risk_token_present":248}` |
| `no_risk_changed` | 40 | 0.000 | 0.500 | `{"event_object_appeared_near_path":4,"event_object_disappeared_clear_path":4,"event_object_moved":12,"fallback_no_risk_move_ahead":120,"fallback_risk_token_present":232}` |

| Scenario / Variant | Runs | Avg Disagreement | Avg Event-triggered Actions |
|---|---:|---:|---:|
| `clear_path | full` | 4 | 0.000 | 0.000 |
| `clear_path | logging_only` | 4 | 0.000 | 0.000 |
| `clear_path | no_risk_changed` | 4 | 0.000 | 0.000 |
| `far_obstacle | full` | 4 | 0.000 | 1.500 |
| `far_obstacle | logging_only` | 4 | 0.000 | 0.000 |
| `far_obstacle | no_risk_changed` | 4 | 0.000 | 0.000 |
| `near_obstacle | full` | 4 | 0.000 | 0.000 |
| `near_obstacle | logging_only` | 4 | 0.000 | 0.000 |
| `near_obstacle | no_risk_changed` | 4 | 0.000 | 0.000 |
| `object_appears | full` | 4 | 0.000 | 1.000 |
| `object_appears | logging_only` | 4 | 0.000 | 0.000 |
| `object_appears | no_risk_changed` | 4 | 0.000 | 1.000 |
| `object_disappears | full` | 4 | 0.000 | 1.000 |
| `object_disappears | logging_only` | 4 | 0.000 | 0.000 |
| `object_disappears | no_risk_changed` | 4 | 0.000 | 1.000 |
| `object_moves | full` | 4 | 1.000 | 2.000 |
| `object_moves | logging_only` | 4 | 0.000 | 0.000 |
| `object_moves | no_risk_changed` | 4 | 0.000 | 2.000 |
| `planner_disagreement | full` | 4 | 0.000 | 0.000 |
| `planner_disagreement | logging_only` | 4 | 0.000 | 0.000 |
| `planner_disagreement | no_risk_changed` | 4 | 0.000 | 0.000 |
| `risk_increases | full` | 4 | 1.000 | 1.000 |
| `risk_increases | logging_only` | 4 | 0.000 | 0.000 |
| `risk_increases | no_risk_changed` | 4 | 0.000 | 1.000 |
| `target_reachable | full` | 4 | 0.000 | 0.000 |
| `target_reachable | logging_only` | 4 | 0.000 | 0.000 |
| `target_reachable | no_risk_changed` | 4 | 0.000 | 0.000 |
| `unknown_near_path | full` | 4 | 0.000 | 0.000 |
| `unknown_near_path | logging_only` | 4 | 0.000 | 0.000 |
| `unknown_near_path | no_risk_changed` | 4 | 0.000 | 0.000 |

- variant별 reason_code distribution은 event rule 활성/비활성에 따른 action trace 차이를 보는 용도입니다.
- 현재 Event-aware planner는 deterministic rule-based policy이며 learned extractor나 learned policy가 아닙니다.

## Threshold and Noise Sensitivity Summary

- risk_threshold와 near_miss_threshold는 aggregate row에 보존되어 threshold sweep 분석에 사용할 수 있습니다.
- noise 값은 WindowsMetadataSim metadata에 적용한 synthetic seeded noise이며 실제 perception error가 아닙니다.
- 아래 값은 deterministic metadata simulator에서의 sensitivity 관찰용이며 real-world robustness claim을 지원하지 않습니다.

| Risk Threshold | Runs | Avg Near-miss | Avg RAST vs Event-aware Disagreement | Avg Event-triggered Actions |
|---|---:|---:|---:|---:|
| `1.5` | 280 | 4.664 | 0.164 | 0.571 |

| Noise Level | Runs | Success Rate | Avg Near-miss | Avg Disagreement |
|---|---:|---:|---:|---:|
| `position=0.0, distance=0.0, visibility=0.0` | 140 | 1.000 | 4.686 | 0.157 |
| `position=0.02, distance=0.02, visibility=0.0` | 140 | 1.000 | 4.643 | 0.171 |

- default suite가 작게 유지되는 경우 threshold/noise level 수가 제한될 수 있습니다.
- 더 강한 결론을 위해서는 별도 extended config로 threshold와 synthetic noise grid를 확장해야 합니다.

## Latency Summary

- Average latency: 0.371 ms
- Average p50 latency: 0.368 ms
- Average p95 latency: 0.437 ms
- Average token generation latency: 0.109 ms
- Average planning latency: 0.092 ms
- 이 latency는 Python metadata simulator 경로에서 측정된 값이며, real rendering이나 perception model overhead를 포함하지 않습니다.

| Apply Policy | Runs | Avg Latency ms | Avg Planning ms |
|---|---:|---:|---:|
| `event_aware_rast` | 120 | 0.372 | 0.092 |
| `flat_feature` | 40 | 0.373 | 0.093 |
| `object_list` | 40 | 0.371 | 0.092 |
| `rast` | 40 | 0.371 | 0.094 |
| `scene_graph` | 40 | 0.368 | 0.091 |

## Incremental Update Summary

- 이 섹션은 full token recomputation과 TokenMemory 기반 event-aware incremental update의 latency protocol을 비교합니다.
- incremental update optimization is experimental; 현재 결과는 최적화 완료나 planner 성능 개선을 의미하지 않습니다.
- WindowsMetadataSim은 metadata-only toy simulator이므로 absolute latency value는 매우 작고 실제 perception/model cost를 포함하지 않습니다.
- 이번 runner는 같은 snapshot에서 full_recompute와 incremental 후보를 모두 측정하고, 선택된 update_mode의 token generation latency를 step latency에 기록합니다.
- Overall changed object count avg: 0.255
- Overall affected token count avg: 1.325
- Overall full recompute latency avg: 0.131 ms
- Overall incremental update latency avg: 0.089 ms
- Overall incremental update benefit avg: 0.320

| Update Mode | Runs | Changed Objects Avg | Affected Tokens Avg | Full ms | Incremental ms | Benefit |
|---|---:|---:|---:|---:|---:|---:|
| `full_recompute` | 140 | 0.255 | 2.164 | 0.129 | 0.090 | 0.310 |
| `incremental` | 140 | 0.255 | 0.486 | 0.132 | 0.089 | 0.330 |

| Scenario | Runs | Changed Objects Avg | Affected Tokens Avg | Incremental Benefit Avg |
|---|---:|---:|---:|---:|
| `clear_path` | 28 | 0.250 | 1.175 | 0.311 |
| `far_obstacle` | 28 | 0.357 | 1.279 | 0.357 |
| `near_obstacle` | 28 | 0.100 | 1.100 | 0.330 |
| `object_appears` | 28 | 0.200 | 1.750 | 0.279 |
| `object_disappears` | 28 | 0.300 | 0.950 | 0.353 |
| `object_moves` | 28 | 0.500 | 2.250 | 0.260 |
| `planner_disagreement` | 28 | 0.114 | 1.129 | 0.315 |
| `risk_increases` | 28 | 0.300 | 1.850 | 0.290 |
| `target_reachable` | 28 | 0.333 | 0.667 | 0.383 |
| `unknown_near_path` | 28 | 0.100 | 1.100 | 0.323 |

## What This Result Supports

- WindowsMetadataSim 기반 scenario suite를 반복 실행할 수 있음을 보여줍니다.
- Object List / Flat Feature Table / RAST 세 representation과 planner action을 같은 log/summary contract로 기록할 수 있음을 보여줍니다.
- scenario별 disagreement, near-miss, success, latency를 aggregate table로 모을 수 있음을 보여줍니다.
- Flat Feature baseline을 통해 정보량 효과와 token contract 효과를 분리해서 보기 위한 실험 인프라가 준비되었음을 보여줍니다.
- EventToken이 semantic event를 감지하고 step log, episode summary, aggregate result에 기록될 수 있음을 보여줍니다.
- 별도 Event-aware RAST planner가 EventToken을 decision reason으로 사용할 수 있음을 보여줍니다.
- 세 planner의 action 선택 사유를 PlannerDecision trace로 기록하고 집계할 수 있음을 보여줍니다.

## What This Result Does Not Support

- This result does not support real-world performance claims.
- RAST가 Object List나 Flat Feature보다 일반적으로 우수하다는 결론을 지원하지 않습니다.
- Event-aware planner나 EventToken이 planning 성능, success, near-miss, disagreement를 개선했다는 결론을 지원하지 않습니다.
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
- Event-aware RAST planner는 deterministic rule-based policy이며 learned policy나 learned explanation이 아닙니다.
- TokenMemory는 현재 semantic diff와 incremental latency protocol에 사용되지만, incremental update optimization is experimental입니다.
- Batch 9의 incremental update는 measurement protocol 단계이며, 일부 token 계산은 correctness를 위해 여전히 재계산됩니다.
- full_recompute와 incremental 후보를 같은 step에서 모두 측정하므로 report의 selected token_generation latency와 실제 Python wall-clock은 다를 수 있습니다.
- EventToken은 별도 Event-aware planner에만 연결되므로, success/near-miss/disagreement 변화는 일반 RAST 효과로 해석하면 안 됩니다.
- PlannerDecision은 현재 deterministic rule-based policy의 내부 규칙을 기록한 것이며, learned model interpretability는 아닙니다.
- 동일 action이라도 planner별 reason_code와 trigger feature가 다를 수 있으므로 action count만으로 의사결정 근거를 해석하면 안 됩니다.
- RelationToken과 Scene Graph baseline은 MVP용 geometry-rule 구현이며, UncertaintyToken은 아직 포함하지 않습니다.
- Flat Feature와 RAST가 동일한 scalar risk rule에 강하게 묶여 있어 token contract 효과는 아직 제한적으로만 관찰됩니다.

## Next Steps

- scenario별 failure case와 action trace를 함께 저장해 decision explainability 분석을 강화합니다.
- threshold sensitivity sweep을 넓혀 RAST/Object List/Flat Feature disagreement boundary를 더 명확히 봅니다.
- noise injection과 unknown/occlusion scenario를 추가해 metadata-only 결과의 한계를 점진적으로 줄입니다.
- 이후 단계에서 Event-aware policy를 더 공정하게 ablation하고, 실제 incremental cache 재사용 최적화와 분리해 검토합니다.
- UncertaintyToken과 perception-bound adapter는 별도 Batch로 추가합니다.
- AI2-THOR나 다른 simulator로 확장할 때도 같은 aggregate/report contract를 유지합니다.
