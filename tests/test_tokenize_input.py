# pylint: disable=redefined-outer-name

"""
test_tokenize_input

This test module tests the functioning of the``okenize_input_strin``function from``okenize_input.p``

Fixtures
--------
multichar_symbols
    Defines the multi-character symbols to use for the tests.

Functions
---------
test_tokenize_input_string_match_all_multichar_symbols
    Tests that all symbols are multichar symbols.
test_tokenize_input_string_no_multichar_symbols
    Tests that no symbols are multichar symbols.
test_tokenize_input_string_partial_multichar_symbol_match
    Tests that partial symbol match doesn't get treated as a full multichar symbol match.
test_tokenize_input_string_partial_overlapping_match
    Tests that a partially overlapping match doesn't get treated as a full match.
test_tokenize_input_string_longer_multichar_symbol
    Tests that the longest multichar symbol gets chosen over the shorter when they have overlapping characters.
test_tokenize_input_string_empty_input
    Tests how the tokenize method responds to empty input.
"""

import pytest
from fst_runtime.tokenize_input import tokenize_input_string

@pytest.fixture
def _multichar_symbols():
    """
    Defines the multi-character symbols to use for the tests.

    Returns
    -------
    set[str]
        A set of multi-character symbols.
    """
    return {"abc", "de"}

# All symbols are multichar.
def test_tokenize_input_string_match_all_multichar_symbols(_multichar_symbols):
    """
    Tests that all symbols are multichar symbols.

    Parameters
    ----------
    _multichar_symbols : set[str]
        The set of multi-character symbols. Provided automatically by Pytest.

    """
    input_string = "abcde"
    expected_tokens = ["abc", "de"]
    tokens = tokenize_input_string(input_string, _multichar_symbols)
    assert tokens == expected_tokens

# No multichar symbols exist.
def test_tokenize_input_string_no_multichar_symbols():
    """
    Tests that no symbols are multichar symbols.
    """
    input_string = "abcde"
    multichar_symbols = set()
    expected_tokens = ["a", "b", "c", "d", "e"]
    tokens = tokenize_input_string(input_string, multichar_symbols)
    assert tokens == expected_tokens

# Part multichar, part not.
def test_tokenize_input_string_partial_multichar_symbol_match(_multichar_symbols):
    """
    Tests that partial symbol match doesn't get treated as a full multichar symbol match.

    Parameters
    ----------
    multichar_symbols : set[str]
        The set of multi-character symbols.
    """
    input_string = "dabccba"
    expected_tokens = ["d", "abc", "c", "b", "a"]
    tokens = tokenize_input_string(input_string, _multichar_symbols)
    assert tokens == expected_tokens

# Partial multichar match.
def test_tokenize_input_string_partial_overlapping_match(_multichar_symbols):
    """
    Tests that a partially overlapping match doesn't get treated as a full match.

    Parameters
    ----------
    multichar_symbols : set[str]
        The set of multi-character symbols.
    """
    input_string = "abcdc"
    expected_tokens = ["abc", "d", "c"]
    tokens = tokenize_input_string(input_string, _multichar_symbols)
    assert tokens == expected_tokens

# Longest multichar first.
def test_tokenize_input_string_longer_multichar_symbol():
    """
    Tests that the longest multichar symbol gets chosen over the shorter when they have overlapping characters.
    """
    input_string = "abcdef"
    multichar_symbols = {"abc", "abcdef"}
    expected_tokens = ["abcdef"]
    tokens = tokenize_input_string(input_string, multichar_symbols)
    assert tokens == expected_tokens

# Empty input.
def test_tokenize_input_string_empty_input(_multichar_symbols):
    """
    Tests how the tokenize method responds to empty input.

    Parameters
    ----------
    multichar_symbols : set[str]
        The set of multi-character symbols.
    """
    input_string = ""
    expected_tokens = []
    tokens = tokenize_input_string(input_string, _multichar_symbols)
    assert tokens == expected_tokens
