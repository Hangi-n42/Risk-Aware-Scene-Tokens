# RAST Evaluation Comparison Report

이 문서는 baseline evaluation run과 sampled extended evaluation run을 비교합니다.
비교 목적은 성능 우수성 판단이 아니라 sensitivity exploration과 coverage 확인입니다.

## Evaluation Comparison Summary

- baseline run id: `windows_eval_suite_20260612_162821`
- candidate run id: `windows_eval_suite_20260612_224531`
- baseline total runs: 900
- candidate total runs: 500
- baseline failed runs: 0
- candidate failed runs: 0
- candidate sampling mode: `stratified`
- candidate sample size: `500`
- candidate sample seed: `42`
- candidate가 full extended grid가 아니라 sampled extended result라는 전제로 해석합니다.

## Metric Comparison

| Metric | Baseline | Candidate | Delta |
|---|---:|---:|---:|
| success rate | 1.000 | 1.000 | 0.000 |
| avg near-miss | 3.151 | 1.844 | -1.307 |
| avg latency ms | 0.663 | 0.889 | 0.226 |
| avg token generation latency ms | 0.162 | 0.217 | 0.056 |
| avg planning latency ms | 0.300 | 0.370 | 0.071 |
| RAST vs Object List disagreement | 4.122 | 2.946 | -1.176 |
| RAST vs Flat Feature disagreement | 0.124 | 0.022 | -0.102 |
| RAST vs Scene Graph disagreement | 2.811 | 1.888 | -0.923 |
| RAST vs Event-aware disagreement | 0.153 | 0.198 | 0.045 |
| RAST vs Uncertainty-aware disagreement | 0.431 | 0.752 | 0.321 |
| RAST vs Affordance-aware disagreement | 5.720 | 5.950 | 0.230 |
| event-triggered actions | 0.511 | 1.856 | 1.345 |
| uncertainty-triggered actions | 2.438 | 2.838 | 0.400 |
| affordance-triggered actions | 9.080 | 8.518 | -0.562 |
| EvidenceToken avg | 8.614 | 8.829 | 0.215 |

| Replay Metric | Baseline | Candidate |
|---|---:|---:|
| replay count | 0 | 10 |

## Scenario Coverage Comparison

- baseline scenario count: 25
- candidate scenario count: 25
- candidate scenarios: `avoid_required_blocking_path, blocking_relation_without_high_risk, clear_path, event_changes_risk_but_graph_static, far_obstacle, inspect_required_uncertain_path, low_sensor_agreement, narrow_passage, near_obstacle, noisy_position_boundary, object_appears, object_disappears, object_moves, partially_occluded_obstacle, passable_clear_gap, planner_disagreement, relation_near_but_low_risk, risk_increases, risk_without_graph_blocking, target_reachable, target_reachable_affordance, uncertainty_near_path, uncertainty_without_high_risk, unknown_near_path, unknown_uncertain_object`
- missing baseline scenarios in candidate: `none`

## Interpretation

- sampled extended result는 exhaustive grid result가 아닙니다.
- sampling 결과는 sample seed와 sample size에 의존합니다.
- observed metric difference는 성능 개선/악화 증거가 아니라 sensitivity exploration입니다.
- 모든 결과는 WindowsMetadataSim metadata simulator 기반입니다.
- 실제 perception-bound extractor, real robot, 또는 real simulator 성능을 대변하지 않습니다.
- candidate coverage artifact: `docs\sampling_coverage_report.md`
- candidate seed stability artifact: `docs\seed_stability_report.md`
- candidate sample-size convergence artifact: `docs\sample_size_convergence_report.md`

## Inputs

- baseline_results: `runs\windows_eval_suite\windows_eval_suite_20260612_162821\aggregate_results.csv`
- baseline_summary: `runs\windows_eval_suite\windows_eval_suite_20260612_162821\aggregate_summary.csv`
- candidate_results: `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\aggregate_results.csv`
- candidate_summary: `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\aggregate_summary.csv`
- baseline_metadata: `not provided`
- candidate_metadata: `runs\windows_eval_suite_extended\windows_eval_suite_20260612_224531\suite_metadata.json`
- candidate_coverage: `docs\sampling_coverage_report.md`
- candidate_seed_stability: `docs\seed_stability_report.md`
- candidate_sample_size_convergence: `docs\sample_size_convergence_report.md`
