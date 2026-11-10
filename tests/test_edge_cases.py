"""
This file tests edge cases in reading ``.att`` files, in the traversals, and in the semirings.

Attributes
----------
test_up_analysis_first_transition_outputs_epsilon : function
    Tests that an analysis is found when the first transition of its path outputs epsilon.

test_up_analysis_multichar_output_symbol : function
    Tests that the up direction matches output symbols that are more than one character long.

test_up_and_down_weights_agree : function
    Tests that the same path has the same weight in both directions, including the final state weight.

test_accepting_start_state_accepts_empty_input : function
    Tests that the empty string is accepted in both directions when the start state is accepting.

test_recursion_limit_does_not_change_interpreter_limit : function
    Tests that querying the FST leaves the interpreter's recursion limit alone.

test_long_input_is_not_cut_off : function
    Tests that an input longer than the interpreter's recursion limit still returns its result.

test_epsilon_cycle_is_bounded_by_recursion_limit : function
    Tests that the recursion limit bounds how many times an epsilon cycle is followed.

test_blank_lines_are_skipped : function
    Tests that blank lines in the ``.att`` file are ignored.

test_malformed_line_raises_att_format_error : function
    Tests that malformed lines raise an ``AttFormatError`` rather than exiting the interpreter.

test_malformed_weight_raises_att_format_error : function
    Tests that a weight that isn't in the semiring's domain raises an ``AttFormatError``.

test_invalid_path_raises_value_error : function
    Tests that an empty path or a path to a non-``.att`` file raises a ``ValueError``.

test_epsilon_is_a_multichar_symbol : function
    Tests that the epsilon symbol is read in as a multi-character symbol.

test_serialization_dictionary_is_a_copy : function
    Tests that the serialization dictionary is a copy of the output's fields under both spellings of the method.

test_boolean_semiring_rejects_non_boolean_weights : function
    Tests that only boolean weights are converted by the boolean semiring.

test_log_semiring_add_extreme_values : function
    Tests that log addition handles infinities and very large or small values.

test_check_membership_rejects_non_numbers : function
    Tests that the real-valued semirings reject ``None``, NaN, and booleans.
"""

import math
import sys

import pytest

from fst_runtime.att_format_error import AttFormatError
from fst_runtime.fst import Fst, FstOutput
from fst_runtime.semiring import BooleanSemiring, LogSemiring, ProbabilitySemiring, TropicalSemiring


def _make_fst(tmp_path, att_lines: list[str], **fst_arguments) -> Fst:
    """
    Writes the given lines to a temporary ``.att`` file and reads it in as an FST.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The temporary directory. Provided automatically to the tests by Pytest.

    att_lines : list[str]
        The lines of the ``.att`` file, with the items of each line separated by single spaces instead of tabs.

    **fst_arguments
        Any keyword arguments to pass on to the ``Fst`` constructor.

    Returns
    -------
    Fst
        The FST that was read in from the file.
    """

    att_file = tmp_path / 'test.att'
    att_file.write_text(''.join(line.replace(' ', '\t') + '\n' for line in att_lines), encoding='utf-8')
    return Fst(att_file, **fst_arguments)


#region Traversal

def test_up_analysis_first_transition_outputs_epsilon(tmp_path):
    """Tests that an analysis is found when the first transition of its path outputs epsilon."""

    fst = _make_fst(tmp_path, ['0 1 PRE+ @0@', '1 2 a a', '2'])

    assert [output.output_string for output in fst.down_generation('PRE+a')] == ['a']
    assert [output.output_string for output in fst.up_analysis('a')] == ['PRE+a']


def test_up_analysis_multichar_output_symbol(tmp_path):
    """Tests that the up direction matches output symbols that are more than one character long."""

    fst = _make_fst(tmp_path, ['0 1 a XY', '1 2 b Z', '2'])

    assert [output.output_string for output in fst.down_generation('ab')] == ['XYZ']
    assert [output.output_string for output in fst.up_analysis('XYZ')] == ['ab']
    assert not list(fst.up_analysis('YZ'))


def test_up_and_down_weights_agree(tmp_path):
    """Tests that the same path has the same weight in both directions, including the final state weight."""

    fst = _make_fst(tmp_path, ['0 1 a b 1.0', '1 2 c d 0.5', '2 2.0'], semiring=TropicalSemiring())

    down_results = list(fst.down_generation('ac'))
    up_results = list(fst.up_analysis('bd'))

    assert down_results == [FstOutput('bd', 3.5, 'ac')]
    assert up_results == [FstOutput('ac', 3.5, 'bd')]


def test_accepting_start_state_accepts_empty_input(tmp_path):
    """Tests that the empty string is accepted in both directions when the start state is accepting."""

    fst = _make_fst(tmp_path, ['0', '0 1 a b', '1'])

    assert [output.output_string for output in fst.down_generation('')] == ['']
    assert [output.output_string for output in fst.up_analysis('')] == ['']


def test_recursion_limit_does_not_change_interpreter_limit(tmp_path):
    """Tests that querying the FST leaves the interpreter's recursion limit alone."""

    fst = _make_fst(tmp_path, ['0 1 a b', '0 1 c d', '1'], recursion_limit=5000)
    original_recursion_limit = sys.getrecursionlimit()

    # A generator that is started but never finished.
    abandoned_generation = fst.down_generation('a')
    next(abandoned_generation)
    assert sys.getrecursionlimit() == original_recursion_limit

    abandoned_analysis = fst.up_analysis('b')
    next(abandoned_analysis)
    assert sys.getrecursionlimit() == original_recursion_limit

    # Generators that are consumed in turns.
    generations = fst.down_generations(['a', 'c'])
    first_result = next(generations['a'])
    second_result = next(generations['c'])

    assert first_result.output_string == 'b'
    assert second_result.output_string == 'd'
    assert sys.getrecursionlimit() == original_recursion_limit


def test_long_input_is_not_cut_off(tmp_path):
    """Tests that an input longer than the interpreter's recursion limit still returns its result."""

    fst = _make_fst(tmp_path, ['0 0 a b', '0'])
    input_length = sys.getrecursionlimit() * 2

    down_results = list(fst.down_generation('a' * input_length))
    up_results = list(fst.up_analysis('b' * input_length))

    assert [output.output_string for output in down_results] == ['b' * input_length]
    assert [output.output_string for output in up_results] == ['a' * input_length]


def test_epsilon_cycle_is_bounded_by_recursion_limit(tmp_path):
    """Tests that the recursion limit bounds how many times an epsilon cycle is followed."""

    fst = _make_fst(tmp_path, ['0 0 @0@ x', '0 1 a b', '1'], recursion_limit=3)

    results = [output.output_string for output in fst.down_generation('a')]

    assert sorted(results) == ['b', 'xb', 'xxb', 'xxxb']

#endregion


#region Reading the File

def test_blank_lines_are_skipped(tmp_path):
    """Tests that blank lines in the ``.att`` file are ignored."""

    fst = _make_fst(tmp_path, ['0 1 a b', '', '1', ''])

    assert [output.output_string for output in fst.down_generation('a')] == ['b']


@pytest.mark.parametrize('att_lines', [
    ['0 1 a'],
    ['0 1 a b 1.0 extra'],
    ['zero 1 a b'],
    ['0 one a b'],
    ['0 1 a b', 'one'],
])
def test_malformed_line_raises_att_format_error(tmp_path, att_lines):
    """Tests that malformed lines raise an ``AttFormatError`` rather than exiting the interpreter."""

    with pytest.raises(AttFormatError):
        _make_fst(tmp_path, att_lines)


def test_malformed_weight_raises_att_format_error(tmp_path):
    """Tests that a weight that isn't in the semiring's domain raises an ``AttFormatError``."""

    with pytest.raises(AttFormatError):
        _make_fst(tmp_path, ['0 1 a b heavy', '1'], semiring=TropicalSemiring())


@pytest.mark.parametrize('att_file_path', ['', 'fst.txt'])
def test_invalid_path_raises_value_error(att_file_path):
    """Tests that an empty path or a path to a non-``.att`` file raises a ``ValueError``."""

    with pytest.raises(ValueError):
        Fst(att_file_path)


def test_epsilon_is_a_multichar_symbol(tmp_path):
    """Tests that the epsilon symbol is read in as a multi-character symbol."""

    fst = _make_fst(tmp_path, ['0 1 @0@ b', '1 2 +TAG @0@', '2'])

    assert fst.multichar_symbols == {'@0@', '+TAG'}

#endregion


#region Outputs and Semirings

def test_serialization_dictionary_is_a_copy():
    """Tests that the serialization dictionary is a copy of the output's fields under both spellings of the method."""

    output = FstOutput('walking', 1.0, 'wal+VERB+GER')
    expected_dictionary = {'output_string': 'walking', 'path_weight': 1.0, 'input_string': 'wal+VERB+GER'}

    dictionary = output.get_serialization_dictionary()

    assert dictionary == expected_dictionary
    assert output.get_serialialization_dictionary() == expected_dictionary

    dictionary['output_string'] = 'changed'

    assert output.output_string == 'walking'


def test_boolean_semiring_rejects_non_boolean_weights():
    """Tests that only boolean weights are converted by the boolean semiring."""

    semiring = BooleanSemiring()

    assert semiring.convert_string_into_domain('1') is True
    assert semiring.convert_string_into_domain('0') is False
    assert semiring.convert_string_into_domain('True') is True
    assert semiring.convert_string_into_domain('False') is False

    for non_boolean_weight in ['7', '-1', '0.5', 'yes']:
        with pytest.raises(ValueError):
            semiring.convert_string_into_domain(non_boolean_weight)


def test_log_semiring_add_extreme_values():
    """Tests that log addition handles infinities and very large or small values."""

    semiring = LogSemiring()

    assert semiring.add(math.inf, math.inf) == math.inf
    assert semiring.add(math.inf, 2.5) == 2.5
    assert semiring.add(2.5, math.inf) == 2.5
    assert semiring.add(-math.inf, 2.5) == -math.inf

    # ``-ln(2 * e^(-a)) = a - ln(2)``.
    assert semiring.add(1000.0, 1000.0) == pytest.approx(1000.0 - math.log(2))
    assert semiring.add(-1000.0, -1000.0) == pytest.approx(-1000.0 - math.log(2))

    assert semiring.get_path_set_weight() == math.inf


def test_check_membership_rejects_non_numbers():
    """Tests that the real-valued semirings reject ``None``, NaN, and booleans."""

    for semiring in [LogSemiring(), ProbabilitySemiring(), TropicalSemiring()]:
        assert semiring.check_membership(0.5, 1, 2.0) is True
        assert semiring.check_membership(None) is False
        assert semiring.check_membership(math.nan) is False
        assert semiring.check_membership(True) is False
        assert semiring.check_membership('abc') is False

    assert TropicalSemiring().check_membership(math.inf, -math.inf) is True
    assert ProbabilitySemiring().check_membership(math.inf) is False

#endregion
