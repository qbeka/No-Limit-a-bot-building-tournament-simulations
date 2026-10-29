"""python -m castle <command>

  quick       seconds: rules, counterexamples, game 1 dp, small game 2 check
  game1       replay the exhaustive game 1 run (~1 min, ~1.5 GB memory)
  game2       replay both game 2 searches (a few minutes)
  fresh       replay the frozen fresh check (300,000 groups)
  robustness  new sensitivity experiments (several minutes)
  report      figures and results/summary.md from saved results
  all         everything above in order
"""
import json
import platform
import sys
import time
import tomllib
from pathlib import Path

import numpy as np

from castle import game1, opponents, replay, report, robustness, scoring

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


def quick(cfg):
    g1, g2 = cfg["choices"]["game1"], cfg["choices"]["game2"]
    print("game 1 counterexample:", [4, 6, 28, 3, 59], "vs", g1, "->", scoring.duel([4, 6, 28, 3, 59], g1))
    group = [g2, [3, 35, 0, 0, 62], [0, 0, 0, 60, 40], [0, 0, 99, 0, 1]]
    print("game 2 losing group:", group[1:], "-> payouts", scoring.four_way(group))

    scg = np.load(replay.REFERENCE / "data/game1_compact.npz")["scg"]
    mean_model = scg.mean(axis=0)
    optimum, value = game1.best_response(mean_model)
    print(f"game 1 on the recorded model: chosen {game1.score(mean_model, g1):.6f}, dp optimum {optimum.tolist()} {value:.6f}")

    saved = np.load(replay.REFERENCE / "data/castle_fourway_meta_families.npz")
    families = {k: saved[k] for k in saved.files}
    groups = opponents.sample_groups(families, replay.adaptive_weights(cfg), 2000, 1)
    result = {}
    for name, a in [("chosen", g2), *cfg["baselines"].items()]:
        payout = scoring.play(a, groups)["payout"]
        result[name] = {"allocation": a, "payout": float(payout.mean())}
    print("game 2 on 12,000 groups (seed 1):")
    for name, r in sorted(result.items(), key=lambda kv: -kv[1]["payout"])[:6]:
        print(f"  {name:22s} {r['allocation']}  {r['payout']:.3f}")
    report.save_json(RESULTS / "quick.json", {
        "game1_chosen_on_recorded_model": float(game1.score(mean_model, g1)),
        "game1_dp_optimum": optimum.tolist(), "game2_small_check": result})


def run_game1(cfg):
    summary, model = replay.game1_replay(cfg)
    report.save_json(RESULTS / "game1/summary.json", summary)
    np.savez(RESULTS / "game1/model.npz", **model)
    print(json.dumps(summary["checks"], indent=2))


def run_game2(cfg):
    summary, tables = replay.game2_replay(cfg)
    report.save_json(RESULTS / "game2/summary.json", summary)
    for name, (a, s) in tables.items():
        report.save_scores(RESULTS / f"game2/{name}.csv", a, s)
    print(json.dumps(summary["checks"], indent=2))


def run_fresh(cfg):
    result = replay.fresh_check(cfg)
    report.save_json(RESULTS / "fresh_check.json", result)
    print(json.dumps(result["checks"], indent=2))


def run_robustness(cfg):
    report.save_json(RESULTS / "robustness/game1.json", robustness.game1_robustness(cfg))
    report.save_json(RESULTS / "robustness/game2.json", robustness.game2_robustness(cfg))


def run_report(cfg):
    report.build(cfg, RESULTS)


COMMANDS = {"quick": quick, "game1": run_game1, "game2": run_game2, "fresh": run_fresh,
            "robustness": run_robustness, "report": run_report}


def record(command, seconds):
    """keep a manifest of what ran, when, how long, and on what."""
    path = RESULTS / "manifest.json"
    manifest = report.load(path) or {"runs": {}}
    manifest["environment"] = {"python": sys.version.split()[0], "numpy": np.__version__,
                               "platform": platform.platform(), "machine": platform.machine()}
    manifest["config"] = "config.toml"
    manifest["runs"][command] = {"finished": time.strftime("%Y-%m-%d %H:%M:%S"), "seconds": round(seconds, 1)}
    report.save_json(path, manifest)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in [*COMMANDS, "all"]:
        sys.exit(__doc__)
    cfg = tomllib.loads((ROOT / "config.toml").read_text())
    for command in COMMANDS if sys.argv[1] == "all" else [sys.argv[1]]:
        start = time.time()
        COMMANDS[command](cfg)
        record(command, time.time() - start)


if __name__ == "__main__":
    main()
