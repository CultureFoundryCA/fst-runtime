'''
fst

This file is the main file of this library. It provides a class called `Fst` that defines an FST in-memory as a directed graph.
The class exposes several public endpoints, namely `multichar_symbols`, `down_generation`, and `up_analysis` (which is pending).
It also exposes a constant called `EPSILON`, which defines epsilon as `'@0@'`, according to the AT&T format standard.
'''

from __future__ import annotations
from collections import defaultdict
import sys
import os
from dataclasses import dataclass, field
from . import logger
from .att_format_error import AttFormatError
from .tokenize_input import tokenize_input_string


#region Constants

ATT_FILE_PATH = os.getenv('ATT_FILE_PATH')
'''This is the path to the FST that's been compiled to the AT&T `.att` format.'''

LOG_LEVEL = os.getenv('LOG_LEVEL')
'''The log level of the current environment.'''

EPSILON = "@0@"
'''This is the epsilon character as encoded in the AT&T `.att` FST format.'''

#endregion


#region Helper Classes

@dataclass
class _AttInputInfo:
    '''This class represents input information from the AT&T file format (`.att`) for a transition to a new state.'''

    target_state_id: int
    '''The ID of the state in the FST that is being transitioned to.'''

    transition_output_symbol: str
    '''The symbol that is outputted over the transition.'''

    transition_weight: float = 0
    '''The penalty weight of the transition. Default is zero.'''

    def __iter__(self):
        '''Defines an iterable for this object to allow for object unpacking.'''
        return iter((self.target_state_id, self.transition_output_symbol, self.transition_weight))


@dataclass
class _FstNode:
    '''This class represents a directed node in a graph that represents an FST.'''

    id: int
    '''A unique ID is given to each node in order to allow for easier lookup of nodes.'''

    is_accepting_state: bool
    '''This boolean holds whether the current node is an accepting state of the FST. When we get to the end of our input string,
    if we are at an accepting state, that means that the input is valid according to the FST, and so it will then output a value accordingly.'''

    in_transitions: list[_FstEdge] = field(default_factory=list)
    '''This is a node in a directed graph, and this list holds all the edges that lead to this node.'''

    out_transitions: list[_FstEdge] = field(default_factory=list)
    '''This is a node in a directed graph, and this list holds all the edges that lead out of this node.'''


@dataclass
class _FstEdge:
    '''This class represents a directed edge in a graph that represents an FST.'''

    source_node: _FstNode
    '''This is an edge in a directed graph, and so it leads from somewhere (source node) to somewhere (target node).'''

    target_node: _FstNode
    '''This is an edge in a directed graph, and so it leads from somewhere (source node) to somewhere (target node).'''

    input_symbol: str
    '''This edge is in an FST, and so it consumes input symbols and outputs output symbols.'''

    output_symbol: str
    '''This edge is in an FST, and so it consumes input symbols and outputs output symbols.'''

    penalty_weight: float = 0
    '''
    This represents a weight that penalizes walks through the FST. That is, if there's an edge with 0 weight and another with 1 weight,
    the edge without weight will be prioritized (walked) first.
    '''

    NO_WEIGHT = 0
    '''This value is set as the value of `weight` when no weight has been set for the edge. This is the default value for an edge.'''

#endregion


class Fst:
    '''This class represents a finite-state transducer as a directed graph.'''


    _STARTING_STATE = 0
    '''
    The starting state in the `.att` format is represented by `0`.
    This is the "top" of the graph, so when you query down, you start here and go down. Down is like walk+GER -> walking.
    '''

    _ATT_DEFINES_ACCEPTING_STATE = 1
    '''One input value on a line means that that line represents an accepting state in the `.att` file.'''

    _ATT_DEFINES_UNWEIGHTED_TRANSITION = 4
    '''Four input values an a line means that the line represents an unweighted transition in the `.att` file.'''

    _ATT_DEFINES_WEIGHTED_TRANSITION = 5
    '''Five input values an a line means that the line represents a weighted transition in the `.att` file.'''


    def __init__(self, att_file_path: str):
        '''Initializes the FST via the provided `.att` file.'''

        if not att_file_path:
            logger.error("Failed to provide valid path to input file. Example: `/path/to/fst.att`.")
            sys.exit(1)

        if not str(att_file_path).endswith('.att'):
            logger.error("Provided file path does not point to a `.att` file. Example: `/path/to/fst.att`.")
            sys.exit(1)

        self._start_state: _FstNode = None
        '''This is the entry point into the FST. This is functionally like the root of a tree (even though this is a graph, not a tree).'''

        self._accepting_states: set[_FstNode] = set()
        '''This set holds all the accepting states of the FST.'''

        self._multichar_symbols: set[str] = set()
        '''This set represents all the multi-character symbols that have been defined in the FST.'''

        self._create_graph(att_file_path)


    @property
    def multichar_symbols(self):
        '''Public getter for the multichar_symbols variable.'''
        return self._multichar_symbols.copy()


    def _create_graph(self, att_file_path: str) -> None: # pylint: disable=too-many-locals
        '''Create the graph that represents the FST from reading-in the provided `.att` file.'''

        # This is a dictionary whose key is the source state number as read in from the `.att` file (i.e. 22),
        # and whose value is a dictionary. This child dictionary is keyed to the input symbol from the `.att` file
        # (i.e. 'k' or '+PLURAL'), and whose value is a class that contains the target state number, the output
        # of the transition, and the weight of that transition.
        transitions: dict[int, dict[str, _AttInputInfo]] = defaultdict(dict)
        accepting_states: set[int] = set()

        with open(att_file_path, encoding='utf-8') as att_file:
            att_lines = att_file.readlines()

        # Parse file into FST graph object.
        for line in att_lines:

            # Lines in the AT&T format are tab separated.
            att_line_items = line.strip().split("\t")
            num_defined_items = len(att_line_items)

            # Accepting state read in only.
            if num_defined_items == Fst._ATT_DEFINES_ACCEPTING_STATE:
                accepting_state = int(att_line_items[0])
                accepting_states.add(accepting_state)

            # Unweighted transition.
            elif num_defined_items == Fst._ATT_DEFINES_UNWEIGHTED_TRANSITION:
                current_state, next_state, input_symbol, output_symbol = att_line_items

                if len(input_symbol) > 1:
                    self._multichar_symbols.add(input_symbol)

                transitions[int(current_state)][input_symbol] = _AttInputInfo(int(next_state), output_symbol, _FstEdge.NO_WEIGHT)

            # Weighted transition.
            elif num_defined_items == Fst._ATT_DEFINES_WEIGHTED_TRANSITION:
                current_state, next_state, input_symbol, output_symbol, weight = att_line_items

                if len(input_symbol) > 1:
                    self._multichar_symbols.add(input_symbol)

                transitions[int(current_state)][input_symbol] = _AttInputInfo(int(next_state), output_symbol, weight)

            # Invalid input line.
            else:
                logger.error("Invalid line in %s.", os.path.basename(att_file_path))
                sys.exit(1)

        self._accepting_states = accepting_states

        all_state_ids: list[int] = list(set(transitions.keys()).union(accepting_states))
        nodes: dict[int, _FstNode] = {}


        def _get_or_create_node(state_id: int) -> _FstNode:
            '''Tries to get a node, and if it doesn't exist, it creates it first, then returns it.'''
            try:
                node = nodes[state_id]
            except KeyError:
                node = _FstNode(state_id, state_id in accepting_states)
                nodes[state_id] = node

            return node


        # Add every node to dictionary.
        for current_state in all_state_ids:
            current_node = _get_or_create_node(current_state)

            # Add every edge to nodes in nodes dictionary.
            for input_symbol in transitions[current_state].keys():

                next_state, output_symbol, weight = transitions[current_state][input_symbol]
                next_node = _get_or_create_node(next_state)

                directed_edge = _FstEdge(current_node, next_node, input_symbol, output_symbol, weight)

                current_node.out_transitions.append(directed_edge)
                next_node.in_transitions.append(directed_edge)

        try:
            self._start_state = nodes[Fst._STARTING_STATE]
        except KeyError as key_error:
            raise AttFormatError("There must be a start state specified that has state number `0` in the input `.att` file.") from key_error


    # region Down/Generation Methods

    def down_generation(self,
        prefix_options: list[list[str]],
        lemma: str,
        suffix_options: list[list[str]],
    ) -> list[str]:
        '''
        This function queries the FST in the down/generation direction. That means that, when provided lists of prefixes and suffixes
        as well as the lemma, it fully permutes the the tags based on the slots of the affixes. For example, say you have the lemma "wal"
        in English (for the lemma "walk"), with prefix tags `[["+VERB"], ["+INF", "+PAST", "+GER", "+PRES"]]`. Then, these would be fully
        permuted to "wal+VERB+INF", "wal+VERB+PAST", "wal+VERB+GER", and "wal+VERB+PRES"; likewise with any prefixes. All of these constructions
        are then walked over the FST to see if we end at an accepting state. If so, the generated forms (i.e. walk, walked, walking, walks) will
        be added to a list and returned.
        '''

        permutations: list[list[str]] = prefix_options + [[lemma]] + suffix_options
        logger.debug('Permutations created: %s', permutations)

        queries: list[str] = Fst._permute_tags(permutations)
        logger.debug('Queries created: %s', queries)

        return self._traverse_down(queries)

    def _traverse_down(self, queries: list[str]) -> list[str]:
        '''This function handles all the queries down the FST, and returns all the resulting outputs that were found.'''

        generated_results = []

        for query in queries:
            # This function call is potentially parallelizable in the future, though I'm not sure the queries take long enough for the cost.
            results = Fst.__traverse_down(current_node=self._start_state, input_tokens=tokenize_input_string(query, self._multichar_symbols))

            logger.debug('Query: %s\tResults: %s', query, results)
            generated_results.extend(results)

        return [generation.replace(EPSILON, '') for generation in generated_results]

    @staticmethod
    def __traverse_down(current_node: _FstNode, input_tokens: list[str]) -> list[str]:
        '''
        This method traverses down the FST beginning at an initial provided node. It walks through the FST,
        recursively finding matches that it builds up through the traversal.
        '''

        matches: list[str] = []

        current_token = input_tokens[0] if input_tokens else ''

        for edge in current_node.out_transitions:

            # If the current transition is an epsilon transition, then consume no input and recurse.
            if edge.input_symbol == EPSILON:

                # Case: there are no more input tokens, but you have an epsilon transition to follow.
                # In this case, you follow the epsilon, and see if you're in an accepting state. If so,
                # then add the output of this transition to the matches and continue to the recursive step,
                # since there could be further epsilon transitions to follow.
                if not current_token and edge.target_node.is_accepting_state:
                    matches.append(edge.output_symbol)

                recursive_results = Fst.__traverse_down(edge.target_node, input_tokens)

                for result in recursive_results:
                    matches.append(edge.output_symbol + result)

            # If we have found an explicit match of the current token with the edge's input token, then we are going
            # to want to create the new input symbols for the next level of recursion by chopping off the current token,
            # and getting the resulting output of that recursion. Then, we'll want to loop over that result, and, since
            # we consumed an input token over this current transition, we add `edge.output_symbol + result` to the matches.
            elif current_token == edge.input_symbol:
                new_input_tokens = input_tokens[1:]

                if not new_input_tokens and edge.target_node.is_accepting_state:
                    matches.append(edge.output_symbol)

                recursive_results = Fst.__traverse_down(edge.target_node, new_input_tokens)

                for result in recursive_results:
                    matches.append(edge.output_symbol + result)

        logger.debug('matches: %s', matches)
        return matches

    @staticmethod
    def _permute_tags(parts: list[list[str]]) -> list[str]:
        '''Recursively descend into the tags in order to create all permutations of the given tags in the given order.'''

        if not parts:
            return ['']

        # Remember: EPSILON in a slot mean that slot can be omitted for a construction.
        # Example: parts = [["dis", "re"], ["member"], ["ment", "ing"], ["s", EPSILON]]
        # First pass: first_part = ["dis", "re"], rest_parts = [["member"], ["ment", "ing"], ["s", EPSILON]]
        # Second pass: first_part = ["member"], rest_parts = [["ment", "ing"], ["s", EPSILON]]
        # Third pass: first_part = ["ment", "ing"], rest_parts = [["s", EPSILON]]
        # Fourth pass: first_part = ["s", EPSILON], rest_parts = [] <- base case reached
        # Fourth pass return: ['']
        # Third pass return: ["ments", "ment", "ings", "ing"] <- note the epsilon omissions here
        # Second pass return: ["memberments", "memberment", "memberings", "membering"]
        # First pass return: ["dismemberments", "dismemberment", "dismemberings", "dismembering",
        #                       "rememberments", "rememberment", "rememberings", "remembering"]
        # Having incorrect combinations like this is okay, like "rememberments", as they'll just return no results
        # from the final FST when you try to query it (i.e. ends up in an unaccepting state).
        first_part = parts[0]
        rest_parts = Fst._permute_tags(parts[1:])
        result = []

        for prefix in first_part:
            for suffix in rest_parts:
                if prefix == EPSILON:
                    result.append(suffix)
                else:
                    result.append(prefix + suffix)

        return result

    #endregion
