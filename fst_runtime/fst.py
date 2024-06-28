import os
from collections import defaultdict
import sys
from pprint import pformat
import logging

EXIT_FAILURE = 1

ATT_FILE_PATH = os.getenv('ATT_FILE_PATH')
LOG_LEVEL = os.getenv('LOG_LEVEL')



class Fst:
    '''
    This finite-state transducer (FST) object represents the FST as read in by the required `.att` file. It holds the FST in memory and
    provides several methods that can be used to perform common runtime operations on an FST, such as querying it. This is ultimately
    just a graph under-the-hood.

    Public methods:
        - traverse
    '''

    #region Dunders & Class Variables

    # The starting state in the `.att` format is represented by `0`.
    _STARTING_STATE = 0
    _ATT_DEFINES_ACCEPTING_STATE = 1
    _ATT_DEFINES_UNWEIGHTED_TRANSITION = 4
    _ATT_DEFINES_WEIGHTED_TRANSITION = 5

    def __init__(self, att_file_path: str):

        # The `defaultdict` object is used here with default value `dict` so that while adding transitions to the graph during initialization,
        # checks don't have to be made to see if a dictionary exists for a given key; if it doesn't exist, it adds an empty dictionary.
        # This object is to be read as follows: `dict[current_state, dict[input_symbol, tuple[next_state, output_symbol]]]`.
        self._transitions: dict[int, dict[str, tuple[int, str]]] = defaultdict(dict)

        # These hold the multi-character symbols in the FST. For example, an input symbol could be 'a', but it could also be '+VERB'.
        self._multichar_symbols: set[str] = set()
        self._accepting_states: set[int] = set()

        self._create_graph(att_file_path)
        self._current_state: int = Fst._STARTING_STATE

        logging.debug(f'_transitions: {pformat(self._transitions)}')
        logging.debug(f'_multichar_symbols: {self._multichar_symbols}')
        logging.debug(f'_accepting_states: {self._accepting_states}')

    #endregion


    #region Private Methods

    def _create_graph(self, att_file_path: str) -> None:
        '''Create the graph that represents the FST from reading-in the provided `.att` file.'''

        with open(att_file_path) as att_file:
            att_lines = att_file.readlines()

        # Parse file into FST graph object.
        for line in att_lines:

            # Lines in the AT&T format are tab separated.
            att_line_items = line.strip().split("\t")
            num_defined_items = len(att_line_items)

            # Accepting state read in only.
            if num_defined_items == Fst._ATT_DEFINES_ACCEPTING_STATE:
                accepting_state = int(att_line_items[0])
                self._accepting_states.add(accepting_state)

            # Unweighted transition.
            elif num_defined_items == Fst._ATT_DEFINES_UNWEIGHTED_TRANSITION:
                current_state, next_state, input_symbol, output_symbol = att_line_items

                if len(input_symbol) > 1:
                    self._multichar_symbols.add(input_symbol)

                self._transitions[int(current_state)][input_symbol] = (int(next_state), output_symbol)

            # Weighted transition.
            elif num_defined_items == Fst._ATT_DEFINES_WEIGHTED_TRANSITION:
                # TODO Modify code to accept a fifth input item that defines a transition weight.
                pass

            # Invalid input line.
            else:
                logging.error(f"Invalid line in {os.path.basename(ATT_FILE_PATH)}.")
                sys.exit(EXIT_FAILURE)

    def _tokenize_input_string(self, input_string: str) -> list[str]:
        '''Returns a list containing the individual tokens that make up the `input_string`.'''

        # This gets the character lengs of all the multicharacter symbols and sorts them from highest to lowest.
        # Note lengths are distinct from use of set comprehension.
        multichar_lengths = list({
            len(symbol)
            for symbol
            in self._multichar_symbols
        })

        multichar_lengths.sort(reverse=True)
        logging.debug(f'_tokenize_input_string.multichar_lengths: {multichar_lengths}')

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

                    if substring in self._multichar_symbols:
                        tokens.append(substring)
                        input_string = input_string.removeprefix(substring) # Consume input characters.
                        should_continue_while = True
                        break

                # Continue from nested loop.
                if should_continue_while:
                    continue

            tokens.append(input_string[0])
            input_string = input_string[1:] # Consume input characters.

        logging.debug(f'_tokenize_input_string.tokens: {tokens}')
        return tokens

    # TODO Discuss handling multiple outputs. I think it should maybe be `traverse -> list[str]`?
    def _traverse(self, input_string: str) -> str | None:
        '''TODO Comment this.'''

        input_tokens = self._tokenize_input_string(input_string)
        output_string = ""

        for token in input_tokens:
            current_node = self._transitions[self._current_state]

            try:
                next_state, output_symbol = current_node[token]
            # No transition available; invalid walk.
            except KeyError:
                return None

            output_string += output_symbol
            self._current_state = next_state

        # If we finish on an accepting state, return output string.
        if self._current_state in self._accepting_states:
            return output_string

        return None

    #endregion


    #region Public Methods

    def traverse(self, input_string: str) -> str | None:
        '''TODO Comment this.'''
        output = self._traverse(input_string)
        self._current_state = Fst._STARTING_STATE
        return output

    #endregion


