"""rules of both games.

points are kept as 12 x castle points: 12 splits evenly between 1, 2, 3 or 4
tied bidders, so every score is an exact integer.
"""
import numpy as np

VALUES = np.arange(1, 6)
PAYOUTS = (9, 4, 2, 0)
SCALE = 12


def check(allocation):
    a = np.asarray(allocation)
    if a.shape != (5,) or a.dtype.kind not in "iu" or (a < 0).any() or a.sum() != 100:
        raise ValueError(f"need five nonnegative integers totaling 100, got {allocation}")
    return a


def all_allocations(total=100):
    """every way to split total into five nonnegative integers, in lexicographic order."""
    rows = []
    for a in range(total + 1):
        for b in range(total + 1 - a):
            for c in range(total + 1 - a - b):
                d = np.arange(total + 1 - a - b - c, dtype=np.int16)
                rows.append(np.column_stack([np.full(len(d), a), np.full(len(d), b),
                                             np.full(len(d), c), d, total - a - b - c - d]))
    return np.vstack(rows).astype(np.int16)


# ---- reference scorer: slow and plain, used to check the fast one

def castle_points(players):
    """12 x castle points per player. a castle's top bidders split its value."""
    points = [0] * len(players)
    for castle, value in enumerate(VALUES):
        bids = [player[castle] for player in players]
        top = max(bids)
        winners = [i for i, bid in enumerate(bids) if bid == top]
        for i in winners:
            points[i] += SCALE * int(value) // len(winners)
    return points


def placement_payouts(points):
    """players tied in the ranking average the payouts of the places they share."""
    payouts = []
    for p in points:
        higher = sum(q > p for q in points)
        tied = sum(q == p for q in points)
        payouts.append(sum(PAYOUTS[higher:higher + tied]) / tied)
    return payouts


def duel(a, b):
    """game 1: castle points for a and b."""
    pa, pb = castle_points([check(a), check(b)])
    return pa / SCALE, pb / SCALE


def four_way(players):
    """game 2: placement payout for each of four players."""
    return placement_payouts(castle_points([check(p) for p in players]))


# ---- fast scorer: same rules on numpy arrays

def payout_table():
    """pay12[h, e]: 12 x our payout with h opponents above us and e tied with us."""
    pay12 = np.zeros((4, 4), dtype=np.int64)
    for h in range(4):
        for e in range(4 - h):
            pay12[h, e] = SCALE * sum(PAYOUTS[h:h + e + 1]) // (e + 1)
    return pay12


PAY12 = payout_table()


def our_payout12(points12):
    """points12[..., 0] is us, [..., 1:] the opponents."""
    own = points12[..., :1]
    higher = (points12[..., 1:] > own).sum(axis=-1)
    tied = (points12[..., 1:] == own).sum(axis=-1)
    return PAY12[higher, tied]


def group_points12(players):
    """players: (groups, 4, 5) bids -> (groups, 4) 12 x castle points."""
    winners = players == players.max(axis=1, keepdims=True)
    split = SCALE * VALUES // winners.sum(axis=1)
    return (winners * split[:, None, :]).sum(axis=2)


def play(allocation, opponents):
    """our allocation against every (3, 5) opponent triple. returns per group detail."""
    own = np.broadcast_to(check(allocation), (len(opponents), 1, 5))
    players = np.concatenate([own, opponents], axis=1)
    points12 = group_points12(players)
    higher = (points12[:, 1:] > points12[:, :1]).sum(axis=1)
    tied = (points12[:, 1:] == points12[:, :1]).sum(axis=1)
    return {
        "payout": PAY12[higher, tied] / SCALE,
        "points": points12[:, 0] / SCALE,
        "sole_first": (higher == 0) & (tied == 0),
        "tied_first": (higher == 0) & (tied > 0),
        "castle_wins": players[:, 0, :] > players[:, 1:, :].max(axis=1),
    }


# ---- table scorer: precomputes every bid 0..100 so a search can score many allocations

def castle_table(opponents):
    """table[j, x, g, p]: 12 x points player p gets at castle j of group g when we bid x."""
    groups = len(opponents)
    table = np.zeros((5, 101, groups, 4), dtype=np.int8)
    for j in range(5):
        bids = opponents[:, :, j]
        top = bids.max(axis=1)
        winners = bids == top[:, None]
        count = winners.sum(axis=1)
        for x in range(101):
            win, tie = x > top, x == top
            table[j, x, win, 0] = SCALE * (j + 1)
            table[j, x, tie, 0] = SCALE * (j + 1) // (count[tie] + 1)
            share = SCALE * (j + 1) // (count + tie)
            share[win] = 0
            table[j, x, :, 1:] = winners * share[:, None]
    return table


def evaluate(allocations, table, scenarios, chunk=256):
    """mean payout of each allocation in each scenario (groups are stored scenario by scenario)."""
    allocations = np.asarray(allocations)
    per = table.shape[2] // scenarios
    out = np.empty((len(allocations), scenarios))
    for start in range(0, len(allocations), chunk):
        a = allocations[start:start + chunk]
        points12 = sum(table[j, a[:, j]].astype(np.int16) for j in range(5))
        total = our_payout12(points12).reshape(len(a), scenarios, per).sum(axis=2)
        out[start:start + chunk] = total / (12.0 * per)
    return out
