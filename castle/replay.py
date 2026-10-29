"""historical replays of the original scripts, checked against the recorded outputs."""
import json
from pathlib import Path

import numpy as np

from castle import game1, game2, opponents, scoring

REFERENCE = Path(__file__).resolve().parent.parent / "reference"


def max_diff(a, b):
    return float(np.max(np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))))


def winner(a, s):
    return a[s.mean(axis=1).argmax()].tolist()


def compare_shortlists(a, s, recorded):
    """which allocations both runs kept, and whether their scores agree."""
    ours = {tuple(x): i for i, x in enumerate(a.tolist())}
    theirs = {tuple(x): i for i, x in enumerate(recorded["a"].tolist())}
    common = [k for k in ours if k in theirs]
    return {
        "kept_by_both": len(common),
        "only_in_replay": [list(k) for k in ours if k not in theirs],
        "only_in_recorded": [list(k) for k in theirs if k not in ours],
        "score_max_diff_on_common": max_diff([s[ours[k]] for k in common], [recorded["s"][theirs[k]] for k in common]),
    }


def same_pools(a, b):
    return list(a) == list(b) and all(np.array_equal(a[k], b[k]) for k in a)


def game1_replay(cfg, log=print):
    """castle_analysis.py: build the seven pools, then score all 4,598,126 allocations exactly."""
    c = cfg["game1"]
    log("game 1: building opponent pools")
    families, _ = opponents.build_families(c["families"], c["seed"], c["samples"])
    g = np.array([game1.gains(pool) for pool in families.values()])
    scenarios = np.array(c["scenarios"])
    scg = np.einsum("sf,fij->sij", scenarios, g)

    log("game 1: scoring every legal allocation")
    every, scores, regret, winners = game1.enumerate_objectives(scg)
    objectives = {}
    for name, k in winners.items():
        a = every[k]
        objectives[name] = {
            "allocation": a.tolist(),
            "mean": float(scores[k].mean()),
            "by_scenario": scores[k].tolist(),
            "worst_scenario_regret": float(regret[k]),
            "by_family": game1.score(g, a).tolist(),
        }

    # the dp on the averaged model must land on the same allocation as enumeration
    mean_model = scg.mean(axis=0)
    dp_allocation, dp_value = game1.best_response(mean_model)
    chosen = np.array(cfg["choices"]["game1"])
    k = np.flatnonzero((every == chosen).all(axis=1))[0]
    gain = [float(mean_model[i, chosen[i] + 1] - mean_model[i, chosen[i]]) for i in range(5)]
    loss = [float(mean_model[i, chosen[i]] - mean_model[i, chosen[i] - 1]) for i in range(5)]

    reference = json.loads((REFERENCE / "data/game1_summary.json").read_text())
    recorded = np.load(REFERENCE / "data/game1_compact.npz")
    checks = {
        "pools_g_max_diff_vs_recorded": max_diff(g, recorded["g"]),
        "scenario_g_max_diff_vs_recorded": max_diff(scg, recorded["scg"]),
        "objective_allocations_match_recorded": all(
            objectives[n]["allocation"] == reference["objectives"][n]["allocation"] for n in objectives),
        "objective_values_max_diff_vs_recorded": max(
            max_diff(objectives[n]["by_scenario"], reference["objectives"][n]["by_scenario"]) for n in objectives),
        "dp_mean_optimum": dp_allocation.tolist(),
        "dp_matches_enumeration": dp_allocation.tolist() == objectives["mean_score"]["allocation"],
        "dp_value_minus_enumeration": dp_value - float(scores[winners["mean_score"]].mean()),
    }
    summary = {
        "description": "replay of reference/originals/castle_analysis.py under the synthetic opponent model",
        "legal_allocations": len(every),
        "family_order": list(families),
        "objectives": objectives,
        "chosen": {
            "allocation": chosen.tolist(),
            "rank_by_mean": int((scores.mean(axis=1) > scores[k].mean()).sum()) + 1,
            "castle_contributions": [float(mean_model[i, chosen[i]]) for i in range(5)],
            "add_one_gain": gain,
            "remove_one_loss": loss,
        },
        "family_best_responses": {n: game1.best_response(q)[0].tolist() for n, q in zip(families, g)},
        "scenario_best_responses": [game1.best_response(q)[0].tolist() for q in scg],
        "checks": checks,
    }
    return summary, {"g": g, "scg": scg}


def game2_pools(cfg, top, seed=None, scale_factor=1.0, atom_factor=1.0):
    """castle_fourway.py's six pools, then castle_fourway_meta.py's low_castles pool.

    the meta script keeps drawing from the same generator after the first six
    pools, so low_castles comes from that state. top is the first search's best 80.
    """
    c, ad = cfg["game2"], cfg["game2"]["adaptive"]
    families, rng = opponents.build_families(c["families"], seed or c["seed"], c["samples"],
                                             scale_factor, atom_factor)
    families["low_castles"] = opponents.soften(rng, top, ad["samples"], ad["scale"] * scale_factor,
                                               min(1.0, ad["atom"] * atom_factor))
    return families


def adaptive_weights(cfg):
    base = np.array(cfg["game2"]["scenarios"])
    return np.array([np.append(row * (1 - f), f) for row, f in zip(base, cfg["game2"]["adaptive"]["fractions"])])


def pool_profile(families, chosen):
    """per family: mean bid per castle, and how often a member bids at least our bid there."""
    return {name: {"mean_bid": pool.mean(axis=0).round(2).tolist(),
                   "share_bidding_at_least_ours": (pool >= np.array(chosen)).mean(axis=0).round(4).tolist(),
                   "share_bidding_zero": (pool == 0).mean(axis=0).round(4).tolist()}
            for name, pool in families.items()}


def game2_replay(cfg, log=print):
    c = cfg["game2"]
    weights = np.array(c["scenarios"])
    recorded_search = np.load(REFERENCE / "data/castle_fourway_search.npz")
    recorded_meta = np.load(REFERENCE / "data/castle_fourway_meta.npz")
    recorded_pools = np.load(REFERENCE / "data/castle_fourway_meta_families.npz")
    recorded_pools = {k: recorded_pools[k] for k in recorded_pools.files}

    log("game 2: first search (six families)")
    base, _ = opponents.build_families(c["families"], c["seed"], c["samples"])
    search_a, search_s, groups = game2.search(base, weights, c["search"]["stages"],
                                              c["search"]["grid_step"], c["search"]["radius"], log)
    candidates = np.array([cfg["choices"]["game2"], *cfg["baselines"].values(), cfg["choices"]["game1"]])
    first_candidate_s = scoring.evaluate(candidates, scoring.castle_table(groups), len(weights))

    log("game 2: adaptive search (adds low_castles)")
    top = search_a[np.argsort(search_s.mean(axis=1))[-c["adaptive"]["centers"]:]]
    families = game2_pools(cfg, top)
    meta_weights = adaptive_weights(cfg)
    meta_a, meta_s, groups = game2.search(families, meta_weights, c["adaptive"]["stages"],
                                          c["search"]["grid_step"], c["search"]["radius"], log)
    adaptive_candidate_s = scoring.evaluate(candidates, scoring.castle_table(groups), len(meta_weights))

    # the original's own check: table scorer equals a direct scorer on 200 groups
    best = np.array(winner(meta_a, meta_s))
    direct = [scoring.four_way([best, *triple])[0] for triple in groups[:200]]
    table = scoring.castle_table(groups[:200])
    table_check = max_diff(scoring.evaluate(best[None], table, 1)[0, 0], np.mean(direct))

    checks = {
        "pools_match_recorded": same_pools(families, recorded_pools),
        "first_search_best_matches_recorded": winner(search_a, search_s) == winner(recorded_search["a"], recorded_search["s"]),
        "adaptive_best_matches_recorded": winner(meta_a, meta_s) == winner(recorded_meta["a"], recorded_meta["s"]),
        "first_search_vs_recorded": compare_shortlists(search_a, search_s, recorded_search),
        "adaptive_search_vs_recorded": compare_shortlists(meta_a, meta_s, recorded_meta),
        "adaptive_weights_max_diff_vs_recorded": max_diff(meta_weights, recorded_meta["weights"]),
        "table_vs_direct_scorer_diff": table_check,
    }
    summary = {
        "description": "replay of castle_fourway.py and castle_fourway_meta.py. "
                       "the last stage of each search was also used to pick candidates, so it is a selection stage, not a test.",
        "family_order": list(families),
        "first_search_best": winner(search_a, search_s),
        "adaptive_best": best.tolist(),
        "pool_profile": pool_profile(families, cfg["choices"]["game2"]),
        "adaptive_scenario_best": [{"allocation": meta_a[meta_s[:, j].argmax()].tolist(),
                                    "payout": float(meta_s[:, j].max())} for j in range(len(meta_weights))],
        "checks": checks,
    }
    tables = {
        "first_search": (search_a, search_s),
        "first_search_baselines": (candidates, first_candidate_s),
        "adaptive_search": (meta_a, meta_s),
        "adaptive_baselines": (candidates, adaptive_candidate_s),
    }
    return summary, tables


def fresh_check(cfg, log=print):
    """castle_frozen_check.py: fixed allocations on 300,000 new groups from the saved pools."""
    saved = np.load(REFERENCE / "data/castle_fourway_meta_families.npz")
    families = {k: saved[k] for k in saved.files}
    weights = np.load(REFERENCE / "data/castle_fourway_meta.npz")["weights"]
    f = cfg["fresh_check"]
    groups = opponents.sample_groups(families, weights, f["groups"], f["seed"])
    log(f"fresh check: {len(groups)} groups")

    names = {"selected_game2": cfg["choices"]["game2"], "near_tie_game2": cfg["baselines"]["game2_near_tie"],
             "initial_game2": cfg["baselines"]["game2_initial"], "selected_game1": cfg["choices"]["game1"],
             "equal": cfg["baselines"]["equal"], "proportional": cfg["baselines"]["proportional"],
             "three_high": cfg["baselines"]["top_three"], "two_high": cfg["baselines"]["top_two"],
             "one_high": cfg["baselines"]["near_all_in_5"], "all_five": cfg["baselines"]["all_in_5"]}
    results, payouts = {}, {}
    for name, allocation in names.items():
        results[name], payouts[name] = game2.summarize(allocation, groups, len(weights))
    differences = {name: game2.interval(payouts["selected_game2"] - payouts[name], len(weights))
                   for name in names if name != "selected_game2"}

    reference = json.loads((REFERENCE / "fresh_check/castle_frozen_check.json").read_text())
    checks = {
        "mean_max_diff_vs_recorded": max(abs(results[n]["mean"] - reference["results"][n]["mean"]) for n in names),
        "difference_max_diff_vs_recorded": max(
            abs(differences[n]["mean"] - reference["paired_differences_selected_minus_baseline"][n]["mean"])
            for n in differences),
        "wins_2_and_4_rate_diff": results["selected_game2"]["wins_2_and_4_rate"]
        - reference["results"]["selected_game2"]["strict_win_castles_2_and_4_rate"],
    }
    return {
        "description": "fixed allocations on fresh groups from the fixed synthetic pools. "
                       "intervals cover group sampling only, not the opponent model.",
        "seed": f["seed"], "groups_per_scenario": f["groups"], "total_groups": len(groups),
        "results": results, "paired_differences_selected_minus_other": differences, "checks": checks,
    }
