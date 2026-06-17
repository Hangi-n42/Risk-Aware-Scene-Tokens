# RAST Sample-size Convergence Report

이 문서는 sampled extended evaluation에서 sample-size 변화에 따른 metric 안정성과 coverage 품질을 점검합니다.
전체 extended grid exhaustive result가 아니며, sampling reliability check로만 해석해야 합니다.

## Sample-size Sweep Summary

- sweep id: `sample_size_sweep_20260613_010716`
- config path: `configs\windows_eval_suite_extended.yaml`
- sampling mode: `stratified`
- sample sizes: `100, 200, 500`
- seeds: `7, 13, 42`
- total sampled runs: 2400
- failed runs: 0

## Metric Convergence Table

| Sample Size | Metric | Seed Count | Mean | Std | Min | Max | Range | CV | Relative Range |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | success rate | 3 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| 100 | avg near-miss | 3 | 1.770 | 0.256 | 1.560 | 2.130 | 0.570 | 0.144 | 0.322 |
| 100 | avg latency ms | 3 | 0.841 | 0.025 | 0.806 | 0.864 | 0.057 | 0.030 | 0.068 |
| 100 | avg token generation latency ms | 3 | 0.199 | 0.026 | 0.162 | 0.219 | 0.058 | 0.132 | 0.290 |
| 100 | avg planning latency ms | 3 | 0.352 | 0.002 | 0.350 | 0.355 | 0.004 | 0.005 | 0.012 |
| 100 | RAST vs Object List disagreement | 3 | 3.200 | 0.236 | 2.870 | 3.410 | 0.540 | 0.074 | 0.169 |
| 100 | RAST vs Flat Feature disagreement | 3 | 0.023 | 0.033 | 0.000 | 0.070 | 0.070 | 1.414 | 3.000 |
| 100 | RAST vs Scene Graph disagreement | 3 | 1.977 | 0.327 | 1.590 | 2.390 | 0.800 | 0.166 | 0.405 |
| 100 | RAST vs Event-aware disagreement | 3 | 0.173 | 0.087 | 0.080 | 0.290 | 0.210 | 0.504 | 1.212 |
| 100 | RAST vs Uncertainty-aware disagreement | 3 | 0.760 | 0.181 | 0.590 | 1.010 | 0.420 | 0.238 | 0.553 |
| 100 | RAST vs Affordance-aware disagreement | 3 | 5.953 | 0.127 | 5.840 | 6.130 | 0.290 | 0.021 | 0.049 |
| 100 | event-triggered actions | 3 | 1.750 | 0.250 | 1.460 | 2.070 | 0.610 | 0.143 | 0.349 |
| 100 | uncertainty-triggered actions | 3 | 3.023 | 0.113 | 2.870 | 3.140 | 0.270 | 0.037 | 0.089 |
| 100 | affordance-triggered actions | 3 | 8.613 | 0.024 | 8.580 | 8.630 | 0.050 | 0.003 | 0.006 |
| 100 | EvidenceToken avg | 3 | 8.812 | 0.041 | 8.758 | 8.855 | 0.097 | 0.005 | 0.011 |
| 100 | AffordanceToken avg | 3 | 1.027 | 0.003 | 1.025 | 1.031 | 0.006 | 0.003 | 0.006 |
| 100 | decision trace coverage | 3 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| 100 | replay count | 3 | 3.000 | 0.000 | 3.000 | 3.000 | 0.000 | 0.000 | 0.000 |
| 200 | success rate | 3 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| 200 | avg near-miss | 3 | 1.813 | 0.048 | 1.750 | 1.865 | 0.115 | 0.026 | 0.063 |
| 200 | avg latency ms | 3 | 0.907 | 0.025 | 0.889 | 0.942 | 0.053 | 0.027 | 0.059 |
| 200 | avg token generation latency ms | 3 | 0.212 | 0.013 | 0.194 | 0.222 | 0.027 | 0.060 | 0.129 |
| 200 | avg planning latency ms | 3 | 0.384 | 0.019 | 0.370 | 0.411 | 0.040 | 0.050 | 0.105 |
| 200 | RAST vs Object List disagreement | 3 | 3.102 | 0.064 | 3.020 | 3.175 | 0.155 | 0.020 | 0.050 |
| 200 | RAST vs Flat Feature disagreement | 3 | 0.023 | 0.021 | 0.000 | 0.050 | 0.050 | 0.881 | 2.143 |
| 200 | RAST vs Scene Graph disagreement | 3 | 1.993 | 0.117 | 1.845 | 2.130 | 0.285 | 0.059 | 0.143 |
| 200 | RAST vs Event-aware disagreement | 3 | 0.208 | 0.010 | 0.195 | 0.220 | 0.025 | 0.049 | 0.120 |
| 200 | RAST vs Uncertainty-aware disagreement | 3 | 0.723 | 0.120 | 0.565 | 0.855 | 0.290 | 0.166 | 0.401 |
| 200 | RAST vs Affordance-aware disagreement | 3 | 5.947 | 0.052 | 5.905 | 6.020 | 0.115 | 0.009 | 0.019 |
| 200 | event-triggered actions | 3 | 1.793 | 0.121 | 1.675 | 1.960 | 0.285 | 0.068 | 0.159 |
| 200 | uncertainty-triggered actions | 3 | 2.925 | 0.057 | 2.845 | 2.975 | 0.130 | 0.020 | 0.044 |
| 200 | affordance-triggered actions | 3 | 8.508 | 0.047 | 8.475 | 8.575 | 0.100 | 0.006 | 0.012 |
| 200 | EvidenceToken avg | 3 | 8.839 | 0.033 | 8.811 | 8.886 | 0.074 | 0.004 | 0.008 |
| 200 | AffordanceToken avg | 3 | 1.016 | 0.006 | 1.011 | 1.025 | 0.014 | 0.006 | 0.013 |
| 200 | decision trace coverage | 3 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| 200 | replay count | 3 | 3.000 | 0.000 | 3.000 | 3.000 | 0.000 | 0.000 | 0.000 |
| 500 | success rate | 3 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| 500 | avg near-miss | 3 | 1.810 | 0.060 | 1.726 | 1.858 | 0.132 | 0.033 | 0.073 |
| 500 | avg latency ms | 3 | 0.912 | 0.034 | 0.865 | 0.946 | 0.081 | 0.037 | 0.088 |
| 500 | avg token generation latency ms | 3 | 0.211 | 0.014 | 0.191 | 0.222 | 0.032 | 0.068 | 0.150 |
| 500 | avg planning latency ms | 3 | 0.390 | 0.012 | 0.374 | 0.402 | 0.029 | 0.031 | 0.073 |
| 500 | RAST vs Object List disagreement | 3 | 3.041 | 0.044 | 2.980 | 3.084 | 0.104 | 0.015 | 0.034 |
| 500 | RAST vs Flat Feature disagreement | 3 | 0.024 | 0.003 | 0.022 | 0.028 | 0.006 | 0.118 | 0.250 |
| 500 | RAST vs Scene Graph disagreement | 3 | 2.042 | 0.072 | 1.968 | 2.140 | 0.172 | 0.035 | 0.084 |
| 500 | RAST vs Event-aware disagreement | 3 | 0.206 | 0.009 | 0.198 | 0.218 | 0.020 | 0.042 | 0.097 |
| 500 | RAST vs Uncertainty-aware disagreement | 3 | 0.763 | 0.038 | 0.732 | 0.816 | 0.084 | 0.050 | 0.110 |
| 500 | RAST vs Affordance-aware disagreement | 3 | 5.981 | 0.037 | 5.934 | 6.024 | 0.090 | 0.006 | 0.015 |
| 500 | event-triggered actions | 3 | 1.862 | 0.057 | 1.788 | 1.926 | 0.138 | 0.030 | 0.074 |
| 500 | uncertainty-triggered actions | 3 | 2.915 | 0.029 | 2.886 | 2.954 | 0.068 | 0.010 | 0.023 |
| 500 | affordance-triggered actions | 3 | 8.510 | 0.018 | 8.492 | 8.534 | 0.042 | 0.002 | 0.005 |
| 500 | EvidenceToken avg | 3 | 8.838 | 0.006 | 8.831 | 8.846 | 0.015 | 0.001 | 0.002 |
| 500 | AffordanceToken avg | 3 | 1.016 | 0.002 | 1.014 | 1.018 | 0.004 | 0.002 | 0.004 |
| 500 | decision trace coverage | 3 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| 500 | replay count | 3 | 3.000 | 0.000 | 3.000 | 3.000 | 0.000 | 0.000 | 0.000 |

## Sampling Quality Score

| Sample Size | Coverage Score | Balance Score | Stability Score | Overall Sampling Quality Score |
|---:|---:|---:|---:|---:|
| 100 | 0.900 | 0.731 | 0.828 | 0.828 |
| 200 | 1.000 | 0.836 | 0.915 | 0.925 |
| 500 | 1.000 | 0.901 | 0.972 | 0.962 |

## Coverage by Sample Size

| Sample Size | Axis | Avg Coverage Rate | Avg Balance |
|---:|---|---:|---:|
| 100 | `apply_policy` | 0.571 | 0.000 |
| 100 | `blocking_relation_threshold` | 1.000 | 0.830 |
| 100 | `classification_uncertainty_threshold` | 1.000 | 0.961 |
| 100 | `distance_noise_std` | 1.000 | 0.888 |
| 100 | `event_policy_variant` | 0.333 | 0.267 |
| 100 | `near_agent_relation_threshold` | 1.000 | 0.797 |
| 100 | `near_miss_threshold` | 1.000 | 0.924 |
| 100 | `near_path_relation_threshold` | 1.000 | 0.901 |
| 100 | `occlusion_ratio_threshold` | 1.000 | 0.817 |
| 100 | `position_noise_std` | 1.000 | 0.879 |
| 100 | `position_variance_threshold` | 1.000 | 0.735 |
| 100 | `risk_threshold` | 1.000 | 0.971 |
| 100 | `scenario` | 1.000 | 1.000 |
| 100 | `sensor_agreement_threshold` | 1.000 | 0.809 |
| 100 | `update_mode` | 0.500 | 0.000 |
| 100 | `visibility_flip_prob` | 1.000 | 0.912 |
| 200 | `apply_policy` | 1.000 | 0.500 |
| 200 | `blocking_relation_threshold` | 1.000 | 0.891 |
| 200 | `classification_uncertainty_threshold` | 1.000 | 0.895 |
| 200 | `distance_noise_std` | 1.000 | 0.952 |
| 200 | `event_policy_variant` | 1.000 | 0.800 |
| 200 | `near_agent_relation_threshold` | 1.000 | 0.931 |
| 200 | `near_miss_threshold` | 1.000 | 0.907 |
| 200 | `near_path_relation_threshold` | 1.000 | 0.918 |
| 200 | `occlusion_ratio_threshold` | 1.000 | 0.923 |
| 200 | `position_noise_std` | 1.000 | 0.929 |
| 200 | `position_variance_threshold` | 1.000 | 0.765 |
| 200 | `risk_threshold` | 1.000 | 0.985 |
| 200 | `scenario` | 1.000 | 1.000 |
| 200 | `sensor_agreement_threshold` | 1.000 | 0.870 |
| 200 | `update_mode` | 1.000 | 0.143 |
| 200 | `visibility_flip_prob` | 1.000 | 0.974 |
| 500 | `apply_policy` | 1.000 | 0.667 |
| 500 | `blocking_relation_threshold` | 1.000 | 0.909 |
| 500 | `classification_uncertainty_threshold` | 1.000 | 0.934 |
| 500 | `distance_noise_std` | 1.000 | 0.971 |
| 500 | `event_policy_variant` | 1.000 | 0.912 |
| 500 | `near_agent_relation_threshold` | 1.000 | 0.915 |
| 500 | `near_miss_threshold` | 1.000 | 0.926 |
| 500 | `near_path_relation_threshold` | 1.000 | 0.922 |
| 500 | `occlusion_ratio_threshold` | 1.000 | 0.947 |
| 500 | `position_noise_std` | 1.000 | 0.982 |
| 500 | `position_variance_threshold` | 1.000 | 0.854 |
| 500 | `risk_threshold` | 1.000 | 0.994 |
| 500 | `scenario` | 1.000 | 1.000 |
| 500 | `sensor_agreement_threshold` | 1.000 | 0.961 |
| 500 | `update_mode` | 1.000 | 0.538 |
| 500 | `visibility_flip_prob` | 1.000 | 0.982 |

## High-Variance Metrics by Sample Size

| Sample Size | Metric | Range | CV | Interpretation |
|---:|---|---:|---:|---|
| 100 | RAST vs Flat Feature disagreement | 0.070 | 1.414 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 100 | RAST vs Event-aware disagreement | 0.210 | 0.504 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 100 | RAST vs Uncertainty-aware disagreement | 0.420 | 0.238 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 100 | RAST vs Scene Graph disagreement | 0.800 | 0.166 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 100 | avg near-miss | 0.570 | 0.144 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 200 | RAST vs Flat Feature disagreement | 0.050 | 0.881 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 200 | RAST vs Uncertainty-aware disagreement | 0.290 | 0.166 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 200 | event-triggered actions | 0.285 | 0.068 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 200 | avg token generation latency ms | 0.027 | 0.060 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 200 | RAST vs Scene Graph disagreement | 0.285 | 0.059 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 500 | RAST vs Flat Feature disagreement | 0.006 | 0.118 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 500 | avg token generation latency ms | 0.032 | 0.068 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 500 | RAST vs Uncertainty-aware disagreement | 0.084 | 0.050 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 500 | RAST vs Event-aware disagreement | 0.020 | 0.042 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |
| 500 | avg latency ms | 0.081 | 0.037 | sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |

## Interpretation

- sample-size convergence는 sampled extended evaluation의 대표성/안정성을 보기 위한 보조 분석입니다.
- full extended grid exhaustive result가 아닙니다.
- sampling quality score는 coverage, balance, seed stability를 요약하는 heuristic score입니다.
- score가 높다고 RAST 또는 특정 planner의 task performance가 좋다는 뜻은 아닙니다.
- metric stability가 높아도 real-world 성능 주장을 지원하지 않습니다.
- 모든 결과는 WindowsMetadataSim metadata simulator 기반입니다.
