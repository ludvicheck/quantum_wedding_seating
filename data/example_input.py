# data/sample_instance.py

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

# Rectangular table:
# seats 1..9 on one side, 10..18 on the other side.
# Stored as upper-triangular rows including the diagonal.
DIST_UPPER = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 1],
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1, 2],
    [0, 1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1, 2, 3],
    [0, 1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1, 2, 3, 4],
    [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5],
    [0, 1, 2, 3, 4, 3, 2, 1, 2, 3, 4, 5, 6],
    [0, 1, 2, 3, 2, 1, 2, 3, 4, 5, 6, 7],
    [0, 1, 2, 1, 2, 3, 4, 5, 6, 7, 8],
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [0, 1, 2, 3, 4, 5, 6, 7, 8],
    [0, 1, 2, 3, 4, 5, 6, 7],
    [0, 1, 2, 3, 4, 5, 6],
    [0, 1, 2, 3, 4, 5],
    [0, 1, 2, 3, 4],
    [0, 1, 2, 3],
    [0, 1, 2],
    [0, 1],
    [0],
]

# Pairwise preferences, stored as upper-triangular rows including the diagonal.
# Scale:
#   -5 = strongly dislike
#    0 = neutral / do not know each other
#    5 = pair / must be very close
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

# Additional hard constraints used in the current classical model.
HARD_CONSTRAINTS = {
    # Bride and groom must occupy one of these same-side middle placements.
    "groom_bride_middle_pairs_1based": [(4, 5), (5, 4), (5, 6), (6, 5)],

    # Poli and Natalie must be adjacent on the same side.
    "same_side_adjacent_pairs": [
        ("Poli", "Natalie"),
    ],

    # End-placement rule:
    # - Leny and Jana must be opposite at one end
    # - Max and Martina must be opposite at the other end
    # End seat pairs are (1,18) and (9,10).
    "opposite_end_pair_options_1based": {
        "pair_a": ("Leny", "Jana"),
        "pair_b": ("Max", "Martina"),
        "end_pairs": [(1, 18), (9, 10)],
    },
}

# Objective weights used in the current classical run.
DEFAULT_WEIGHTS = {
    "alpha_closeness": 10,
    "beta_pair_dist1": 40,
    "gamma_pair_same_side": 12,
    "groom_bride_middle_bonus": 80,
    "groom_bride_same_side_bonus": 50,
}