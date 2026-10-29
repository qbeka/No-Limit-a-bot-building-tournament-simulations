"""game 2: four players, maximize expected placement payout.

there are too many allocations and opponent triples to score exactly, so the
search scores a coarse grid on few groups, keeps the best, looks at their
neighbours on more groups, and re-ranks the shortlist on many groups.
"""
import itertools

import numpy as np

from castle import opponents, scoring


def grid(step):
    return scoring.all_allocations(100 // step) * step


def neighbors(allocations, radius):
    """every legal allocation within radius soldiers per castle of any input allocation."""
    deltas = np.array([(*d, -sum(d)) for d in itertools.product(range(-radius, radius + 1), repeat=4)
                       if abs(sum(d)) <= radius], dtype=np.int16)
    near = (allocations[:, None, :] + deltas[None, :, :]).reshape(-1, 5)
    near = near[(near >= 0).all(axis=1) & (near <= 100).all(axis=1)]
    return np.unique(near, axis=0)


def shortlist(allocations, scores, keep):
    """best keep by mean, plus best keep // 3 in each scenario and by worst scenario."""
    picked = set(np.argsort(scores.mean(axis=1))[-keep:].tolist())
    for j in range(scores.shape[1]):
        picked.update(np.argsort(scores[:, j])[-keep // 3:].tolist())
    picked.update(np.argsort(scores.min(axis=1))[-keep // 3:].tolist())
    return allocations[sorted(picked)]


def search(families, weights, stages, step, radius, log=print):
    """returns the final shortlist, its scores, and the groups of the last stage."""
    allocations = grid(step)
    for i, stage in enumerate(stages):
        groups = opponents.sample_groups(families, weights, stage["groups"], stage["seed"])
        scores = scoring.evaluate(allocations, scoring.castle_table(groups), len(weights))
        best = scores.mean(axis=1).argmax()
        log(f"  stage {i + 1}: {len(allocations)} allocations x {len(groups)} groups, "
            f"best {allocations[best].tolist()} {scores[best].mean():.4f}")
        if "keep" in stage:
            allocations = shortlist(allocations, scores, stage["keep"])
            if i == 0:
                allocations = neighbors(allocations, radius)
    return allocations, scores, groups


def summarize(allocation, opponent_groups, scenarios):
    """payout and placement detail for one allocation, with stratified 95% intervals."""
    result = scoring.play(allocation, opponent_groups)
    both = result["castle_wins"][:, 1] & result["castle_wins"][:, 3]
    summary = interval(result["payout"], scenarios)
    summary.update({
        "allocation": list(map(int, allocation)),
        "sole_first_rate": float(result["sole_first"].mean()),
        "tied_first_rate": float(result["tied_first"].mean()),
        "mean_castle_points": float(result["points"].mean()),
        "castle_win_rates": result["castle_wins"].mean(axis=0).tolist(),
        "wins_2_and_4_rate": float(both.mean()),
        "payout_if_wins_2_and_4": float(result["payout"][both].mean()) if both.any() else None,
        "min_payout_if_wins_2_and_4": float(result["payout"][both].min()) if both.any() else None,
    })
    return summary, result["payout"]


def interval(x, scenarios):
    """mean over equally weighted scenarios; the standard error adds each scenario's variance."""
    x = np.asarray(x).reshape(scenarios, -1)
    means = x.mean(axis=1)
    se = np.sqrt((x.var(axis=1, ddof=1) / x.shape[1]).sum()) / scenarios
    mean = float(means.mean())
    return {"mean": mean, "standard_error": float(se),
            "ci95": [mean - 1.96 * se, mean + 1.96 * se], "by_scenario": means.tolist()}
