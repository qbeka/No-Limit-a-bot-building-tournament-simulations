"""game 1: one opponent, maximize expected castle points.

g[i, k] = v_i * (P(Y_i < k) + 0.5 * P(Y_i = k)) is what bidding k on castle i
earns on average, so the expected score of an allocation x is sum_i g[i, x_i].
"""
import numpy as np

from castle.scoring import VALUES, all_allocations


def gains(pool):
    """g[i, k] for a pool of opponent allocations."""
    p = np.array([np.bincount(pool[:, i], minlength=101) for i in range(5)]) / len(pool)
    return (np.cumsum(p, axis=1) - 0.5 * p) * VALUES[:, None]


def score(g, allocation):
    return sum(g[..., i, allocation[i]] for i in range(5))


def best_response(g, budget=100):
    """exact dynamic program.

    best[b] is the most expected points the castles seen so far can earn with
    b soldiers. adding castle i: best_i(b) = max_k best_{i-1}(b - k) + g[i, k].
    ties go to the smallest k, as in the original code.
    """
    soldiers = np.arange(budget + 1)
    left = soldiers[:, None] - soldiers[None, :]
    best = np.full(budget + 1, -1e10)
    best[0] = 0
    choices = []
    for g_i in g:
        q = best[np.maximum(left, 0)] + g_i[None, :budget + 1]
        q[left < 0] = -1e10
        choice = q.argmax(axis=1)
        best = q[soldiers, choice]
        choices.append(choice)
    allocation, b = [], budget
    for choice in reversed(choices):
        allocation.append(int(choice[b]))
        b -= allocation[-1]
    return np.array(allocation[::-1]), float(best[budget])


def enumerate_objectives(scg):
    """score every legal allocation in every scenario and pick the best by four objectives."""
    every = all_allocations()
    scores = np.array([score(q, every.T) for q in scg]).T
    mean = scores.mean(axis=1)
    best_possible = np.array([best_response(q)[1] for q in scg])
    regret = (best_possible - scores).max(axis=1)
    objectives = {
        "mean_score": mean,
        "minimum_worst_scenario_regret": -regret,
        "maximum_minimum_scenario_score": scores.min(axis=1),
        "mean_score_minus_half_regret": mean - 0.5 * regret,
    }
    winners = {name: int(values.argmax()) for name, values in objectives.items()}
    return every, scores, regret, winners
