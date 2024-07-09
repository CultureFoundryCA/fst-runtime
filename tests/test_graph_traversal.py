# pylint: disable=redefined-outer-name

'''This module tests that the traversals and queries made to the FST are correct.'''

from pathlib import Path
import pytest
from fst_runtime.fst import Fst, EPSILON


@pytest.fixture(scope="module")
def data_dir():
    """Fixture to provide the path to the data directory."""
    return Path(__file__).parent / "data"

epsilon = [[EPSILON]]

def test_down_traversal_fst1(data_dir):
    '''Tests traveral for fst1.att.'''

    graph = Fst(data_dir / 'fst1.att')

    stem1 = 'a'
    stem2 = 'c'
    stem3 = 'aaaac'

    stem1_result = graph.down_generation(epsilon, stem1, epsilon)
    stem2_result = graph.down_generation(epsilon, stem2, epsilon)
    stem3_result = graph.down_generation(epsilon, stem3, epsilon)

    assert len(stem1_result) == 0
    assert len(stem2_result) == 1
    assert len(stem3_result) == 1

    assert stem2_result[0] == 'd'
    assert stem3_result[0] == 'bbbbd'

def test_down_traversal_fst2(data_dir):
    '''Tests traveral for fst2.att.'''

    graph = Fst(data_dir / 'fst2.att')

    lemma = 'acccccccd'
    result = graph.down_generation(epsilon, lemma, epsilon)

    assert len(result) == 1
    assert result[0] == 'bccccccce'

def test_down_traversal_fst3(data_dir):
    '''Tests traveral for fst3.att.'''

    graph = Fst(data_dir / 'fst3.att')

    stem1 = 'aaac'
    stem2 = 'aaaaaa'
    stem3 = 'aac'

    stem1_result = graph.down_generation(epsilon, stem1, epsilon)
    stem2_result = graph.down_generation(epsilon, stem2, epsilon)
    stem3_result = graph.down_generation(epsilon, stem3, epsilon)

    assert len(stem1_result) == 0
    assert len(stem2_result) == 1
    assert len(stem3_result) == 1

    assert stem2_result[0] == stem2
    assert stem3_result[0] == stem3


def test_down_traversal_fst4(data_dir):
    '''Tests traveral for fst4.att.'''

    graph = Fst(data_dir / 'fst4.att')

    lemma = 'wal'
    suffix_options = [['+VERB'], ['+INF', '+GER', '+PAST', '+PRES']]

    results = graph.down_generation(epsilon, lemma, suffix_options)

    results = set(results)
    expected_results = {'walk', 'walks', 'walked', 'walking'}

    assert results == expected_results
