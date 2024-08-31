# pylint: disable=redefined-outer-name

"""
This module tests that the traversals and queries made to the FST are correct.

These tests cover many different possible breaking points, such as epsilon loops resulting in infinite recursion,
handling multiple outputted forms, following epsilon cycles successfully, etc.

Attributes
----------
test_down_traversal_fst1 : function
    Tests traversal down for fst1.att.

test_down_traversal_fst2 : function
    Tests traversal down for fst2.att.

test_down_traversal_fst3 : function
    Tests traversal down for fst3.att.

test_down_traversal_fst4 : function
    Tests traversal down for fst4.att.

test_down_traversal_fst5 : function
    Tests traversal down for fst5_epsilon_cycles.att.

test_down_traversal_fst6 : function
    Tests traversal down for fst6_waabam.att.

test_up_traversal_fst1 : function
    Tests traversal up for fst1.att.

test_up_traversal_fst2 : function
    Tests traversal up for fst2.att.

test_up_traversal_fst3 : function
    Tests traversal up for fst3.att.

test_up_traversal_fst4 : function
    Tests traversal up for fst4.att.

test_up_traversal_fst5 : function
    Tests traversal up for fst5_epsilon_cycles.att.
    
test_up_analysis_fst6 : function
    Tests traversal up for fst6_waabam.att.
"""

from pathlib import Path
import pytest
from fst_runtime.fst import Fst


@pytest.fixture(scope="module")
def _data_dir():
    """
    Provides the path to the data directory.

    Returns
    -------
    pathlib.Path
        Path to the data directory.
    """

    return Path(__file__).parent / "data"


#region Down/Generation Tests

def test_down_traversal_fst1(_data_dir):
    """
    Tests traversal down for fst1.att.

    This is a very basic test that tests input to an FST gives the expected output. It also checks that an incorrect form is rejected.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst1.att')

    lemma1 = 'a'  # <- Incorrect form.
    lemma2 = 'c'
    lemma3 = 'aaaac'

    lemma1_results = list(graph.down_generation(lemma1))
    lemma2_results = list(graph.down_generation(lemma2))
    lemma3_results = list(graph.down_generation(lemma3))

    assert len(lemma1_results) == 0  # <- Incorrect form supplied, so there should be zero results.
    assert len(lemma2_results) == 1
    assert len(lemma3_results) == 1

    assert 'd' in [result.output_string for result in lemma2_results]
    assert 'bbbbd' in [result.output_string for result in lemma3_results]


def test_down_traversal_fst2(_data_dir):
    """
    Tests traversal down for fst2.att.

    This is a very basic test that input to an FST gives the expected output. It also checks that an incorrect form is rejected.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst2.att')

    lemma = 'acccccccd'
    results = list(graph.down_generation(lemma))

    assert len(results) == 1
    assert 'bccccccce' in [result.output_string for result in results]


def test_down_traversal_fst3(_data_dir):
    """
    Tests traversal down for fst3.att.

    This also tests the ``down_generations`` function, which can take multiple queries at once.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst3.att')

    lemma1 = 'aaac'
    lemma2 = 'aaaaaa'
    lemma3 = 'aac'

    results_dict = graph.down_generations([lemma1, lemma2, lemma3])
    results1 = list(results_dict[lemma1])
    results2 = list(results_dict[lemma2])
    results3 = list(results_dict[lemma3])

    assert len(results1) == 0
    assert len(results2) == 1
    assert len(results3) == 1

    assert lemma2 in [result.output_string for result in results2]
    assert lemma3 in [result.output_string for result in results3]


def test_down_traversal_fst4(_data_dir):
    """
    Tests traversal down for fst4.att.

    This test tests that adding suffixes to queries produces the correct and expected forms.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst4.att')

    lemma = 'wal'
    suffixes = [['+VERB'], ['+INF', '+GER', '+PAST', '+PRES']]

    results = graph.down_generation(lemma, suffixes=suffixes)

    results = {result.output_string for result in results}
    expected_results = {'walk', 'walks', 'walked', 'walking'}

    assert expected_results == results


def test_down_traversal_fst5(_data_dir):
    """
    Tests traversal down for fst5_epsilon_cycles.att.

    Tests the traversal down through an FST that can fall into an infinite loop during generation via an epsilon cycle.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst5_epsilon_cycle.att', recursion_limit=100)

    lemma = 'abc'

    results = graph.down_generation(lemma)
    results = {result.output_string for result in results}

    expected_results = {'xwv', 'xwzv', 'xywzv', 'xyyyyyyyyyyyyyywv', 'xyyyyyyyyyyyyyywzv'}

    assert results.issuperset(expected_results)


def test_down_traversal_fst6(_data_dir):
    """
    Tests traversal down for fst6_waabam.att.

    Tests the traversal down through the complicated "waabam" FST, and tests the use of both prefixes and suffixes robustly.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst6_waabam.att')

    prefixes = [["PVTense/gii+", "PVTense/wii'+"]]
    lemma = 'waabam'

    suffixes = [['+VTA'],
                ['+Ind'],
                ['+Pos'],
                ['+Neu'],
                ['+1SgSubj'],
                ['+2SgObj', '+2PlObj']]

    results = graph.down_generation(lemma, prefixes=prefixes, suffixes=suffixes)
    results = {result.output_string for result in results}

    expected_results = {
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

def test_up_traversal_fst1(_data_dir):
    """
    Tests traversal up for fst1.att.

    This is a simple test that just gives the FST a form that should be accepted with a single output and checks that it gets that.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst1.att')

    wordform = 'bbbbd'

    results = list(graph.up_analysis(wordform))

    assert len(results) == 1
    assert 'aaaac' in [result.output_string for result in results]


def test_up_traversal_fst2(_data_dir):
    """
    Tests traversal up for fst2.att.

    This is a simple test that just gives the FST a form that should be accepted with a single output and checks that it gets that.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst2.att')

    wordform = 'bccce'

    results = list(graph.up_analysis(wordform))

    assert len(results) == 1
    assert 'acccd' in [result.output_string for result in results]


def test_up_traversal_fst3(_data_dir):
    """
    Tests traversal up for fst3.att.

    This test checks that forms you expect to get accepted are and that the output of that is correct,
    as well as testing to make sure an invalid form is rejected by the FST.

    This also tests the ``up_analyses`` function, which allows for querying multiple wordforms at once.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst3.att')

    wordform1 = 'aac'
    wordform2 = 'aaaab'
    wordform3 = 'aaaac'
    wordform4 = 'aaac'  # <- Not valid in the FST.

    results_dict = graph.up_analyses([wordform1, wordform2, wordform3, wordform4])
    results1 = list(results_dict[wordform1])
    results2 = list(results_dict[wordform2])
    results3 = list(results_dict[wordform3])
    results4 = list(results_dict[wordform4])

    assert len(results1) == 1
    assert len(results2) == 1
    assert len(results3) == 1
    assert len(results4) == 0  # <- No valid form was sent to the FST, so result should be zero.

    assert wordform1 in [result.output_string for result in results1]
    assert wordform2 in [result.output_string for result in results2]
    assert wordform3 in [result.output_string for result in results3]


def test_up_traversal_fst4(_data_dir):
    """
    Tests traversal up for fst4.att.

    This test checks that forms employing multi-character symbols come out correctly and as expected.
    It also tests that the up/analysis direction can output multiple tagged forms that can generate
    our starting wordform.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst4.att')

    wordform1 = 'walking'
    wordform2 = 'walks'  # <- Dummy form was added to the FST so that this input should generate two output forms.

    results1 = list(graph.up_analysis(wordform1))
    results2 = list(graph.up_analysis(wordform2))

    assert len(results1) == 1
    assert len(results2) == 2  # <- Should contain {'wal+VERB+PRES', 'wal+VERB+PRES_DUMMY'}.

    assert 'wal+VERB+GER' in [result.output_string for result in results1]
    assert 'wal+VERB+PRES' in [result.output_string for result in results2]
    assert 'wal+VERB+PRES_DUMMY' in [result.output_string for result in results2]


def test_up_traversal_fst5(_data_dir):
    """
    Tests traversal up for fst5.att.

    fst5.att contains epsilon cycles, and this test is basically just a sanity check that epsilon cycles don't break the logic.
    It also tests some more complicated forms where epsilon loops will be followed in order to get to the output. You can see,
    for example, that ``abc`` can generate wordforms 1 through 4, where an arbitrary number of y's can be inserted.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst5_epsilon_cycle.att')

    wordform1 = 'xyyyyyyyyyywv'
    wordform2 = 'xyyywzv'
    wordform3 = 'xwv'
    wordform4 = 'xyyyyyyyv'

    results1 = list(graph.up_analysis(wordform1))
    results2 = list(graph.up_analysis(wordform2))
    results3 = list(graph.up_analysis(wordform3))
    results4 = list(graph.up_analysis(wordform4))

    assert len(results1) == 1
    assert len(results2) == 1
    assert len(results3) == 1
    assert len(results4) == 0

    assert 'abc' in [result.output_string for result in results1]
    assert 'abc' in [result.output_string for result in results2]
    assert 'abc' in [result.output_string for result in results3]


def test_up_analysis_fst6(_data_dir):
    """
    Tests traversal up for fst6.att.

    This tests the navigation of a complex FST and confirms the correct output given a real wordform.

    Parameters
    ----------
    _data_dir : pathlib.Path
        Path to the data directory. Provided automatically by Pytest.
    """

    graph = Fst(_data_dir / 'fst6_waabam.att')

    wordform1 = "gigii-waabamin"
    wordform2 = "gigii-waabamininim"
    wordform3 = "giwii'-waabamin"
    wordform4 = "giwii'-waabamininim"

    results1 = list(graph.up_analysis(wordform1))
    results2 = list(graph.up_analysis(wordform2))
    results3 = list(graph.up_analysis(wordform3))
    results4 = list(graph.up_analysis(wordform4))

    assert len(results1) == 1
    assert len(results2) == 1
    assert len(results3) == 1
    assert len(results4) == 1

    expected_result1 = "PVTense/gii+waabam+VTA+Ind+Pos+Neu+1SgSubj+2SgObj"
    expected_result2 = "PVTense/gii+waabam+VTA+Ind+Pos+Neu+1SgSubj+2PlObj"
    expected_result3 = "PVTense/wii'+waabam+VTA+Ind+Pos+Neu+1SgSubj+2SgObj"
    expected_result4 = "PVTense/wii'+waabam+VTA+Ind+Pos+Neu+1SgSubj+2PlObj"

    assert expected_result1 in [result.output_string for result in results1]
    assert expected_result2 in [result.output_string for result in results2]
    assert expected_result3 in [result.output_string for result in results3]
    assert expected_result4 in [result.output_string for result in results4]

#endregion
