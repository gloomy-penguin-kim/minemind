from analysis.frontier.frontier import Constraint, Component
from analysis.probability.enumeration import ProbResult, enumerate_component, probs_for_component

def mk_comp(k, constraints):
    # local_to_global irrelevant for enumeration
    return Component(k=k, constraints=constraints, local_to_global=list(range(k)))

def test_k1_remaining0():
    # x0 must be SAFE
    comp = mk_comp(1, [Constraint(mask_local=0b1, mask_global=0, remaining=0)])
    res = enumerate_component(comp)
    assert res.solutions == 1
    assert list(res.mine_counts) == [0]

def test_k1_remaining1():
    # x0 must be MINE
    comp = mk_comp(1, [Constraint(mask_local=0b1, mask_global=0, remaining=1)])
    res = enumerate_component(comp)
    assert res.solutions == 1
    assert list(res.mine_counts) == [1]

def test_k2_sum_equals_1():
    # x0 + x1 = 1 -> 2 solutions: 01, 10
    comp = mk_comp(2, [Constraint(mask_local=0b11, mask_global=0, remaining=1)])
    res = enumerate_component(comp)
    assert res.solutions == 2
    assert list(res.mine_counts) == [1, 1]

def test_k3_exactly_two_mines():
    # among 3 vars, exactly 2 mines -> 3 solutions, each var is mine in 2 solutions
    comp = mk_comp(3, [Constraint(mask_local=0b111, mask_global=0, remaining=2)])
    res = enumerate_component(comp)
    assert res.solutions == 3
    assert list(res.mine_counts) == [2, 2, 2]

def test_conflicting_constraints_zero_solutions():
    # x0 = 0 and x0 = 1 simultaneously -> impossible
    comp = mk_comp(1, [
        Constraint(mask_local=0b1, mask_global=0, remaining=0),
        Constraint(mask_local=0b1, mask_global=0, remaining=1),
    ])
    res = enumerate_component(comp)
    assert res.solutions == 0
    assert list(res.mine_counts) == [0]

def test_partial_constraint_allows_free_var():
    # x0 = 1; x1 unconstrained -> 2 solutions: (1,0) and (1,1)
    comp = mk_comp(2, [Constraint(mask_local=0b01, mask_global=0, remaining=1)])
    res = enumerate_component(comp)
    assert res.solutions == 2
    assert list(res.mine_counts) == [2, 1]  # x0 always mine; x1 half the time

def test_two_constraints_overlap():
    # x0 + x1 = 1
    # x1 + x2 = 1
    # Solutions: 010 and 101 -> mines counts: x0:1, x1:1, x2:1 over 2 solutions
    comp = mk_comp(3, [
        Constraint(mask_local=0b011, mask_global=0, remaining=1),
        Constraint(mask_local=0b110, mask_global=0, remaining=1),
    ])
    res = enumerate_component(comp)
    assert res.solutions == 2
    assert list(res.mine_counts) == [1, 1, 1] 

    
def test_probs_projection_skips_cells():
    comp = Component(
        k=2,
        constraints=[Constraint(mask_local=0b11, mask_global=0, remaining=1)],
        local_to_global=[10, 11]   # (r,c) depends on cols
    )
    res = ProbResult(solutions=2, mine_counts=(1, 1))

    cols = 10
    skip = lambda r,c: (r,c) == (1,0)  # gid 10 -> (1,0)

    probs = probs_for_component(comp, res, cols, skip)
    assert (1,0) not in probs
    assert probs[(1,1)] == 0.5


import pytest

from analysis.frontier.frontier import Constraint, Component
from analysis.probability.enumeration import (
    enumerate_component, 
    probs_for_component,
    build_guess_heap,
)
from analysis.probability.enumeration import ProbResult, ProbabilityEngine 
from core.signatures import component_signature


def mk_comp(k, constraints, local_to_global=None):
    if local_to_global is None:
        local_to_global = list(range(k))
    return Component(k=k, constraints=constraints, local_to_global=local_to_global)


# ---------------------------
# Pure enumeration tests
# ---------------------------

def test_k1_remaining0():
    comp = mk_comp(1, [Constraint(mask_local=0b1, mask_global=0, remaining=0)])
    res = enumerate_component(comp)
    assert res.solutions == 1
    assert list(res.mine_counts) == [0]


def test_k1_remaining1():
    comp = mk_comp(1, [Constraint(mask_local=0b1, mask_global=0, remaining=1)])
    res = enumerate_component(comp)
    assert res.solutions == 1
    assert list(res.mine_counts) == [1]


def test_k2_sum_equals_1():
    # x0 + x1 = 1 -> 2 solutions: 01, 10
    comp = mk_comp(2, [Constraint(mask_local=0b11, mask_global=0, remaining=1)])
    res = enumerate_component(comp)
    assert res.solutions == 2
    assert list(res.mine_counts) == [1, 1]


def test_k3_exactly_two_mines():
    # among 3 vars, exactly 2 mines -> 3 solutions
    comp = mk_comp(3, [Constraint(mask_local=0b111, mask_global=0, remaining=2)])
    res = enumerate_component(comp)
    assert res.solutions == 3
    assert list(res.mine_counts) == [2, 2, 2]


def test_conflicting_constraints_zero_solutions():
    comp = mk_comp(1, [
        Constraint(mask_local=0b1, mask_global=0, remaining=0),
        Constraint(mask_local=0b1, mask_global=0, remaining=1),
    ])
    res = enumerate_component(comp)
    assert res.solutions == 0
    assert list(res.mine_counts) == [0]


def test_partial_constraint_allows_free_var():
    # x0 = 1; x1 unconstrained -> 2 solutions: (1,0) and (1,1)
    comp = mk_comp(2, [Constraint(mask_local=0b01, mask_global=0, remaining=1)])
    res = enumerate_component(comp)
    assert res.solutions == 2
    assert list(res.mine_counts) == [2, 1]


def test_two_constraints_overlap():
    # x0 + x1 = 1
    # x1 + x2 = 1
    # Solutions: 010 and 101
    comp = mk_comp(3, [
        Constraint(mask_local=0b011, mask_global=0, remaining=1),
        Constraint(mask_local=0b110, mask_global=0, remaining=1),
    ])
    res = enumerate_component(comp)
    assert res.solutions == 2
    assert list(res.mine_counts) == [1, 1, 1]


# ---------------------------
# Signature tests
# ---------------------------

def test_component_signature_location_independent():
    c1 = mk_comp(3, [
        Constraint(mask_local=0b011, mask_global=0b101000, remaining=1),
        Constraint(mask_local=0b110, mask_global=0b010100, remaining=1),
    ], local_to_global=[5, 6, 7])

    c2 = mk_comp(3, [
        Constraint(mask_local=0b110, mask_global=0b000111, remaining=1),
        Constraint(mask_local=0b011, mask_global=0b111000, remaining=1),
    ], local_to_global=[20, 21, 22])

    assert component_signature(c1) == component_signature(c2)


# ---------------------------
# Cache reuse tests (pytest monkeypatch)
# ---------------------------

def test_probability_engine_cache_reuse(monkeypatch):
    calls = {"count": 0}

    def fake_enum(comp):
        calls["count"] += 1
        return ProbResult(solutions=2, mine_counts=(1, 1))

    engine = ProbabilityEngine(max_k=10, cache_size=8)

    # patch the module-level enumerate_component that engine calls
    monkeypatch.setattr("analysis.probability.enumeration.enumerate_component", fake_enum)

    comp_a = mk_comp(2, [
        Constraint(mask_local=0b11, mask_global=0b1100, remaining=1)
    ], local_to_global=[10, 11])

    comp_b = mk_comp(2, [
        Constraint(mask_local=0b11, mask_global=0b0011, remaining=1)
    ], local_to_global=[42, 43])

    r1 = engine.get_component_result(comp_a)
    r2 = engine.get_component_result(comp_b)

    assert r1 == r2
    assert calls["count"] == 1  # <- the point of the test


def test_probability_engine_respects_max_k(monkeypatch):
    calls = {"count": 0}

    def fake_enum(comp):
        calls["count"] += 1
        return ProbResult(solutions=1, mine_counts=(0,) * comp.k)

    engine = ProbabilityEngine(max_k=1, cache_size=8)
    monkeypatch.setattr("analysis.probability.enumeration.enumerate_component", fake_enum)

    big = mk_comp(2, [Constraint(mask_local=0b11, mask_global=0, remaining=1)])
    assert engine.get_component_result(big) is None
    assert calls["count"] == 0


# ---------------------------
# probs_for_component + heap tests
# ---------------------------

def test_probs_for_component_skips_cells():
    comp = Component(
        k=2,
        constraints=[Constraint(mask_local=0b11, mask_global=0, remaining=1)],
        local_to_global=[10, 11],  # with cols=10 => (1,0), (1,1)
    )
    res = ProbResult(solutions=2, mine_counts=(1, 1))

    cols = 10
    skip = lambda r, c: (r, c) == (1, 0)

    probs = probs_for_component(comp, res, cols, skip)
    assert (1, 0) not in probs
    assert probs[(1, 1)] == 0.5


def test_build_guess_heap_shape():
    all_probs = {(0, 0): 0.1, (1, 1): 0.9}
    heap = build_guess_heap(all_probs, rows=3, cols=3)
    assert len(heap) == 2
    # heap item: (rating, p, centerness, (r,c))
    rating, p, cent, rc = heap[0]
    assert isinstance(rating, float)
    assert isinstance(p, float)
    assert isinstance(cent, float)
    assert isinstance(rc, tuple) and len(rc) == 2 

