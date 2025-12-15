from analysis.frontier.frontier import Constraint, Component
from analysis.probability.enumeration import ProbResult, ProbabilityEngine, enumerate_component

def test_component_cache_reuse_across_board_positions(monkeypatch):
    calls = {"count": 0}

    def fake_enumerate(comp):
        calls["count"] += 1
        return ProbResult(solutions=2, mine_counts=(1, 1))

    engine = ProbabilityEngine(max_k=10, cache_size=8)
    monkeypatch.setattr(
        "analysis.probability.enumeration.enumerate_component",
        fake_enumerate
    )

    # Component A (location 1)
    comp_a = Component(
        k=2,
        constraints=[
            Constraint(mask_local=0b11, mask_global=0b1100, remaining=1)
        ],
        local_to_global=[10, 11]
    )

    # Component B (same logic, different location)
    comp_b = Component(
        k=2,
        constraints=[
            Constraint(mask_local=0b11, mask_global=0b0011, remaining=1)
        ],
        local_to_global=[42, 43]
    )

    r1 = engine.get_component_result(comp_a)
    r2 = engine.get_component_result(comp_b)

    assert r1 == r2
    assert calls["count"] == 1   # ← THIS is the money line
