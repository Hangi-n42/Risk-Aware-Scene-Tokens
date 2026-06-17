# RAST MVP-0 Technical Report

문서 버전: Batch 15B-R 업데이트  
최신 결과 기준: `runs/windows_eval_suite/windows_eval_suite_20260612_162821`  
관련 보고서: `docs/result_report.md`

## 1. Abstract

RAST, Risk-Aware Scene Tokens는 embodied agent의 planner가 raw observation 전체를 직접 처리하는 대신, action과 safety decision에 필요한 정보를 구조화된 token representation으로 받도록 설계한 연구형 프로토타입입니다. 현재 MVP-0는 WindowsMetadataSim 기반 deterministic metadata simulator에서 Object List, Flat Feature Table, Scene Graph, RAST, Event-aware RAST, Uncertainty-aware RAST, Affordance-aware RAST planner를 비교할 수 있는 evaluation harness를 제공합니다. 구현된 token은 EntityToken, RiskToken, RelationToken, EventToken, UncertaintyToken, EvidenceToken, AffordanceToken입니다. Batch 15B 이후 RAST MVP-0는 token, planner decision, evidence pointer, replay trace에 더해 navigation affordance 기반 action possibility를 기록하고, Affordance-aware RAST planner가 이를 별도 experimental policy로 사용할 수 있습니다. 최신 suite는 25개 scenario에서 900 runs를 실행했으며 failed run은 0개입니다. 다만 이 결과는 WindowsMetadataSim metadata simulator 기반이며 real sensor evidence, visual replay, 실제 RGB-D perception, detector error, real robot performance, 실제 robot action feasibility를 반영하지 않습니다. 따라서 본 보고서는 RAST의 real-world 성능 우수성을 주장하는 문서가 아니라, MVP-0의 방법론, 비교 구조, 관찰 결과, 한계를 정리하는 기술 보고서입니다.

## 2. Introduction

일반적인 embodied AI 또는 robotics pipeline은 RGB-D image, segmentation, object detection, scene graph, dense feature를 perception output으로 사용합니다. 하지만 planner가 직접 필요로 하는 정보는 픽셀 전체라기보다 object, risk, uncertainty, event, relation, decision evidence처럼 action과 연결되는 구조화된 정보입니다. RAST는 raw observation과 planner 사이의 interface를 planner-facing token contract로 정의하려는 시도입니다.

Object List는 object id, category, position, distance를 제공하지만 위험, 불확실성, semantic event, decision reason을 명시적으로 담기 어렵습니다. Scene Graph는 relation edge를 제공하지만 RiskToken의 severity, recommended policy, EventToken의 semantic diff, UncertaintyToken의 level과 recommended action, EvidenceToken의 metadata pointer와는 구분됩니다. RAST는 이 사이의 interface를 명시적인 token contract로 정의합니다.

현재 MVP-0는 실제 로봇 배포나 고성능 perception model 검증이 아니라, deterministic metadata simulator에서 representation과 evaluation harness가 동작하는지 검증하는 단계입니다. 따라서 결과 해석은 "성능 우수성"보다 "비교 가능한 실험 구조와 traceability가 구축되었는가"에 초점을 둡니다.

## 3. Problem Statement

Dense observation은 풍부하지만 planner input으로 사용하기에는 latency, memory footprint, planning complexity가 커질 수 있습니다. Object List는 가볍지만 risk, uncertainty, semantic change, evidence pointer를 표현하기 어렵습니다. Scene Graph는 relation structure를 제공하지만 planner-facing risk contract나 uncertainty-driven policy boundary를 직접 표현하지 않습니다.

RAST가 다루는 핵심 문제는 다음과 같습니다.

| 문제 | 기존 표현의 한계 | MVP-0에서 확인하려는 방향 |
| --- | --- | --- |
| Risk representation | object가 가까운지 여부만으로는 risk severity와 policy trigger를 구분하기 어렵습니다. | RiskToken과 decision trace로 risk 기반 action 이유를 기록합니다. |
| Event representation | 매 step 전체 상태만 보면 무엇이 변했는지 별도로 드러나지 않습니다. | EventToken으로 appeared, disappeared, moved, risk_changed를 기록합니다. |
| Relation representation | graph edge는 유용하지만 risk severity와 uncertainty를 직접 담지는 않습니다. | RelationToken과 Scene Graph baseline을 분리해 비교합니다. |
| Uncertainty representation | unknown object, occlusion, position variance, sensor disagreement를 object list만으로 표현하기 어렵습니다. | UncertaintyToken과 Uncertainty-aware planner를 별도 실험 조건으로 둡니다. |
| Evidence traceability | token과 decision의 근거 source를 사후 추적하기 어렵습니다. | EvidenceToken으로 metadata pointer, bbox-like field, feature source, decision trace를 연결합니다. |
| Affordance representation | risk 또는 relation만으로는 agent가 취할 수 있는 action possibility를 명시적으로 분리하기 어렵습니다. | AffordanceToken으로 passable, blocking, inspect_required, avoid_required 같은 navigation strategy hint를 기록합니다. |

## 4. Proposed Representation: RAST

### 4.1 Implemented Tokens

| Token | 상태 | 설명 | Planner-facing 역할 |
| --- | --- | --- | --- |
| EntityToken | 구현 완료 | object id, category, position, distance, confidence를 표현합니다. | planner와 baseline이 공통으로 사용하는 object-level semantic unit입니다. |
| RiskToken | 구현 완료 | near path, near agent, unknown object 등 navigation risk를 표현합니다. | risk severity와 trigger token을 통해 보수적 action reason을 제공합니다. |
| RelationToken | 구현 완료 | near_agent, near_path, blocking_path, target_reachable relation을 표현합니다. | RAST와 Scene Graph baseline을 공정하게 비교하기 위한 relation unit입니다. |
| EventToken | 구현 완료 | object_appeared, object_disappeared, object_moved, risk_changed를 표현합니다. | semantic event logging과 Event-aware planner의 reason source로 사용됩니다. |
| UncertaintyToken | 구현 완료 | classification uncertainty, position uncertainty, partial occlusion, low sensor agreement, unknown object를 표현합니다. | synthetic uncertainty를 명시적 token으로 보존하고, Uncertainty-aware planner의 decision reason으로 사용할 수 있습니다. |
| EvidenceToken | 구현 완료 | metadata pointer, bbox-like field, risk/uncertainty/event feature, planner decision evidence를 표현합니다. | token과 PlannerDecision이 어떤 snapshot, object, feature source에서 비롯되었는지 audit 가능하게 연결합니다. |
| AffordanceToken | 구현 완료 | passable, blocking, narrow_passage, target_reachable, inspect_required, avoid_required navigation affordance를 표현합니다. | agent가 취할 수 있는 action possibility 또는 strategy hint를 Affordance-aware planner의 decision reason으로 사용할 수 있습니다. |

UncertaintyToken은 RiskToken과 동일하지 않습니다. High uncertainty가 항상 high risk를 뜻하지 않도록 설계되어 있으며, uncertainty가 path와 관련될 때 별도 experimental planner가 보수적으로 반응할 수 있게 합니다. 현재 UncertaintyToken은 WindowsMetadataSim의 synthetic metadata uncertainty 기반이며 실제 perception uncertainty calibration 결과가 아닙니다.

EvidenceToken은 현재 metadata pointer 기반입니다. WindowsMetadataSim에는 실제 RGB/depth frame이나 image crop이 없으므로, EvidenceToken은 raw sensor evidence가 아니라 object id, metadata path, bbox-like field, token id, decision reason 같은 traceability 정보를 저장합니다. 따라서 EvidenceToken은 성능 개선 근거가 아니라 audit과 replay를 위한 infrastructure입니다.

AffordanceToken은 RiskToken, UncertaintyToken, EvidenceToken과 구분됩니다. RiskToken은 위험을 표현하고, UncertaintyToken은 정보의 불확실성을 표현하며, EvidenceToken은 판단 근거를 추적합니다. AffordanceToken은 이들과 별도로 agent가 취할 수 있는 action possibility 또는 strategy hint를 표현합니다. 예를 들어 high uncertainty near path는 high RiskToken이 없어도 `inspect_required` affordance를 만들 수 있고, blocking object는 RiskToken으로도 표현될 수 있지만 AffordanceToken에서는 `avoid_required` 또는 `blocking`이라는 action-oriented interpretation으로 표현됩니다.

### 4.2 Future Extension

현재 core token set은 MVP-0 범위에서 모두 구현되었습니다. 후속 확장은 token 자체의 추가보다 manipulation affordance, learned extractor, perception-bound adapter, real simulator adapter처럼 extraction 품질과 simulator 현실성을 높이는 방향으로 둡니다.

## 5. System Architecture

현재 MVP-0 pipeline은 다음과 같습니다.

```text
WindowsMetadataSim
→ ObservationSnapshot
→ Tokenizers
→ EvidenceToken generation
→ Baselines
→ Planners
→ PlannerDecision
→ Evidence-linked Step Log
→ Aggregate Report
→ Decision Replay Export
```

| Module | 역할 |
| --- | --- |
| WindowsMetadataSim | deterministic metadata 기반 scenario, object, goal, synthetic uncertainty, synthetic event를 생성합니다. |
| ObservationSnapshot | scene id, step, agent pose, object metadata를 공통 입력 구조로 정규화합니다. |
| Tokenizers | Entity, Risk, Relation, Event, Uncertainty, Evidence, Affordance token을 생성합니다. |
| TokenMemory | 직전 state와 현재 state를 비교해 semantic event와 incremental update 측정 정보를 제공합니다. |
| Baselines | Object List, Flat Feature Table, Scene Graph representation을 생성합니다. |
| Planners | Object List, Flat Feature, Scene Graph, RAST, Event-aware RAST, Uncertainty-aware RAST, Affordance-aware RAST planner가 PlannerDecision을 생성합니다. |
| Evaluation Logger | step log, episode summary, aggregate result, report input을 기록합니다. |
| Replay Exporter | 중요한 decision step을 metadata/action/evidence trace markdown/json으로 재구성합니다. |

## 6. Baselines

| 비교군 | 사용하는 정보 | 사용하지 않는 정보 |
| --- | --- | --- |
| Object List | object id, category, position, visible, distance | risk_score, recommended_policy, token contract, event, uncertainty, evidence |
| Flat Feature Table | RAST와 동일한 scalar feature 일부, risk_score_scalar, within_risk_threshold | token_type, risk_type, severity, recommended_policy, evidence pointer |
| Scene Graph | agent/object/goal node, near_agent, near_path, blocking_path, target_reachable edge | RiskToken severity, recommended_policy, EventToken, UncertaintyToken, EvidenceToken |
| RAST | EntityToken, RiskToken, RelationToken, EventToken/UncertaintyToken/EvidenceToken logging, PlannerDecision trace | 기본 RAST planner는 EventToken 또는 UncertaintyToken으로 action을 바꾸지 않습니다. |
| Event-aware RAST | EntityToken, RiskToken, EventToken | 기존 RAST planner를 대체하지 않는 별도 experimental planner이며, EventToken을 decision reason으로 사용할 수 있습니다. |
| Uncertainty-aware RAST | EntityToken, RiskToken, EventToken optional, UncertaintyToken | 기존 RAST planner를 대체하지 않는 별도 experimental planner이며, UncertaintyToken을 decision reason으로 사용할 수 있습니다. |
| Affordance-aware RAST | EntityToken, RiskToken, RelationToken, UncertaintyToken optional, AffordanceToken | 기존 RAST planner를 대체하지 않는 별도 experimental planner이며, navigation AffordanceToken을 decision reason으로 사용할 수 있습니다. |

Event-aware RAST, Uncertainty-aware RAST, Affordance-aware RAST는 각각 EventToken, UncertaintyToken, AffordanceToken이 action/reason boundary에 연결될 수 있는지 관찰하기 위한 실험 조건입니다. 이 planner들이 action을 바꾼다는 사실만으로 safety나 task success가 개선되었다고 해석하면 안 됩니다.

## 7. Experimental Setup

| 항목 | 값 |
| --- | --- |
| Simulator | WindowsMetadataSim |
| Simulation type | deterministic metadata simulator |
| Total scenarios | 25 |
| Total runs | 900 |
| Failed runs | 0 |
| Apply policies | object_list, flat_feature, scene_graph, rast, event_aware_rast, uncertainty_aware_rast, affordance_aware_rast |
| Update modes | full_recompute, incremental |
| Event policy variants | full, logging_only, no_risk_changed, no_object_appeared, no_object_moved, no_object_disappeared |
| Noise | synthetic metadata noise fields, default suite에서는 제한적 variation |
| Result source | `runs/windows_eval_suite/windows_eval_suite_20260612_162821` |

Batch 16D 이후에는 full extended grid `8,294,400`개 조합을 모두 실행하지 않고, stratified sampled extended evaluation으로 sensitivity를 점검하는 보조 경로가 추가되었습니다. 최신 sampled seed sweep은 `configs/windows_eval_suite_extended.yaml`에서 sample-size 500, sample seeds `7, 13, 42`를 사용했으며 각 seed별 failed run은 0개였습니다. 이 sampled result는 exhaustive grid 결과가 아니며, seed와 sample composition에 의존하는 coverage/stability artifact로 해석해야 합니다.

대표 scenario는 clear_path, near_obstacle, far_obstacle, unknown_near_path, target_reachable, planner_disagreement, object_appears, object_disappears, object_moves, risk_increases, relation_near_but_low_risk, risk_without_graph_blocking, event_changes_risk_but_graph_static, unknown_uncertain_object, partially_occluded_obstacle, noisy_position_boundary, low_sensor_agreement, uncertainty_without_high_risk, uncertainty_near_path 등을 포함합니다. Affordance 관련 scenario로는 `narrow_passage`, `passable_clear_gap`, `inspect_required_uncertain_path`, `avoid_required_blocking_path`, `target_reachable_affordance`가 추가되었습니다.

주요 metric은 다음과 같습니다.

| Metric group | 예시 |
| --- | --- |
| Task and safety proxy | success, goal_reached, collision_count, near_miss_count |
| Latency | planning latency, token generation latency, total latency, p50, p95 |
| Representation size | token_count_avg, object_count_avg, flat_feature_row_count_avg, scene_graph_node/edge count |
| Token summary | risk/event/relation/uncertainty/evidence/affordance token count와 type distribution |
| Planner comparison | action counts, disagreement counts, same-action-different-reason |
| Explainability | reason_code_counts, trigger token/object counts, decision_trace_coverage, affordance-aware decision trace coverage |
| Incremental protocol | update_mode, changed_object_count, affected_token_count, incremental_update_benefit |
| Evidence and replay | evidence_type_counts, decision_evidence_coverage, replay export availability |
| Affordance metrics | affordance_token_count, affordance_type_counts, rast_vs_affordance_aware_disagreement, affordance_triggered_action_count |

## 8. Results

### 8.1 Aggregate Run Summary

최신 suite는 900 runs를 실행했고 failed run은 0개였습니다. 이 수치는 WindowsMetadataSim evaluation harness가 현재 scenario, planner, token, logging, aggregation path를 오류 없이 순회했다는 의미입니다. 실제 robot task success나 perception robustness를 의미하지는 않습니다.

### 8.1.1 Sampling Coverage and Seed Stability

Batch 16D에서는 sampled extended evaluation의 coverage와 seed-to-seed stability를 별도 artifact로 생성했습니다. 최신 coverage report는 `docs/sampling_coverage_report.md`이며, seed stability report는 `docs/seed_stability_report.md`입니다. Seed 42 sampled run 기준으로 25개 scenario와 주요 threshold/noise 축이 모두 관측되었고, `event_policy_variant`는 `apply_policy=event_aware_rast` subset 안에서 `full: 9`, `logging_only: 9`, `no_object_appeared: 8`, `no_object_disappeared: 8`, `no_object_moved: 8`, `no_risk_changed: 8`로 균형 있게 샘플링되었습니다.

Seed stability 분석은 seeds `7, 13, 42`와 sample-size 500으로 수행되었습니다. 세 seed 모두 25개 scenario를 포함했으며 failed run은 0개였습니다. High-variance 후보 metric은 `RAST vs Flat Feature disagreement`, `RAST vs Uncertainty-aware disagreement`, `avg token generation latency ms` 등으로 관찰되었으나, 이는 sample composition sensitivity로 보아야 하며 성능 개선 또는 악화로 해석하면 안 됩니다.

Sample-size convergence artifact는 sample-size 100/200/500 등에서 metric stability와 sampling quality score를 비교하는 reliability check입니다. 이 역시 full extended grid exhaustive result가 아니며, sampling quality score는 RAST 또는 특정 planner의 성능 점수가 아니라 coverage, balance, seed stability를 요약하는 heuristic입니다.

### 8.2 EventToken Summary

EventToken은 semantic diff 기반으로 생성되며 object_appeared, object_disappeared, object_moved, risk_changed를 기록합니다. EventToken은 Event-aware RAST planner의 reason source로 연결될 수 있지만, Event-aware policy는 deterministic rule-based experimental policy입니다. 따라서 EventToken이 action을 바꾸는 관찰은 event-driven representation 연결이 가능하다는 infrastructure-level 결과로 해석해야 합니다.

### 8.3 RelationToken Summary

RelationToken은 near_agent, near_path, blocking_path, target_reachable relation을 표현합니다. Scene Graph baseline도 같은 ObservationSnapshot에서 relation edge를 생성합니다. 이 구조는 RAST와 Scene Graph가 같은 action을 내더라도 decision basis가 다를 수 있음을 기록하기 위해 도입되었습니다.

### 8.4 UncertaintyToken Summary

UncertaintyToken은 총 5120개 생성되었습니다. episode당 평균 UncertaintyToken count는 8.000입니다. 총 high uncertainty count는 3840입니다.

| Uncertainty type | Count |
| --- | ---: |
| classification_uncertainty | 960 |
| position_uncertainty | 640 |
| partial_occlusion | 640 |
| low_sensor_agreement | 640 |
| unknown_object | 2240 |

Uncertainty-aware RAST planner의 평균 RAST vs Uncertainty-aware RAST disagreement는 0.447입니다. Total uncertainty-triggered actions는 1824개였고, episode당 평균 uncertainty-triggered actions는 2.850입니다. Decision trace coverage는 1.000입니다.

이 결과는 UncertaintyToken이 planner reason/action boundary에 연결될 수 있음을 보여주는 infrastructure-level 결과입니다. 성능 개선, safety improvement, real-world uncertainty handling 증거는 아닙니다.

### 8.5 EvidenceToken Summary

EvidenceToken은 총 47440개 생성되었습니다. episode당 평균 EvidenceToken count는 7.622입니다. Decision evidence coverage는 1.000으로 기록되었습니다.

| Evidence type | Count |
| --- | ---: |
| planner_decision | 37056 |
| risk_feature | 4570 |
| uncertainty_feature | 5120 |
| event_diff | 694 |

EvidenceToken은 RiskToken, UncertaintyToken, EventToken, PlannerDecision과 연결됩니다. 현재 evidence는 metadata pointer, bbox-like field, token id, decision reason, feature source를 포함하는 traceability record입니다. WindowsMetadataSim에는 실제 frame이 없으므로 raw image crop, RGB frame, depth frame, real sensor evidence는 저장하지 않습니다.

### 8.6 Replay Trace Summary

`experiments/export_decision_replay.py`를 사용하면 특정 run directory의 `step_log.jsonl`에서 중요한 decision step을 추출해 replay markdown/json을 생성할 수 있습니다. 현재 replay 대상은 다음 case를 포함합니다.

| Replay case | 설명 |
| --- | --- |
| planner disagreement | planner 간 selected action 또는 reason이 다른 step |
| uncertainty-triggered action | Uncertainty-aware planner가 uncertainty reason으로 반응한 step |
| event-triggered action | Event-aware planner가 event reason으로 반응한 step |
| high RiskToken step | high severity risk가 포함된 step |
| high UncertaintyToken step | high level uncertainty가 포함된 step |
| near-miss step | geometry threshold 기반 near-miss proxy가 true인 step |

Replay는 visual replay가 아니라 metadata/action/evidence trace 재구성입니다. 즉, 실제 이미지나 센서 프레임을 다시 보여주는 기능이 아니라, 어떤 metadata object와 token, planner reason이 action에 연결되었는지를 사람이 읽을 수 있게 정리하는 기능입니다.

### 8.7 AffordanceToken Summary

AffordanceToken은 총 9346개 생성되었습니다. episode당 평균 AffordanceToken count는 10.384이고, step당 평균 count는 1.150입니다. Affordance-triggered action count는 8172개로 기록되었습니다.

| Affordance type | Count |
| --- | ---: |
| passable | 5734 |
| blocking | 1170 |
| narrow_passage | 104 |
| target_reachable | 216 |
| inspect_required | 1994 |
| avoid_required | 128 |

AffordanceToken은 MVP-0에서 navigation affordance만 표현합니다. `graspable`, `openable`, `movable`, `container`, `fragile` 같은 manipulation affordance는 포함하지 않습니다. 또한 현재 AffordanceToken은 simple geometry/rule 기반 metadata affordance이며 실제 robot action feasibility를 검증한 결과가 아닙니다.

### 8.8 Affordance-aware Planner Summary

Affordance-aware RAST planner는 기존 RAST planner를 대체하지 않는 별도 experimental planner입니다. 기존 RAST planner는 AffordanceToken으로 action을 바꾸지 않으며, Affordance-aware RAST planner에서만 navigation affordance가 decision reason으로 사용됩니다.

| Metric | Value |
| --- | ---: |
| Average RAST vs Affordance-aware RAST disagreement | 5.720 |
| Total affordance-triggered actions | 8172 |
| Average affordance-triggered actions per episode | 9.080 |
| Average Affordance-aware decision trace coverage | 1.000 |

Affordance-aware reason code distribution은 `affordance_avoid_required`, `affordance_inspect_required`, `affordance_narrow_passage_slow_or_rotate`, `affordance_passable_move_ahead`, `affordance_target_reachable` 등을 포함합니다. 이 action 변화는 affordance가 planner reason/action boundary에 연결될 수 있음을 보여주는 infrastructure-level 관찰이며, task performance improvement 또는 real robot feasibility를 의미하지 않습니다.

### 8.9 Baseline Disagreement

Object List, Flat Feature Table, Scene Graph, RAST, Event-aware RAST, Uncertainty-aware RAST, Affordance-aware RAST는 모두 같은 ObservationSnapshot에서 출발합니다. Flat Feature Table은 RAST와 같은 scalar feature를 일부 공유하지만 token contract field는 제거합니다. Scene Graph는 relation edge를 사용하지만 RiskToken severity, EventToken semantic diff, UncertaintyToken, EvidenceToken, AffordanceToken을 사용하지 않습니다.

따라서 disagreement는 단순히 "어느 planner가 더 좋다"는 결과가 아니라, representation과 rule boundary가 어떻게 다른 action/reason을 만들었는지 관찰하기 위한 signal입니다.

### 8.10 Decision Trace Coverage

PlannerDecision은 planner_name, action, reason_code, reason_text, trigger_object_ids, trigger_token_ids, trigger_features, confidence를 포함합니다. MVP-0에서는 rule-based planner가 deterministic reason_code를 생성하므로 decision_trace_coverage가 높게 유지됩니다. 단, 이는 learned model interpretability가 아니라 rule-based decision trace입니다.

### 8.11 Incremental Update Summary

MVP-0는 full_recompute와 incremental update mode를 모두 기록합니다. incremental mode는 TokenMemory와 semantic diff를 사용해 changed object count, affected token count, incremental_update_benefit을 기록합니다. 하지만 현재 WindowsMetadataSim latency는 매우 작고 Python-level measurement이므로 absolute latency 수치는 조심해서 해석해야 합니다. 이 결과는 incremental optimization 완료가 아니라 비교 protocol 구축으로 해석해야 합니다.

### 8.12 Scene Graph vs RAST Differentiation

Batch 13B 이후 relation threshold와 risk threshold를 분리해 Scene Graph와 RAST의 decision basis 차이를 관찰할 수 있게 했습니다. `rast_vs_scene_graph_same_action_different_reason_count`는 action disagreement가 없더라도 Scene Graph와 RAST가 서로 다른 reason으로 같은 action을 선택했는지 기록합니다. 이는 representation 차이를 관찰하기 위한 metric이며, RAST 우수성의 직접 증거가 아닙니다.

### 8.13 Event-aware Planner Ablation

Event-aware planner는 full, logging_only, no_risk_changed, no_object_appeared, no_object_moved, no_object_disappeared variant를 지원합니다. logging_only는 EventToken을 입력으로 받지만 기존 RAST planner와 유사하게 행동하도록 설계되어, event policy 자체의 action boundary 영향을 분리할 수 있습니다.

### 8.14 Threshold and Noise Sensitivity

Risk threshold, near-miss threshold, synthetic position noise, distance noise, visibility flip probability는 aggregate row에 기록됩니다. 현재 noise는 deterministic-seeded synthetic metadata noise이며 실제 perception error나 sensor noise를 대표하지 않습니다. 따라서 sensitivity 결과는 실험 infrastructure 검증으로 해석해야 합니다.

## 9. Discussion

### 9.1 RAST와 Flat Feature가 자주 일치한다는 것은 무엇을 의미하는가?

Flat Feature Table은 RAST와 유사한 scalar risk feature와 within_risk_threshold를 받기 때문에 단순 navigation risk boundary에서는 같은 action을 선택하기 쉽습니다. 따라서 현재 결과만으로 token contract의 고유 효과를 강하게 주장할 수 없습니다. 다만 RAST는 같은 scalar feature 위에 token type, reason trace, EventToken, RelationToken, UncertaintyToken, EvidenceToken을 연결할 수 있는 구조를 제공합니다.

### 9.2 RAST와 Scene Graph가 같은 action을 내도 reason이 다를 수 있다는 것은 무엇을 의미하는가?

Scene Graph는 relation edge를 기반으로 action을 선택합니다. RAST는 RiskToken, RelationToken, EventToken, UncertaintyToken, EvidenceToken을 포함한 token contract와 PlannerDecision trace를 함께 기록합니다. 두 planner가 같은 action을 선택해도 Scene Graph는 `graph_blocking_path`, RAST는 `high_risk_token`처럼 다른 reason_code를 가질 수 있습니다. 이 차이는 action-level metric만으로는 보이지 않는 representation basis 차이를 보여줍니다.

### 9.3 Event-aware planner가 action을 바꾸는 것이 곧 성능 개선을 의미하지 않는 이유는 무엇인가?

Event-aware planner는 deterministic rule-based policy입니다. EventToken은 semantic diff 기반이며 실제 perception event detection이 아닙니다. 따라서 Event-aware planner가 기존 RAST와 다른 action을 선택했다는 사실은 EventToken이 policy boundary에 연결될 수 있음을 보여줄 뿐, task success나 safety metric 개선을 증명하지 않습니다.

### 9.4 Uncertainty-aware planner가 action을 바꾸는 것이 곧 안전성 개선을 의미하지 않는 이유는 무엇인가?

Uncertainty-aware planner는 synthetic metadata uncertainty 기반입니다. classification uncertainty, position variance, occlusion ratio, sensor agreement는 WindowsMetadataSim에서 생성한 field이며 실제 perception uncertainty calibration이나 real multi-sensor fusion 결과가 아닙니다. 또한 현재 policy는 deterministic rule-based planner입니다. 따라서 action change는 uncertainty token이 decision reason에 연결될 수 있음을 보여주는 것이며, 안전성 개선을 의미하지 않습니다.

### 9.5 EvidenceToken이 왜 필요한가?

RiskToken, UncertaintyToken, EventToken만 있으면 planner가 어떤 판단을 했는지는 알 수 있지만, 그 근거가 어디서 왔는지는 약하게 남습니다. EvidenceToken은 token과 PlannerDecision을 metadata snapshot, object id, bbox-like field, feature source에 연결합니다. 이는 RAST의 planner-facing representation을 더 audit 가능하게 만들고, 중요한 action decision을 replay trace로 재구성할 수 있게 합니다. 단, 현재 EvidenceToken은 real image crop이나 real sensor evidence가 아니라 WindowsMetadataSim metadata pointer입니다.

### 9.6 AffordanceToken이 RiskToken/UncertaintyToken과 다른 점은 무엇인가?

RiskToken은 위험을 표현합니다. UncertaintyToken은 정보의 불확실성을 표현합니다. AffordanceToken은 agent가 취할 수 있는 action possibility 또는 strategy hint를 표현합니다. 예를 들어 high uncertainty near path는 RiskToken이 없더라도 `inspect_required` affordance를 만들 수 있습니다. 또한 blocking object는 RiskToken으로도 표현될 수 있지만, AffordanceToken에서는 `avoid_required` 또는 `blocking`이라는 action-oriented interpretation으로 표현됩니다. 이 구분은 planner가 "무엇이 위험한가"와 "어떤 전략을 취할 수 있는가"를 분리해 기록하도록 돕습니다.

### 9.7 Affordance-aware planner가 action을 바꾸는 것이 곧 성능 개선을 의미하지 않는 이유는 무엇인가?

Affordance-aware planner는 simple geometry/rule 기반의 deterministic experimental policy입니다. 현재 AffordanceToken은 navigation affordance만 다루며 manipulation affordance를 포함하지 않습니다. 또한 실제 robot action feasibility, locomotion constraint, controller success 여부를 검증하지 않습니다. 따라서 Affordance-aware planner가 기존 RAST planner와 다른 action을 선택했다는 사실은 affordance token이 decision reason에 연결될 수 있음을 보여주는 것이며, success나 near-miss 개선을 통계적으로 입증하는 결과가 아닙니다.

### 9.8 incremental update benefit을 어떻게 해석해야 하는가?

현재 incremental update protocol은 full recompute와 incremental mode를 같은 scenario에서 비교하고 기록하는 실험 구조입니다. MVP-0의 toy metadata simulator에서는 latency가 매우 작아 measurement noise의 영향을 받을 수 있습니다. 따라서 incremental_update_benefit은 최적화 성능 주장보다 measurement protocol이 동작하는지 확인하는 지표로 해석해야 합니다.

## 10. Limitations

- WindowsMetadataSim은 deterministic metadata simulator입니다.
- 실제 3D rendering, physics, RGB-D perception, detector error를 반영하지 않습니다.
- AI2-THOR, Webots, CoppeliaSim, real robot 결과가 아닙니다.
- Rule-based tokenization과 rule-based planner 기반입니다.
- Learned model interpretability가 아닙니다.
- Scene Graph baseline은 MVP용 simplified graph입니다.
- RelationToken은 simple geometry rule 기반이며 learned relation extraction이 아닙니다.
- UncertaintyToken은 synthetic metadata uncertainty 기반입니다.
- UncertaintyToken은 실제 perception uncertainty calibration이 아닙니다.
- low sensor agreement는 simulated field이며 real multi-sensor fusion 결과가 아닙니다.
- Uncertainty-aware RAST planner는 deterministic rule-based experimental policy입니다.
- EvidenceToken은 현재 WindowsMetadataSim metadata pointer 기반입니다.
- raw image crop, RGB/depth frame, real sensor evidence는 저장하지 않습니다.
- decision replay는 visual replay가 아니라 metadata/action trace 재구성입니다.
- EvidenceToken은 traceability infrastructure이며 성능 개선 근거가 아닙니다.
- AffordanceToken은 현재 navigation affordance only입니다.
- manipulation affordance는 구현하지 않았습니다.
- AffordanceToken은 simple geometry/rule 기반입니다.
- 실제 robot action feasibility를 검증하지 않습니다.
- Affordance-aware RAST planner는 deterministic rule-based experimental policy입니다.
- AffordanceToken이 action을 바꾼다고 해서 task performance improvement를 의미하지 않습니다.
- 현재 결과만으로 RAST가 Object List, Flat Feature Table, Scene Graph보다 우수하다고 결론낼 수 없습니다.

## 11. Future Work

### P0 Next

| 항목 | 목적 |
| --- | --- |
| decision trace/failure case replay 고도화 | replay trace에 더 풍부한 object transition, token diff, scenario context를 연결합니다. |
| sampling-aware extended threshold/noise sweep | risk, relation, uncertainty threshold와 synthetic noise sensitivity를 seed/sample-size 변화와 함께 더 넓게 검증합니다. |
| evidence replay와 report 연결 강화 | replay artifact와 result/technical report 사이의 참조 경로를 더 명확히 연결합니다. |
| technical report polish | MVP-0 방법론, 실험 한계, 포트폴리오용 설명을 더 읽기 쉬운 형태로 정리합니다. |

### P1

| 항목 | 목적 |
| --- | --- |
| Webots adapter spike | Windows native에서 실제 3D simulator adapter 가능성을 검토합니다. |
| perception-bound adapter | simulator metadata가 아니라 detector/segmentation/depth output에서 token을 생성하는 경로를 추가합니다. |
| real simulator metadata adapter | AI2-THOR, Webots, CoppeliaSim 등 실제 simulator metadata와 ObservationSnapshot adapter를 연결합니다. |
| manipulation affordance extension | graspable, openable, movable 등 manipulation affordance를 별도 후속 범위로 검토합니다. |

### P2

| 항목 | 목적 |
| --- | --- |
| learned extractor | rule-based tokenizer를 learned or foundation-model-assisted extractor와 비교합니다. |
| VLA/LLM planner integration | structured token JSON 또는 text rendering을 VLA/LLM planner에 전달하는 실험을 설계합니다. |
| real robot bridge | 실제 로봇 sensor stream과 RAST interface 연결 가능성을 검토합니다. |
