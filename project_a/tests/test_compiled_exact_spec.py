
from project_a.implementations.compiled_rules import load_compiled_rules


def slab(lower, upper, rate):
    return {"lower": lower, "upper": upper, "rate": rate}


OLD_BELOW_60 = [
    slab(0, 250000, 0.00),
    slab(250000, 500000, 0.05),
    slab(500000, 1000000, 0.20),
    slab(1000000, None, 0.30),
]

OLD_SENIOR = [
    slab(0, 300000, 0.00),
    slab(300000, 500000, 0.05),
    slab(500000, 1000000, 0.20),
    slab(1000000, None, 0.30),
]

OLD_SUPER_SENIOR = [
    slab(0, 500000, 0.00),
    slab(500000, 1000000, 0.20),
    slab(1000000, None, 0.30),
]


def test_fy_2024_25_new_regime_exact_slabs():
    rules = load_compiled_rules()
    expected = [
            slab(0, 300000, 0.00),
            slab(300000, 700000, 0.05),
            slab(700000, 1000000, 0.10),
            slab(1000000, 1200000, 0.15),
            slab(1200000, 1500000, 0.20),
            slab(1500000, None, 0.30),
        ]
    assert rules["2024-25"]["new_regime"] == expected


def test_fy_2025_26_new_regime_exact_slabs():
    rules = load_compiled_rules()
    expected = [
        slab(0, 400000, 0.00),
        slab(400000, 800000, 0.05),
        slab(800000, 1200000, 0.10),
        slab(1200000, 1600000, 0.15),
        slab(1600000, 2000000, 0.20),
        slab(2000000, 2400000, 0.25),
        slab(2400000, None, 0.30),
    ]
    assert rules["2025-26"]["new_regime"] == expected


def test_old_regime_slabs_exact_in_both_years():
    rules = load_compiled_rules()

    expected_old = {
        "below_60": OLD_BELOW_60,
        "senior_60_to_79": OLD_SENIOR,
        "super_senior_80_plus": OLD_SUPER_SENIOR,
    }

    assert rules["2024-25"]["old_regime"] == expected_old
    assert rules["2025-26"]["old_regime"] == expected_old
