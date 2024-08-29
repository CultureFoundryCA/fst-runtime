from fst_runtime.fst import Fst
from fst_runtime.semiring import BooleanSemiring, LogSemiring, ProbabilitySemiring, TropicalSemiring

fst = Fst('tests/data/weighted_graph.att')

def test_weighted_graph_boolean():
    semiring = BooleanSemiring()
    fst = Fst('tests/data/weighted_graph_boolean.att')
    assert True

def test_weighted_graph_log():
    semiring = LogSemiring()
    assert True

def test_weighted_graph_probability():
    semiring = ProbabilitySemiring()
    assert True

def test_weighted_graph_tropical():
    semiring = TropicalSemiring()
    assert True
