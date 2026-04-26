from ortools.sat.python import cp_model

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
    # 1<->18, 2<->17, ..., 9<->10
    for top in range(0, 9):
        bottom = 17 - top
        opp[top][bottom] = 1
        opp[bottom][top] = 1
    return opp


def add_fixed_end_pair(model, x, i, j, seat_a, seat_b, active_bool, prefix):
    z1 = model.NewBoolVar(f"{prefix}_order1")  # i->seat_a, j->seat_b
    z2 = model.NewBoolVar(f"{prefix}_order2")  # i->seat_b, j->seat_a

    model.Add(z1 + z2 == 1).OnlyEnforceIf(active_bool)
    model.Add(z1 + z2 == 0).OnlyEnforceIf(active_bool.Not())

    model.Add(x[i, seat_a] == 1).OnlyEnforceIf(z1)
    model.Add(x[j, seat_b] == 1).OnlyEnforceIf(z1)

    model.Add(x[i, seat_b] == 1).OnlyEnforceIf(z2)
    model.Add(x[j, seat_a] == 1).OnlyEnforceIf(z2)

    return z1, z2


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


def score_solution(
    guests,
    seat_of_guest,
    pref,
    dist,
    same_side_adj,
    alpha_closeness=10,
    beta_pair_dist1=40,
    gamma_pair_same_side=12,
    groom_bride_middle_bonus=80,
    groom_bride_same_side_bonus=50,
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

    s_groom = seat_of_guest[GROOM]
    s_bride = seat_of_guest[BRIDE]
    if {s_groom, s_bride} == {4, 5} or {s_groom, s_bride} == {5, 6}:
        total += groom_bride_middle_bonus
        terms.append((groom_bride_middle_bonus, "groom+bride middle bonus"))
    if same_side_adj[s_groom - 1][s_bride - 1] == 1:
        total += groom_bride_same_side_bonus
        terms.append((groom_bride_same_side_bonus, "groom+bride same-side adjacency bonus"))

    return total, sorted(terms, reverse=True, key=lambda x: x[0])

# =========================
# 3) VALIDATE INPUT
# =========================

n = len(GUESTS)
DIST = symmetrize_upper_triangle(DIST_UPPER, n)
PREF = symmetrize_upper_triangle(PREF_UPPER, n)

for i in range(n):
    if DIST[i][i] != 0:
        raise ValueError(f"Distance diagonal should be 0 at ({i},{i})")
    if PREF[i][i] != 0:
        raise ValueError(f"Preference diagonal should be 0 at ({i},{i})")

name_to_idx = {g: i for i, g in enumerate(GUESTS)}
for a, b in PAIR_COUPLES:
    ia, ib = name_to_idx[a], name_to_idx[b]
    if PREF[ia][ib] != 5:
        print(f"WARNING: declared pair ({a}, {b}) has preference {PREF[ia][ib]}, not 5")

SAME_SIDE_ADJ = build_same_side_adjacency(n)
OPPOSITE_ADJ = build_opposite_adjacency(n)
DIST1 = [[1 if DIST[i][j] == 1 else 0 for j in range(n)] for i in range(n)]

# =========================
# 4) MODEL
# =========================

def solve_wedding_seating(
    guests,
    pref,
    dist,
    same_side_adj,
    dist1,
    pair_couples,
    groom,
    bride,
    alpha_closeness=10,
    beta_pair_dist1=40,
    gamma_pair_same_side=12,
    groom_bride_middle_bonus=80,
    groom_bride_same_side_bonus=50,
    time_limit_sec=60,
    num_workers=8,
):
    n = len(guests)
    idx = {g: i for i, g in enumerate(guests)}
    model = cp_model.CpModel()

    x = {}
    for g in range(n):
        for s in range(n):
            x[g, s] = model.NewBoolVar(f"x_{g}_{s}")

    # One seat per guest
    for g in range(n):
        model.Add(sum(x[g, s] for s in range(n)) == 1)

    # One guest per seat
    for s in range(n):
        model.Add(sum(x[g, s] for g in range(n)) == 1)

    # Groom & bride in the middle: {4,5} or {5,6}
    groom_i = idx[groom]
    bride_i = idx[bride]

    # Hard constraint: Poli and Natalie must be same-side adjacent
    poli_i = idx["Poli"]
    natalie_i = idx["Natalie"]

    poli_natalie_adj = []
    for sp in range(n):
        for sn in range(n):
            if same_side_adj[sp][sn] == 1:
                z = model.NewBoolVar(f"poli_natalie_adj_{sp}_{sn}")
                model.AddBoolAnd([x[poli_i, sp], x[natalie_i, sn]]).OnlyEnforceIf(z)
                model.AddImplication(z, x[poli_i, sp])
                model.AddImplication(z, x[natalie_i, sn])
                poli_natalie_adj.append(z)

    model.Add(sum(poli_natalie_adj) == 1)


    allowed_middle_pairs = [(3, 4), (4, 3), (4, 5), (5, 4)]
    gb_middle_vars = []
    for a, b in allowed_middle_pairs:
        z = model.NewBoolVar(f"gb_middle_{a}_{b}")
        model.AddBoolAnd([x[groom_i, a], x[bride_i, b]]).OnlyEnforceIf(z)
        model.AddImplication(z, x[groom_i, a])
        model.AddImplication(z, x[bride_i, b])
        gb_middle_vars.append(z)
    model.Add(sum(gb_middle_vars) == 1)

    # All declared couples must be within distance 1
    for a_name, b_name in pair_couples:
        ia, ib = idx[a_name], idx[b_name]
        allowed = []
        for sa in range(n):
            for sb in range(n):
                if dist[sa][sb] == 1:
                    z = model.NewBoolVar(f"pair_{ia}_{ib}_{sa}_{sb}")
                    model.AddBoolAnd([x[ia, sa], x[ib, sb]]).OnlyEnforceIf(z)
                    model.AddImplication(z, x[ia, sa])
                    model.AddImplication(z, x[ib, sb])
                    allowed.append(z)
        model.Add(sum(allowed) == 1)

    # Hard end-placement constraints:
    # Leny & Jana opposite at one end, Max & Martina opposite at the other end.
    # Ends:
    # left end  -> seats 1 and 18 -> zero-based (0,17)
    # right end -> seats 9 and 10 -> zero-based (8,9)
    leny_i = idx["Leny"]
    jana_i = idx["Jana"]
    max_i = idx["Max"]
    martina_i = idx["Martina"]

    lj_left_mm_right = model.NewBoolVar("lj_left_mm_right")
    lj_right_mm_left = model.NewBoolVar("lj_right_mm_left")
    model.Add(lj_left_mm_right + lj_right_mm_left == 1)

    add_fixed_end_pair(model, x, leny_i, jana_i, 0, 17, lj_left_mm_right, "leny_jana_left")
    add_fixed_end_pair(model, x, max_i, martina_i, 8, 9, lj_left_mm_right, "max_martina_right")

    add_fixed_end_pair(model, x, leny_i, jana_i, 8, 9, lj_right_mm_left, "leny_jana_right")
    add_fixed_end_pair(model, x, max_i, martina_i, 0, 17, lj_right_mm_left, "max_martina_left")

    objective_terms = []

    # General pairwise compatibility score
    for i in range(n):
        for j in range(i + 1, n):
            p = pref[i][j]
            if p == 0:
                continue
            for si in range(n):
                for sj in range(n):
                    if si == sj:
                        continue
                    closeness = alpha_closeness - dist[si][sj]
                    coeff = p * closeness
                    if coeff == 0:
                        continue
                    y = model.NewBoolVar(f"y_{i}_{j}_{si}_{sj}")
                    model.AddMultiplicationEquality(y, [x[i, si], x[j, sj]])
                    objective_terms.append(coeff * y)

    # Extra couple bonuses
    couple_set = set(tuple(sorted(p)) for p in pair_couples)
    for a_name, b_name in couple_set:
        ia, ib = idx[a_name], idx[b_name]
        for sa in range(n):
            for sb in range(n):
                if sa == sb:
                    continue
                if dist[sa][sb] == 1:
                    y = model.NewBoolVar(f"bonus_d1_{ia}_{ib}_{sa}_{sb}")
                    model.AddMultiplicationEquality(y, [x[ia, sa], x[ib, sb]])
                    objective_terms.append(beta_pair_dist1 * y)
                if same_side_adj[sa][sb] == 1:
                    y2 = model.NewBoolVar(f"bonus_side_{ia}_{ib}_{sa}_{sb}")
                    model.AddMultiplicationEquality(y2, [x[ia, sa], x[ib, sb]])
                    objective_terms.append(gamma_pair_same_side * y2)

    # Special bride-groom same-side adjacency bonus
    for sa in range(n):
        for sb in range(n):
            if same_side_adj[sa][sb] == 1:
                y = model.NewBoolVar(f"gb_same_side_{sa}_{sb}")
                model.AddMultiplicationEquality(y, [x[groom_i, sa], x[bride_i, sb]])
                objective_terms.append(groom_bride_same_side_bonus * y)

    # Special bride-groom middle-position bonus
    for z in gb_middle_vars:
        objective_terms.append(groom_bride_middle_bonus * z)

    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_sec
    solver.parameters.num_search_workers = num_workers
    solver.parameters.log_search_progress = True

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"No feasible solution found. Solver status = {status}")

    seat_of_guest = {}
    guest_at_seat = {}
    for g in range(n):
        for s in range(n):
            if solver.Value(x[g, s]):
                seat_of_guest[guests[g]] = s + 1
                guest_at_seat[s + 1] = guests[g]
                break

    return solver, seat_of_guest, guest_at_seat

# =========================
# 5) RUN
# =========================

if __name__ == "__main__":
    solver, seat_of_guest, guest_at_seat = solve_wedding_seating(
        guests=GUESTS,
        pref=PREF,
        dist=DIST,
        same_side_adj=SAME_SIDE_ADJ,
        dist1=DIST1,
        pair_couples=PAIR_COUPLES,
        groom=GROOM,
        bride=BRIDE,
        alpha_closeness=10,
        beta_pair_dist1=40,
        gamma_pair_same_side=12,
        groom_bride_middle_bonus=80,
        groom_bride_same_side_bonus=50,
        time_limit_sec=60,
        num_workers=8,
    )

    print("Solver objective value:", solver.ObjectiveValue())
    pretty_print_solution(GUESTS, seat_of_guest)

    total_score, terms = score_solution(
        guests=GUESTS,
        seat_of_guest=seat_of_guest,
        pref=PREF,
        dist=DIST,
        same_side_adj=SAME_SIDE_ADJ,
        alpha_closeness=10,
        beta_pair_dist1=40,
        gamma_pair_same_side=12,
        groom_bride_middle_bonus=80,
        groom_bride_same_side_bonus=50,
    )

    print("\nRecomputed total score:", total_score)
    print("\nTop positive score contributions:")
    for value, description in terms[:25]:
        print(f"  {value:>4}: {description}")