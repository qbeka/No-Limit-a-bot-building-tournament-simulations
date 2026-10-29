"""new checks with both choices frozen: change the opponent model and see what survives.

every experiment is listed in config.toml. game 1 is scored exactly; game 2 uses
the same sampled groups for every allocation so paired differences are fair.
"""
import numpy as np

from castle import game1, game2, opponents, replay


def candidates(cfg, game):
    """the chosen allocation plus every baseline fixed in config.toml."""
    other = "game2" if game == "game1" else "game1"
    pool = {"chosen": cfg["choices"][game], **cfg["baselines"], f"{other}_choice": cfg["choices"][other]}
    return {name: a for name, a in pool.items() if name == "chosen" or a != pool["chosen"]}


def with_extra(rows, fraction):
    """scale every scenario row by 1 - fraction and give the new family the rest."""
    return np.array([np.append(row * (1 - fraction), fraction) for row in rows])


def tilted(rows, tilt):
    """for each family: that family gets tilt, the rest keep their mix."""
    for f in range(rows.shape[1]):
        yield f, rows * (1 - tilt) + tilt * np.eye(rows.shape[1])[f]


# ---- game 1

def game1_models(cfg):
    c, r = cfg["game1"], cfg["robustness"]
    rows = np.array(c["scenarios"])

    def pools(seed=c["seed"], scale=1.0, atom=1.0):
        families, _ = opponents.build_families(c["families"], seed, c["samples"], scale, atom)
        return families

    def model(families, weights):
        g = np.array([game1.gains(p) for p in families.values()])
        return np.einsum("sf,fij->sij", weights, g)

    base = pools()
    yield "original", "original", None, model(base, rows)
    for seed in r["seeds"]:
        yield f"new pools seed {seed}", "pools", seed, model(pools(seed=seed), rows)
    for f in r["noise_factors"]:
        yield f"noise x{f}", "noise", f, model(pools(scale=f), rows)
    for f in r["atom_factors"]:
        yield f"exact templates x{f}", "atom", f, model(pools(atom=f), rows)
    for f, weights in tilted(rows, r["tilt"]):
        name = list(base)[f]
        yield f"tilt to {name}", "tilt", name, model(base, weights)

    rng = np.random.default_rng(r["group_seed"])
    copies = opponents.soften(rng, [cfg["choices"]["game1"]], c["samples"], r["copy_scale"], r["copy_atom"])
    counters = opponents.soften(rng, r["game1_counters"], c["samples"], r["copy_scale"], r["copy_atom"])
    for p in r["prevalence"]:
        yield f"copies {p}", "copies", p, model({**base, "copies": copies}, with_extra(rows, p))
    for p in r["prevalence"]:
        yield f"counters {p}", "counters", p, model({**base, "counters": counters}, with_extra(rows, p))


def game1_robustness(cfg, log=print):
    allocations = candidates(cfg, "game1")
    rows = []
    for name, kind, param, scg in game1_models(cfg):
        mean_model = scg.mean(axis=0)
        optimum, best_value = game1.best_response(mean_model)
        scores = {n: float(game1.score(mean_model, a)) for n, a in allocations.items()}
        rows.append({
            "experiment": name, "kind": kind, "param": param, "scores": scores,
            "worst_scenario": {n: float(min(game1.score(q, a) for q in scg)) for n, a in allocations.items()},
            "optimum": optimum.tolist(), "optimum_score": best_value,
            "chosen_regret": best_value - scores["chosen"],
            "chosen_rank": 1 + sum(s > scores["chosen"] for s in scores.values()),
        })
        log(f"  game 1 {name}: chosen {scores['chosen']:.3f}, optimum {optimum.tolist()} {best_value:.3f}")
    return rows


# ---- game 2

def recorded_top(cfg):
    saved = np.load(replay.REFERENCE / "data/castle_fourway_search.npz")
    return saved["a"][np.argsort(saved["s"].mean(axis=1))[-cfg["game2"]["adaptive"]["centers"]:]]


def game2_models(cfg):
    r = cfg["robustness"]
    top = recorded_top(cfg)
    saved = np.load(replay.REFERENCE / "data/castle_fourway_meta_families.npz")
    base = {k: saved[k] for k in saved.files}
    weights = replay.adaptive_weights(cfg)
    six = np.array(cfg["game2"]["scenarios"])

    yield "original", "original", None, base, weights
    for seed in r["seeds"]:
        yield f"new pools seed {seed}", "pools", seed, replay.game2_pools(cfg, top, seed=seed), weights
    for f in r["noise_factors"]:
        yield f"noise x{f}", "noise", f, replay.game2_pools(cfg, top, scale_factor=f), weights
    for f in r["atom_factors"]:
        yield f"exact templates x{f}", "atom", f, replay.game2_pools(cfg, top, atom_factor=f), weights
    for f, tilt in tilted(weights, r["tilt"]):
        name = list(base)[f]
        yield f"tilt to {name}", "tilt", name, base, tilt

    rng = np.random.default_rng(r["group_seed"])
    samples = cfg["game2"]["samples"]
    copies = opponents.soften(rng, [cfg["choices"]["game2"]], samples, r["copy_scale"], r["copy_atom"])
    counters = opponents.soften(rng, r["game2_counters"], samples, r["copy_scale"], r["copy_atom"])
    # base already ends with low_castles, so the extra column is its share
    for p in r["prevalence"]:
        yield f"low_castles {p}", "low_castles", p, base, with_extra(six, p)
    for p in r["prevalence"]:
        yield f"copies {p}", "copies", p, {**base, "copies": copies}, with_extra(weights, p)
    for p in r["prevalence"]:
        yield f"counters {p}", "counters", p, {**base, "counters": counters}, with_extra(weights, p)


def game2_robustness(cfg, log=print):
    r, step, radius = cfg["robustness"], cfg["game2"]["search"]["grid_step"], cfg["game2"]["search"]["radius"]
    allocations = candidates(cfg, "game2")
    rows = []
    for name, kind, param, families, weights in game2_models(cfg):
        groups = opponents.sample_groups(families, weights, r["groups"], r["group_seed"])
        scenarios = len(weights)
        a, s, _ = game2.search(families, weights, r["search"], step, radius, log=lambda *_: None)
        found = replay.winner(a, s)
        tested = dict(allocations)
        if found not in tested.values():
            tested["searched_best"] = found
        results, payouts = {}, {}
        for n, a in tested.items():
            results[n], payouts[n] = game2.summarize(a, groups, scenarios)
        differences = {n: game2.interval(payouts["chosen"] - payouts[n], scenarios) for n in tested if n != "chosen"}
        best = max(results, key=lambda n: results[n]["mean"])
        rows.append({
            "experiment": name, "kind": kind, "param": param, "results": results,
            "chosen_minus_other": differences, "searched_best": found, "best_tested": best,
            "chosen_rank": 1 + sum(v["mean"] > results["chosen"]["mean"] for v in results.values()),
        })
        log(f"  game 2 {name}: chosen {results['chosen']['mean']:.3f}, best {best} "
            f"{results[best]['mean']:.3f}, search found {found}")
    return rows
