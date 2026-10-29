"""synthetic opponent pools.

all opponents are made up from templates and random draws. none are real entries.
the order of random calls matches reference/originals so seeds give the same pools.
"""
import numpy as np

from castle import game1
from castle.scoring import VALUES


def round_rows(x):
    """round each row to integers totaling 100, giving leftovers to the largest fractions."""
    a = np.floor(x).astype(np.int16)
    missing = 100 - a.sum(axis=1)
    order = np.argsort(x - a, axis=1)[:, ::-1]
    for j in range(5):
        rows = np.flatnonzero(missing > j)
        a[rows, order[rows, j]] += 1
    assert np.all(a.sum(axis=1) == 100)
    return a


def soften(rng, templates, n, scale, atom):
    """pick a template, add gaussian noise, renormalize. with probability atom keep it exact."""
    base = np.asarray(templates)[rng.integers(len(templates), size=n)]
    x = np.maximum(0, base + rng.normal(0, scale, base.shape))
    a = round_rows(x / x.sum(axis=1, keepdims=True) * 100)
    exact = rng.random(n) < atom
    a[exact] = base[exact]
    return a


def diverse(rng, n, castles_used, castles_used_p, concentration):
    """random castles (higher values more likely), random dirichlet split between them."""
    rows = []
    for _ in range(n):
        k = rng.choice(castles_used, p=castles_used_p)
        active = rng.choice(5, size=k, replace=False, p=VALUES / VALUES.sum())
        x = np.zeros(5)
        x[active] = rng.dirichlet(VALUES[active] * rng.choice(concentration)) * 100
        rows.append(x)
    return round_rows(np.array(rows))


def build_family(rng, spec, n, families, scale_factor=1.0, atom_factor=1.0):
    if "castles_used" in spec:
        return diverse(rng, n, spec["castles_used"], spec["castles_used_p"], spec["concentration"])
    if "responses" in spec:
        g = np.array([game1.gains(pool) for pool in families.values()])
        templates = []
        for _ in range(spec["responses"]):
            weights = rng.dirichlet(spec["dirichlet"])
            templates.append(game1.best_response(np.einsum("f,fij->ij", weights, g))[0])
        spec = dict(spec, templates=templates)
    scale = spec["scale"] * scale_factor
    atom = min(1.0, spec["atom"] * atom_factor)
    return soften(rng, spec["templates"], n, scale, atom)


def build_families(specs, seed, n, scale_factor=1.0, atom_factor=1.0):
    """returns the pools and the generator, whose state later steps continue from."""
    rng = np.random.default_rng(seed)
    families = {}
    for name, spec in specs.items():
        families[name] = build_family(rng, spec, n, families, scale_factor, atom_factor)
    return families, rng


def sample_groups(families, weights, per_scenario, seed):
    """for each scenario row, draw opponent triples: a family by weight, then a pool member."""
    rng = np.random.default_rng(seed)
    groups = []
    for row in weights:
        family = rng.choice(len(families), size=(per_scenario, 3), p=row)
        triples = np.empty((per_scenario, 3, 5), dtype=np.int16)
        for i, pool in enumerate(families.values()):
            use = family == i
            triples[use] = pool[rng.integers(len(pool), size=int(use.sum()))]
        groups.append(triples)
    return np.concatenate(groups)
