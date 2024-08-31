from fst_runtime.fst import Fst
from fst_runtime.semiring import BooleanSemiring, TropicalSemiring

def test_weighted_fst_boolean():
    semiring = BooleanSemiring()
    fst = Fst('tests/data/weighted_boolean.att', semiring=semiring)

    input = 'abc'

    results = list(fst.down_generation(input))

    assert len(results) == 2

    outputs = {result.output_string:result.path_weight for result in results}

    assert 'wyz' in outputs
    assert 'xyz' in outputs

    assert outputs['wyz'] == False
    assert outputs['xyz'] == True

def test_weighted_fst_tropical():
    semiring = TropicalSemiring()
    fst = Fst('tests/data/weighted.att', semiring=semiring)

    input = 'aaaabc'
    input_bad = 'hi there hello'

    results = list(fst.down_generation(input))
    results_bad = (list(fst.down_generation(input_bad)))

    assert len(results) == 16
    assert len(results_bad) == 0

    results.sort(key=lambda result: result.path_weight)

    assert results[0].output_string == 'wwwwyz'
    assert round(results[0].path_weight, 2) == 1.2

def test_fresh():
    fst = Fst('tests/data/fst1.att')

    input = 'aaac'

    results = list(fst.down_generation(input))

    assert len(results) == 1
    assert results[0] == 'bbbd'