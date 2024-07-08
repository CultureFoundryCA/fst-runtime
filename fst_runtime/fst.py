from __future__ import annotations
from collections import defaultdict
import sys
import os
from dataclasses import dataclass, field
from . import logger
from .att_format_error import AttFormatError
from .tokenize_input import tokenize_input_string

ATT_FILE_PATH = os.getenv('ATT_FILE_PATH')
LOG_LEVEL = os.getenv('LOG_LEVEL')
EPSILON = "@0@"

@dataclass
class FstNode:
    id: int
    is_accepting_state: bool
    in_transitions: list[FstEdge] = field(default_factory=list)
    out_transitions: list[FstEdge] = field(default_factory=list)

@dataclass
class FstEdge:
    source_node: FstNode
    target_node: FstNode
    input_symbol: str
    output_symbol: str
    penalty_weight: float = 0

    NO_WEIGHT = 0
    '''This value is set as the value of `weight` when no weight has been set for the edge.'''

class Fst:

    # The starting state in the `.att` format is represented by `0`.
    # This is the "top" of the graph, so when you query down, you start here and go down. Down is like walk+GER -> walking.
    _STARTING_STATE = 0

    # These values are based on how many values of input you're getting from one line of the `.att` file; i.e. "0 1 +PLURAL s" is 4.
    _ATT_DEFINES_ACCEPTING_STATE = 1
    _ATT_DEFINES_UNWEIGHTED_TRANSITION = 4
    _ATT_DEFINES_WEIGHTED_TRANSITION = 5

    def __init__(self, att_file_path: str):
        if not att_file_path:
            logger.error("Failed to provide valid path to input file.")
            sys.exit(1)

        self.start_state: FstNode = None
        self.accepting_states: list[FstNode] = []
        self.multichar_symbols: set[str] = set()

        self._create_graph(att_file_path)

    def _create_graph(self, att_file_path: str) -> None:
        '''Create the graph that represents the FST from reading-in the provided `.att` file.'''

        # This is a dictionary whose key is the source state number as read in from the `.att` file (i.e. 22),
        # and whose value is dictionary. This child dictionary is keyed to the input symbol from the `.att` file
        # (i.e. 'k' or '+PLURAL'), and whose value is a tuple that contains the target state number, the output
        # of the transition, and the weight of that transition.
        transitions: dict[int, dict[str, tuple[int, str, float]]] = defaultdict(dict)
        accepting_states: set[int] = set()

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
                accepting_states.add(accepting_state)

            # Unweighted transition.
            elif num_defined_items == Fst._ATT_DEFINES_UNWEIGHTED_TRANSITION:
                current_state, next_state, input_symbol, output_symbol = att_line_items

                if len(input_symbol) > 1:
                    self.multichar_symbols.add(input_symbol)

                transitions[int(current_state)][input_symbol] = (int(next_state), output_symbol, FstEdge.NO_WEIGHT)

            # Weighted transition.
            elif num_defined_items == Fst._ATT_DEFINES_WEIGHTED_TRANSITION:
                current_state, next_state, input_symbol, output_symbol, weight = att_line_items

                if len(input_symbol) > 1:
                    self.multichar_symbols.add(input_symbol)

                transitions[int(current_state)][input_symbol] = (int(next_state), output_symbol, weight)

            # Invalid input line.
            else:
                logger.error("Invalid line in %s.", os.path.basename(att_file_path))
                sys.exit(1)

        self.accepting_states = list(accepting_states)

        all_state_ids: list[int] = list(set(transitions.keys()).union(accepting_states))
        nodes: dict[int, FstNode] = {}

        def _get_or_create_node(state_id: int) -> FstNode:
            try:
                node = nodes[state_id]
            except KeyError:
                node = FstNode(state_id, state_id in accepting_states)
                nodes[state_id] = node

            return node

        # Add every node to dictionary.
        for current_state in all_state_ids:
            current_node = _get_or_create_node(current_state)

            # Add every edge to nodes in nodes dictionary.
            for input_symbol in transitions[current_state].keys():

                next_state, output_symbol, weight = transitions[current_state][input_symbol]
                next_node = _get_or_create_node(next_state)

                directed_edge = FstEdge(current_node, next_node, input_symbol, output_symbol, weight)

                current_node.out_transitions.append(directed_edge)
                next_node.in_transitions.append(directed_edge)

        try:
            self.start_state = nodes[Fst._STARTING_STATE]
        except KeyError as key_error:
            raise AttFormatError("There must be a start state specified that has state number `0` in the input `.att` file.") from key_error

    # `input` is a list of list of strings, where each inner-list of strings represents the valid options that should
    # be queried in the given order. I.e. [["PVDir/East"], ["waabam"], ["VAI"], ["Ind", "Neu"], ...]
    # must fully explore every inner list (slot) , every possible option in the correct order
    # TODO Check the star forces parameter naming for parameters following it.
    # TODO Follow epsilon symbols.
    # TODO Check and handle infinite loops -> no input consumption via epsilon transition that has already been walked = loop.
    # Consumed 4 symbols, if in same branch of serach we end up in the state but again having only consumed 4 symbols of the input,
    # then somewhere there is an epsilon loop that has had us end up in the same state with having done nothing in the input.
    # down_generation = `WAL+GER -> walking` GER = gerund verb becomes noun-like
    def down_generation(self,
        prefix_options: list[list[str]],
        stem: str,
        suffix_options: list[list[str]],
        max_weight: float = FstEdge.NO_WEIGHT
    ) -> list[str]:

        if max_weight != FstEdge.NO_WEIGHT:
            raise NotImplementedError("The weight feature is not currently available.")

        permutations: list[list[str]] = prefix_options + [[stem]] + suffix_options
        logger.debug('Permutations created: %s', permutations)

        queries: list[str] = self._permute_tags(permutations)
        logger.debug('Queries created: %s', queries)

        return self._traverse_down(queries)

    def _traverse_down(self, queries: list[str]) -> list[str]:

        generated_results = []

        for query in queries:
            # This function call is potentially parallelizable in the future, though I'm not sure the queries take long enough for the cost.
            results = Fst.__traverse_down(current_node=self.start_state, input_tokens=tokenize_input_string(query, self.multichar_symbols))

            logger.debug('Query: %s\tResults: %s', query, results)
            generated_results.extend(results)

        return [generation.replace(EPSILON, '') for generation in generated_results]

    @staticmethod
    def __traverse_down(current_node: FstNode, input_tokens: list[str]) -> list[str]:
        '''
        Okay, I just have to write this out here. So what am I trying to do. I have a query string. For the query string, I want to
        look at the first character(s) to see if they match the input symbol for a transition out of the current node. If that symbol matches,
        I want to consume those characters, then call this function recursively with the next node selected and the new query added. Concantenting
        the return values of these recursive calls together will then give me an output string, assuming an accepting walk was found.

        Regardless, once that one walk is completed, I need to make sure that I don't do the exact same walk again. So, I start at the start state again,
        but this time I IGNORE the transitions_out that I have already visited. This way, I can see if there are other accepting states to explore.
        But, this can't happen at the recursive level, because then we'll have gibberish returned. UNLESS we instead return a list[str], in which case
        all the returned values from the recursive call get permuted together as valid combinations from that node. Yes yes yes.

        Base case is accepting state + no further input, OR no further input.
        '''

        matches: list[str] = []

        current_token = input_tokens[0] if input_tokens else ''

        for edge in current_node.out_transitions:

            # If there are no input symbols left to consume and no epsilon transations to follow, then
            # we are currently at an unaccepting state, and so we do nothing and continue.
            if not current_token and edge.input_symbol != EPSILON:
                logger.debug('no token no epsilon')
                continue

            # If the current transition is an epsilon transition, then consume no input and recurse.
            elif edge.input_symbol == EPSILON:

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

            # No epsilon transitions to follow, and current token doesn't match the input symbol of the current edge.
            else:
                continue

        logger.debug('matches: %s', matches)
        return matches

    def _permute_tags(self, parts: list[list[str]]) -> list[str]:
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
        rest_parts = self._permute_tags(parts[1:])
        result = []

        for prefix in first_part:
            for suffix in rest_parts:
                if prefix == EPSILON:
                    result.append(suffix)
                else:
                    result.append(prefix + suffix)

        return result

    def up_analysis():
        raise NotImplementedError("Up direction not yet coded.")
