"""
This file tests weighted boolean and real-valued FSTs, the latter using the tropical semiring.

Attributes
----------
test_weighted_fst_boolean : function
    Tests a weighted FST whose weights are in {0, 1}.

test_weighted_fst_tropical : function
    Tests a weighted FST whose weights are real-valued with +/- inf using the tropical semiring for testing.
"""

from fst_runtime.fst import Fst
from fst_runtime.semiring import BooleanSemiring, TropicalSemiring

def test_weighted_fst_boolean():
    """Tests a weighted FST whose weights are in {0, 1}."""
    
    semiring = BooleanSemiring()
    fst = Fst('tests/data/weighted_boolean.att', semiring=semiring)

    input_string = 'abc'

    results = list(fst.down_generation(input_string))

    assert len(results) == 2

    outputs = {result.output_string:result.path_weight for result in results}

    assert 'wyz' in outputs
    assert 'xyz' in outputs

    assert outputs['wyz'] is False
    assert outputs['xyz'] is True

def test_weighted_fst_tropical():
    """Tests a weighted FST whose weights are real-valued with +/- inf using the tropical semiring for testing."""

    semiring = TropicalSemiring()
    fst = Fst('tests/data/weighted.att', semiring=semiring)

    input_string = 'aaaabc'
    input_bad = 'hi there hello'

    results = list(fst.down_generation(input_string))
    results_bad = (list(fst.down_generation(input_bad)))

    assert len(results) == 16
    assert len(results_bad) == 0

    results.sort(key=lambda result: result.path_weight)

    assert results[0].output_string == 'wwwwyz'
    assert round(results[0].path_weight, 2) == 1.2
