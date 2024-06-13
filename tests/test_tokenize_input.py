import pytest
from fst_runtime.tokenize_input import tokenize_input_string

@pytest.fixture
def multichar_symbols():
    return {"abc", "de"}

def test_tokenize_input_string_match_all_multichar_symbols(multichar_symbols):
    input_string = "abcde"
    expected_tokens = ["abc", "de"]
    tokens = tokenize_input_string(None, input_string, multichar_symbols)
    assert tokens == expected_tokens

def test_tokenize_input_string_no_multichar_symbols():
    input_string = "abcde"
    multichar_symbols = set()
    expected_tokens = ["a", "b", "c", "d", "e"]
    tokens = tokenize_input_string(None, input_string, multichar_symbols)
    assert tokens == expected_tokens

def test_tokenize_input_string_partial_multichar_symbol_match(multichar_symbols):
    input_string = "abccba"
    expected_tokens = ["abc", "c", "b", "a"]
    tokens = tokenize_input_string(None, input_string, multichar_symbols)
    assert tokens == expected_tokens

def test_tokenize_input_string_partial_overlapping_match(multichar_symbols):
    input_string = "abcdc"
    expected_tokens = ["abc", "d", "c"]
    tokens = tokenize_input_string(None, input_string, multichar_symbols)
    assert tokens == expected_tokens

def test_tokenize_input_string_longer_multichar_symbol():
    input_string = "abcdef"
    multichar_symbols = {"abc", "abcdef"}
    expected_tokens = ["abcdef"]
    tokens = tokenize_input_string(None, input_string, multichar_symbols)
    assert tokens == expected_tokens

def test_tokenize_input_string_empty_input(multichar_symbols):
    input_string = ""
    expected_tokens = []
    tokens = tokenize_input_string(None, input_string, multichar_symbols)
    assert tokens == expected_tokens
