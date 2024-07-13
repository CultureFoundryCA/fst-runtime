# pylint: disable=redefined-outer-name

'''This module tests that the traversals and queries made to the FST are correct.'''

from pathlib import Path
import pytest
from fst_runtime.fst import Fst, EPSILON


@pytest.fixture(scope="module")
def data_dir():
    """Fixture to provide the path to the data directory."""
    return Path(__file__).parent / "data"

epsilon = [EPSILON]


#region Down/Generation Tests

def test_down_traversal_fst1(data_dir):
    '''Tests traveral down for fst1.att.'''

    graph = Fst(data_dir / 'fst1.att')

    stem1 = 'a'
    stem2 = 'c'
    stem3 = 'aaaac'

    stem1_result = graph.down_generation([epsilon], stem1, [epsilon])
    stem2_result = graph.down_generation([epsilon], stem2, [epsilon])
    stem3_result = graph.down_generation([epsilon], stem3, [epsilon])

    assert len(stem1_result) == 0
    assert len(stem2_result) == 1
    assert len(stem3_result) == 1

    assert stem2_result[0] == 'd'
    assert stem3_result[0] == 'bbbbd'


def test_down_traversal_fst2(data_dir):
    '''Tests traveral down for fst2.att.'''

    graph = Fst(data_dir / 'fst2.att')

    lemma = 'acccccccd'
    result = graph.down_generation([epsilon], lemma, [epsilon])

    assert len(result) == 1
    assert result[0] == 'bccccccce'


def test_down_traversal_fst3(data_dir):
    '''Tests traveral down for fst3.att.'''

    graph = Fst(data_dir / 'fst3.att')

    stem1 = 'aaac'
    stem2 = 'aaaaaa'
    stem3 = 'aac'

    stem1_result = graph.down_generation([epsilon], stem1, [epsilon])
    stem2_result = graph.down_generation([epsilon], stem2, [epsilon])
    stem3_result = graph.down_generation([epsilon], stem3, [epsilon])

    assert len(stem1_result) == 0
    assert len(stem2_result) == 1
    assert len(stem3_result) == 1

    assert stem2_result[0] == stem2
    assert stem3_result[0] == stem3


def test_down_traversal_fst4(data_dir):
    '''Tests traveral down for fst4.att.'''

    graph = Fst(data_dir / 'fst4.att')

    lemma = 'wal'
    suffix_options = [['+VERB'], ['+INF', '+GER', '+PAST', '+PRES']]

    results = graph.down_generation([epsilon], lemma, suffix_options)

    results = set(results)
    expected_results = {'walk', 'walks', 'walked', 'walking'}

    assert expected_results == results


def test_down_traversal_fst5(data_dir):
    '''Tests the traversal down through the epsilon cycle FST.'''

    graph = Fst(data_dir / 'fst5_epsilon_cycle.att', recursion_limit=100)

    lemma = 'abc'

    results = set(graph.down_generation([epsilon], lemma, [epsilon]))
    expected_results = {'xwv', 'xwzv', 'xywzv', 'xyyyyyyyyyyyyyywv', 'xyyyyyyyyyyyyyywzv'}

    assert results.issuperset(expected_results)


def test_down_traversal_fst6(data_dir):
    '''Tests the traversal down through the "waabam" FST.'''

    graph = Fst(data_dir / 'fst6_waabam.att')

    prefix_options = [["PVTense/gii+", "PVTense/wii'+"]]
    lemma = 'waabam'

    suffix_options = [['+VTA'],
                      ['+Ind'],
                      ['+Pos'],
                      ['+Neu'],
                      ['+1SgSubj'],
                      ['+2SgObj', '+2PlObj']]

    results = set(graph.down_generation(prefix_options, lemma, suffix_options))

    expected_results = \
    {
        "gigiiwaabamin",
        "gigii-waabamin",
        "gigii waabamin",
        "gigiiwaabamininim",
        "gigii-waabamininim",
        "gigii waabamininim",
        "giwii'waabamin",
        "giwii'-waabamin",
        "giwii' waabamin",
        "giwii'waabamininim",
        "giwii'-waabamininim",
        "giwii' waabamininim"
    }

    assert expected_results == results

#endregion


#region Up/Analysis Tests

def test_up_traversal_fst1(data_dir):

    graph = Fst(data_dir / 'fst1.att')

    wordform = 'bbbbd'

    results = graph.up_analysis(wordform)

    assert len(results) == 1
    assert 'aaaac' in results


def test_up_traversal_fst2(data_dir):

    graph = Fst(data_dir / 'fst2.att')

    wordform = 'bccce'

    results = graph.up_analysis(wordform)

    assert len(results) == 1
    assert 'acccd' in results


def test_up_traversal_fst3(data_dir):

    graph = Fst(data_dir / 'fst3.att')

    wordform1 = 'aac'
    wordform2 = 'aaaab'
    wordform3 = 'aaaac'
    wordform4 = 'aaac'

    results1 = set(graph.up_analysis(wordform1))
    results2 = set(graph.up_analysis(wordform2))
    results3 = set(graph.up_analysis(wordform3))
    results4 = set(graph.up_analysis(wordform4))

    assert len(results1) == 1
    assert len(results2) == 1
    assert len(results3) == 1
    assert len(results4) == 0

    assert wordform1 in results1
    assert wordform2 in results2
    assert wordform3 in results3


def test_up_traversal_fst4(data_dir):

    graph = Fst(data_dir / 'fst4.att')

    wordform1 = 'walking'
    wordform2 = 'walks'

    results1 = graph.up_analysis(wordform1)
    results2 = graph.up_analysis(wordform2)

    assert len(results1) == 1
    assert len(results2) == 1

    assert 'wal+VERB+GER' in results1
    assert 'wal+VERB+PRES' in results2


def test_up_traversal_fst5(data_dir):

    graph = Fst(data_dir / 'fst5_epsilon_cycle.att')

    wordform1 = 'xyyyyyyyyyywv'
    wordform2 = 'xyyywzv'
    wordform3 = 'xwv'
    wordform4 = 'xyyyyyyyv'

    results1 = graph.up_analysis(wordform1)
    results2 = graph.up_analysis(wordform2)
    results3 = graph.up_analysis(wordform3)
    results4 = graph.up_analysis(wordform4)

    assert len(results1) == 1
    assert len(results2) == 1
    assert len(results3) == 1
    assert len(results4) == 0

    assert 'abc' in results1
    assert 'abc' in results2
    assert 'abc' in results3


def test_up_analysis_fst6(data_dir):

    graph = Fst(data_dir / 'fst6_waabam.att')

    wordform1 = "gigii-waabamin"
    wordform2 = "gigii-waabamininim"
    wordform3 = "giwii'-waabamin"
    wordform4 ="giwii'-waabamininim"

    results1 = graph.up_analysis(wordform1)
    results2 = graph.up_analysis(wordform2)
    results3 = graph.up_analysis(wordform3)
    results4 = graph.up_analysis(wordform4)

    assert len(results1) == 1
    assert len(results2) == 1
    assert len(results3) == 1
    assert len(results4) == 1
    
    expected_result1 = "PVTense/gii+waabam+VTA+Ind+Pos+Neu+1SgSubj+2SgObj"
    expected_result2 = "PVTense/gii+waabam+VTA+Ind+Pos+Neu+1SgSubj+2PlObj"
    expected_result3 = "PVTense/wii'+waabam+VTA+Ind+Pos+Neu+1SgSubj+2SgObj"
    expected_result4 = "PVTense/wii'+waabam+VTA+Ind+Pos+Neu+1SgSubj+2PlObj"

    assert expected_result1 in results1
    assert expected_result2 in results2
    assert expected_result3 in results3
    assert expected_result4 in results4

#endregion
