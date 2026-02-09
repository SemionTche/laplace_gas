from laplace_gas.core.conversions import bar_to_propar, propar_to_bar

def test_roundtrip():
    cap = 10.0
    for p in (0, 1, 5, 9.5):
        raw = bar_to_propar(p, cap)
        assert abs(propar_to_bar(raw, cap) - p) < 0.01