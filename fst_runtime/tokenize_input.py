"""
This module holds a tokenization function that splits an input string into its constituent parts,
while considering the set of provided multi-character symbols.

Attributes
----------
tokenize_input_string : function
    Tokenizes the input string while respecting the multichar_symbols.
"""

from fst_runtime import logger

def tokenize_input_string(input_string: str, multichar_symbols: set[str]) -> list[str]:
    """
    Returns a list containing the individual tokens that make up the ``input_string``.

    Parameters
    ----------
    input_string : str
        The input string to be tokenized.
        
    multichar_symbols : set[str]
        A set of multi-character symbols that need to be recognized as single tokens.

    Returns
    -------
    list[str]
        A list of individual tokens that make up the input string.

    Note
    -----
    This function tokenizes the input string into individual tokens, taking into account
    the multi-character symbols specified in the ``multichar_symbols`` set. It ensures that
    the multi-character symbols are recognized as single tokens rather than being split
    into multiple tokens.
    """

    # This gets the character lengs of all the multicharacter symbols and sorts them from highest to lowest.
    # Note lengths are distinct from use of set comprehension.
    multichar_lengths = list({
        len(symbol)
        for symbol
        in multichar_symbols
    })

    multichar_lengths.sort(reverse=True)

    tokens = []

    # Loop until all input characters are consumed.
    while len(input_string) > 0:
        # This is used to continue from a nested loop.
        should_continue_while = False

        # If any multi-character symbols exist in the FST, then loop over the lengths. For each length, take a slice
        # of the current input from the start up to the length. Then, given that slice, check if it exists in the set
        # of multi-character symbols for the FST. If it does exist, then add it as a token, consume the input characters,
        # and continue the outer loop. If it doesn't exist, continue looping through the multichar lengths. If nothing is
        # found, then token found is a single character. This continues until the whole input has been consumed.
        if multichar_lengths:
            for symbol_length in multichar_lengths:
                try:
                    substring = input_string[:symbol_length]
                # Not enough input left.
                except IndexError:
                    continue

                if substring in multichar_symbols:
                    tokens.append(substring)
                    input_string = input_string.removeprefix(substring) # Consume input characters.
                    should_continue_while = True
                    break

            # Continue from nested loop.
            if should_continue_while:
                continue

        tokens.append(input_string[0])
        input_string = input_string[1:] # Consume input characters.

    logger.debug('_tokenize_input_string.tokens: %s', tokens)
    return tokens
