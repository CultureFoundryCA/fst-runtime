'''This module tests that the traversals and queries made to the FST are correct.'''

from fst_runtime.fst import Fst, EPSILON

epsilon = [[EPSILON]]

def test_down_traversal_fst1(att_data_file = '/home/parkhill/Documents/Coding/fst-runtime/tests/data/fst1.att'):
    '''Tests traveral for fst1.att.'''

    graph = Fst(att_data_file)

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

def test_down_traversal_fst2(att_data_file = '/home/parkhill/Documents/Coding/fst-runtime/tests/data/fst2.att'):
    '''Tests traveral for fst2.att.'''

    graph = Fst(att_data_file)

    stem = 'acccccccd'
    result = graph.down_generation(epsilon, stem, epsilon)

    assert len(result) == 1
    assert result[0] == 'bccccccce'

def test_down_traversal_fst3(att_data_file = '/home/parkhill/Documents/Coding/fst-runtime/tests/data/fst3.att'):
    '''Tests traveral for fst3.att.'''

    graph = Fst(att_data_file)

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


def test_down_traversal_fst4(att_data_file = '/home/parkhill/Documents/Coding/fst-runtime/tests/data/fst4.att'):
    '''Tests traveral for fst4.att.'''

    graph = Fst(att_data_file)

    stem = 'wal'
    suffix_options = [['+VERB'], ['+INF', '+GER', '+PAST', '+PRES']]

    results = graph.down_generation(epsilon, stem, suffix_options)

    results = set(results)
    expected_results = {'walk', 'walks', 'walked', 'walking'}

    assert results == expected_results
