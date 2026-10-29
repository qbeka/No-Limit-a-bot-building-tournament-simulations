import hashlib
import itertools
import json
import tomllib

import numpy as np
import pytest

from castle import game1, game2, opponents, replay, scoring

CFG = tomllib.loads((replay.REFERENCE.parent / "config.toml").read_text())
G1, G2 = CFG["choices"]["game1"], CFG["choices"]["game2"]


def random_allocations(n, seed):
    rng = np.random.default_rng(seed)
    x = rng.dirichlet(np.ones(5) * 0.5, size=n) * 100
    x[rng.random((n, 5)) < 0.3] = 0  # many zero bids, so many ties
    x[x.sum(axis=1) == 0, 0] = 1
    return opponents.round_rows(x / x.sum(axis=1, keepdims=True) * 100)


# ---- rules

@pytest.mark.parametrize("bad", [[20, 20, 20, 20], [20, 20, 20, 20, 21], [-1, 21, 20, 30, 30], [20.5, 19.5, 20, 20, 20]])
def test_rejects_illegal_allocations(bad):
    with pytest.raises(ValueError):
        scoring.check(bad)


def test_accepts_legal_allocations():
    for a in [G1, G2, [100, 0, 0, 0, 0], [20] * 5]:
        scoring.check(a)


def test_zero_against_zero_splits():
    assert scoring.duel([0, 0, 0, 0, 100], [0, 0, 0, 0, 100]) == (7.5, 7.5)
    assert scoring.duel([100, 0, 0, 0, 0], [0, 0, 0, 0, 100]) == (1 + 2 / 2 + 3 / 2 + 4 / 2, 5 + 2 / 2 + 3 / 2 + 4 / 2)
    assert scoring.four_way([[0, 0, 0, 0, 100]] * 4) == [3.75] * 4


@pytest.mark.parametrize("size", [1, 2, 3, 4])
def test_castle_ties_of_every_size(size):
    # size players bid 50 on castle 5, the rest bid 10. castles 1-4 are four-way ties at 0.
    players = [[0, 0, 0, 0, 50 if i < size else 10] for i in range(4)]
    points = scoring.castle_points(players)
    for i in range(4):
        castle5 = scoring.SCALE * 5 / size if i < size else 0
        assert points[i] == castle5 + scoring.SCALE * (1 + 2 + 3 + 4) / 4


def test_tied_places_average_their_payouts():
    assert scoring.placement_payouts([5, 5, 5, 5]) == [3.75] * 4
    assert scoring.placement_payouts([9, 9, 1, 0]) == [6.5, 6.5, 2, 0]
    assert scoring.placement_payouts([9, 9, 9, 0]) == [5, 5, 5, 0]
    assert scoring.placement_payouts([9, 4, 4, 0]) == [9, 3, 3, 0]
    assert scoring.placement_payouts([9, 4, 1, 1]) == [9, 4, 1, 1]


def test_payout_table_matches_original():
    original = [[108, 78, 60, 45], [48, 36, 24, 0], [24, 12, 0, 0], [0, 0, 0, 0]]
    assert scoring.PAY12.tolist() == original


def test_points_and_payouts_are_conserved():
    a = random_allocations(4000, 0).reshape(-1, 4, 5)
    for players in a:
        assert sum(scoring.castle_points(players.tolist())) == 15 * scoring.SCALE
        assert sum(scoring.placement_payouts(scoring.castle_points(players.tolist()))) == 15
    assert (scoring.group_points12(a).sum(axis=1) == 15 * scoring.SCALE).all()


def test_player_order_does_not_matter():
    for players in random_allocations(400, 1).reshape(-1, 4, 5).tolist():
        payouts = scoring.four_way(players)
        for order in itertools.permutations(range(4)):
            assert scoring.four_way([players[i] for i in order]) == [payouts[i] for i in order]


def test_fast_and_table_scorers_match_reference():
    rng = np.random.default_rng(2)
    pool = random_allocations(6000, 3)
    groups = pool[rng.integers(len(pool), size=(1200, 3))]
    table = scoring.castle_table(groups)
    for ours in pool[:40]:
        reference = [scoring.four_way([ours, *triple])[0] for triple in groups]
        fast = scoring.play(ours, groups)["payout"]
        assert np.array_equal(fast, reference)
        assert scoring.evaluate(ours[None], table, 1)[0, 0] == pytest.approx(np.mean(reference), abs=1e-12)


def test_constructed_counterexamples():
    assert scoring.duel([4, 6, 28, 3, 59], G1) == (10, 5)
    payouts = scoring.four_way([G2, [3, 35, 0, 0, 62], [0, 0, 0, 60, 40], [0, 0, 99, 0, 1]])
    assert scoring.castle_points([G2, [3, 35, 0, 0, 62], [0, 0, 0, 60, 40], [0, 0, 99, 0, 1]])[0] == 0
    assert payouts[0] == 0


# ---- game 1 math

def test_one_more_soldier_formula():
    pool = random_allocations(5000, 4)
    g = game1.gains(pool)
    p = np.array([np.bincount(pool[:, i], minlength=101) for i in range(5)]) / len(pool)
    for i in range(5):
        assert np.allclose(np.diff(g[i]), 0.5 * (i + 1) * (p[i, :-1] + p[i, 1:]))


def test_independent_bids_give_the_same_expectation():
    """game 1 only needs the five marginals: shuffling bids across opponents keeps the score."""
    pool = random_allocations(3000, 5)
    shuffled = np.column_stack([np.random.default_rng(i).permutation(pool[:, i]) for i in range(5)])
    assert np.allclose(game1.gains(pool), game1.gains(shuffled))
    duels = np.mean([scoring.duel(G1, opp)[0] for opp in pool])
    assert duels == pytest.approx(game1.score(game1.gains(pool), G1), abs=1e-12)


@pytest.mark.parametrize("budget", [0, 1, 5, 12, 20])
def test_dp_matches_brute_force(budget):
    rng = np.random.default_rng(budget)
    g = np.cumsum(rng.random((5, 101)), axis=1) * np.arange(1, 6)[:, None] / 50
    allocation, value = game1.best_response(g, budget)
    every = scoring.all_allocations(budget)
    brute = max(game1.score(g, a) for a in every)
    assert allocation.sum() == budget and (allocation >= 0).all()
    assert value == pytest.approx(brute, abs=1e-12)
    assert game1.score(g, allocation) == pytest.approx(value, abs=1e-12)


def test_legal_allocation_count():
    assert len(scoring.all_allocations()) == 4598126
    assert len(game2.grid(2)) == 316251


def test_dp_on_recorded_model_gives_recorded_answer():
    scg = np.load(replay.REFERENCE / "data/game1_compact.npz")["scg"]
    recorded = json.loads((replay.REFERENCE / "data/game1_summary.json").read_text())
    allocation, value = game1.best_response(scg.mean(axis=0))
    assert allocation.tolist() == G1
    assert value == pytest.approx(recorded["objectives"]["mean_score"]["mean"], abs=1e-12)


# ---- opponents and reproducibility

def test_rounding_keeps_integers_totaling_100():
    rng = np.random.default_rng(6)
    x = np.maximum(0, rng.normal(20, 15, (20000, 5)))
    x[:, rng.integers(5)] += 1
    a = opponents.round_rows(x / x.sum(axis=1, keepdims=True) * 100)
    assert a.dtype.kind == "i" and (a >= 0).all() and (a.sum(axis=1) == 100).all()
    assert (np.abs(a - x / x.sum(axis=1, keepdims=True) * 100) < 1).all()


def test_game1_pools_regenerate_exactly():
    c = CFG["game1"]
    families, _ = opponents.build_families(c["families"], c["seed"], c["samples"])
    g = np.array([game1.gains(p) for p in families.values()])
    assert np.array_equal(g, np.load(replay.REFERENCE / "data/game1_compact.npz")["g"])


def test_game2_pools_regenerate_exactly():
    saved = np.load(replay.REFERENCE / "data/castle_fourway_meta_families.npz")
    from castle import robustness
    families = replay.game2_pools(CFG, robustness.recorded_top(CFG))
    assert list(families) == saved.files
    for name in saved.files:
        assert np.array_equal(families[name], saved[name])


def test_group_sampling_is_deterministic():
    saved = np.load(replay.REFERENCE / "data/castle_fourway_meta_families.npz")
    families = {k: saved[k] for k in saved.files}
    weights = replay.adaptive_weights(CFG)
    a = opponents.sample_groups(families, weights, 50, 9)
    assert a.shape == (300, 3, 5) and np.array_equal(a, opponents.sample_groups(families, weights, 50, 9))
    assert np.allclose(weights, np.load(replay.REFERENCE / "data/castle_fourway_meta.npz")["weights"])


def test_originals_are_unchanged():
    for line in (replay.REFERENCE / "SHA256SUMS.txt").read_text().splitlines():
        digest, name = line.split()
        assert hashlib.sha256((replay.REFERENCE / name).read_bytes()).hexdigest() == digest, name
