# RAST Sampling Coverage Report

이 문서는 sampled extended evaluation의 축별 포함 여부를 점검합니다.
missing 또는 underrepresented 값은 성능 문제가 아니라 sampling coverage 문제로 해석해야 합니다.

## Context

- suite_run_id: `windows_eval_suite_20260612_231908`
- results: `runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_42\windows_eval_suite_20260612_231908\aggregate_results.csv`
- metadata: `runs\windows_eval_suite_extended_seed_sweep\seed_sweep_20260612_231815\seed_42\windows_eval_suite_20260612_231908\suite_metadata.json`
- analyzed rows: 500

## Axis Coverage

| Axis | Row Scope | Observed Values | Observed Counts | Coverage Rate | Missing Values | Underrepresented Values |
|---|---|---|---|---:|---|---|
| `scenario` | all rows (500 rows) | `avoid_required_blocking_path, blocking_relation_without_high_risk, clear_path, event_changes_risk_but_graph_static, far_obstacle, inspect_required_uncertain_path, low_sensor_agreement, narrow_passage, near_obstacle, noisy_position_boundary, object_appears, object_disappears, object_moves, partially_occluded_obstacle, passable_clear_gap, planner_disagreement, relation_near_but_low_risk, risk_increases, risk_without_graph_blocking, target_reachable, target_reachable_affordance, uncertainty_near_path, uncertainty_without_high_risk, unknown_near_path, unknown_uncertain_object` | `{"avoid_required_blocking_path": 20, "blocking_relation_without_high_risk": 20, "clear_path": 20, "event_changes_risk_but_graph_static": 20, "far_obstacle": 20, "inspect_required_uncertain_path": 20, "low_sensor_agreement": 20, "narrow_passage": 20, "near_obstacle": 20, "noisy_position_boundary": 20, "object_appears": 20, "object_disappears": 20, "object_moves": 20, "partially_occluded_obstacle": 20, "passable_clear_gap": 20, "planner_disagreement": 20, "relation_near_but_low_risk": 20, "risk_increases": 20, "risk_without_graph_blocking": 20, "target_reachable": 20, "target_reachable_affordance": 20, "uncertainty_near_path": 20, "uncertainty_without_high_risk": 20, "unknown_near_path": 20, "unknown_uncertain_object": 20}` | 1.000 | `none` | `none` |
| `apply_policy` | all rows (500 rows) | `affordance_aware_rast, event_aware_rast, flat_feature, object_list, rast, scene_graph, uncertainty_aware_rast` | `{"affordance_aware_rast": 75, "event_aware_rast": 50, "flat_feature": 75, "object_list": 75, "rast": 75, "scene_graph": 75, "uncertainty_aware_rast": 75}` | 1.000 | `none` | `none` |
| `update_mode` | all rows (500 rows) | `full_recompute, incremental` | `{"full_recompute": 325, "incremental": 175}` | 1.000 | `none` | `none` |
| `event_policy_variant` | `apply_policy=event_aware_rast` (50 rows) | `full, logging_only, no_object_appeared, no_object_disappeared, no_object_moved, no_risk_changed` | `{"full": 9, "logging_only": 9, "no_object_appeared": 8, "no_object_disappeared": 8, "no_object_moved": 8, "no_risk_changed": 8}` | 1.000 | `none` | `none` |
| `risk_threshold` | all rows (500 rows) | `1, 1.5, 2` | `{"1": 167, "1.5": 166, "2": 167}` | 1.000 | `none` | `none` |
| `near_miss_threshold` | all rows (500 rows) | `0.75, 1` | `{"0.75": 243, "1": 257}` | 1.000 | `none` | `none` |
| `near_agent_relation_threshold` | all rows (500 rows) | `1, 1.5` | `{"1": 273, "1.5": 227}` | 1.000 | `none` | `none` |
| `near_path_relation_threshold` | all rows (500 rows) | `0.5, 0.75` | `{"0.5": 232, "0.75": 268}` | 1.000 | `none` | `none` |
| `blocking_relation_threshold` | all rows (500 rows) | `0.35, 0.5` | `{"0.35": 236, "0.5": 264}` | 1.000 | `none` | `none` |
| `classification_uncertainty_threshold` | all rows (500 rows) | `0.4, 0.6` | `{"0.4": 245, "0.6": 255}` | 1.000 | `none` | `none` |
| `position_variance_threshold` | all rows (500 rows) | `0.03, 0.05` | `{"0.03": 231, "0.05": 269}` | 1.000 | `none` | `none` |
| `occlusion_ratio_threshold` | all rows (500 rows) | `0.3, 0.5` | `{"0.3": 233, "0.5": 267}` | 1.000 | `none` | `none` |
| `sensor_agreement_threshold` | all rows (500 rows) | `0.5, 0.7` | `{"0.5": 256, "0.7": 244}` | 1.000 | `none` | `none` |
| `position_noise_std` | all rows (500 rows) | `0, 0.02, 0.05` | `{"0": 165, "0.02": 167, "0.05": 168}` | 1.000 | `none` | `none` |
| `distance_noise_std` | all rows (500 rows) | `0, 0.02, 0.05` | `{"0": 171, "0.02": 167, "0.05": 162}` | 1.000 | `none` | `none` |
| `visibility_flip_prob` | all rows (500 rows) | `0, 0.05` | `{"0": 251, "0.05": 249}` | 1.000 | `none` | `none` |

## Interpretation

- expected values를 metadata에서 알 수 없는 축은 observed distribution만 표시합니다.
- coverage rate는 metadata/config에서 expected value list를 확인할 수 있는 축에만 계산합니다.
- 이 보고서는 sampled extended result가 full extended grid를 대체하지 않는다는 점을 확인하기 위한 보조 artifact입니다.
- WindowsMetadataSim metadata simulator 기반 결과이며 real-world performance claim을 지원하지 않습니다.
