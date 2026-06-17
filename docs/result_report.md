# RAST MVP-0 Result Report

이 문서는 WindowsMetadataSim 기반 RAST MVP-0 evaluation suite 결과를 자동 요약한 보고서입니다.

## Experiment Context

- Results source: `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\aggregate_results.csv`
- Summary source: `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\aggregate_summary.csv`
- Total runs: 500
- Successful runs: 500
- Failed runs: 0
- Current report purpose: evaluation infrastructure 검증과 관찰 결과 정리입니다.

## Suite Execution Metadata

- suite_metadata: `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\suite_metadata.json`
- suite_run_id: `windows_eval_suite_20260612_224531`
- config_path: `configs\windows_eval_suite_extended.yaml`
- config_name: `windows_eval_suite_extended`
- planned_runs_total: 8294400
- executed_runs: 500
- failed_runs: 0
- sampling_mode: `stratified`
- sample_size: `500`
- sample_seed: `42`
- limit: `None`
- allow_large_run: `False`
- replay_export_enabled: `True`
- replay_index_path: `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\replay_index.json`
- This report summarizes a sampled subset of the extended grid, not the full extended grid.

## Simulator and Scope

- 이 결과는 WindowsMetadataSim 기반 deterministic metadata simulator 결과입니다.
- 실제 AI2-THOR / Webots / CoppeliaSim / real robot 결과가 아닙니다.
- 실제 RGB-D perception latency나 perception error를 반영하지 않습니다.
- collision, near-miss, goal reaching은 simple geometry rule 기반입니다.
- 현재 seed는 metadata에 기록되지만 stochastic variation은 아직 제한적입니다.
- 현재 결과는 연구 주장이라기보다 evaluation infrastructure 검증입니다.

## Scenarios

- `avoid_required_blocking_path`
- `blocking_relation_without_high_risk`
- `clear_path`
- `event_changes_risk_but_graph_static`
- `far_obstacle`
- `inspect_required_uncertain_path`
- `low_sensor_agreement`
- `narrow_passage`
- `near_obstacle`
- `noisy_position_boundary`
- `object_appears`
- `object_disappears`
- `object_moves`
- `partially_occluded_obstacle`
- `passable_clear_gap`
- `planner_disagreement`
- `relation_near_but_low_risk`
- `risk_increases`
- `risk_without_graph_blocking`
- `target_reachable`
- `target_reachable_affordance`
- `uncertainty_near_path`
- `uncertainty_without_high_risk`
- `unknown_near_path`
- `unknown_uncertain_object`

## Baselines

- Object List: object id, category, position, visible, distance, confidence 중심의 baseline입니다.
- Flat Feature Table: RAST와 유사한 scalar feature를 받지만 token contract field를 제거한 baseline입니다.
- Scene Graph: 같은 ObservationSnapshot에서 agent/object/goal node와 relation edge를 구성하는 graph baseline입니다.
- RAST: EntityToken, RiskToken, RelationToken, EventToken, UncertaintyToken, EvidenceToken, AffordanceToken logging을 포함한 planner-facing token contract 경로입니다.
- Event-aware RAST: 기존 RAST planner와 분리된 실험용 planner이며 EventToken을 decision reason에 반영합니다.
- Uncertainty-aware RAST: 기존 RAST planner와 분리된 실험용 planner이며 UncertaintyToken을 decision reason에 반영합니다.
- Affordance-aware RAST: 기존 RAST planner를 대체하지 않는 별도 experimental planner이며, navigation AffordanceToken을 decision reason으로 사용할 수 있습니다.
- 기존 RAST planner는 EventToken으로 action을 바꾸지 않으며, Event-aware RAST planner에서만 실험적으로 EventToken reason을 사용합니다.
- 기존 RAST planner는 UncertaintyToken으로 action을 바꾸지 않으며, Uncertainty-aware RAST planner에서만 실험적으로 uncertainty reason을 사용합니다.
- 기존 RAST planner는 AffordanceToken으로 action을 바꾸지 않으며, Affordance-aware RAST planner에서만 navigation affordance reason을 사용합니다.
- Affordance-aware RAST의 action 변화는 성능 개선이나 real robot feasibility를 의미하지 않습니다.

## Metrics

- success / goal_reached
- completed_steps
- collision_count / near_miss_count
- RAST vs Object List disagreement
- RAST vs Flat Feature disagreement
- Object List vs Flat Feature disagreement
- RAST vs Event-aware RAST disagreement
- RAST vs Uncertainty-aware RAST disagreement
- RAST vs Affordance-aware RAST disagreement
- RAST vs Scene Graph disagreement / same-action-different-reason
- token_count_avg / object_count_avg / flat_feature_row_count_avg
- event_token_count_total / event_token_count_avg / event_type_counts
- uncertainty_token_count_total / uncertainty_token_count_avg / uncertainty_type_counts / high_uncertainty_count
- evidence_token_count_total / evidence_token_count_avg / evidence_type_counts / decision_evidence_coverage
- affordance_token_count_total / affordance_token_count_avg / affordance_type_counts
- rast_vs_affordance_aware_disagreement_count / affordance_triggered_action_count
- affordance_aware_decision_trace_coverage
- update_mode / changed_object_count_avg / affected_token_count_avg
- full_recompute_latency_avg_ms / incremental_update_latency_avg_ms / incremental_update_benefit_avg
- rast_reason_code_counts / object_list_reason_code_counts / flat_feature_reason_code_counts
- event_aware_rast_reason_code_counts / event_triggered_action_count
- uncertainty_aware_rast_reason_code_counts / uncertainty_triggered_action_count
- affordance_aware_rast_reason_code_counts / affordance_triggered_action_count
- event_policy_variant / event_policy_variant_action_counts / event_policy_variant_reason_code_counts
- risk_threshold / relation thresholds / near_miss_threshold
- position_noise_std / distance_noise_std / visibility_flip_prob
- rast_trigger_token_count_total / decision_trace_coverage
- scene_graph_trigger_edge_count / rast_trigger_risk_token_count / event_aware_trigger_event_count
- event_aware_decision_trace_coverage
- uncertainty_aware_decision_trace_coverage
- latency_avg_ms / latency_p50_ms / latency_p95_ms
- token_generation_latency_avg_ms / planning_latency_avg_ms / total_latency_avg_ms

## Before/After Context

- 현재 report는 EventToken, UncertaintyToken, EvidenceToken, AffordanceToken이 step log, episode summary, aggregate result에 포함된 이후의 결과입니다.
- Event-aware, Uncertainty-aware, Affordance-aware planner는 각각 별도 experimental planner이며 기존 RAST planner를 대체하지 않습니다.
- action 변화는 성능 개선 주장이 아니라 token-to-decision 연결 가능성과 decision boundary 차이를 관찰하기 위한 것입니다.
- TokenMemory는 semantic diff와 incremental latency protocol에 사용됩니다. incremental update optimization is experimental.
- UncertaintyToken은 WindowsMetadataSim의 synthetic metadata uncertainty를 기록하며 실제 perception uncertainty calibration이 아닙니다.
- EvidenceToken은 metadata pointer 기반 traceability이며 raw image crop이나 real sensor evidence가 아닙니다.
- AffordanceToken은 navigation affordance only이며 real robot action feasibility 검증을 의미하지 않습니다.

## EventToken Summary

- EventToken included in this report: yes
- Total EventToken count across successful runs: 2108
- Average EventToken count per episode: 4.216
- Average EventToken count per step: 0.440
- EventToken affects only the separate Event-aware RAST experimental planner; the existing RAST planner remains unchanged.
- EventToken은 현재 semantic event diff 기반으로 생성되며 실제 perception event detection 결과가 아닙니다.

| Event Type | Occurred | Count |
|---|---:|---:|
| `object_appeared` | yes | 190 |
| `object_moved` | yes | 1106 |
| `risk_changed` | yes | 635 |
| `object_disappeared` | yes | 177 |

| Scenario | Runs | Avg Event Tokens / Episode | Avg Event Tokens / Step | Event Type Counts |
|---|---:|---:|---:|---|
| `avoid_required_blocking_path` | 20 | 2.000 | 0.200 | `{"object_moved":30,"risk_changed":10}` |
| `blocking_relation_without_high_risk` | 20 | 5.950 | 0.595 | `{"object_appeared":22,"object_disappeared":11,"object_moved":45,"risk_changed":41}` |
| `clear_path` | 20 | 5.650 | 0.565 | `{"object_appeared":11,"object_disappeared":11,"object_moved":91}` |
| `event_changes_risk_but_graph_static` | 20 | 9.650 | 0.965 | `{"object_appeared":22,"object_disappeared":22,"object_moved":96,"risk_changed":53}` |
| `far_obstacle` | 20 | 5.350 | 0.535 | `{"object_appeared":11,"object_disappeared":11,"object_moved":35,"risk_changed":50}` |
| `inspect_required_uncertain_path` | 20 | 2.400 | 0.240 | `{"object_moved":40,"risk_changed":8}` |
| `low_sensor_agreement` | 20 | 3.400 | 0.340 | `{"object_moved":45,"risk_changed":23}` |
| `narrow_passage` | 20 | 8.750 | 0.875 | `{"object_appeared":9,"object_disappeared":9,"object_moved":89,"risk_changed":68}` |
| `near_obstacle` | 20 | 1.350 | 0.135 | `{"object_moved":18,"risk_changed":9}` |
| `noisy_position_boundary` | 20 | 1.950 | 0.195 | `{"object_appeared":9,"object_moved":10,"risk_changed":20}` |
| `object_appears` | 20 | 6.700 | 0.670 | `{"object_appeared":38,"object_disappeared":18,"object_moved":40,"risk_changed":38}` |
| `object_disappears` | 20 | 4.500 | 0.450 | `{"object_appeared":10,"object_disappeared":30,"object_moved":36,"risk_changed":14}` |
| `object_moves` | 20 | 7.600 | 0.760 | `{"object_moved":100,"risk_changed":52}` |
| `partially_occluded_obstacle` | 20 | 2.800 | 0.280 | `{"object_disappeared":10,"object_moved":20,"risk_changed":26}` |
| `passable_clear_gap` | 20 | 4.700 | 0.470 | `{"object_appeared":11,"object_moved":44,"risk_changed":39}` |
| `planner_disagreement` | 20 | 2.150 | 0.215 | `{"object_moved":28,"risk_changed":15}` |
| `relation_near_but_low_risk` | 20 | 4.400 | 0.440 | `{"object_appeared":9,"object_disappeared":9,"object_moved":60,"risk_changed":10}` |
| `risk_increases` | 20 | 7.200 | 0.720 | `{"object_appeared":9,"object_disappeared":9,"object_moved":101,"risk_changed":25}` |
| `risk_without_graph_blocking` | 20 | 2.350 | 0.235 | `{"object_disappeared":8,"object_moved":27,"risk_changed":12}` |
| `target_reachable` | 20 | 0.900 | 0.300 | `{"object_appeared":10,"object_moved":8}` |
| `target_reachable_affordance` | 20 | 1.100 | 0.367 | `{"object_moved":22}` |
| `uncertainty_near_path` | 20 | 3.800 | 0.380 | `{"object_appeared":9,"object_disappeared":9,"object_moved":27,"risk_changed":31}` |
| `uncertainty_without_high_risk` | 20 | 3.350 | 0.335 | `{"object_disappeared":10,"object_moved":24,"risk_changed":33}` |
| `unknown_near_path` | 20 | 4.050 | 0.405 | `{"object_appeared":10,"object_disappeared":10,"object_moved":40,"risk_changed":21}` |
| `unknown_uncertain_object` | 20 | 3.350 | 0.335 | `{"object_moved":30,"risk_changed":37}` |

## RelationToken Summary

- RelationToken included in this report: yes
- Total RelationToken count across successful runs: 4445
- Average RelationToken count per episode: 8.890
- Average RelationToken count per step: 0.945
- Relation type distribution: `{"near_agent":2874,"near_path":1451,"target_reachable":120}`
- RelationToken은 MVP에서 navigation relation만 다루며 learned relation extraction 결과가 아닙니다.
- Relation은 simple geometry rule 기반이므로 실제 perception relation 품질을 검증하지 않습니다.

| Scenario | Runs | Avg Relation Tokens / Episode | Avg Relation Tokens / Step | Relation Type Counts |
|---|---:|---:|---:|---|
| `avoid_required_blocking_path` | 20 | 11.400 | 1.140 | `{"near_agent":173,"near_path":55}` |
| `blocking_relation_without_high_risk` | 20 | 7.850 | 0.785 | `{"near_agent":110,"near_path":47}` |
| `clear_path` | 20 | 0.000 | 0.000 | `{}` |
| `event_changes_risk_but_graph_static` | 20 | 11.300 | 1.130 | `{"near_agent":153,"near_path":73}` |
| `far_obstacle` | 20 | 6.350 | 0.635 | `{"near_agent":55,"near_path":72}` |
| `inspect_required_uncertain_path` | 20 | 10.900 | 1.090 | `{"near_agent":131,"near_path":87}` |
| `low_sensor_agreement` | 20 | 9.700 | 0.970 | `{"near_agent":122,"near_path":72}` |
| `narrow_passage` | 20 | 21.600 | 2.160 | `{"near_agent":299,"near_path":133}` |
| `near_obstacle` | 20 | 11.950 | 1.195 | `{"near_agent":185,"near_path":54}` |
| `noisy_position_boundary` | 20 | 10.150 | 1.015 | `{"near_agent":97,"near_path":106}` |
| `object_appears` | 20 | 9.050 | 0.905 | `{"near_agent":135,"near_path":46}` |
| `object_disappears` | 20 | 1.400 | 0.140 | `{"near_agent":8,"near_path":20}` |
| `object_moves` | 20 | 8.950 | 0.895 | `{"near_agent":113,"near_path":66}` |
| `partially_occluded_obstacle` | 20 | 10.050 | 1.005 | `{"near_agent":116,"near_path":85}` |
| `passable_clear_gap` | 20 | 16.700 | 1.670 | `{"near_agent":319,"near_path":15}` |
| `planner_disagreement` | 20 | 10.300 | 1.030 | `{"near_agent":122,"near_path":84}` |
| `relation_near_but_low_risk` | 20 | 0.350 | 0.035 | `{"near_path":7}` |
| `risk_increases` | 20 | 8.550 | 0.855 | `{"near_agent":104,"near_path":67}` |
| `risk_without_graph_blocking` | 20 | 13.750 | 1.375 | `{"near_agent":192,"near_path":83}` |
| `target_reachable` | 20 | 3.000 | 1.000 | `{"target_reachable":60}` |
| `target_reachable_affordance` | 20 | 3.000 | 1.000 | `{"target_reachable":60}` |
| `uncertainty_near_path` | 20 | 10.750 | 1.075 | `{"near_agent":136,"near_path":79}` |
| `uncertainty_without_high_risk` | 20 | 8.350 | 0.835 | `{"near_agent":58,"near_path":109}` |
| `unknown_near_path` | 20 | 12.550 | 1.255 | `{"near_agent":172,"near_path":79}` |
| `unknown_uncertain_object` | 20 | 4.300 | 0.430 | `{"near_agent":74,"near_path":12}` |

## UncertaintyToken Summary

- UncertaintyToken included in this report: yes
- Total UncertaintyToken count across successful runs: 3496
- Average UncertaintyToken count per episode: 6.992
- Average UncertaintyToken count per step: 0.699
- Total high uncertainty count: 2524
- Average high uncertainty count per step: 0.505
- Uncertainty type distribution: `{"classification_uncertainty":781,"low_sensor_agreement":391,"partial_occlusion":581,"position_uncertainty":381,"unknown_object":1362}`
- UncertaintyToken은 WindowsMetadataSim의 synthetic metadata uncertainty 기반이며 실제 perception uncertainty calibration이 아닙니다.
- sensor disagreement는 simulated field이며 실제 multi-sensor fusion 결과가 아닙니다.

| Uncertainty Type | Occurred | Count |
|---|---:|---:|
| `classification_uncertainty` | yes | 781 |
| `position_uncertainty` | yes | 381 |
| `partial_occlusion` | yes | 581 |
| `low_sensor_agreement` | yes | 391 |
| `unknown_object` | yes | 1362 |

| Scenario | Runs | Avg Uncertainty Tokens / Episode | Avg High Uncertainty / Episode | Uncertainty Type Counts |
|---|---:|---:|---:|---|
| `avoid_required_blocking_path` | 20 | 0.000 | 0.000 | `{}` |
| `blocking_relation_without_high_risk` | 20 | 0.000 | 0.000 | `{}` |
| `clear_path` | 20 | 0.000 | 0.000 | `{}` |
| `event_changes_risk_but_graph_static` | 20 | 9.450 | 9.450 | `{"unknown_object":189}` |
| `far_obstacle` | 20 | 0.000 | 0.000 | `{}` |
| `inspect_required_uncertain_path` | 20 | 20.000 | 10.000 | `{"classification_uncertainty":200,"partial_occlusion":200}` |
| `low_sensor_agreement` | 20 | 10.000 | 0.000 | `{"low_sensor_agreement":200}` |
| `narrow_passage` | 20 | 0.000 | 0.000 | `{}` |
| `near_obstacle` | 20 | 0.000 | 0.000 | `{}` |
| `noisy_position_boundary` | 20 | 9.550 | 9.550 | `{"position_uncertainty":191}` |
| `object_appears` | 20 | 0.000 | 0.000 | `{}` |
| `object_disappears` | 20 | 0.000 | 0.000 | `{}` |
| `object_moves` | 20 | 0.000 | 0.000 | `{}` |
| `partially_occluded_obstacle` | 20 | 9.500 | 9.500 | `{"partial_occlusion":190}` |
| `passable_clear_gap` | 20 | 0.000 | 0.000 | `{}` |
| `planner_disagreement` | 20 | 10.000 | 10.000 | `{"unknown_object":200}` |
| `relation_near_but_low_risk` | 20 | 0.000 | 0.000 | `{}` |
| `risk_increases` | 20 | 10.000 | 10.000 | `{"unknown_object":200}` |
| `risk_without_graph_blocking` | 20 | 9.600 | 9.600 | `{"unknown_object":192}` |
| `target_reachable` | 20 | 0.000 | 0.000 | `{}` |
| `target_reachable_affordance` | 20 | 0.000 | 0.000 | `{}` |
| `uncertainty_near_path` | 20 | 38.200 | 19.100 | `{"classification_uncertainty":191,"low_sensor_agreement":191,"partial_occlusion":191,"unknown_object":191}` |
| `uncertainty_without_high_risk` | 20 | 19.000 | 9.500 | `{"classification_uncertainty":190,"position_uncertainty":190}` |
| `unknown_near_path` | 20 | 9.500 | 9.500 | `{"unknown_object":190}` |
| `unknown_uncertain_object` | 20 | 20.000 | 20.000 | `{"classification_uncertainty":200,"unknown_object":200}` |

## EvidenceToken Summary

- EvidenceToken included in this report: yes
- Total EvidenceToken count: 42092
- Average EvidenceToken count per episode: 8.829
- Evidence type distribution: `{"event_diff":2108,"planner_decision":33040,"risk_feature":3448,"uncertainty_feature":3496}`
- Risk evidence count: 3448
- Uncertainty evidence count: 3496
- Event evidence count: 2108
- Decision evidence count: 33040
- Decision evidence coverage: 1.000
- EvidenceToken currently stores metadata pointers, bbox-like fields, token ids, and decision trace references.
- It does not store raw image crops, RGB frames, or real sensor evidence in WindowsMetadataSim.
- EvidenceToken presence supports traceability infrastructure only; it is not evidence of performance improvement.

| Scenario | Runs | Avg EvidenceToken | Evidence Types | Decision Evidence Coverage |
|---|---:|---:|---|---:|
| `avoid_required_blocking_path` | 20 | 8.130 | `{"event_diff":40,"planner_decision":1400,"risk_feature":186}` | 1.000 |
| `blocking_relation_without_high_risk` | 20 | 8.205 | `{"event_diff":119,"planner_decision":1400,"risk_feature":122}` | 1.000 |
| `clear_path` | 20 | 7.565 | `{"event_diff":113,"planner_decision":1400}` | 1.000 |
| `event_changes_risk_but_graph_static` | 20 | 9.720 | `{"event_diff":193,"planner_decision":1400,"risk_feature":162,"uncertainty_feature":189}` | 1.000 |
| `far_obstacle` | 20 | 7.880 | `{"event_diff":107,"planner_decision":1400,"risk_feature":69}` | 1.000 |
| `inspect_required_uncertain_path` | 20 | 10.050 | `{"event_diff":48,"planner_decision":1400,"risk_feature":162,"uncertainty_feature":400}` | 1.000 |
| `low_sensor_agreement` | 20 | 9.090 | `{"event_diff":68,"planner_decision":1400,"risk_feature":150,"uncertainty_feature":200}` | 1.000 |
| `narrow_passage` | 20 | 9.535 | `{"event_diff":175,"planner_decision":1400,"risk_feature":332}` | 1.000 |
| `near_obstacle` | 20 | 8.080 | `{"event_diff":27,"planner_decision":1400,"risk_feature":189}` | 1.000 |
| `noisy_position_boundary` | 20 | 8.845 | `{"event_diff":39,"planner_decision":1400,"risk_feature":139,"uncertainty_feature":191}` | 1.000 |
| `object_appears` | 20 | 8.420 | `{"event_diff":134,"planner_decision":1400,"risk_feature":150}` | 1.000 |
| `object_disappears` | 20 | 7.520 | `{"event_diff":90,"planner_decision":1400,"risk_feature":14}` | 1.000 |
| `object_moves` | 20 | 8.540 | `{"event_diff":152,"planner_decision":1400,"risk_feature":156}` | 1.000 |
| `partially_occluded_obstacle` | 20 | 9.050 | `{"event_diff":56,"planner_decision":1400,"risk_feature":164,"uncertainty_feature":190}` | 1.000 |
| `passable_clear_gap` | 20 | 9.195 | `{"event_diff":94,"planner_decision":1400,"risk_feature":345}` | 1.000 |
| `planner_disagreement` | 20 | 9.030 | `{"event_diff":43,"planner_decision":1400,"risk_feature":163,"uncertainty_feature":200}` | 1.000 |
| `relation_near_but_low_risk` | 20 | 7.670 | `{"event_diff":88,"planner_decision":1400,"risk_feature":46}` | 1.000 |
| `risk_increases` | 20 | 9.405 | `{"event_diff":144,"planner_decision":1400,"risk_feature":137,"uncertainty_feature":200}` | 1.000 |
| `risk_without_graph_blocking` | 20 | 9.155 | `{"event_diff":47,"planner_decision":1400,"risk_feature":192,"uncertainty_feature":192}` | 1.000 |
| `target_reachable` | 20 | 7.300 | `{"event_diff":18,"planner_decision":420}` | 1.000 |
| `target_reachable_affordance` | 20 | 7.367 | `{"event_diff":22,"planner_decision":420}` | 1.000 |
| `uncertainty_near_path` | 20 | 11.985 | `{"event_diff":76,"planner_decision":1400,"risk_feature":157,"uncertainty_feature":764}` | 1.000 |
| `uncertainty_without_high_risk` | 20 | 9.785 | `{"event_diff":67,"planner_decision":1400,"risk_feature":110,"uncertainty_feature":380}` | 1.000 |
| `unknown_near_path` | 20 | 9.260 | `{"event_diff":81,"planner_decision":1400,"risk_feature":181,"uncertainty_feature":190}` | 1.000 |
| `unknown_uncertain_object` | 20 | 9.945 | `{"event_diff":67,"planner_decision":1400,"risk_feature":122,"uncertainty_feature":400}` | 1.000 |

## AffordanceToken Summary

- AffordanceToken included in this report: yes
- Total AffordanceToken count: 4520
- Average AffordanceToken count per episode: 9.040
- Average AffordanceToken count per step: 1.016
- Affordance type distribution: `{"avoid_required":18,"inspect_required":1379,"narrow_passage":59,"passable":2944,"target_reachable":120}`
- AffordanceToken is limited to navigation affordance in MVP-0.
- Manipulation affordance such as graspable, movable, openable, container, and fragile is not included.
- These affordances are simple geometry/rule-based metadata affordances, not verified real robot action feasibility.

| Affordance Type | Occurred | Count |
|---|---:|---:|
| `passable` | yes | 2944 |
| `blocking` | no | 0 |
| `narrow_passage` | yes | 59 |
| `target_reachable` | yes | 120 |
| `inspect_required` | yes | 1379 |
| `avoid_required` | yes | 18 |

| Scenario | Runs | Avg Affordance Tokens / Episode | Affordance Type Counts |
|---|---:|---:|---|
| `avoid_required_blocking_path` | 20 | 7.250 | `{"passable":145}` |
| `blocking_relation_without_high_risk` | 20 | 7.650 | `{"passable":153}` |
| `clear_path` | 20 | 10.000 | `{"passable":200}` |
| `event_changes_risk_but_graph_static` | 20 | 10.000 | `{"inspect_required":126,"passable":74}` |
| `far_obstacle` | 20 | 6.400 | `{"passable":128}` |
| `inspect_required_uncertain_path` | 20 | 10.000 | `{"inspect_required":119,"passable":81}` |
| `low_sensor_agreement` | 20 | 6.400 | `{"avoid_required":1,"passable":127}` |
| `narrow_passage` | 20 | 9.950 | `{"avoid_required":15,"narrow_passage":59,"passable":125}` |
| `near_obstacle` | 20 | 7.300 | `{"passable":146}` |
| `noisy_position_boundary` | 20 | 10.000 | `{"inspect_required":136,"passable":64}` |
| `object_appears` | 20 | 7.700 | `{"passable":154}` |
| `object_disappears` | 20 | 9.000 | `{"passable":180}` |
| `object_moves` | 20 | 6.750 | `{"avoid_required":2,"passable":133}` |
| `partially_occluded_obstacle` | 20 | 10.000 | `{"inspect_required":117,"passable":83}` |
| `passable_clear_gap` | 20 | 9.250 | `{"passable":185}` |
| `planner_disagreement` | 20 | 10.000 | `{"inspect_required":115,"passable":85}` |
| `relation_near_but_low_risk` | 20 | 9.650 | `{"passable":193}` |
| `risk_increases` | 20 | 10.000 | `{"inspect_required":113,"passable":87}` |
| `risk_without_graph_blocking` | 20 | 10.000 | `{"inspect_required":129,"passable":71}` |
| `target_reachable` | 20 | 6.000 | `{"passable":60,"target_reachable":60}` |
| `target_reachable_affordance` | 20 | 6.000 | `{"passable":60,"target_reachable":60}` |
| `uncertainty_near_path` | 20 | 15.800 | `{"inspect_required":232,"passable":84}` |
| `uncertainty_without_high_risk` | 20 | 10.000 | `{"inspect_required":139,"passable":61}` |
| `unknown_near_path` | 20 | 10.000 | `{"inspect_required":117,"passable":83}` |
| `unknown_uncertain_object` | 20 | 10.900 | `{"inspect_required":36,"passable":182}` |

## Aggregate Results

- Total runs: 500
- Failed runs: 0
- Overall success rate: 1.000
- Overall average near-miss count: 1.844
- Overall latency avg / p50 / p95 ms: 0.889 / 0.883 / 1.067

## Scenario-level Observations

| Scenario | Runs | Success Rate | Avg Near-miss | Avg RAST vs Object | Avg RAST vs Flat | Avg Object vs Flat | Avg RAST vs Event-aware |
|---|---:|---:|---:|---:|---:|---:|---:|
| `avoid_required_blocking_path` | 20 | 1.000 | 4.250 | 0.900 | 0.000 | 0.900 | 0.050 |
| `blocking_relation_without_high_risk` | 20 | 1.000 | 1.300 | 4.100 | 0.000 | 4.100 | 0.100 |
| `clear_path` | 20 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `event_changes_risk_but_graph_static` | 20 | 1.000 | 3.250 | 0.900 | 0.000 | 0.900 | 0.600 |
| `far_obstacle` | 20 | 1.000 | 0.450 | 2.650 | 0.000 | 2.650 | 0.250 |
| `inspect_required_uncertain_path` | 20 | 1.000 | 0.400 | 5.700 | 0.000 | 5.700 | 0.150 |
| `low_sensor_agreement` | 20 | 1.000 | 1.800 | 5.500 | 0.050 | 5.450 | 0.350 |
| `narrow_passage` | 20 | 1.000 | 1.900 | 7.750 | 0.400 | 7.350 | 0.350 |
| `near_obstacle` | 20 | 1.000 | 3.300 | 0.300 | 0.000 | 0.300 | 0.000 |
| `noisy_position_boundary` | 20 | 1.000 | 1.400 | 4.150 | 0.000 | 4.150 | 0.250 |
| `object_appears` | 20 | 1.000 | 4.300 | 0.700 | 0.000 | 0.700 | 0.000 |
| `object_disappears` | 20 | 1.000 | 0.000 | 0.300 | 0.000 | 0.300 | 0.000 |
| `object_moves` | 20 | 1.000 | 3.250 | 5.200 | 0.100 | 5.100 | 0.850 |
| `partially_occluded_obstacle` | 20 | 1.000 | 1.600 | 5.450 | 0.000 | 5.450 | 0.250 |
| `passable_clear_gap` | 20 | 1.000 | 0.550 | 8.550 | 0.000 | 8.550 | 0.100 |
| `planner_disagreement` | 20 | 1.000 | 2.500 | 4.750 | 0.000 | 4.750 | 0.200 |
| `relation_near_but_low_risk` | 20 | 1.000 | 0.000 | 2.300 | 0.000 | 2.300 | 0.000 |
| `risk_increases` | 20 | 1.000 | 2.400 | 1.450 | 0.000 | 1.450 | 0.600 |
| `risk_without_graph_blocking` | 20 | 1.000 | 5.700 | 0.000 | 0.000 | 0.000 | 0.050 |
| `target_reachable` | 20 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `target_reachable_affordance` | 20 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `uncertainty_near_path` | 20 | 1.000 | 2.000 | 4.800 | 0.000 | 4.800 | 0.150 |
| `uncertainty_without_high_risk` | 20 | 1.000 | 1.100 | 3.700 | 0.000 | 3.700 | 0.350 |
| `unknown_near_path` | 20 | 1.000 | 3.400 | 0.350 | 0.000 | 0.350 | 0.000 |
| `unknown_uncertain_object` | 20 | 1.000 | 1.250 | 4.150 | 0.000 | 4.150 | 0.300 |

## Baseline Disagreement Analysis

- Average RAST vs Object List disagreement: 2.946
- Average RAST vs Flat Feature disagreement: 0.022
- Average Object List vs Flat Feature disagreement: 2.924
- Average RAST vs Event-aware RAST disagreement: 0.198
- Flat Feature가 RAST와 자주 일치한다면, 현재 toy setup에서는 scalar risk feature가 두 planner의 action을 크게 좌우한다는 뜻으로 해석해야 합니다.
- Object List와 RAST가 달라지는 경우는 distance-only object view와 risk-aware scalar/token view가 서로 다른 action boundary를 만들 수 있음을 보여줍니다.
- 이 차이는 아직 RAST의 우수성을 뜻하지 않으며, 같은 information bound에서 구조화 효과를 더 분리해 검증해야 합니다.

## Decision Trace Summary

- PlannerDecision trace is included in this report when planner reason_code fields are present in aggregate results.
- Average decision_trace_coverage: 1.000
- Total RAST trigger token references: 3119
- Average RAST trigger token references per episode: 6.238
- RAST, Object List, and Flat Feature planners can choose the same action for different reasons.
- These traces are rule-based planner explanations, not learned model interpretability results.
- EventToken is used only by the separate Event-aware RAST experimental planner; the existing RAST planner remains unchanged.

| Planner | Reason Code Counts |
|---|---|
| RAST | `{"high_risk_token":11,"no_risk_move_ahead":1601,"risk_token_present":3108}` |
| Object List | `{"near_object_distance":1769,"no_near_object_move_ahead":2951}` |
| Flat Feature | `{"no_risk_scalar_move_ahead":1601,"within_risk_threshold":3119}` |
| Event-aware RAST | `{"event_object_appeared_near_path":86,"event_object_disappeared_clear_path":142,"event_object_moved":427,"event_risk_increased":273,"fallback_no_risk_move_ahead":1459,"fallback_risk_token_present":2333}` |

| Scenario | Runs | Decision Trace Coverage | RAST Reason Codes |
|---|---:|---:|---|
| `avoid_required_blocking_path` | 20 | 1.000 | `{"no_risk_move_ahead":14,"risk_token_present":186}` |
| `blocking_relation_without_high_risk` | 20 | 1.000 | `{"no_risk_move_ahead":78,"risk_token_present":122}` |
| `clear_path` | 20 | 1.000 | `{"no_risk_move_ahead":200}` |
| `event_changes_risk_but_graph_static` | 20 | 1.000 | `{"no_risk_move_ahead":38,"risk_token_present":162}` |
| `far_obstacle` | 20 | 1.000 | `{"no_risk_move_ahead":131,"risk_token_present":69}` |
| `inspect_required_uncertain_path` | 20 | 1.000 | `{"no_risk_move_ahead":38,"risk_token_present":162}` |
| `low_sensor_agreement` | 20 | 1.000 | `{"high_risk_token":1,"no_risk_move_ahead":50,"risk_token_present":149}` |
| `narrow_passage` | 20 | 1.000 | `{"high_risk_token":8,"no_risk_move_ahead":25,"risk_token_present":167}` |
| `near_obstacle` | 20 | 1.000 | `{"no_risk_move_ahead":11,"risk_token_present":189}` |
| `noisy_position_boundary` | 20 | 1.000 | `{"no_risk_move_ahead":61,"risk_token_present":139}` |
| `object_appears` | 20 | 1.000 | `{"no_risk_move_ahead":50,"risk_token_present":150}` |
| `object_disappears` | 20 | 1.000 | `{"no_risk_move_ahead":186,"risk_token_present":14}` |
| `object_moves` | 20 | 1.000 | `{"high_risk_token":2,"no_risk_move_ahead":44,"risk_token_present":154}` |
| `partially_occluded_obstacle` | 20 | 1.000 | `{"no_risk_move_ahead":36,"risk_token_present":164}` |
| `passable_clear_gap` | 20 | 1.000 | `{"no_risk_move_ahead":27,"risk_token_present":173}` |
| `planner_disagreement` | 20 | 1.000 | `{"no_risk_move_ahead":37,"risk_token_present":163}` |
| `relation_near_but_low_risk` | 20 | 1.000 | `{"no_risk_move_ahead":154,"risk_token_present":46}` |
| `risk_increases` | 20 | 1.000 | `{"no_risk_move_ahead":63,"risk_token_present":137}` |
| `risk_without_graph_blocking` | 20 | 1.000 | `{"no_risk_move_ahead":8,"risk_token_present":192}` |
| `target_reachable` | 20 | 1.000 | `{"no_risk_move_ahead":60}` |
| `target_reachable_affordance` | 20 | 1.000 | `{"no_risk_move_ahead":60}` |
| `uncertainty_near_path` | 20 | 1.000 | `{"no_risk_move_ahead":43,"risk_token_present":157}` |
| `uncertainty_without_high_risk` | 20 | 1.000 | `{"no_risk_move_ahead":90,"risk_token_present":110}` |
| `unknown_near_path` | 20 | 1.000 | `{"no_risk_move_ahead":19,"risk_token_present":181}` |
| `unknown_uncertain_object` | 20 | 1.000 | `{"no_risk_move_ahead":78,"risk_token_present":122}` |

## Scene Graph Baseline Summary

- Scene Graph baseline은 MVP용 simplified graph입니다.
- Graph node는 agent/object/optional goal이며 edge는 near_agent, near_path, blocking_path, target_reachable relation입니다.
- Scene Graph planner는 RiskToken의 severity, risk_type, recommended_policy 같은 RAST-only contract field를 사용하지 않습니다.
- Average Scene Graph node count: 2.436
- Average Scene Graph edge count: 0.945
- Average RAST vs Scene Graph disagreement: 1.888
- Average Scene Graph vs Flat Feature disagreement: 1.866
- Average Scene Graph decision trace coverage: 1.000
- Scene Graph reason code distribution: `{"graph_near_object":2574,"graph_no_blocking_move_ahead":2026,"graph_target_reachable":120}`
- RAST와 Scene Graph의 차이는 representation 차이를 관찰하기 위한 것이며 RAST 우수성을 의미하지 않습니다.

| Scenario | Runs | Avg Nodes | Avg Edges | Avg RAST vs Scene Graph | Scene Graph Reason Codes |
|---|---:|---:|---:|---:|---|
| `avoid_required_blocking_path` | 20 | 2.000 | 1.140 | 0.850 | `{"graph_near_object":173,"graph_no_blocking_move_ahead":27}` |
| `blocking_relation_without_high_risk` | 20 | 1.890 | 0.785 | 2.200 | `{"graph_near_object":110,"graph_no_blocking_move_ahead":90}` |
| `clear_path` | 20 | 2.945 | 0.000 | 0.000 | `{"graph_no_blocking_move_ahead":200}` |
| `event_changes_risk_but_graph_static` | 20 | 2.890 | 1.130 | 0.550 | `{"graph_near_object":153,"graph_no_blocking_move_ahead":47}` |
| `far_obstacle` | 20 | 1.945 | 0.635 | 2.000 | `{"graph_near_object":55,"graph_no_blocking_move_ahead":145}` |
| `inspect_required_uncertain_path` | 20 | 2.000 | 1.090 | 3.750 | `{"graph_near_object":131,"graph_no_blocking_move_ahead":69}` |
| `low_sensor_agreement` | 20 | 2.000 | 0.970 | 3.350 | `{"graph_near_object":122,"graph_no_blocking_move_ahead":78}` |
| `narrow_passage` | 20 | 3.955 | 2.160 | 2.750 | `{"graph_near_object":158,"graph_no_blocking_move_ahead":42}` |
| `near_obstacle` | 20 | 2.000 | 1.195 | 0.500 | `{"graph_near_object":185,"graph_no_blocking_move_ahead":15}` |
| `noisy_position_boundary` | 20 | 1.955 | 1.015 | 2.300 | `{"graph_near_object":97,"graph_no_blocking_move_ahead":103}` |
| `object_appears` | 20 | 2.810 | 0.905 | 0.950 | `{"graph_near_object":135,"graph_no_blocking_move_ahead":65}` |
| `object_disappears` | 20 | 2.050 | 0.140 | 0.600 | `{"graph_near_object":8,"graph_no_blocking_move_ahead":192}` |
| `object_moves` | 20 | 3.000 | 0.895 | 2.550 | `{"graph_near_object":113,"graph_no_blocking_move_ahead":87}` |
| `partially_occluded_obstacle` | 20 | 1.950 | 1.005 | 3.700 | `{"graph_near_object":116,"graph_no_blocking_move_ahead":84}` |
| `passable_clear_gap` | 20 | 3.945 | 1.670 | 1.550 | `{"graph_near_object":160,"graph_no_blocking_move_ahead":40}` |
| `planner_disagreement` | 20 | 2.000 | 1.030 | 4.450 | `{"graph_near_object":122,"graph_no_blocking_move_ahead":78}` |
| `relation_near_but_low_risk` | 20 | 2.955 | 0.035 | 2.300 | `{"graph_no_blocking_move_ahead":200}` |
| `risk_increases` | 20 | 2.955 | 0.855 | 2.250 | `{"graph_near_object":104,"graph_no_blocking_move_ahead":96}` |
| `risk_without_graph_blocking` | 20 | 1.960 | 1.375 | 0.000 | `{"graph_near_object":192,"graph_no_blocking_move_ahead":8}` |
| `target_reachable` | 20 | 2.833 | 1.000 | 0.000 | `{"graph_target_reachable":60}` |
| `target_reachable_affordance` | 20 | 3.000 | 1.000 | 0.000 | `{"graph_target_reachable":60}` |
| `uncertainty_near_path` | 20 | 1.955 | 1.075 | 2.150 | `{"graph_near_object":136,"graph_no_blocking_move_ahead":64}` |
| `uncertainty_without_high_risk` | 20 | 1.950 | 0.835 | 3.900 | `{"graph_near_object":58,"graph_no_blocking_move_ahead":142}` |
| `unknown_near_path` | 20 | 1.950 | 1.255 | 0.450 | `{"graph_near_object":172,"graph_no_blocking_move_ahead":28}` |
| `unknown_uncertain_object` | 20 | 2.000 | 0.430 | 4.100 | `{"graph_near_object":74,"graph_no_blocking_move_ahead":126}` |

## Scene Graph vs RAST Differentiation Summary

- 이 섹션은 Scene Graph baseline과 RAST의 우수/열위를 주장하지 않고 representation 차이를 관찰합니다.
- action disagreement가 0이어도 같은 action을 서로 다른 reason_code로 선택할 수 있으므로 decision basis metric을 별도로 봅니다.
- Average RAST vs Scene Graph action disagreement: 1.888
- Average same-action-different-reason count: 7.552
- Average same-action-different-reason rate: 0.811
- Total Scene Graph trigger edge count: 2694
- Total RAST trigger RiskToken count: 3119
- Total Event-aware trigger EventToken count: 928
- relation edge 기반 decision과 Risk/EventToken 기반 decision은 같은 ObservationSnapshot에서 출발하지만 서로 다른 contract를 사용합니다.
- risk_threshold와 relation threshold는 분리되어 있어 relation edge와 RiskToken boundary를 독립적으로 관찰할 수 있습니다.
- 이 결과는 RAST 우수성 증거가 아니라 controlled metadata suite에서 decision basis 차이가 기록됨을 보여주는 자료입니다.

| Scenario | Runs | RAST vs Scene Graph Disagreement | Same Action Different Reason | Same Action Different Reason Rate | Relation Tokens Avg | Graph Edges Avg | RAST Risk Triggers Avg | Event Triggers Avg |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `avoid_required_blocking_path` | 20 | 0.850 | 9.150 | 0.915 | 1.140 | 1.140 | 9.300 | 1.550 |
| `blocking_relation_without_high_risk` | 20 | 2.200 | 7.800 | 0.780 | 0.785 | 0.785 | 6.100 | 3.050 |
| `clear_path` | 20 | 0.000 | 10.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.550 |
| `event_changes_risk_but_graph_static` | 20 | 0.550 | 9.450 | 0.945 | 1.130 | 1.130 | 8.100 | 3.650 |
| `far_obstacle` | 20 | 2.000 | 8.000 | 0.800 | 0.635 | 0.635 | 3.450 | 2.800 |
| `inspect_required_uncertain_path` | 20 | 3.750 | 6.250 | 0.625 | 1.090 | 1.090 | 8.100 | 1.850 |
| `low_sensor_agreement` | 20 | 3.350 | 6.650 | 0.665 | 0.970 | 0.970 | 7.500 | 2.000 |
| `narrow_passage` | 20 | 2.750 | 7.250 | 0.725 | 2.160 | 2.160 | 8.750 | 3.100 |
| `near_obstacle` | 20 | 0.500 | 9.500 | 0.950 | 1.195 | 1.195 | 9.450 | 0.850 |
| `noisy_position_boundary` | 20 | 2.300 | 7.700 | 0.770 | 1.015 | 1.015 | 6.950 | 1.350 |
| `object_appears` | 20 | 0.950 | 9.050 | 0.905 | 0.905 | 0.905 | 7.500 | 2.400 |
| `object_disappears` | 20 | 0.600 | 9.400 | 0.940 | 0.140 | 0.140 | 0.700 | 1.450 |
| `object_moves` | 20 | 2.550 | 7.450 | 0.745 | 0.895 | 0.895 | 7.800 | 2.550 |
| `partially_occluded_obstacle` | 20 | 3.700 | 6.300 | 0.630 | 1.005 | 1.005 | 8.200 | 1.850 |
| `passable_clear_gap` | 20 | 1.550 | 8.450 | 0.845 | 1.670 | 1.670 | 8.650 | 1.850 |
| `planner_disagreement` | 20 | 4.450 | 5.550 | 0.555 | 1.030 | 1.030 | 8.150 | 1.350 |
| `relation_near_but_low_risk` | 20 | 2.300 | 7.700 | 0.770 | 0.035 | 0.035 | 2.300 | 0.900 |
| `risk_increases` | 20 | 2.250 | 7.750 | 0.775 | 0.855 | 0.855 | 6.850 | 2.700 |
| `risk_without_graph_blocking` | 20 | 0.000 | 10.000 | 1.000 | 1.375 | 1.375 | 9.600 | 1.800 |
| `target_reachable` | 20 | 0.000 | 3.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| `target_reachable_affordance` | 20 | 0.000 | 3.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| `uncertainty_near_path` | 20 | 2.150 | 7.850 | 0.785 | 1.075 | 1.075 | 7.850 | 2.200 |
| `uncertainty_without_high_risk` | 20 | 3.900 | 6.100 | 0.610 | 0.835 | 0.835 | 5.500 | 1.600 |
| `unknown_near_path` | 20 | 0.450 | 9.550 | 0.955 | 1.255 | 1.255 | 9.050 | 2.850 |
| `unknown_uncertain_object` | 20 | 4.100 | 5.900 | 0.590 | 0.430 | 0.430 | 6.100 | 2.150 |

- `relation_near_but_low_risk`, `blocking_relation_without_high_risk`, `risk_without_graph_blocking`, `event_changes_risk_but_graph_static`는 representation 차이를 관찰하기 위한 controlled scenario입니다.
- Scene Graph는 simplified relation edge baseline이고, RelationToken은 simple geometry rule 기반입니다.

## Event-aware Planner Summary

- Event-aware RAST planner included in this report: yes
- Average RAST vs Event-aware RAST disagreement: 0.198
- Total event-triggered Event-aware actions: 928
- Average event-triggered Event-aware actions per episode: 1.856
- Average Event-aware decision trace coverage: 1.000
- Event-aware reason code distribution: `{"event_object_appeared_near_path":86,"event_object_disappeared_clear_path":142,"event_object_moved":427,"event_risk_increased":273,"fallback_no_risk_move_ahead":1459,"fallback_risk_token_present":2333}`
- Scenarios with observed RAST vs Event-aware disagreement: `avoid_required_blocking_path, blocking_relation_without_high_risk, event_changes_risk_but_graph_static, far_obstacle, inspect_required_uncertain_path, low_sensor_agreement, narrow_passage, noisy_position_boundary, object_moves, partially_occluded_obstacle, passable_clear_gap, planner_disagreement, risk_increases, risk_without_graph_blocking, uncertainty_near_path, uncertainty_without_high_risk, unknown_uncertain_object`
- 같은 action이 선택되더라도 기존 RAST와 Event-aware RAST의 reason_code는 다를 수 있습니다.
- Event-aware planner는 deterministic rule-based experimental policy이며 성능 개선을 단정하는 근거가 아닙니다.

| Scenario | Runs | Avg RAST vs Event-aware Disagreement | Avg Event-triggered Actions | Event-aware Reason Codes |
|---|---:|---:|---:|---|
| `avoid_required_blocking_path` | 20 | 0.050 | 1.550 | `{"event_object_moved":28,"event_risk_increased":3,"fallback_no_risk_move_ahead":14,"fallback_risk_token_present":155}` |
| `blocking_relation_without_high_risk` | 20 | 0.100 | 3.050 | `{"event_object_appeared_near_path":14,"event_object_disappeared_clear_path":11,"event_object_moved":26,"event_risk_increased":10,"fallback_no_risk_move_ahead":67,"fallback_risk_token_present":72}` |
| `clear_path` | 20 | 0.000 | 0.550 | `{"event_object_disappeared_clear_path":11,"fallback_no_risk_move_ahead":189}` |
| `event_changes_risk_but_graph_static` | 20 | 0.600 | 3.650 | `{"event_object_appeared_near_path":9,"event_object_disappeared_clear_path":10,"event_object_moved":32,"event_risk_increased":22,"fallback_no_risk_move_ahead":28,"fallback_risk_token_present":99}` |
| `far_obstacle` | 20 | 0.250 | 2.800 | `{"event_object_appeared_near_path":3,"event_object_disappeared_clear_path":11,"event_object_moved":13,"event_risk_increased":29,"fallback_no_risk_move_ahead":120,"fallback_risk_token_present":24}` |
| `inspect_required_uncertain_path` | 20 | 0.150 | 1.850 | `{"event_object_moved":29,"event_risk_increased":8,"fallback_no_risk_move_ahead":38,"fallback_risk_token_present":125}` |
| `low_sensor_agreement` | 20 | 0.350 | 2.000 | `{"event_object_moved":24,"event_risk_increased":16,"fallback_no_risk_move_ahead":50,"fallback_risk_token_present":110}` |
| `narrow_passage` | 20 | 0.350 | 3.100 | `{"event_object_appeared_near_path":9,"event_object_moved":34,"event_risk_increased":19,"fallback_no_risk_move_ahead":25,"fallback_risk_token_present":113}` |
| `near_obstacle` | 20 | 0.000 | 0.850 | `{"event_object_moved":17,"fallback_no_risk_move_ahead":11,"fallback_risk_token_present":172}` |
| `noisy_position_boundary` | 20 | 0.250 | 1.350 | `{"event_object_appeared_near_path":6,"event_object_moved":8,"event_risk_increased":13,"fallback_no_risk_move_ahead":61,"fallback_risk_token_present":112}` |
| `object_appears` | 20 | 0.000 | 2.400 | `{"event_object_appeared_near_path":26,"event_object_disappeared_clear_path":12,"event_object_moved":10,"fallback_no_risk_move_ahead":38,"fallback_risk_token_present":114}` |
| `object_disappears` | 20 | 0.000 | 1.450 | `{"event_object_disappeared_clear_path":29,"fallback_no_risk_move_ahead":157,"fallback_risk_token_present":14}` |
| `object_moves` | 20 | 0.850 | 2.550 | `{"event_object_moved":10,"event_risk_increased":41,"fallback_no_risk_move_ahead":44,"fallback_risk_token_present":105}` |
| `partially_occluded_obstacle` | 20 | 0.250 | 1.850 | `{"event_object_disappeared_clear_path":10,"event_object_moved":16,"event_risk_increased":11,"fallback_no_risk_move_ahead":26,"fallback_risk_token_present":137}` |
| `passable_clear_gap` | 20 | 0.100 | 1.850 | `{"event_object_moved":24,"event_risk_increased":13,"fallback_no_risk_move_ahead":27,"fallback_risk_token_present":136}` |
| `planner_disagreement` | 20 | 0.200 | 1.350 | `{"event_object_moved":17,"event_risk_increased":10,"fallback_no_risk_move_ahead":37,"fallback_risk_token_present":136}` |
| `relation_near_but_low_risk` | 20 | 0.000 | 0.900 | `{"event_object_appeared_near_path":3,"event_object_disappeared_clear_path":9,"event_object_moved":6,"fallback_no_risk_move_ahead":145,"fallback_risk_token_present":37}` |
| `risk_increases` | 20 | 0.600 | 2.700 | `{"event_object_disappeared_clear_path":2,"event_object_moved":33,"event_risk_increased":19,"fallback_no_risk_move_ahead":61,"fallback_risk_token_present":85}` |
| `risk_without_graph_blocking` | 20 | 0.050 | 1.800 | `{"event_object_disappeared_clear_path":8,"event_object_moved":27,"event_risk_increased":1,"fallback_risk_token_present":164}` |
| `target_reachable` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":60}` |
| `target_reachable_affordance` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":60}` |
| `uncertainty_near_path` | 20 | 0.150 | 2.200 | `{"event_object_appeared_near_path":9,"event_object_disappeared_clear_path":9,"event_object_moved":18,"event_risk_increased":8,"fallback_no_risk_move_ahead":34,"fallback_risk_token_present":122}` |
| `uncertainty_without_high_risk` | 20 | 0.350 | 1.600 | `{"event_object_disappeared_clear_path":10,"event_object_moved":3,"event_risk_increased":19,"fallback_no_risk_move_ahead":80,"fallback_risk_token_present":88}` |
| `unknown_near_path` | 20 | 0.000 | 2.850 | `{"event_object_appeared_near_path":7,"event_object_disappeared_clear_path":10,"event_object_moved":36,"event_risk_increased":4,"fallback_no_risk_move_ahead":9,"fallback_risk_token_present":134}` |
| `unknown_uncertain_object` | 20 | 0.300 | 2.150 | `{"event_object_moved":16,"event_risk_increased":27,"fallback_no_risk_move_ahead":78,"fallback_risk_token_present":79}` |

## Uncertainty-aware Planner Summary

- Uncertainty-aware RAST planner included in this report: yes
- Average RAST vs Uncertainty-aware RAST disagreement: 0.752
- Total uncertainty-triggered actions: 1419
- Average uncertainty-triggered actions per episode: 2.838
- Average Uncertainty-aware decision trace coverage: 1.000
- Uncertainty-aware reason code distribution: `{"fallback_no_risk_move_ahead":1301,"fallback_risk_token_present":2000,"high_uncertainty_near_path":157,"low_sensor_agreement":113,"partial_occlusion_uncertainty":236,"position_uncertainty_boundary":179,"unknown_object_uncertainty":734}`
- Scenarios with observed RAST vs Uncertainty-aware disagreement: `event_changes_risk_but_graph_static, inspect_required_uncertain_path, low_sensor_agreement, noisy_position_boundary, partially_occluded_obstacle, planner_disagreement, risk_increases, uncertainty_near_path, uncertainty_without_high_risk, unknown_near_path, unknown_uncertain_object`
- Uncertainty-aware planner는 deterministic rule-based experimental policy이며 성능 개선을 단정하는 근거가 아닙니다.
- uncertainty가 action/reason을 바꾸더라도 실제 perception uncertainty calibration이나 safety improvement를 의미하지 않습니다.

| Scenario | Runs | Avg RAST vs Uncertainty-aware Disagreement | Avg Uncertainty-triggered Actions | Reason Codes |
|---|---:|---:|---:|---|
| `avoid_required_blocking_path` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":14,"fallback_risk_token_present":186}` |
| `blocking_relation_without_high_risk` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":78,"fallback_risk_token_present":122}` |
| `clear_path` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":200}` |
| `event_changes_risk_but_graph_static` | 20 | 1.100 | 6.300 | `{"fallback_no_risk_move_ahead":16,"fallback_risk_token_present":58,"unknown_object_uncertainty":126}` |
| `far_obstacle` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":131,"fallback_risk_token_present":69}` |
| `inspect_required_uncertain_path` | 20 | 1.250 | 5.950 | `{"fallback_no_risk_move_ahead":13,"fallback_risk_token_present":68,"partial_occlusion_uncertainty":119}` |
| `low_sensor_agreement` | 20 | 1.550 | 5.650 | `{"fallback_no_risk_move_ahead":20,"fallback_risk_token_present":67,"low_sensor_agreement":113}` |
| `narrow_passage` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":25,"fallback_risk_token_present":175}` |
| `near_obstacle` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":11,"fallback_risk_token_present":189}` |
| `noisy_position_boundary` | 20 | 5.400 | 8.200 | `{"fallback_no_risk_move_ahead":9,"fallback_risk_token_present":27,"high_uncertainty_near_path":83,"position_uncertainty_boundary":81}` |
| `object_appears` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":50,"fallback_risk_token_present":150}` |
| `object_disappears` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":186,"fallback_risk_token_present":14}` |
| `object_moves` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":44,"fallback_risk_token_present":156}` |
| `partially_occluded_obstacle` | 20 | 0.900 | 5.850 | `{"fallback_no_risk_move_ahead":18,"fallback_risk_token_present":65,"partial_occlusion_uncertainty":117}` |
| `passable_clear_gap` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":27,"fallback_risk_token_present":173}` |
| `planner_disagreement` | 20 | 1.000 | 5.750 | `{"fallback_no_risk_move_ahead":17,"fallback_risk_token_present":68,"unknown_object_uncertainty":115}` |
| `relation_near_but_low_risk` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":154,"fallback_risk_token_present":46}` |
| `risk_increases` | 20 | 1.500 | 5.650 | `{"fallback_no_risk_move_ahead":33,"fallback_risk_token_present":54,"unknown_object_uncertainty":113}` |
| `risk_without_graph_blocking` | 20 | 0.000 | 6.450 | `{"fallback_no_risk_move_ahead":8,"fallback_risk_token_present":63,"unknown_object_uncertainty":129}` |
| `target_reachable` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":60}` |
| `target_reachable_affordance` | 20 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":60}` |
| `uncertainty_near_path` | 20 | 1.050 | 5.800 | `{"fallback_no_risk_move_ahead":22,"fallback_risk_token_present":62,"unknown_object_uncertainty":116}` |
| `uncertainty_without_high_risk` | 20 | 4.550 | 8.600 | `{"fallback_no_risk_move_ahead":18,"fallback_risk_token_present":10,"high_uncertainty_near_path":74,"position_uncertainty_boundary":98}` |
| `unknown_near_path` | 20 | 0.400 | 5.850 | `{"fallback_no_risk_move_ahead":11,"fallback_risk_token_present":72,"unknown_object_uncertainty":117}` |
| `unknown_uncertain_object` | 20 | 0.100 | 0.900 | `{"fallback_no_risk_move_ahead":76,"fallback_risk_token_present":106,"unknown_object_uncertainty":18}` |

## Affordance-aware Planner Summary

- Affordance-aware RAST planner included in this report: yes
- Average RAST vs Affordance-aware RAST disagreement: 5.950
- Total affordance-triggered actions: 4259
- Average affordance-triggered actions per episode: 8.518
- Average Affordance-aware decision trace coverage: 1.000
- Affordance-aware reason code distribution: `{"affordance_avoid_required":11,"affordance_inspect_required":1245,"affordance_narrow_passage_slow_or_rotate":59,"affordance_passable_move_ahead":2824,"affordance_target_reachable":120,"fallback_no_risk_move_ahead":93,"fallback_risk_token_present":368}`
- Scenarios with observed RAST vs Affordance-aware disagreement: `avoid_required_blocking_path, blocking_relation_without_high_risk, event_changes_risk_but_graph_static, far_obstacle, inspect_required_uncertain_path, low_sensor_agreement, narrow_passage, near_obstacle, noisy_position_boundary, object_appears, object_moves, partially_occluded_obstacle, passable_clear_gap, planner_disagreement, relation_near_but_low_risk, risk_increases, risk_without_graph_blocking, uncertainty_near_path, uncertainty_without_high_risk, unknown_near_path, unknown_uncertain_object`
- Affordance-aware planner is a deterministic rule-based experimental policy.
- Affordance-triggered action changes do not imply verified performance improvement or real robot feasibility.

| Scenario | Runs | Avg RAST vs Affordance-aware Disagreement | Avg Affordance-triggered Actions | Reason Codes |
|---|---:|---:|---:|---|
| `avoid_required_blocking_path` | 20 | 6.600 | 7.250 | `{"affordance_passable_move_ahead":145,"fallback_no_risk_move_ahead":1,"fallback_risk_token_present":54}` |
| `blocking_relation_without_high_risk` | 20 | 4.250 | 7.650 | `{"affordance_passable_move_ahead":153,"fallback_no_risk_move_ahead":10,"fallback_risk_token_present":37}` |
| `clear_path` | 20 | 0.000 | 10.000 | `{"affordance_passable_move_ahead":200}` |
| `event_changes_risk_but_graph_static` | 20 | 9.200 | 10.000 | `{"affordance_inspect_required":126,"affordance_passable_move_ahead":74}` |
| `far_obstacle` | 20 | 1.850 | 6.400 | `{"affordance_passable_move_ahead":128,"fallback_no_risk_move_ahead":40,"fallback_risk_token_present":32}` |
| `inspect_required_uncertain_path` | 20 | 9.350 | 10.000 | `{"affordance_inspect_required":119,"affordance_passable_move_ahead":81}` |
| `low_sensor_agreement` | 20 | 4.850 | 6.400 | `{"affordance_avoid_required":1,"affordance_passable_move_ahead":127,"fallback_no_risk_move_ahead":19,"fallback_risk_token_present":53}` |
| `narrow_passage` | 20 | 6.300 | 9.600 | `{"affordance_avoid_required":8,"affordance_narrow_passage_slow_or_rotate":59,"affordance_passable_move_ahead":125,"fallback_risk_token_present":8}` |
| `near_obstacle` | 20 | 6.750 | 7.300 | `{"affordance_passable_move_ahead":146,"fallback_risk_token_present":54}` |
| `noisy_position_boundary` | 20 | 9.350 | 10.000 | `{"affordance_inspect_required":136,"affordance_passable_move_ahead":64}` |
| `object_appears` | 20 | 5.250 | 7.700 | `{"affordance_passable_move_ahead":154,"fallback_no_risk_move_ahead":1,"fallback_risk_token_present":45}` |
| `object_disappears` | 20 | 0.000 | 9.000 | `{"affordance_passable_move_ahead":180,"fallback_no_risk_move_ahead":6,"fallback_risk_token_present":14}` |
| `object_moves` | 20 | 5.350 | 6.750 | `{"affordance_avoid_required":2,"affordance_passable_move_ahead":133,"fallback_no_risk_move_ahead":16,"fallback_risk_token_present":49}` |
| `partially_occluded_obstacle` | 20 | 9.100 | 10.000 | `{"affordance_inspect_required":117,"affordance_passable_move_ahead":83}` |
| `passable_clear_gap` | 20 | 7.900 | 9.250 | `{"affordance_passable_move_ahead":185,"fallback_risk_token_present":15}` |
| `planner_disagreement` | 20 | 9.150 | 10.000 | `{"affordance_inspect_required":115,"affordance_passable_move_ahead":85}` |
| `relation_near_but_low_risk` | 20 | 1.950 | 9.650 | `{"affordance_passable_move_ahead":193,"fallback_risk_token_present":7}` |
| `risk_increases` | 20 | 8.350 | 10.000 | `{"affordance_inspect_required":113,"affordance_passable_move_ahead":87}` |
| `risk_without_graph_blocking` | 20 | 9.600 | 10.000 | `{"affordance_inspect_required":129,"affordance_passable_move_ahead":71}` |
| `target_reachable` | 20 | 0.000 | 3.000 | `{"affordance_target_reachable":60}` |
| `target_reachable_affordance` | 20 | 0.000 | 3.000 | `{"affordance_target_reachable":60}` |
| `uncertainty_near_path` | 20 | 8.900 | 10.000 | `{"affordance_inspect_required":116,"affordance_passable_move_ahead":84}` |
| `uncertainty_without_high_risk` | 20 | 9.050 | 10.000 | `{"affordance_inspect_required":139,"affordance_passable_move_ahead":61}` |
| `unknown_near_path` | 20 | 9.450 | 10.000 | `{"affordance_inspect_required":117,"affordance_passable_move_ahead":83}` |
| `unknown_uncertain_object` | 20 | 6.200 | 10.000 | `{"affordance_inspect_required":18,"affordance_passable_move_ahead":182}` |

## Event-aware Ablation Summary

- Event-aware policy variant가 aggregate row에 기록되어 variant별 비교가 가능합니다.
- `logging_only` variant는 EventToken을 입력으로 받지만 action에는 사용하지 않는 비교 조건입니다.
- 이 표는 어떤 event rule이 action change와 함께 관찰되는지 분리하기 위한 infrastructure이며, 성능 개선 주장으로 해석하면 안 됩니다.

| Event Policy Variant | Runs | Avg RAST vs Event-aware Disagreement | Avg Event-triggered Actions | Reason Codes |
|---|---:|---:|---:|---|
| `full` | 9 | 0.000 | 1.778 | `{"event_object_appeared_near_path":2,"event_object_disappeared_clear_path":3,"event_object_moved":8,"event_risk_increased":3,"fallback_no_risk_move_ahead":11,"fallback_risk_token_present":63}` |
| `logging_only` | 8 | 0.000 | 0.000 | `{"fallback_no_risk_move_ahead":23,"fallback_risk_token_present":50}` |
| `no_object_appeared` | 7 | 0.143 | 2.429 | `{"event_object_disappeared_clear_path":2,"event_object_moved":12,"event_risk_increased":3,"fallback_no_risk_move_ahead":16,"fallback_risk_token_present":37}` |
| `no_object_disappeared` | 9 | 0.000 | 0.778 | `{"event_object_appeared_near_path":1,"event_object_moved":3,"event_risk_increased":3,"fallback_no_risk_move_ahead":27,"fallback_risk_token_present":42}` |
| `no_object_moved` | 10 | 0.100 | 1.800 | `{"event_object_appeared_near_path":6,"event_object_disappeared_clear_path":6,"event_risk_increased":6,"fallback_no_risk_move_ahead":25,"fallback_risk_token_present":57}` |
| `no_risk_changed` | 7 | 0.000 | 1.143 | `{"event_object_disappeared_clear_path":2,"event_object_moved":6,"fallback_no_risk_move_ahead":23,"fallback_risk_token_present":32}` |

| Scenario / Variant | Runs | Avg Disagreement | Avg Event-triggered Actions |
|---|---:|---:|---:|
| `avoid_required_blocking_path | no_object_appeared` | 1 | 0.000 | 5.000 |
| `avoid_required_blocking_path | no_risk_changed` | 1 | 0.000 | 5.000 |
| `blocking_relation_without_high_risk | logging_only` | 1 | 0.000 | 0.000 |
| `blocking_relation_without_high_risk | no_object_moved` | 1 | 0.000 | 3.000 |
| `clear_path | no_object_disappeared` | 1 | 0.000 | 0.000 |
| `clear_path | no_risk_changed` | 1 | 0.000 | 1.000 |
| `event_changes_risk_but_graph_static | logging_only` | 2 | 0.000 | 0.000 |
| `far_obstacle | full` | 1 | 0.000 | 5.000 |
| `far_obstacle | no_object_moved` | 1 | 0.000 | 2.000 |
| `inspect_required_uncertain_path | full` | 1 | 0.000 | 5.000 |
| `inspect_required_uncertain_path | no_object_moved` | 1 | 0.000 | 0.000 |
| `low_sensor_agreement | full` | 1 | 0.000 | 0.000 |
| `low_sensor_agreement | logging_only` | 1 | 0.000 | 0.000 |
| `narrow_passage | no_object_appeared` | 1 | 0.000 | 0.000 |
| `narrow_passage | no_object_disappeared` | 1 | 0.000 | 2.000 |
| `near_obstacle | full` | 1 | 0.000 | 0.000 |
| `near_obstacle | no_object_appeared` | 1 | 0.000 | 0.000 |
| `noisy_position_boundary | full` | 1 | 0.000 | 1.000 |
| `noisy_position_boundary | logging_only` | 1 | 0.000 | 0.000 |
| `object_appears | no_object_disappeared` | 1 | 0.000 | 4.000 |
| `object_appears | no_object_moved` | 1 | 0.000 | 3.000 |
| `object_disappears | no_object_appeared` | 1 | 0.000 | 1.000 |
| `object_disappears | no_object_disappeared` | 1 | 0.000 | 0.000 |
| `object_moves | full` | 1 | 0.000 | 1.000 |
| `object_moves | no_object_moved` | 1 | 1.000 | 3.000 |
| `partially_occluded_obstacle | full` | 1 | 0.000 | 1.000 |
| `partially_occluded_obstacle | no_object_disappeared` | 1 | 0.000 | 1.000 |
| `passable_clear_gap | no_object_moved` | 1 | 0.000 | 1.000 |
| `passable_clear_gap | no_risk_changed` | 1 | 0.000 | 0.000 |
| `planner_disagreement | logging_only` | 1 | 0.000 | 0.000 |
| `planner_disagreement | no_object_disappeared` | 1 | 0.000 | 0.000 |
| `relation_near_but_low_risk | logging_only` | 1 | 0.000 | 0.000 |
| `relation_near_but_low_risk | no_object_moved` | 1 | 0.000 | 0.000 |
| `risk_increases | no_object_appeared` | 1 | 1.000 | 8.000 |
| `risk_increases | no_risk_changed` | 1 | 0.000 | 1.000 |
| `risk_without_graph_blocking | no_object_appeared` | 1 | 0.000 | 0.000 |
| `risk_without_graph_blocking | no_object_moved` | 1 | 0.000 | 1.000 |
| `target_reachable | no_object_disappeared` | 1 | 0.000 | 0.000 |
| `target_reachable | no_risk_changed` | 1 | 0.000 | 0.000 |
| `target_reachable_affordance | logging_only` | 1 | 0.000 | 0.000 |
| `target_reachable_affordance | no_object_disappeared` | 1 | 0.000 | 0.000 |
| `uncertainty_near_path | full` | 1 | 0.000 | 2.000 |
| `uncertainty_near_path | no_object_moved` | 1 | 0.000 | 3.000 |
| `uncertainty_without_high_risk | no_object_appeared` | 1 | 0.000 | 3.000 |
| `uncertainty_without_high_risk | no_risk_changed` | 1 | 0.000 | 1.000 |
| `unknown_near_path | no_object_disappeared` | 1 | 0.000 | 0.000 |
| `unknown_near_path | no_object_moved` | 1 | 0.000 | 2.000 |
| `unknown_uncertain_object | full` | 1 | 0.000 | 1.000 |
| `unknown_uncertain_object | no_risk_changed` | 1 | 0.000 | 0.000 |

- variant별 reason_code distribution은 event rule 활성/비활성에 따른 action trace 차이를 보는 용도입니다.
- 현재 Event-aware planner는 deterministic rule-based policy이며 learned extractor나 learned policy가 아닙니다.

## Threshold and Noise Sensitivity Summary

- risk_threshold와 near_miss_threshold는 aggregate row에 보존되어 threshold sweep 분석에 사용할 수 있습니다.
- noise 값은 WindowsMetadataSim metadata에 적용한 synthetic seeded noise이며 실제 perception error가 아닙니다.
- 아래 값은 deterministic metadata simulator에서의 sensitivity 관찰용이며 real-world robustness claim을 지원하지 않습니다.

| Risk Threshold | Runs | Avg Near-miss | Avg RAST vs Event-aware Disagreement | Avg Event-triggered Actions |
|---|---:|---:|---:|---:|
| `1.0` | 167 | 2.425 | 0.036 | 1.491 |
| `1.5` | 166 | 1.572 | 0.217 | 1.934 |
| `2.0` | 167 | 1.533 | 0.341 | 2.144 |

| Noise Level | Runs | Success Rate | Avg Near-miss | Avg Disagreement |
|---|---:|---:|---:|---:|
| `position=0.0, distance=0.0, visibility=0.0` | 27 | 1.000 | 3.222 | 0.333 |
| `position=0.0, distance=0.0, visibility=0.05` | 27 | 1.000 | 1.741 | 0.111 |
| `position=0.0, distance=0.02, visibility=0.0` | 30 | 1.000 | 2.000 | 0.133 |
| `position=0.0, distance=0.02, visibility=0.05` | 27 | 1.000 | 1.296 | 0.111 |
| `position=0.0, distance=0.05, visibility=0.0` | 27 | 1.000 | 2.296 | 0.259 |
| `position=0.0, distance=0.05, visibility=0.05` | 27 | 1.000 | 2.333 | 0.185 |
| `position=0.02, distance=0.0, visibility=0.0` | 27 | 1.000 | 2.259 | 0.222 |
| `position=0.02, distance=0.0, visibility=0.05` | 30 | 1.000 | 1.067 | 0.167 |
| `position=0.02, distance=0.02, visibility=0.0` | 29 | 1.000 | 1.345 | 0.138 |
| `position=0.02, distance=0.02, visibility=0.05` | 27 | 1.000 | 1.815 | 0.185 |
| `position=0.02, distance=0.05, visibility=0.0` | 27 | 1.000 | 1.333 | 0.074 |
| `position=0.02, distance=0.05, visibility=0.05` | 27 | 1.000 | 1.556 | 0.148 |
| `position=0.05, distance=0.0, visibility=0.0` | 30 | 1.000 | 1.833 | 0.133 |
| `position=0.05, distance=0.0, visibility=0.05` | 30 | 1.000 | 1.967 | 0.267 |
| `position=0.05, distance=0.02, visibility=0.0` | 27 | 1.000 | 1.741 | 0.185 |
| `position=0.05, distance=0.02, visibility=0.05` | 27 | 1.000 | 2.259 | 0.296 |
| `position=0.05, distance=0.05, visibility=0.0` | 27 | 1.000 | 1.481 | 0.444 |
| `position=0.05, distance=0.05, visibility=0.05` | 27 | 1.000 | 1.741 | 0.185 |

- default suite가 작게 유지되는 경우 threshold/noise level 수가 제한될 수 있습니다.
- 더 강한 결론을 위해서는 별도 extended config로 threshold와 synthetic noise grid를 확장해야 합니다.

## Latency Summary

- Average latency: 0.889 ms
- Average p50 latency: 0.883 ms
- Average p95 latency: 1.067 ms
- Average token generation latency: 0.217 ms
- Average planning latency: 0.370 ms
- 이 latency는 Python metadata simulator 경로에서 측정된 값이며, real rendering이나 perception model overhead를 포함하지 않습니다.

| Apply Policy | Runs | Avg Latency ms | Avg Planning ms |
|---|---:|---:|---:|
| `affordance_aware_rast` | 75 | 0.832 | 0.342 |
| `event_aware_rast` | 50 | 0.923 | 0.407 |
| `flat_feature` | 75 | 0.901 | 0.375 |
| `object_list` | 75 | 0.937 | 0.385 |
| `rast` | 75 | 0.833 | 0.346 |
| `scene_graph` | 75 | 0.925 | 0.387 |
| `uncertainty_aware_rast` | 75 | 0.885 | 0.364 |

## Incremental Update Summary

- 이 섹션은 full token recomputation과 TokenMemory 기반 event-aware incremental update의 latency protocol을 비교합니다.
- incremental update optimization is experimental; 현재 결과는 최적화 완료나 planner 성능 개선을 의미하지 않습니다.
- WindowsMetadataSim은 metadata-only toy simulator이므로 absolute latency value는 매우 작고 실제 perception/model cost를 포함하지 않습니다.
- 이번 runner는 같은 snapshot에서 full_recompute와 incremental 후보를 모두 측정하고, 선택된 update_mode의 token generation latency를 step latency에 기록합니다.
- Overall changed object count avg: 0.514
- Overall affected token count avg: 2.026
- Overall full recompute latency avg: 0.241 ms
- Overall incremental update latency avg: 0.181 ms
- Overall incremental update benefit avg: 0.256

| Update Mode | Runs | Changed Objects Avg | Affected Tokens Avg | Full ms | Incremental ms | Benefit |
|---|---:|---:|---:|---:|---:|---:|
| `full_recompute` | 325 | 0.504 | 2.474 | 0.236 | 0.180 | 0.248 |
| `incremental` | 175 | 0.532 | 1.194 | 0.250 | 0.183 | 0.271 |

| Scenario | Runs | Changed Objects Avg | Affected Tokens Avg | Incremental Benefit Avg |
|---|---:|---:|---:|---:|
| `avoid_required_blocking_path` | 20 | 0.295 | 1.570 | 0.275 |
| `blocking_relation_without_high_risk` | 20 | 0.485 | 1.805 | 0.278 |
| `clear_path` | 20 | 0.765 | 2.000 | 0.230 |
| `event_changes_risk_but_graph_static` | 20 | 0.955 | 3.070 | 0.218 |
| `far_obstacle` | 20 | 0.555 | 1.615 | 0.290 |
| `inspect_required_uncertain_path` | 20 | 0.320 | 1.535 | 0.254 |
| `low_sensor_agreement` | 20 | 0.390 | 1.675 | 0.260 |
| `narrow_passage` | 20 | 1.000 | 4.435 | 0.194 |
| `near_obstacle` | 20 | 0.225 | 1.515 | 0.273 |
| `noisy_position_boundary` | 20 | 0.210 | 1.405 | 0.283 |
| `object_appears` | 20 | 0.585 | 2.735 | 0.227 |
| `object_disappears` | 20 | 0.580 | 1.305 | 0.274 |
| `object_moves` | 20 | 0.755 | 2.905 | 0.218 |
| `partially_occluded_obstacle` | 20 | 0.310 | 1.570 | 0.263 |
| `passable_clear_gap` | 20 | 0.715 | 4.015 | 0.197 |
| `planner_disagreement` | 20 | 0.305 | 1.675 | 0.269 |
| `relation_near_but_low_risk` | 20 | 0.605 | 2.155 | 0.254 |
| `risk_increases` | 20 | 0.800 | 3.000 | 0.226 |
| `risk_without_graph_blocking` | 20 | 0.285 | 1.715 | 0.277 |
| `target_reachable` | 20 | 0.467 | 0.950 | 0.334 |
| `target_reachable_affordance` | 20 | 0.700 | 1.200 | 0.286 |
| `uncertainty_near_path` | 20 | 0.375 | 1.810 | 0.235 |
| `uncertainty_without_high_risk` | 20 | 0.375 | 1.580 | 0.262 |
| `unknown_near_path` | 20 | 0.400 | 1.840 | 0.277 |
| `unknown_uncertain_object` | 20 | 0.385 | 1.570 | 0.253 |

## Replay Trace Summary

- Decision replay export is available through `experiments/export_decision_replay.py`.
- Replay cases include collision, near-miss, planner disagreement, RAST vs Scene Graph disagreement, RAST vs Uncertainty-aware disagreement, RAST vs Affordance-aware disagreement, event-triggered action, uncertainty-triggered action, affordance-triggered action, high RiskToken, and high UncertaintyToken steps.
- The exported replay contains selected actions, planner decisions, reason codes, trigger tokens, EvidenceToken references, object metadata summary, and risk/uncertainty/event/affordance summaries.
- This is metadata/action trace reconstruction, not visual replay and not learned interpretability.
- Future versions can attach real image crop, bbox, sensor frame pointer, or perception-bound evidence references.

## Replay Artifact Summary

- replay artifact export enabled: yes
- replay_index.json: `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\replay_index.json`
- generated replay count: 10
- case_type distribution: `{"affordance_triggered_action":1,"event_triggered_action":1,"high_risk_token":1,"high_uncertainty_token":1,"near_miss":2,"rast_vs_affordance_aware_disagreement":1,"rast_vs_scene_graph_disagreement":1,"rast_vs_uncertainty_aware_disagreement":1,"uncertainty_triggered_action":1}`
- Replay artifacts are metadata/action/evidence trace reconstruction, not visual replay.

| Case Type | Scenario | Step | Markdown Path | Summary |
|---|---|---:|---|---|
| `near_miss` | `avoid_required_blocking_path` | 0 | `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\avoid_required_blocking_path_near_miss_step0.md` | selected_action=RotateRight; reason_codes={"affordance_aware_rast": "fallback_risk_token_present", "event_aware_rast": "fallback_risk_token_present", "flat_feature": "within_risk_threshold", "object_list": "near_object_distance", "rast": "risk_token_present", "scene_graph": "graph_near_object", "uncertainty_aware_rast": "fallback_risk_token_present"} |
| `rast_vs_scene_graph_disagreement` | `avoid_required_blocking_path` | 3 | `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\avoid_required_blocking_path_rast_vs_scene_graph_disagreement_step3.md` | selected_action=MoveAhead; reason_codes={"affordance_aware_rast": "affordance_passable_move_ahead", "event_aware_rast": "event_object_moved", "flat_feature": "within_risk_threshold", "object_list": "no_near_object_move_ahead", "rast": "risk_token_present", "scene_graph": "graph_no_blocking_move_ahead", "uncertainty_aware_rast": "fallback_risk_token_present"} |
| `rast_vs_uncertainty_aware_disagreement` | `event_changes_risk_but_graph_static` | 0 | `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\event_changes_risk_but_graph_static_rast_vs_uncertainty_aware_disagreement_step0.md` | selected_action=Stop; reason_codes={"affordance_aware_rast": "affordance_inspect_required", "event_aware_rast": "fallback_no_risk_move_ahead", "flat_feature": "no_risk_scalar_move_ahead", "object_list": "no_near_object_move_ahead", "rast": "no_risk_move_ahead", "scene_graph": "graph_no_blocking_move_ahead", "uncertainty_aware_rast": "unknown_object_uncertainty"} |
| `rast_vs_affordance_aware_disagreement` | `avoid_required_blocking_path` | 1 | `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\avoid_required_blocking_path_rast_vs_affordance_aware_disagreement_step1.md` | selected_action=MoveAhead; reason_codes={"affordance_aware_rast": "affordance_passable_move_ahead", "event_aware_rast": "fallback_risk_token_present", "flat_feature": "within_risk_threshold", "object_list": "near_object_distance", "rast": "risk_token_present", "scene_graph": "graph_near_object", "uncertainty_aware_rast": "fallback_risk_token_present"} |
| `event_triggered_action` | `avoid_required_blocking_path` | 3 | `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\avoid_required_blocking_path_event_triggered_action_step3.md` | selected_action=MoveAhead; reason_codes={"affordance_aware_rast": "affordance_passable_move_ahead", "event_aware_rast": "event_object_moved", "flat_feature": "within_risk_threshold", "object_list": "no_near_object_move_ahead", "rast": "risk_token_present", "scene_graph": "graph_no_blocking_move_ahead", "uncertainty_aware_rast": "fallback_risk_token_present"} |
| `uncertainty_triggered_action` | `event_changes_risk_but_graph_static` | 0 | `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\event_changes_risk_but_graph_static_uncertainty_triggered_action_step0.md` | selected_action=Stop; reason_codes={"affordance_aware_rast": "affordance_inspect_required", "event_aware_rast": "fallback_no_risk_move_ahead", "flat_feature": "no_risk_scalar_move_ahead", "object_list": "no_near_object_move_ahead", "rast": "no_risk_move_ahead", "scene_graph": "graph_no_blocking_move_ahead", "uncertainty_aware_rast": "unknown_object_uncertainty"} |
| `affordance_triggered_action` | `avoid_required_blocking_path` | 1 | `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\avoid_required_blocking_path_affordance_triggered_action_step1.md` | selected_action=MoveAhead; reason_codes={"affordance_aware_rast": "affordance_passable_move_ahead", "event_aware_rast": "fallback_risk_token_present", "flat_feature": "within_risk_threshold", "object_list": "near_object_distance", "rast": "risk_token_present", "scene_graph": "graph_near_object", "uncertainty_aware_rast": "fallback_risk_token_present"} |
| `high_risk_token` | `low_sensor_agreement` | 9 | `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\low_sensor_agreement_high_risk_token_step9.md` | selected_action=RotateRight; reason_codes={"affordance_aware_rast": "affordance_avoid_required", "event_aware_rast": "event_object_moved", "flat_feature": "within_risk_threshold", "object_list": "near_object_distance", "rast": "high_risk_token", "scene_graph": "graph_near_object", "uncertainty_aware_rast": "low_sensor_agreement"} |
| `high_uncertainty_token` | `event_changes_risk_but_graph_static` | 0 | `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\event_changes_risk_but_graph_static_high_uncertainty_token_step0.md` | selected_action=Stop; reason_codes={"affordance_aware_rast": "affordance_inspect_required", "event_aware_rast": "fallback_no_risk_move_ahead", "flat_feature": "no_risk_scalar_move_ahead", "object_list": "no_near_object_move_ahead", "rast": "no_risk_move_ahead", "scene_graph": "graph_no_blocking_move_ahead", "uncertainty_aware_rast": "unknown_object_uncertainty"} |
| `near_miss` | `avoid_required_blocking_path` | 1 | `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\replays\avoid_required_blocking_path_near_miss_step1.md` | selected_action=MoveAhead; reason_codes={"affordance_aware_rast": "affordance_passable_move_ahead", "event_aware_rast": "fallback_risk_token_present", "flat_feature": "within_risk_threshold", "object_list": "near_object_distance", "rast": "risk_token_present", "scene_graph": "graph_near_object", "uncertainty_aware_rast": "fallback_risk_token_present"} |

## Representative Decision Trace Summary

- 이 섹션은 scenario별 disagreement가 큰 decision trace 후보를 요약합니다.
- 성능 우수성 주장이 아니라 representation별 decision boundary가 갈라지는 case를 찾기 위한 요약입니다.

| Scenario | Disagreement Type | Avg Disagreement | Relevant Reason Codes | Interpretation |
|---|---|---:|---|---|
| `risk_without_graph_blocking` | RAST vs Affordance-aware | 9.600 | `{"affordance_inspect_required":129,"affordance_passable_move_ahead":71}` | AffordanceToken 기반 action possibility가 기존 RAST risk boundary와 다르게 작동한 case입니다. |
| `unknown_near_path` | RAST vs Affordance-aware | 9.450 | `{"affordance_inspect_required":117,"affordance_passable_move_ahead":83}` | AffordanceToken 기반 action possibility가 기존 RAST risk boundary와 다르게 작동한 case입니다. |
| `inspect_required_uncertain_path` | RAST vs Affordance-aware | 9.350 | `{"affordance_inspect_required":119,"affordance_passable_move_ahead":81}` | AffordanceToken 기반 action possibility가 기존 RAST risk boundary와 다르게 작동한 case입니다. |
| `noisy_position_boundary` | RAST vs Affordance-aware | 9.350 | `{"affordance_inspect_required":136,"affordance_passable_move_ahead":64}` | AffordanceToken 기반 action possibility가 기존 RAST risk boundary와 다르게 작동한 case입니다. |
| `event_changes_risk_but_graph_static` | RAST vs Affordance-aware | 9.200 | `{"affordance_inspect_required":126,"affordance_passable_move_ahead":74}` | AffordanceToken 기반 action possibility가 기존 RAST risk boundary와 다르게 작동한 case입니다. |

## Sampling Coverage and Stability Artifacts

- 이 섹션은 sampled extended result를 해석하기 전에 coverage와 seed sensitivity를 점검하기 위한 artifact 연결입니다.
- sampling coverage report: `docs\sampling_coverage_report.md`
- seed stability report: `docs\seed_stability_report.md`
- 이 artifact들은 sampled extended result의 coverage/stability 검토용이며, 성능 우수성 주장을 지원하지 않습니다.
- sampled result는 full extended grid exhaustive result가 아니므로 seed와 sample size에 의존할 수 있습니다.

## Sample-size Convergence Artifact

- 이 섹션은 sampled extended evaluation에서 sample-size 변화에 따른 metric/coverage 안정성을 점검하기 위한 artifact 연결입니다.
- sample-size convergence report: `docs\sample_size_convergence_report.md`
- 이 artifact는 sample-size sensitivity와 sampling quality score를 보기 위한 보조 자료입니다.
- full extended grid exhaustive evaluation이 아니며, sampling quality score는 RAST 성능 점수가 아닙니다.

## What This Result Supports

- WindowsMetadataSim 기반 scenario suite를 반복 실행할 수 있음을 보여줍니다.
- Object List / Flat Feature Table / RAST 세 representation과 planner action을 같은 log/summary contract로 기록할 수 있음을 보여줍니다.
- scenario별 disagreement, near-miss, success, latency를 aggregate table로 모을 수 있음을 보여줍니다.
- Flat Feature baseline을 통해 정보량 효과와 token contract 효과를 분리해서 보기 위한 실험 인프라가 준비되었음을 보여줍니다.
- EventToken이 semantic event를 감지하고 step log, episode summary, aggregate result에 기록될 수 있음을 보여줍니다.
- 별도 Event-aware RAST planner가 EventToken을 decision reason으로 사용할 수 있음을 보여줍니다.
- UncertaintyToken이 synthetic classification/position/occlusion/sensor agreement uncertainty를 기록할 수 있음을 보여줍니다.
- 별도 Uncertainty-aware RAST planner가 UncertaintyToken을 decision reason으로 사용할 수 있음을 보여줍니다.
- EvidenceToken이 risk/uncertainty/event/planner decision evidence를 metadata pointer로 연결할 수 있음을 보여줍니다.
- decision replay markdown/json을 생성해 metadata/action/evidence trace를 재구성할 수 있음을 보여줍니다.
- AffordanceToken이 navigation affordance를 기록하고, 별도 Affordance-aware RAST planner가 이를 decision reason으로 사용할 수 있음을 보여줍니다.
- 세 planner의 action 선택 사유를 PlannerDecision trace로 기록하고 집계할 수 있음을 보여줍니다.
- Scene Graph와 RAST가 같은 action을 선택해도 서로 다른 decision basis를 가질 수 있음을 기록할 수 있습니다.

## What This Result Does Not Support

- This result does not support real-world performance claims.
- RAST가 Object List나 Flat Feature보다 일반적으로 우수하다는 결론을 지원하지 않습니다.
- Event-aware planner나 EventToken이 planning 성능, success, near-miss, disagreement를 개선했다는 결론을 지원하지 않습니다.
- Uncertainty-aware planner나 UncertaintyToken이 planning 성능, success, near-miss, disagreement를 개선했다는 결론을 지원하지 않습니다.
- Affordance-aware planner나 AffordanceToken이 task performance, safety, real robot action feasibility를 개선했다는 결론을 지원하지 않습니다.
- EvidenceToken이 real sensor evidence, raw image crop, RGB/depth frame, visual evidence를 제공한다는 결론을 지원하지 않습니다.
- Decision trace는 rule-based planner 로그이며 learned model explanation 품질을 검증하지 않습니다.
- 실제 perception uncertainty calibration이나 multi-sensor fusion 품질을 검증하지 않습니다.
- 실제 RGB-D perception, detector error, occlusion error, sim-to-real 성능을 검증하지 않습니다.
- 상용 자율주행 또는 real robot safety guarantee를 제공하지 않습니다.
- AI2-THOR / Webots / CoppeliaSim / real robot 환경에서의 성능을 대변하지 않습니다.

## Limitations

- deterministic metadata simulator이므로 물리, 렌더링, 센서 노이즈가 제한적입니다.
- collision, near-miss, goal reaching은 simple geometry rule 기반입니다.
- seed가 기록되지만 현재 stochastic variation은 제한적입니다.
- token generation latency는 metadata 기반 Python 경로의 비용이며, perception-bound extractor 비용이 아닙니다.
- EventToken은 semantic diff 기반으로 생성되며, 실제 perception event detection이 아닙니다.
- UncertaintyToken은 synthetic metadata uncertainty 기반이며, 실제 perception uncertainty calibration이 아닙니다.
- sensor disagreement는 simulated field이며 실제 multi-sensor fusion 결과가 아닙니다.
- EvidenceToken은 metadata pointer 기반입니다.
- raw image crop, RGB/depth frame, real sensor evidence는 저장하지 않습니다.
- decision replay는 visual replay가 아니라 metadata/action trace reconstruction입니다.
- AffordanceToken은 navigation affordance only입니다.
- manipulation affordance는 구현하지 않았습니다.
- AffordanceToken은 simple geometry/rule 기반입니다.
- 실제 robot action feasibility를 검증하지 않습니다.
- Event-aware RAST planner는 deterministic rule-based policy이며 learned policy나 learned explanation이 아닙니다.
- Uncertainty-aware RAST planner는 deterministic rule-based experimental policy이며 learned policy가 아닙니다.
- Affordance-aware RAST planner는 deterministic rule-based experimental policy입니다.
- TokenMemory는 현재 semantic diff와 incremental latency protocol에 사용되지만, incremental update optimization is experimental입니다.
- Batch 9의 incremental update는 measurement protocol 단계이며, 일부 token 계산은 correctness를 위해 여전히 재계산됩니다.
- full_recompute와 incremental 후보를 같은 step에서 모두 측정하므로 report의 selected token_generation latency와 실제 Python wall-clock은 다를 수 있습니다.
- EventToken은 별도 Event-aware planner에만 연결되므로, success/near-miss/disagreement 변화는 일반 RAST 효과로 해석하면 안 됩니다.
- PlannerDecision은 현재 deterministic rule-based policy의 내부 규칙을 기록한 것이며, learned model interpretability는 아닙니다.
- 동일 action이라도 planner별 reason_code와 trigger feature가 다를 수 있으므로 action count만으로 의사결정 근거를 해석하면 안 됩니다.
- RelationToken과 Scene Graph baseline은 MVP용 geometry-rule 구현이며, UncertaintyToken 역시 synthetic metadata rule 기반입니다.
- Scene Graph vs RAST differentiation scenario는 controlled metadata case이며, 일반적인 representation 우수성 결론을 지원하지 않습니다.
- Flat Feature와 RAST가 동일한 scalar risk rule에 강하게 묶여 있어 token contract 효과는 아직 제한적으로만 관찰됩니다.

## Next Steps

P0 next:
- extended threshold/noise sweep을 넓혀 RAST/Object List/Flat Feature/Scene Graph/Event-aware/Uncertainty-aware/Affordance-aware disagreement boundary를 더 명확히 봅니다.
- replay artifact와 report 연결을 강화해 decision trace, evidence pointer, scenario context를 함께 추적합니다.
- result/technical report polish를 통해 현재 MVP-0의 관찰 결과와 한계를 더 읽기 쉽게 정리합니다.
- failure case/action trace analysis를 강화해 planner별 reason_code와 trigger token 차이를 더 세밀하게 분석합니다.

P1:
- Webots adapter spike로 Windows native에서 실제 3D simulator adapter 가능성을 검토합니다.
- perception-bound adapter를 추가해 simulator metadata가 아니라 detector/segmentation/depth output에서 token을 생성하는 경로를 검토합니다.
- real simulator metadata adapter로 AI2-THOR, Webots, CoppeliaSim metadata와 ObservationSnapshot adapter 연결을 검토합니다.
- manipulation affordance extension으로 graspable, openable, movable 등 navigation 외 affordance를 별도 후속 범위로 둡니다.

P2:
- learned extractor와 rule-based tokenizer를 비교합니다.
- VLA/LLM planner integration을 통해 structured token JSON 또는 text rendering 전달 방식을 실험합니다.
- real robot bridge로 실제 robot sensor stream과 RAST interface 연결 가능성을 검토합니다.
