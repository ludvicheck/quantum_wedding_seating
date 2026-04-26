from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable, Optional

import dimod

# Prefer the clique sampler for dense BQMs.
try:
    from dwave.system import DWaveCliqueSampler
    HAVE_CLIQUE = True
except Exception:
    DWaveCliqueSampler = None
    HAVE_CLIQUE = False

try:
    from dwave.system import DWaveSampler, EmbeddingComposite
    HAVE_EMBED = True
except Exception:
    DWaveSampler = None
    EmbeddingComposite = None
    HAVE_EMBED = False


# =========================
# 1) INPUT DATA
# =========================

GUESTS = [
    "Foggy", "Lily", "Jana", "Ludek", "Majda", "Honza", "Leny", "Lea",
    "Kemr", "Kaja", "Vladimir", "Lena", "Natalie", "Paolo", "Max",
    "Martina", "Ludvajz", "Poli"
]

GROOM = "Ludvajz"
BRIDE = "Poli"

PAIR_COUPLES = [
    ("Foggy", "Lily"),
    ("Jana", "Ludek"),
    ("Majda", "Honza"),
    ("Leny", "Lea"),
    ("Kemr", "Kaja"),
    ("Vladimir", "Lena"),
    ("Natalie", "Paolo"),
    ("Max", "Martina"),
    ("Ludvajz", "Poli"),
]

DIST_UPPER = [
    [0,1,2,3,4,5,6,7,8,9,8,7,6,5,4,3,2,1],
    [0,1,2,3,4,5,6,7,8,7,6,5,4,3,2,1,2],
    [0,1,2,3,4,5,6,7,6,5,4,3,2,1,2,3],
    [0,1,2,3,4,5,6,5,4,3,2,1,2,3,4],
    [0,1,2,3,4,5,4,3,2,1,2,3,4,5],
    [0,1,2,3,4,3,2,1,2,3,4,5,6],
    [0,1,2,3,2,1,2,3,4,5,6,7],
    [0,1,2,1,2,3,4,5,6,7,8],
    [0,1,2,3,4,5,6,7,8,9],
    [0,1,2,3,4,5,6,7,8],
    [0,1,2,3,4,5,6,7],
    [0,1,2,3,4,5,6],
    [0,1,2,3,4,5],
    [0,1,2,3,4],
    [0,1,2,3],
    [0,1,2],
    [0,1],
    [0],
]

PREF_UPPER = [
    [0, 5, -3, -5, -3, -2, 4, 1, 3, 0, 1, 0, 0, 0, 0, 0, 4, 3],
    [0, -3, -1, -1, 0, 3, 0, 0, 0, 2, 3, 2, 0, 1, 0, 2, 3],
    [0, 5, 4, 4, 4, 3, 2, 1, 0, 0, 3, 0, 1, 1, 4, 3],
    [0, -4, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, -3, -1],
    [0, 5, 4, 3, 1, 1, 0, 0, 2, 0, 1, 1, 4, 4],
    [0, 4, 2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1],
    [0, 5, 4, 1, 0, 0, 1, 0, 2, 1, 4, 4],
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 2, 3],
    [0, 5, 0, 0, 0, 0, 1, 0, 4, 3],
    [0, 0, 0, 0, 0, 0, 1, 1, 1],
    [0, 5, -5, -4, -5, -5, 3, 3],
    [0, -5, -4, -5, -5, 3, 4],
    [0, 5, 4, 4, 3, 4],
    [0, 3, 2, 1, 3],
    [0, 5, 2, 4],
    [0, 1, 3],
    [0, 5],
    [0],
]


# =========================
# 2) HELPERS
# =========================

def symmetrize_upper_triangle(rows, n):
    if len(rows) != n:
        raise ValueError(f"Expected {n} rows, got {len(rows)}")
    m = [[None] * n for _ in range(n)]
    for i, row in enumerate(rows):
        expected = n - i
        if len(row) != expected:
            raise ValueError(
                f"Row {i} has length {len(row)}, expected {expected}. Row={row}"
            )
        for k, val in enumerate(row):
            j = i + k
            m[i][j] = val
            m[j][i] = val
    return m


def build_same_side_adjacency(n=18):
    adj = [[0] * n for _ in range(n)]
    for a in range(0, 8):
        adj[a][a + 1] = 1
        adj[a + 1][a] = 1
    for a in range(9, 17):
        adj[a][a + 1] = 1
        adj[a + 1][a] = 1
    return adj


def build_opposite_adjacency(n=18):
    opp = [[0] * n for _ in range(n)]
    for top in range(0, 9):
        bottom = 17 - top
        opp[top][bottom] = 1
        opp[bottom][top] = 1
    return opp


def seat_var(guest: str, seat: int) -> Tuple[str, int]:
    return (guest, seat)


def add_exactly_one(bqm: dimod.BinaryQuadraticModel, vars_: List[Tuple[str, int]], strength: float):
    # strength * (sum(x_i) - 1)^2
    # = strength * ( -sum x_i + 2*sum_{i<j} x_i x_j + 1 )
    bqm.offset += strength
    for v in vars_:
        bqm.add_variable(v, -strength)
    for i in range(len(vars_)):
        for j in range(i + 1, len(vars_)):
            bqm.add_interaction(vars_[i], vars_[j], 2.0 * strength)


def add_forbidden_linear(
    bqm: dimod.BinaryQuadraticModel,
    var: Tuple[str, int],
    strength: float,
):
    # Penalize x=1 by +strength
    bqm.add_variable(var, strength)


def add_forbidden_pair(
    bqm: dimod.BinaryQuadraticModel,
    var_u,
    var_v,
    strength: float,
):
    # Penalize x_u = x_v = 1 by +strength
    bqm.add_interaction(var_u, var_v, strength)


def pretty_print_solution(guests, seat_of_guest):
    top = [None] * 9
    bottom = [None] * 9
    for g, s in seat_of_guest.items():
        if 1 <= s <= 9:
            top[s - 1] = g
        else:
            bottom[s - 10] = g

    print("\nTop side (seats 1..9, left -> right):")
    for idx, g in enumerate(top, start=1):
        print(f"  Seat {idx:2d}: {g}")

    print("\nBottom side (seats 10..18, left -> right):")
    for idx, g in enumerate(bottom, start=10):
        print(f"  Seat {idx:2d}: {g}")


def seat_of_guest_from_sample(sample: Dict[Tuple[str, int], int], guests: List[str]) -> Dict[str, int]:
    out = {}
    for g in guests:
        chosen = [s for s in range(len(guests)) if sample.get(seat_var(g, s), 0) > 0]
        if len(chosen) == 1:
            out[g] = chosen[0] + 1
    return out


def score_solution(
    guests,
    seat_of_guest,
    pref,
    dist,
    same_side_adj,
    alpha_closeness=10,
    beta_pair_dist1=40,
    gamma_pair_same_side=12,
):
    idx = {g: i for i, g in enumerate(guests)}
    total = 0
    terms = []

    for i in range(len(guests)):
        for j in range(i + 1, len(guests)):
            gi, gj = guests[i], guests[j]
            si, sj = seat_of_guest[gi] - 1, seat_of_guest[gj] - 1
            closeness = alpha_closeness - dist[si][sj]
            contrib = pref[i][j] * closeness
            total += contrib
            if contrib != 0:
                terms.append((contrib, f"pref {gi} - {gj}: {pref[i][j]} * (10-d={closeness})"))

    couples = set(tuple(sorted(p)) for p in PAIR_COUPLES)
    for a, b in couples:
        ia, ib = idx[a], idx[b]
        sa, sb = seat_of_guest[a] - 1, seat_of_guest[b] - 1
        if dist[sa][sb] == 1:
            total += beta_pair_dist1
            terms.append((beta_pair_dist1, f"pair distance-1 bonus: {a} - {b}"))
        if same_side_adj[sa][sb] == 1:
            total += gamma_pair_same_side
            terms.append((gamma_pair_same_side, f"pair same-side-adj bonus: {a} - {b}"))

    return total, sorted(terms, reverse=True, key=lambda x: x[0])


def is_feasible(
    sample: Dict[Tuple[str, int], int],
    guests: List[str],
    dist: List[List[int]],
    same_side_adj: List[List[int]],
    pair_couples: List[Tuple[str, str]],
    groom: str,
    bride: str,
    end_case: str,
) -> bool:
    n = len(guests)
    seat_of = seat_of_guest_from_sample(sample, guests)
    if len(seat_of) != n:
        return False

    # one seat per seat
    used = list(seat_of.values())
    if len(set(used)) != n:
        return False

    # groom/bride middle hard constraint
    s_groom = seat_of[groom]
    s_bride = seat_of[bride]
    if {s_groom, s_bride} not in ({4, 5}, {5, 6}):
        return False

    # all couples distance 1
    for a, b in pair_couples:
        sa = seat_of[a] - 1
        sb = seat_of[b] - 1
        if dist[sa][sb] != 1:
            return False

    # Poli and Natalie same-side adjacent
    if same_side_adj[seat_of["Poli"] - 1][seat_of["Natalie"] - 1] != 1:
        return False

    # end-case hard rules
    lj = {seat_of["Leny"], seat_of["Jana"]}
    mm = {seat_of["Max"], seat_of["Martina"]}
    left = {1, 18}
    right = {9, 10}

    if end_case == "lj_left_mm_right":
        if lj != left or mm != right:
            return False
    elif end_case == "lj_right_mm_left":
        if lj != right or mm != left:
            return False
    else:
        raise ValueError(end_case)

    return True


@dataclass
class Penalties:
    assignment_guest: float = 140.0
    assignment_seat: float = 140.0
    hard_pair_dist1: float = 120.0
    hard_middle: float = 120.0
    hard_same_side_adj: float = 120.0
    hard_fixed_end: float = 140.0


# =========================
# 3) BUILD BQM
# =========================

def build_wedding_bqm(
    guests: List[str],
    pref: List[List[int]],
    dist: List[List[int]],
    same_side_adj: List[List[int]],
    pair_couples: List[Tuple[str, str]],
    groom: str,
    bride: str,
    end_case: str,
    penalties: Penalties = Penalties(),
    alpha_closeness: int = 10,
    beta_pair_dist1: int = 40,
    gamma_pair_same_side: int = 12,
    interaction_distance_cutoff: Optional[int] = None,
    min_abs_preference_for_objective: int = 1,
) -> dimod.BinaryQuadraticModel:
    """
    Build a QUBO/BQM for direct QPU submission.

    end_case:
      - 'lj_left_mm_right'
      - 'lj_right_mm_left'

    interaction_distance_cutoff:
      If not None, include general preference terms only for seat pairs with
      dist <= cutoff. This is a sparsification knob that can make embeddings
      easier on real QPUs.
    """
    n = len(guests)
    idx = {g: i for i, g in enumerate(guests)}
    bqm = dimod.BinaryQuadraticModel({}, {}, 0.0, dimod.BINARY)

    # One-hot constraints.
    for g in guests:
        add_exactly_one(bqm, [seat_var(g, s) for s in range(n)], penalties.assignment_guest)
    for s in range(n):
        add_exactly_one(bqm, [seat_var(g, s) for g in guests], penalties.assignment_seat)

    # General preference objective (reward = negative energy).
    for i in range(n):
        for j in range(i + 1, n):
            p = pref[i][j]
            if abs(p) < min_abs_preference_for_objective:
                continue
            gi, gj = guests[i], guests[j]
            for si in range(n):
                for sj in range(n):
                    if si == sj:
                        continue
                    if interaction_distance_cutoff is not None and dist[si][sj] > interaction_distance_cutoff:
                        continue
                    closeness = alpha_closeness - dist[si][sj]
                    coeff = p * closeness
                    if coeff != 0:
                        bqm.add_interaction(seat_var(gi, si), seat_var(gj, sj), -float(coeff))

    # Couple bonuses.
    for a_name, b_name in set(tuple(sorted(p)) for p in pair_couples):
        for sa in range(n):
            for sb in range(n):
                if sa == sb:
                    continue
                if dist[sa][sb] == 1:
                    bqm.add_interaction(seat_var(a_name, sa), seat_var(b_name, sb), -float(beta_pair_dist1))
                if same_side_adj[sa][sb] == 1:
                    bqm.add_interaction(seat_var(a_name, sa), seat_var(b_name, sb), -float(gamma_pair_same_side))

    # Hard: all couples at distance 1.
    for a_name, b_name in pair_couples:
        for sa in range(n):
            for sb in range(n):
                if sa == sb:
                    continue
                if dist[sa][sb] != 1:
                    add_forbidden_pair(
                        bqm,
                        seat_var(a_name, sa),
                        seat_var(b_name, sb),
                        penalties.hard_pair_dist1,
                    )

    # Hard: groom/bride in middle ({4,5} or {5,6} in 1-based seats).
    allowed_middle_pairs = {(3, 4), (4, 3), (4, 5), (5, 4)}
    for sa in range(n):
        for sb in range(n):
            if sa == sb:
                continue
            if (sa, sb) not in allowed_middle_pairs:
                add_forbidden_pair(
                    bqm,
                    seat_var(groom, sa),
                    seat_var(bride, sb),
                    penalties.hard_middle,
                )

    # Hard: Poli and Natalie same-side adjacent.
    for sp in range(n):
        for sn in range(n):
            if sp == sn:
                continue
            if same_side_adj[sp][sn] != 1:
                add_forbidden_pair(
                    bqm,
                    seat_var("Poli", sp),
                    seat_var("Natalie", sn),
                    penalties.hard_same_side_adj,
                )

    # Hard: selected end case.
    if end_case == "lj_left_mm_right":
        allowed = {
            "Leny": {0, 17},
            "Jana": {0, 17},
            "Max": {8, 9},
            "Martina": {8, 9},
        }
    elif end_case == "lj_right_mm_left":
        allowed = {
            "Leny": {8, 9},
            "Jana": {8, 9},
            "Max": {0, 17},
            "Martina": {0, 17},
        }
    else:
        raise ValueError("end_case must be 'lj_left_mm_right' or 'lj_right_mm_left'")

    for g, seatset in allowed.items():
        for s in range(n):
            if s not in seatset:
                add_forbidden_linear(bqm, seat_var(g, s), penalties.hard_fixed_end)

    return bqm


# =========================
# 4) SOLVE ON QPU
# =========================

def try_get_sampler(prefer_clique: bool = True, prefer_advantage2: bool = True):
    if prefer_clique and HAVE_CLIQUE:
        solver = {"category": "qpu"}
        if prefer_advantage2:
            solver["topology__type"] = "zephyr"
        return DWaveCliqueSampler(solver=solver)

    if HAVE_EMBED:
        solver = {"category": "qpu"}
        if prefer_advantage2:
            solver["topology__type"] = "zephyr"
        return EmbeddingComposite(DWaveSampler(solver=solver))

    raise RuntimeError(
        "No D-Wave QPU sampler imports succeeded. Install dwave-ocean-sdk and configure your Leap token."
    )


def solve_one_case_qpu(
    end_case: str,
    num_reads: int = 200,
    interaction_distance_cutoff: Optional[int] = None,
    min_abs_preference_for_objective: int = 1,
    penalties: Penalties = Penalties(),
    prefer_clique: bool = True,
    prefer_advantage2: bool = True,
    label: Optional[str] = None,
):
    n = len(GUESTS)
    dist = symmetrize_upper_triangle(DIST_UPPER, n)
    pref = symmetrize_upper_triangle(PREF_UPPER, n)
    same_side = build_same_side_adjacency(n)

    bqm = build_wedding_bqm(
        guests=GUESTS,
        pref=pref,
        dist=dist,
        same_side_adj=same_side,
        pair_couples=PAIR_COUPLES,
        groom=GROOM,
        bride=BRIDE,
        end_case=end_case,
        penalties=penalties,
        interaction_distance_cutoff=interaction_distance_cutoff,
        min_abs_preference_for_objective=min_abs_preference_for_objective,
    )

    sampler = try_get_sampler(prefer_clique=prefer_clique, prefer_advantage2=prefer_advantage2)
    kwargs = dict(num_reads=num_reads, auto_scale=True)
    if label is not None:
        kwargs["label"] = label

    sampleset = sampler.sample(bqm, **kwargs)

    feasible = []
    for rec in sampleset.data(["sample", "energy", "num_occurrences"]):
        sample = dict(rec.sample)
        if is_feasible(sample, GUESTS, dist, same_side, PAIR_COUPLES, GROOM, BRIDE, end_case):
            seat_of = seat_of_guest_from_sample(sample, GUESTS)
            raw_score, _ = score_solution(
                guests=GUESTS,
                seat_of_guest=seat_of,
                pref=pref,
                dist=dist,
                same_side_adj=same_side,
            )
            feasible.append((rec.energy, rec.num_occurrences, seat_of, raw_score))

    feasible.sort(key=lambda t: (t[0], -t[1], -t[3]))
    return bqm, sampleset, feasible


def solve_both_cases_qpu(
    num_reads: int = 200,
    interaction_distance_cutoff: Optional[int] = None,
    min_abs_preference_for_objective: int = 1,
    penalties: Penalties = Penalties(),
    prefer_clique: bool = True,
    prefer_advantage2: bool = True,
):
    results = {}
    for end_case in ("lj_left_mm_right", "lj_right_mm_left"):
        bqm, sampleset, feasible = solve_one_case_qpu(
            end_case=end_case,
            num_reads=num_reads,
            interaction_distance_cutoff=interaction_distance_cutoff,
            min_abs_preference_for_objective=min_abs_preference_for_objective,
            penalties=penalties,
            prefer_clique=prefer_clique,
            prefer_advantage2=prefer_advantage2,
            label=f"wedding-seating-{end_case}",
        )
        results[end_case] = dict(bqm=bqm, sampleset=sampleset, feasible=feasible)

    # pick best feasible solution by raw wedding score, then energy
    best = None
    for end_case, result in results.items():
        if result["feasible"]:
            energy, occ, seat_of, raw_score = result["feasible"][0]
            candidate = (raw_score, -energy, occ, end_case, seat_of)
            if best is None or candidate > best:
                best = candidate

    return results, best


# =========================
# 5) LOCAL DEBUG / CLASSICAL CHECK
# =========================

def solve_classically_with_sa(
    end_case: str,
    num_reads: int = 2000,
    interaction_distance_cutoff: Optional[int] = None,
    min_abs_preference_for_objective: int = 1,
    penalties: Penalties = Penalties(),
):
    sampler = dimod.SimulatedAnnealingSampler()
    n = len(GUESTS)
    dist = symmetrize_upper_triangle(DIST_UPPER, n)
    pref = symmetrize_upper_triangle(PREF_UPPER, n)
    same_side = build_same_side_adjacency(n)

    bqm = build_wedding_bqm(
        guests=GUESTS,
        pref=pref,
        dist=dist,
        same_side_adj=same_side,
        pair_couples=PAIR_COUPLES,
        groom=GROOM,
        bride=BRIDE,
        end_case=end_case,
        penalties=penalties,
        interaction_distance_cutoff=interaction_distance_cutoff,
        min_abs_preference_for_objective=min_abs_preference_for_objective,
    )
    sampleset = sampler.sample(bqm, num_reads=num_reads)

    feasible = []
    for rec in sampleset.data(["sample", "energy", "num_occurrences"]):
        sample = dict(rec.sample)
        if is_feasible(sample, GUESTS, dist, same_side, PAIR_COUPLES, GROOM, BRIDE, end_case):
            seat_of = seat_of_guest_from_sample(sample, GUESTS)
            raw_score, _ = score_solution(
                guests=GUESTS,
                seat_of_guest=seat_of,
                pref=pref,
                dist=dist,
                same_side_adj=same_side,
            )
            feasible.append((rec.energy, rec.num_occurrences, seat_of, raw_score))

    feasible.sort(key=lambda t: (t[0], -t[1], -t[3]))
    return bqm, sampleset, feasible


if __name__ == "__main__":
    # Before using a real QPU:
    #   pip install dwave-ocean-sdk
    #   dwave setup
    # and make sure your Leap account has QPU access.

    # 1) First, test the formulation locally with simulated annealing.
    for end_case in ("lj_left_mm_right", "lj_right_mm_left"):
        bqm, sampleset, feasible = solve_classically_with_sa(
            end_case=end_case,
            num_reads=3000,
            interaction_distance_cutoff=3,  # sparsify; set to None for the full dense objective
            min_abs_preference_for_objective=1,
        )
        print(f"\nCASE = {end_case}")
        print("Logical variables:", len(bqm.variables))
        print("Quadratic terms:", len(bqm.quadratic))
        if feasible:
            best_energy, occ, seat_of_guest, raw_score = feasible[0]
            print("Best feasible SA energy:", best_energy)
            print("Best feasible raw wedding score:", raw_score)
            pretty_print_solution(GUESTS, seat_of_guest)
        else:
            print("No feasible sample found in simulated annealing run.")

    # 2) Uncomment this once you have Leap QPU access.
    # results, best = solve_both_cases_qpu(
    #     num_reads=200,
    #     interaction_distance_cutoff=3,  # start sparse; increase later if embedding succeeds
    #     min_abs_preference_for_objective=1,
    #     prefer_clique=True,
    #     prefer_advantage2=True,
    # )
    #
    # if best is None:
    #     print("No feasible QPU sample found in either case.")
    # else:
    #     raw_score, neg_energy, occ, end_case, seat_of_guest = best
    #     print("\nBEST QPU CASE:", end_case)
    #     print("Best feasible raw wedding score:", raw_score)
    #     pretty_print_solution(GUESTS, seat_of_guest)
