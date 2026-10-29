"""saving results, and turning saved results into figures and a summary.

figures and summary.md read only from files in results/, never from memory.
"""
import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

CASTLE_COLORS = ["#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#08519c"]


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def save_scores(path, allocations, scores):
    path.parent.mkdir(parents=True, exist_ok=True)
    order = scores.mean(axis=1).argsort()[::-1]
    with open(path, "w", newline="") as f:
        out = csv.writer(f)
        out.writerow([f"castle{i}" for i in range(1, 6)] + ["mean"] + [f"scenario{j + 1}" for j in range(scores.shape[1])])
        for k in order:
            out.writerow(allocations[k].tolist() + [scores[k].mean()] + scores[k].tolist())


def save_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        out = csv.DictWriter(f, fieldnames=list(rows[0]))
        out.writeheader()
        out.writerows(rows)


def load(path):
    return json.loads(path.read_text()) if path.exists() else None


# ---- figures

def fig_scenarios(g1, fresh, path):
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4))
    for name, label in [("mean_score", "best mean (chosen)"), ("minimum_worst_scenario_regret", "least regret"),
                        ("maximum_minimum_scenario_score", "best worst case")]:
        o = g1["objectives"][name]
        left.plot(range(1, 7), o["by_scenario"], marker="o", label=f"{label} {o['allocation']}")
    left.set(title="game 1: expected castle points", xlabel="scenario", ylabel="points (of 15)")
    left.legend(fontsize=8)
    for name in ["selected_game2", "near_tie_game2", "one_high", "all_five", "initial_game2"]:
        r = fresh["results"][name]
        right.plot(range(1, 7), r["by_scenario"], marker="o", label=f"{name} {r['allocation']}")
    right.set(title="game 2: expected payout, fresh groups", xlabel="scenario", ylabel="payout (of 9)")
    right.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_paired(fresh, g2_rows, path):
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 6))
    diffs = fresh["paired_differences_selected_minus_other"]
    names = sorted(diffs, key=lambda n: diffs[n]["mean"])
    for i, n in enumerate(names):
        d = diffs[n]
        left.errorbar(d["mean"], i, xerr=1.96 * d["standard_error"], fmt="o", color="black", capsize=3)
    left.axvline(0, color="gray", lw=0.8)
    left.set(yticks=range(len(names)), yticklabels=names, xlabel="chosen minus other (payout)",
             title="game 2 fresh check: paired differences, 95% ci")

    labels, means, errors = [], [], []
    for row in g2_rows:
        others = row["chosen_minus_other"]
        closest = min(others, key=lambda n: others[n]["mean"])
        labels.append(f"{row['experiment']} vs {closest}")
        means.append(others[closest]["mean"])
        errors.append(1.96 * others[closest]["standard_error"])
    for i, (m, e) in enumerate(zip(means, errors)):
        right.errorbar(m, i, xerr=e, fmt="o", color="firebrick" if m + e < 0 else "black", capsize=3)
    right.axvline(0, color="gray", lw=0.8)
    right.set(yticks=range(len(labels)), xlabel="chosen minus strongest other (payout)",
              title="game 2 robustness: closest rival per experiment")
    right.set_yticklabels(labels, fontsize=6)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_prevalence(g1_rows, g2_rows, path):
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    shown = ["chosen", "game2_near_tie", "near_all_in_5", "game2_two_castles", "game2_initial"]
    for ax, kind in zip(axes[0], ["low_castles", "copies", "counters"]):
        rows = [r for r in g2_rows if r["kind"] == kind]
        x = [r["param"] for r in rows]
        for n in shown:
            m = [r["results"][n]["mean"] for r in rows]
            e = [1.96 * r["results"][n]["standard_error"] for r in rows]
            ax.errorbar(x, m, yerr=e, marker="o", ms=3, capsize=2, label=n)
        ax.set(title=f"game 2: share of {kind}", xlabel="share of opponents", ylabel="payout")
    axes[0, 0].legend(fontsize=7)
    shown = ["chosen", "game1_minimax_regret", "game1_maximin", "game1_counterexample", "near_all_in_5"]
    for ax, kind in zip(axes[1], ["copies", "counters"]):
        rows = [r for r in g1_rows if r["kind"] == kind]
        x = [r["param"] for r in rows]
        for n in shown:
            ax.plot(x, [r["scores"][n] for r in rows], marker="o", ms=3, label=n)
        ax.plot(x, [r["optimum_score"] for r in rows], "k--", lw=1, label="exact optimum")
        ax.set(title=f"game 1: share of {kind}", xlabel="share of opponents", ylabel="expected points")
    axes[1, 0].legend(fontsize=7)
    axes[1, 2].axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_allocations(cfg, path):
    named = {"game 1 chosen": cfg["choices"]["game1"], "game 2 chosen": cfg["choices"]["game2"], **cfg["baselines"]}
    fig, ax = plt.subplots(figsize=(8, 6))
    for i, (name, a) in enumerate(named.items()):
        left = 0
        for castle, soldiers in enumerate(a):
            ax.barh(i, soldiers, left=left, color=CASTLE_COLORS[castle], edgecolor="white",
                    label=f"castle {castle + 1}" if i == 0 else None)
            if soldiers >= 6:
                ax.text(left + soldiers / 2, i, soldiers, ha="center", va="center", fontsize=7,
                        color="white" if castle > 2 else "black")
            left += soldiers
    ax.set(yticks=range(len(named)), yticklabels=list(named), xlabel="soldiers", xlim=(0, 100))
    ax.invert_yaxis()
    ax.legend(ncol=5, fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---- summary

def fmt(x, digits=4):
    return f"{x:.{digits}f}"


def summary_markdown(results_dir):
    g1 = load(results_dir / "game1/summary.json")
    g2 = load(results_dir / "game2/summary.json")
    fresh = load(results_dir / "fresh_check.json")
    g1r = load(results_dir / "robustness/game1.json")
    g2r = load(results_dir / "robustness/game2.json")
    lines = ["# generated summary", "", "made by `python -m castle report` from the files in this folder.", ""]

    lines += ["## replay checks against the recorded outputs", ""]
    for name, part in [("game 1", g1), ("game 2", g2), ("fresh check", fresh)]:
        if part:
            for key, value in part["checks"].items():
                lines.append(f"- {name}: `{key}` = `{value}`")
    lines.append("")

    if g1:
        lines += ["## game 1 objectives (exhaustive, all 4,598,126 allocations)", "",
                  "| objective | allocation | mean | worst scenario | worst regret |", "|---|---|---:|---:|---:|"]
        for name, o in g1["objectives"].items():
            lines.append(f"| {name} | {o['allocation']} | {fmt(o['mean'])} | {fmt(min(o['by_scenario']))} "
                         f"| {fmt(o['worst_scenario_regret'])} |")
        c = g1["chosen"]
        lines += ["", f"chosen {c['allocation']}: castle contributions "
                  f"{[round(x, 4) for x in c['castle_contributions']]}, "
                  f"add one {[round(x, 4) for x in c['add_one_gain']]}, "
                  f"remove one {[round(x, 4) for x in c['remove_one_loss']]}", ""]

    if fresh:
        lines += ["## game 2 fresh check (300,000 new groups, fixed pools)", "",
                  "| allocation | payout | 95% ci | sole first | tied first | chosen minus this |",
                  "|---|---:|---|---:|---:|---|"]
        diffs = fresh["paired_differences_selected_minus_other"]
        for name, r in sorted(fresh["results"].items(), key=lambda kv: -kv[1]["mean"]):
            d = diffs.get(name)
            diff = f"{fmt(d['mean'])} [{fmt(d['ci95'][0])}, {fmt(d['ci95'][1])}]" if d else ""
            lines.append(f"| {r['allocation']} | {fmt(r['mean'])} | [{fmt(r['ci95'][0])}, {fmt(r['ci95'][1])}] "
                         f"| {fmt(r['sole_first_rate'], 3)} | {fmt(r['tied_first_rate'], 3)} | {diff} |")
        s = fresh["results"]["selected_game2"]
        lines += ["", f"chosen wins castles 2 and 4 outright in {fmt(s['wins_2_and_4_rate'], 5)} of groups; "
                  f"mean payout then {fmt(s['payout_if_wins_2_and_4'])}, minimum {s['min_payout_if_wins_2_and_4']}.",
                  f"outright win rate per castle: {[round(x, 4) for x in s['castle_win_rates']]}", ""]

    if g1r:
        lines += ["## game 1 robustness (exact)", "",
                  "| experiment | chosen | exact optimum | optimum score | chosen regret | chosen rank among baselines |",
                  "|---|---:|---|---:|---:|---:|"]
        for r in g1r:
            lines.append(f"| {r['experiment']} | {fmt(r['scores']['chosen'])} | {r['optimum']} | "
                         f"{fmt(r['optimum_score'])} | {fmt(r['chosen_regret'])} | {r['chosen_rank']} of {len(r['scores'])} |")
        lines.append("")

    if g2r:
        lines += ["## game 2 robustness (paired, same groups for every allocation)", "",
                  "| experiment | chosen payout | best tested | chosen minus best other, 95% ci | search found |",
                  "|---|---:|---|---|---|"]
        for r in g2r:
            others = r["chosen_minus_other"]
            rival = min(others, key=lambda n: others[n]["mean"])
            d = others[rival]
            verdict = "chosen ahead" if d["ci95"][0] > 0 else "chosen behind" if d["ci95"][1] < 0 else "unresolved"
            lines.append(f"| {r['experiment']} | {fmt(r['results']['chosen']['mean'])} | {r['best_tested']} | "
                         f"{rival}: {fmt(d['mean'])} [{fmt(d['ci95'][0])}, {fmt(d['ci95'][1])}] {verdict} "
                         f"| {r['searched_best']} |")
        lines.append("")
    (results_dir / "summary.md").write_text("\n".join(lines))


def build(cfg, results_dir):
    g1 = load(results_dir / "game1/summary.json")
    fresh = load(results_dir / "fresh_check.json")
    g1r = load(results_dir / "robustness/game1.json")
    g2r = load(results_dir / "robustness/game2.json")
    figures = results_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    if g1 and fresh:
        fig_scenarios(g1, fresh, figures / "scenarios.png")
    if fresh and g2r:
        fig_paired(fresh, g2r, figures / "paired.png")
    if g1r and g2r:
        fig_prevalence(g1r, g2r, figures / "prevalence.png")
    fig_allocations(cfg, figures / "allocations.png")
    summary_markdown(results_dir)
