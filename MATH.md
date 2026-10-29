# The math behind the two allocations

Each allocation is five nonnegative integers `x = (x_1, ..., x_5)` that total 100. Castle `i` is worth `v_i = i`, so all castles together are worth 15 points.

The rules settle what counts as a good allocation. The opponent model settles which allocation is best. No answer here holds independent of the opponent model. Every opponent used below is synthetic. They come from the templates and random draws in `config.toml`, which were copied from the original scripts.

## Exact arithmetic

A castle can be split between 1, 2, 3 or 4 tied bidders. Since 12 is divisible by every one of those counts, the code stores all scores as **12 × castle points**. Every split is then an integer, ties between players' scores are detected exactly, and the payout table never has a rounding error (`castle/scoring.py`).

## Game 1: one opponent, average castle points

### The objective is additive

Let `Y_i` be the opponent's bid on castle `i`, with `p_i(k) = P(Y_i = k)`. Our bid `x_i` wins `v_i` when it is higher, half of `v_i` on a tie, and nothing otherwise. The expected points from castle `i` are therefore

```
g_i(k) = v_i * ( P(Y_i < k) + 0.5 * P(Y_i = k) )
```

and the expected score is

```
E[score(x)] = sum_i g_i(x_i).
```

The opponent's five bids are dependent, since they share one budget. That doesn't matter here: linearity of expectation holds for dependent variables too, so only the five **marginal** distributions enter. `tests/test_castle.py::test_independent_bids_give_the_same_expectation` checks this. It shuffles each castle's bids across opponents and shows the expected score doesn't change.

The model is a mixture of opponent families. Mixing families mixes their marginals, so the `g` for scenario `s` is `sum_f w_sf * g_f`. That is `np.einsum("sf,fij->sij", ...)` in the code. The study averages the six scenarios equally, so the objective is the `g` of the averaged model.

### The value of one more soldier

Raising a bid from `k` to `k+1` changes the outcome against only two kinds of opponent. One who bid exactly `k` turns from a tie into a loss for them, and we gain `v_i / 2`. One who bid `k+1` turns from a win for them into a tie, and we gain another `v_i / 2`. Every other opponent's result stays the same. So

```
g_i(k+1) - g_i(k) = 0.5 * v_i * ( p_i(k) + p_i(k+1) ).
```

An extra soldier only pays off at bid levels many opponents actually use. A castle's value alone doesn't make it a good investment: a valuable castle can be too contested to win cheaply.

### The budget forces trade-offs

Every soldier has to come from another castle. Moving one from castle `j` to castle `i` changes the score by

```
Δ = [ g_i(x_i + 1) - g_i(x_i) ]  -  [ g_j(x_j) - g_j(x_j - 1) ].
```

For the chosen allocation `[3, 5, 27, 2, 63]`, under the averaged original model (`results/game1/summary.json`):

| castle | bid | expected points | gain from +1 | loss from −1 |
|---|---:|---:|---:|---:|
| 1 | 3 | 0.6331 | 0.0589 | 0.0939 |
| 2 | 5 | 1.2316 | 0.0822 | 0.0802 |
| 3 | 27 | 2.2991 | 0.0733 | 0.1129 |
| 4 | 2 | 0.4327 | 0.0765 | 0.1167 |
| 5 | 63 | 4.7577 | 0.0592 | 0.1118 |
| total | 100 | **9.3542** | | |

The largest gain anywhere is 0.0822 (castle 2). The smallest loss on any other castle is 0.0939 (castle 1). So every one-soldier move lowers the score. For example, moving a soldier from castle 5 to castle 4 gains 0.0765 but loses 0.1118.

That only shows the allocation is a *local* optimum. The functions `g_i` are not concave: their gains spike wherever opponents' bids cluster. Moving several soldiers at once can therefore pay off even when every single-soldier move loses. Local checks prove nothing global.

### An exact solver

Let `D_i(b)` be the most expected points castles `1..i` can earn with `b` soldiers:

```
D_0(0) = 0,   D_0(b > 0) = -inf
D_i(b) = max_{0 <= k <= b} [ D_{i-1}(b - k) + g_i(k) ]
```

`D_5(100)` is the optimum. Recording which `k` achieved each maximum and backtracking from `b = 100` recovers the allocation. This takes 5 × 101 × 101 steps (`castle/game1.py::best_response`).

As a check, the replay also scores **all** `C(104, 4) = 4,598,126` legal allocations, which is the number of ways to split 100 soldiers among 5 castles. The dynamic program and the enumeration agree. The tests also compare the dynamic program with brute force on random models with smaller budgets.

This proves `[3, 5, 27, 2, 63]` has the highest mean score **for this finite synthetic model**. It says nothing about the unknown field of real entries.

### Why this allocation, in plain terms

- **Castle 5 (63 soldiers)** earns 4.76 of its possible 5 points. Every hand-written Game 1 template bids 61 or less there, so 63 clears them. Only the random `diverse` family and the best-response families (`meta1`, `meta2`) sometimes bid more.
- **Castle 3 (27 soldiers)** earns 2.30 of its 3 points. 27 beats the 15–20 that the `weighted` templates bid. It also beats the 20–26 that about half the `high3` templates bid, but loses to their 30–34.
- **Castle 4 is conceded (2 soldiers)** and earns only 0.43 of its 4 points. Opponents bid heavily on it, so the soldiers needed to win it are worth more on castles 3 and 5.
- **The small bids (3, 5, 2) on castles 1, 2 and 4** pick up castles from the many opponents who bid zero or one there.

The numbers 27 and 63 have no special meaning. They are just above where the modeled opponents cluster.

### Different objectives give different answers

| objective (exhaustive over the six scenarios) | allocation | mean | worst scenario |
|---|---|---:|---:|
| highest mean score | `[3, 5, 27, 2, 63]` | 9.3542 | 8.8188 |
| smallest worst-scenario regret | `[6, 4, 27, 1, 62]` | 9.2230 | 8.9061 |
| highest worst-scenario score | `[6, 5, 28, 1, 60]` | 9.1440 | 8.9275 |

The chosen allocation maximizes the **mean**. It is not the minimax choice. In the per-family breakdown it loses to other allocations against some individual families.

### A benchmark and a counterexample

Every duel splits exactly 15 points, so the average score across any whole field is 7.5. One fixed allocation can score above 7.5 against a predictable field, but nothing guarantees it. `[4, 6, 28, 3, 59]` outbids us by one soldier on castles 1–4 and beats us 10 to 5.

## Game 2: four players, placement payout

### From bids to payout

For each castle, find the highest bid; the players who made it split the castle's value. Let `S_p` be player `p`'s total castle points. Rank players by `S_p`. Places 1–4 pay `b = (9, 4, 2, 0)`, and tied players share the payouts of the places they occupy.

If `h` opponents score strictly more than us and `t` players (including us) tie at our score, our payout is

```
R = (1/t) * sum_{j=h+1}^{h+t} b_j.
```

If all four tie, everyone gets 15/4 = 3.75. If two tie for first, each gets (9+4)/2 = 6.5. Payouts always total 15, so the field average is 3.75.

### Why Game 1's objective doesn't carry over

The goal is to maximize `E[R]` over random opponent triples. That expectation can't be split into per-castle terms:

- **`R` depends on ranks, not points.** Going from second to first adds 5 to the payout, while going from third to second adds only 2. A small extra point is worth a lot or nothing depending on the other players' totals.
- **Castle outcomes are dependent within a group.** Whether we win castle 5 depends on all three opponents' castle-5 bids. Those same opponents' other bids decide whether winning it changes our rank.
- **Three head-to-head results are not a group result.** To win a castle outright we need to beat all three bids. If we beat one independently drawn opponent with probability `p`, we beat three with probability `p^3`; for example, 0.8 becomes 0.512. Moderate bids spread over many castles therefore do worse than in Game 1. This is intuition only: the code always scores full four-player groups.

The search scores each candidate on whole sampled groups of three opponents, using the payout table above (`castle/scoring.py`).

### Why castles 2 and 4

`[2, 34, 3, 59, 2]` puts 93 soldiers on castles 2 and 4, which are worth 6 points together.

**If we win both outright, we finish at least second.** We then have at least 6 points, and the other three players share at most the remaining 9. Two opponents would need more than 12 points between them to both beat us, and two opponents tying us would need 12, so neither can happen. At most one player can finish ahead of us, so our payout is at least 4.

**First place still depends on how castles 1, 3 and 5 split.** If three different opponents take them, they score 1, 3 and 5, and our 6 wins. If one opponent takes castles 3 and 5, that player has 8 and finishes ahead of us. Six points is a strong target but does not guarantee first place.

In the fresh check, the chosen allocation won castles 2 and 4 outright in 77.27% of groups. Its average payout in those groups was 8.39, and its minimum was exactly 4, as the argument predicts.

**Why 34 and 59.** `results/game2/summary.json → pool_profile` lists, for each family, the share of members bidding at least our amount on each castle.

| castle | our bid | families with ≥ 5% of members bidding at least ours |
|---|---:|---|
| 2 | 34 | `diverse` 8.7% |
| 4 | 59 | `one_big` 24.8%, `split_small` 9.5%, `diverse` 12.4% |

The `low_castles` family was built around the first search's best answers. It bids about 30 on castle 2 (mean 29.9), so 34 sits just above it. Its members bid 1.2 on castle 4 on average, so they leave castle 4 to us.

**The small bids (2, 3, 2) on castles 1, 3 and 5** win castles when all three opponents leave them empty. In the fresh check this happened on castle 1 in 10.5% of groups, castle 3 in 4.2% and castle 5 in 2.9%. These seven soldiers come out of castles 2 and 4, so the search had to trade them against the main targets. The near-tie below shows how flat that trade-off is.

### Why abandoning castle 5 works here, and how it can fail

Under this model most opponents bid heavily on castle 5. Winning it outright means outbidding three such players, which costs most of the budget (`near_all_in_5 = [1,1,1,1,96]` scores 5.85). Leaving castle 5 to the field lets those opponents spend their soldiers there while we take castles they've thinned out.

The obvious counter is to also skip castle 5 and concentrate on castles 1, 2 and 3. The first search, without the `low_castles` family, found exactly this: `[17, 31, 51, 1, 0]`. Once such players make up part of the field, `[2, 34, 3, 59, 2]` beats them on castle 2 (34 > ~30) and takes castle 4, which they abandon. Neither allocation dominates the other. Which one is better depends on how common each type of player is. The robustness runs vary that share (`results/robustness/game2.json`, kind `low_castles`).

`[3,35,0,0,62]`, `[0,0,0,60,40]`, `[0,0,99,0,1]` is a group where the chosen allocation wins no castle at all and gets 0.

### What the search does and does not show

The original Game 2 search was a coarse-to-fine Monte Carlo search, not an exhaustive one:

1. A step-2 grid (316,251 allocations) scored on a few groups.
2. The neighbors (±2 soldiers) of the best few hundred, scored on more groups.
3. The final shortlist re-ranked on many groups.

The last stage was also used to pick the answer, so it is a selection-stage score. It is not an untouched test. The fresh check afterward uses new groups and freezes the allocation. Its confidence intervals cover only the sampling of groups from fixed synthetic pools. They do not cover whether those pools resemble real players.
