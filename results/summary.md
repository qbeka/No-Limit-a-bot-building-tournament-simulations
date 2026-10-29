# generated summary

made by `python -m castle report` from the files in this folder.

## replay checks against the recorded outputs

- game 1: `pools_g_max_diff_vs_recorded` = `0.0`
- game 1: `scenario_g_max_diff_vs_recorded` = `8.881784197001252e-16`
- game 1: `objective_allocations_match_recorded` = `True`
- game 1: `objective_values_max_diff_vs_recorded` = `1.7763568394002505e-15`
- game 1: `dp_mean_optimum` = `[3, 5, 27, 2, 63]`
- game 1: `dp_matches_enumeration` = `True`
- game 1: `dp_value_minus_enumeration` = `-1.7763568394002505e-15`
- game 2: `pools_match_recorded` = `True`
- game 2: `first_search_best_matches_recorded` = `True`
- game 2: `adaptive_best_matches_recorded` = `True`
- game 2: `first_search_vs_recorded` = `{'kept_by_both': 262, 'only_in_replay': [], 'only_in_recorded': [[18, 29, 47, 6, 0]], 'score_max_diff_on_common': 0.0}`
- game 2: `adaptive_search_vs_recorded` = `{'kept_by_both': 722, 'only_in_replay': [[2, 16, 0, 0, 82], [6, 34, 2, 57, 1], [6, 34, 6, 54, 0]], 'only_in_recorded': [[19, 1, 0, 3, 77], [21, 28, 50, 1, 0]], 'score_max_diff_on_common': 0.0}`
- game 2: `adaptive_weights_max_diff_vs_recorded` = `0.0`
- game 2: `table_vs_direct_scorer_diff` = `0.0`
- fresh check: `mean_max_diff_vs_recorded` = `0.0`
- fresh check: `difference_max_diff_vs_recorded` = `0.0`
- fresh check: `wins_2_and_4_rate_diff` = `0.0`

## game 1 objectives (exhaustive, all 4,598,126 allocations)

| objective | allocation | mean | worst scenario | worst regret |
|---|---|---:|---:|---:|
| mean_score | [3, 5, 27, 2, 63] | 9.3542 | 8.8188 | 0.7448 |
| minimum_worst_scenario_regret | [6, 4, 27, 1, 62] | 9.2230 | 8.9061 | 0.6575 |
| maximum_minimum_scenario_score | [6, 5, 28, 1, 60] | 9.1440 | 8.9275 | 0.8178 |
| mean_score_minus_half_regret | [3, 5, 27, 2, 63] | 9.3542 | 8.8188 | 0.7448 |

chosen [3, 5, 27, 2, 63]: castle contributions [0.6331, 1.2316, 2.2991, 0.4327, 4.7577], add one [0.0589, 0.0822, 0.0733, 0.0765, 0.0592], remove one [0.0939, 0.0802, 0.1129, 0.1167, 0.1118]

## game 2 fresh check (300,000 new groups, fixed pools)

| allocation | payout | 95% ci | sole first | tied first | chosen minus this |
|---|---:|---|---:|---:|---|
| [2, 35, 2, 59, 2] | 6.9417 | [6.9302, 6.9533] | 0.668 | 0.073 | -0.0004 [-0.0021, 0.0012] |
| [2, 34, 3, 59, 2] | 6.9413 | [6.9298, 6.9528] | 0.665 | 0.076 |  |
| [1, 1, 1, 1, 96] | 5.8466 | [5.8375, 5.8557] | 0.352 | 0.113 | 1.0947 [1.0796, 1.1098] |
| [0, 0, 0, 0, 100] | 5.6758 | [5.6677, 5.6839] | 0.286 | 0.138 | 1.2655 [1.2510, 1.2801] |
| [17, 31, 51, 1, 0] | 5.0761 | [5.0641, 5.0881] | 0.420 | 0.043 | 1.8652 [1.8475, 1.8830] |
| [3, 5, 27, 2, 63] | 4.0690 | [4.0569, 4.0811] | 0.285 | 0.058 | 2.8723 [2.8548, 2.8898] |
| [0, 0, 0, 49, 51] | 3.8418 | [3.8315, 3.8520] | 0.209 | 0.018 | 3.0995 [3.0857, 3.1133] |
| [0, 0, 33, 33, 34] | 2.4945 | [2.4851, 2.5040] | 0.106 | 0.026 | 4.4467 [4.4328, 4.4607] |
| [20, 20, 20, 20, 20] | 2.4283 | [2.4183, 2.4383] | 0.102 | 0.093 | 4.5130 [4.4988, 4.5272] |
| [7, 13, 20, 27, 33] | 2.0248 | [2.0155, 2.0341] | 0.090 | 0.022 | 4.9165 [4.9023, 4.9307] |

chosen wins castles 2 and 4 outright in 0.77274 of groups; mean payout then 8.3881, minimum 4.0.
outright win rate per castle: [0.1052, 0.9593, 0.0424, 0.8065, 0.0294]

## game 1 robustness (exact)

| experiment | chosen | exact optimum | optimum score | chosen regret | chosen rank among baselines |
|---|---:|---|---:|---:|---:|
| original | 9.3542 | [3, 5, 27, 2, 63] | 9.3542 | 0.0000 | 1 of 18 |
| new pools seed 101 | 9.2956 | [3, 4, 27, 3, 63] | 9.3022 | 0.0067 | 1 of 18 |
| new pools seed 202 | 9.3511 | [3, 4, 27, 3, 63] | 9.3608 | 0.0096 | 1 of 18 |
| new pools seed 303 | 9.3768 | [3, 5, 27, 2, 63] | 9.3768 | 0.0000 | 1 of 18 |
| noise x0.5 | 9.5423 | [3, 4, 27, 3, 63] | 9.5451 | 0.0027 | 1 of 18 |
| noise x2.0 | 9.2874 | [3, 4, 28, 2, 63] | 9.2988 | 0.0115 | 1 of 18 |
| exact templates x0.5 | 9.1873 | [2, 6, 28, 2, 62] | 9.2133 | 0.0260 | 1 of 18 |
| exact templates x1.5 | 9.5665 | [3, 4, 27, 3, 63] | 9.5737 | 0.0072 | 1 of 18 |
| tilt to equal | 8.6499 | [2, 4, 27, 41, 26] | 9.8761 | 1.2262 | 2 of 18 |
| tilt to weighted | 8.7601 | [1, 15, 1, 37, 46] | 9.3016 | 0.5414 | 3 of 18 |
| tilt to high3 | 9.2178 | [3, 7, 3, 41, 46] | 10.3597 | 1.1419 | 2 of 18 |
| tilt to high2 | 10.0135 | [7, 14, 8, 6, 65] | 10.1310 | 0.1175 | 1 of 18 |
| tilt to diverse | 9.1103 | [1, 1, 2, 38, 58] | 9.2105 | 0.1001 | 1 of 18 |
| tilt to meta1 | 9.9090 | [7, 17, 6, 5, 65] | 10.0436 | 0.1346 | 1 of 18 |
| tilt to meta2 | 9.2252 | [8, 10, 8, 7, 67] | 10.2287 | 1.0035 | 1 of 18 |
| copies 0.0 | 9.3542 | [3, 5, 27, 2, 63] | 9.3542 | 0.0000 | 1 of 18 |
| copies 0.1 | 9.1756 | [7, 16, 5, 5, 67] | 9.4040 | 0.2284 | 1 of 18 |
| copies 0.2 | 8.9970 | [7, 15, 5, 6, 67] | 9.6624 | 0.6655 | 2 of 18 |
| copies 0.3 | 8.8184 | [7, 14, 5, 6, 68] | 9.9334 | 1.1150 | 2 of 18 |
| copies 0.4 | 8.6397 | [7, 14, 5, 6, 68] | 10.2121 | 1.5724 | 2 of 18 |
| copies 0.5 | 8.4611 | [8, 11, 5, 7, 69] | 10.4986 | 2.0375 | 2 of 18 |
| counters 0.0 | 9.3542 | [3, 5, 27, 2, 63] | 9.3542 | 0.0000 | 1 of 18 |
| counters 0.1 | 9.0322 | [7, 16, 5, 6, 66] | 9.4049 | 0.3727 | 1 of 18 |
| counters 0.2 | 8.7102 | [7, 16, 5, 6, 66] | 9.6569 | 0.9466 | 1 of 18 |
| counters 0.3 | 8.3883 | [7, 14, 5, 7, 67] | 9.9253 | 1.5370 | 1 of 18 |
| counters 0.4 | 8.0663 | [7, 13, 5, 7, 68] | 10.2010 | 2.1348 | 1 of 18 |
| counters 0.5 | 7.7443 | [8, 11, 5, 8, 68] | 10.4907 | 2.7464 | 2 of 18 |

## game 2 robustness (paired, same groups for every allocation)

| experiment | chosen payout | best tested | chosen minus best other, 95% ci | search found |
|---|---:|---|---|---|
| original | 6.9562 | game2_near_tie | game2_near_tie: -0.0019 [-0.0045, 0.0007] unresolved | [2, 34, 3, 59, 2] |
| new pools seed 101 | 6.9539 | chosen | game2_near_tie: 0.0012 [-0.0014, 0.0037] unresolved | [2, 34, 3, 59, 2] |
| new pools seed 202 | 6.9437 | chosen | game2_near_tie: 0.0001 [-0.0025, 0.0027] unresolved | [19, 0, 0, 0, 81] |
| new pools seed 303 | 6.9280 | game2_1_and_5 | game2_1_and_5: -0.0150 [-0.0414, 0.0115] unresolved | [19, 0, 0, 0, 81] |
| noise x0.5 | 7.0779 | chosen | game2_runner_up: 0.0220 [0.0192, 0.0248] chosen ahead | [2, 34, 3, 59, 2] |
| noise x2.0 | 6.8459 | searched_best | searched_best: -0.0880 [-0.0941, -0.0819] chosen behind | [1, 36, 1, 61, 1] |
| exact templates x0.5 | 6.8708 | game2_near_tie | game2_near_tie: -0.0169 [-0.0199, -0.0140] chosen behind | [19, 0, 0, 0, 81] |
| exact templates x1.5 | 7.0416 | chosen | game2_runner_up: 0.0108 [0.0085, 0.0132] chosen ahead | [2, 34, 3, 59, 2] |
| tilt to balanced | 7.2695 | searched_best | searched_best: -0.0777 [-0.0833, -0.0721] chosen behind | [0, 34, 0, 66, 0] |
| tilt to high3 | 7.4491 | searched_best | searched_best: -0.1707 [-0.1752, -0.1662] chosen behind | [7, 34, 0, 59, 0] |
| tilt to high2 | 7.3978 | game2_1_and_5 | game2_1_and_5: -0.2838 [-0.3050, -0.2626] chosen behind | [19, 0, 0, 0, 81] |
| tilt to one_big | 5.9744 | searched_best | searched_best: -1.6439 [-1.6683, -1.6196] chosen behind | [11, 32, 55, 2, 0] |
| tilt to split_small | 6.7363 | searched_best | searched_best: -0.4626 [-0.4871, -0.4381] chosen behind | [15, 31, 54, 0, 0] |
| tilt to diverse | 6.1107 | game2_1_and_5 | game2_1_and_5: -0.3529 [-0.3817, -0.3242] chosen behind | [19, 0, 0, 0, 81] |
| tilt to low_castles | 8.0587 | searched_best | searched_best: -0.1476 [-0.1530, -0.1421] chosen behind | [0, 36, 0, 60, 4] |
| low_castles 0.0 | 6.3737 | searched_best | searched_best: -1.2718 [-1.2954, -1.2482] chosen behind | [17, 30, 52, 1, 0] |
| low_castles 0.1 | 6.6535 | searched_best | searched_best: -0.1223 [-0.1466, -0.0980] chosen behind | [12, 33, 55, 0, 0] |
| low_castles 0.2 | 6.9558 | game2_runner_up | game2_runner_up: -0.0085 [-0.0112, -0.0057] chosen behind | [1, 34, 1, 63, 1] |
| low_castles 0.3 | 7.2312 | searched_best | searched_best: -0.0273 [-0.0319, -0.0227] chosen behind | [1, 35, 1, 61, 2] |
| low_castles 0.4 | 7.5246 | searched_best | searched_best: -0.0653 [-0.0703, -0.0603] chosen behind | [0, 35, 1, 61, 3] |
| low_castles 0.5 | 7.7810 | searched_best | searched_best: -0.1055 [-0.1111, -0.1000] chosen behind | [0, 36, 0, 60, 4] |
| copies 0.0 | 6.9562 | game2_near_tie | game2_near_tie: -0.0019 [-0.0045, 0.0007] unresolved | [2, 34, 3, 59, 2] |
| copies 0.1 | 5.7824 | searched_best | searched_best: -0.9919 [-1.0075, -0.9764] chosen behind | [0, 36, 0, 63, 1] |
| copies 0.2 | 4.8246 | searched_best | searched_best: -1.8843 [-1.9031, -1.8654] chosen behind | [0, 37, 0, 63, 0] |
| copies 0.3 | 4.0271 | searched_best | searched_best: -2.7434 [-2.7681, -2.7187] chosen behind | [6, 37, 54, 0, 3] |
| copies 0.4 | 3.3953 | searched_best | searched_best: -3.6375 [-3.6604, -3.6147] chosen behind | [6, 37, 54, 0, 3] |
| copies 0.5 | 2.9009 | searched_best | searched_best: -4.3812 [-4.4019, -4.3604] chosen behind | [6, 37, 54, 0, 3] |
| counters 0.0 | 6.9562 | game2_near_tie | game2_near_tie: -0.0019 [-0.0045, 0.0007] unresolved | [2, 34, 3, 59, 2] |
| counters 0.1 | 5.7686 | game2_1_and_5 | game2_1_and_5: -1.1170 [-1.1444, -1.0895] chosen behind | [0, 36, 1, 63, 0] |
| counters 0.2 | 4.7693 | game2_1_and_5 | game2_1_and_5: -2.1050 [-2.1323, -2.0777] chosen behind | [19, 0, 0, 0, 81] |
| counters 0.3 | 3.9198 | game2_1_and_5 | game2_1_and_5: -2.9790 [-3.0057, -2.9523] chosen behind | [19, 0, 0, 0, 81] |
| counters 0.4 | 3.2033 | game2_1_and_5 | game2_1_and_5: -3.7662 [-3.7917, -3.7408] chosen behind | [19, 0, 0, 0, 81] |
| counters 0.5 | 2.6284 | game2_1_and_5 | game2_1_and_5: -4.4400 [-4.4639, -4.4161] chosen behind | [19, 0, 0, 0, 81] |
