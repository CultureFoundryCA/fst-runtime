from fst_runtime.fst import Fst
from fst_runtime.semiring import BooleanSemiring, LogSemiring, ProbabilitySemiring, TropicalSemiring

def test_weighted_fst_boolean():
    semiring = BooleanSemiring()
    fst = Fst('tests/data/weighted_graph_boolean.att', semiring=semiring)
    assert True

def test_weighted_fst_log():
    semiring = LogSemiring()
    fst = Fst('tests/data/weighted_graph.att', semiring=semiring)
    assert True

def test_weighted_fst_probability():
    semiring = ProbabilitySemiring()
    fst = Fst('tests/data/weighted_graph.att', semiring=semiring)
    assert True

def test_weighted_fst_tropical():
    semiring = TropicalSemiring()
    fst = Fst('tests/data/weighted_graph.att', semiring=semiring)
    assert True
