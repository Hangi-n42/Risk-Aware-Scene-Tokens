# RAST Seed Stability Report

이 문서는 sampled extended evaluation의 sample seed 변화에 따른 metric 변동을 점검합니다.
metric variation은 성능 변화가 아니라 sample composition 차이일 수 있습니다.

## Seed Stability Summary

- seed_sweep_index: `runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_sweep_index.json`
- config_path: `configs\windows_eval_suite_extended.yaml`
- sample_size: `500`
- sampling_mode: `stratified`
- seeds: `7, 13, 42`

| Seed | Run Directory | Run Count | Failed Runs | Replay Count |
|---:|---|---:|---:|---:|
| 7 | `C:\Projects\Risk-Aware-Scene-Tokens\runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_7\windows_eval_suite_20260612_231816` | 500 | 0 | 5 |
| 13 | `C:\Projects\Risk-Aware-Scene-Tokens\runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_13\windows_eval_suite_20260612_231842` | 500 | 0 | 5 |
| 42 | `C:\Projects\Risk-Aware-Scene-Tokens\runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_42\windows_eval_suite_20260612_231908` | 500 | 0 | 5 |

## Metric Stability Table

| Metric | Mean | Min | Max | Range | Std | Coefficient of Variation |
|---|---:|---:|---:|---:|---:|---:|
| success rate | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| avg near-miss | 1.810 | 1.726 | 1.858 | 0.132 | 0.060 | 0.033 |
| avg latency ms | 0.708 | 0.699 | 0.712 | 0.013 | 0.006 | 0.008 |
| avg token generation latency ms | 0.161 | 0.150 | 0.167 | 0.017 | 0.007 | 0.046 |
| avg planning latency ms | 0.295 | 0.289 | 0.302 | 0.013 | 0.005 | 0.018 |
| RAST vs Object List disagreement | 3.041 | 2.980 | 3.084 | 0.104 | 0.044 | 0.015 |
| RAST vs Flat Feature disagreement | 0.024 | 0.022 | 0.028 | 0.006 | 0.003 | 0.118 |
| RAST vs Scene Graph disagreement | 2.042 | 1.968 | 2.140 | 0.172 | 0.072 | 0.035 |
| RAST vs Event-aware disagreement | 0.206 | 0.198 | 0.218 | 0.020 | 0.009 | 0.042 |
| RAST vs Uncertainty-aware disagreement | 0.763 | 0.732 | 0.816 | 0.084 | 0.038 | 0.050 |
| RAST vs Affordance-aware disagreement | 5.981 | 5.934 | 6.024 | 0.090 | 0.037 | 0.006 |
| event-triggered actions | 1.862 | 1.788 | 1.926 | 0.138 | 0.057 | 0.030 |
| uncertainty-triggered actions | 2.915 | 2.886 | 2.954 | 0.068 | 0.029 | 0.010 |
| affordance-triggered actions | 8.510 | 8.492 | 8.534 | 0.042 | 0.018 | 0.002 |
| EvidenceToken avg | 8.838 | 8.831 | 8.846 | 0.015 | 0.006 | 0.001 |
| AffordanceToken avg | 1.016 | 1.014 | 1.018 | 0.004 | 0.002 | 0.002 |
| replay count | 5.000 | 5.000 | 5.000 | 0.000 | 0.000 | 0.000 |

## High-Variance Metrics

| Metric | Range | Coefficient of Variation | Interpretation |
|---|---:|---:|---|
| RAST vs Flat Feature disagreement | 0.006 | 0.118 | sample seed에 따른 subset 구성이 metric에 영향을 준 후보입니다. |
| RAST vs Uncertainty-aware disagreement | 0.084 | 0.050 | sample seed에 따른 subset 구성이 metric에 영향을 준 후보입니다. |
| avg token generation latency ms | 0.017 | 0.046 | sample seed에 따른 subset 구성이 metric에 영향을 준 후보입니다. |
| RAST vs Event-aware disagreement | 0.020 | 0.042 | sample seed에 따른 subset 구성이 metric에 영향을 준 후보입니다. |
| RAST vs Scene Graph disagreement | 0.172 | 0.035 | sample seed에 따른 subset 구성이 metric에 영향을 준 후보입니다. |

## Scenario Coverage Stability

- all-seed scenario intersection: `avoid_required_blocking_path, blocking_relation_without_high_risk, clear_path, event_changes_risk_but_graph_static, far_obstacle, inspect_required_uncertain_path, low_sensor_agreement, narrow_passage, near_obstacle, noisy_position_boundary, object_appears, object_disappears, object_moves, partially_occluded_obstacle, passable_clear_gap, planner_disagreement, relation_near_but_low_risk, risk_increases, risk_without_graph_blocking, target_reachable, target_reachable_affordance, uncertainty_near_path, uncertainty_without_high_risk, unknown_near_path, unknown_uncertain_object`
- partial scenarios: `none`

| Seed | Scenario Count | Scenarios |
|---:|---:|---|
| 7 | 25 | `avoid_required_blocking_path, blocking_relation_without_high_risk, clear_path, event_changes_risk_but_graph_static, far_obstacle, inspect_required_uncertain_path, low_sensor_agreement, narrow_passage, near_obstacle, noisy_position_boundary, object_appears, object_disappears, object_moves, partially_occluded_obstacle, passable_clear_gap, planner_disagreement, relation_near_but_low_risk, risk_increases, risk_without_graph_blocking, target_reachable, target_reachable_affordance, uncertainty_near_path, uncertainty_without_high_risk, unknown_near_path, unknown_uncertain_object` |
| 13 | 25 | `avoid_required_blocking_path, blocking_relation_without_high_risk, clear_path, event_changes_risk_but_graph_static, far_obstacle, inspect_required_uncertain_path, low_sensor_agreement, narrow_passage, near_obstacle, noisy_position_boundary, object_appears, object_disappears, object_moves, partially_occluded_obstacle, passable_clear_gap, planner_disagreement, relation_near_but_low_risk, risk_increases, risk_without_graph_blocking, target_reachable, target_reachable_affordance, uncertainty_near_path, uncertainty_without_high_risk, unknown_near_path, unknown_uncertain_object` |
| 42 | 25 | `avoid_required_blocking_path, blocking_relation_without_high_risk, clear_path, event_changes_risk_but_graph_static, far_obstacle, inspect_required_uncertain_path, low_sensor_agreement, narrow_passage, near_obstacle, noisy_position_boundary, object_appears, object_disappears, object_moves, partially_occluded_obstacle, passable_clear_gap, planner_disagreement, relation_near_but_low_risk, risk_increases, risk_without_graph_blocking, target_reachable, target_reachable_affordance, uncertainty_near_path, uncertainty_without_high_risk, unknown_near_path, unknown_uncertain_object` |

## Interpretation

- seed-to-seed stability는 sampled extended evaluation의 신뢰도를 보기 위한 보조 분석입니다.
- metric variation은 성능 개선/악화가 아니라 sample composition 차이일 수 있습니다.
- 이 결과는 full extended grid exhaustive result가 아닙니다.
- 모든 결과는 WindowsMetadataSim metadata simulator 기반이며 real-world performance claim을 지원하지 않습니다.
