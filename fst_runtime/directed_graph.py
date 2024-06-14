from __future__ import annotations
from collections import defaultdict
import sys
import os
from dataclasses import dataclass, field
from . import logger
from .att_format_error import AttFormatError

@dataclass
class DirectedNode:
    id: int
    is_accepting_state: bool
    transitions_in: list[DirectedEdge] = field(default_factory=list)
    transitions_out: list[DirectedEdge] = field(default_factory=list)

@dataclass
class DirectedEdge:
    source_node: DirectedNode
    target_node: DirectedNode
    input_symbol: str
    output_symbol: str
    penalty_weight: float = 0

    NO_WEIGHT = 0
    '''This value is set as the value of `weight` when no weight has been set for the edge.'''

class DirectedGraph:

    # The starting state in the `.att` format is represented by `0`.
    _STARTING_STATE = 0

    # These values are based on how many values of input you're getting from one line of the `.att` file; i.e. "0 1 +PLURAL s" is 4.
    _ATT_DEFINES_ACCEPTING_STATE = 1
    _ATT_DEFINES_UNWEIGHTED_TRANSITION = 4
    _ATT_DEFINES_WEIGHTED_TRANSITION = 5

    def __init__(self, att_file_path: str):
        if not att_file_path:
            logger.error("Failed to provide valid path to input file.")
            sys.exit(1)

        self.start_state: DirectedNode = None
        self.accepting_states: list[DirectedNode] = []
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
            if num_defined_items == DirectedGraph._ATT_DEFINES_ACCEPTING_STATE:
                accepting_state = int(att_line_items[0])
                accepting_states.add(accepting_state)

            # Unweighted transition.
            elif num_defined_items == DirectedGraph._ATT_DEFINES_UNWEIGHTED_TRANSITION:
                current_state, next_state, input_symbol, output_symbol = att_line_items

                if len(input_symbol) > 1:
                    self.multichar_symbols.add(input_symbol)

                transitions[int(current_state)][input_symbol] = (int(next_state), output_symbol, DirectedEdge.NO_WEIGHT)    

            # Weighted transition.
            elif num_defined_items == DirectedGraph._ATT_DEFINES_WEIGHTED_TRANSITION:
                current_state, next_state, input_symbol, output_symbol, weight = att_line_items

                if len(input_symbol) > 1:
                    self.multichar_symbols.add(input_symbol)

                transitions[int(current_state)][input_symbol] = (int(next_state), output_symbol, weight)    

            # Invalid input line.
            else:
                logger.error(f"Invalid line in {os.path.basename(att_file_path)}.")
                sys.exit(1)

        self.accepting_states = list(accepting_states)

        all_state_ids: list[int] = list(set(transitions.keys()).union(accepting_states))
        nodes: dict[int, DirectedNode] = {}

        def _get_or_create_node(state_id: int) -> DirectedNode:
            try:
                node = nodes[state_id]
            except KeyError:
                node = DirectedNode(state_id, state_id in accepting_states)
                nodes[state_id] = node

            return node

        # Add every node to dictionary.
        for current_state in all_state_ids:
            current_node = _get_or_create_node(current_state)

            # Add every edge to nodes in nodes dictionary.
            for input_symbol in transitions[current_state].keys():

                next_state, output_symbol, weight = transitions[current_state][input_symbol]
                next_node = _get_or_create_node(next_state)

                directed_edge = DirectedEdge(current_node, next_node, input_symbol, output_symbol, weight)

                current_node.transitions_out.append(directed_edge)
                next_node.transitions_in.append(directed_edge)

        try:
            self.start_state = nodes[DirectedGraph._STARTING_STATE]
        except KeyError as key_error:
            raise AttFormatError("There must be a start state specified that has state number `0` in the input `.att` file.") from key_error

    # `input` is a list of list of strings, where each inner-list of strings represents the valid options that should
    # be queried in the given order. I.e. [["PVDir/East"], ["waabam"], ["VAI"], ["Ind", "Neu"], ...]
    # TODO Check the star forces parameter naming for parameters following it.
    # TODO Follow epsilon symbols.
    # TODO Check and handle infinite loops -> no input consumption via epsilon transition that has already been walked = loop.
    # Consumed 4 symbols, if in same branch of serach we end up in the state but again having only consumed 4 symbols of the input,
    # then somewhere there is an epsilon loop that has had us end up in the same state with having done nothing in the input.
    # down_generation = `WAL+GER -> walking`
    def down_generation(self,
                 max_weight: float = DirectedEdge.NO_WEIGHT,
                 *,
                 prefix_options: list[list[str]],
                 stem: str,
                 suffix_options: list[list[str]]
            ) -> list[str]:
        ...

    # test push for github actions
    # second dummy commit
    