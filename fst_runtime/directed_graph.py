from __future__ import annotations
import logging
from collections import defaultdict
import uuid
from pprint import pformat
import sys
import os
from . import logger

from dataclasses import dataclass, field
from typing import List

@dataclass
class DirectedNode:
    id: int
    is_accepting_state: bool
    transitions_in: List["DirectedEdge"] = field(default_factory=list)
    transitions_out: List["DirectedEdge"] = field(default_factory=list)

@dataclass
class DirectedEdge:
    source_node: DirectedNode
    target_node: DirectedNode
    input_symbol: str
    output_symbol: str
    penalty_weight: float = -1

    NO_WEIGHT = -1
    '''This value is set as the value of `weight` when no weight has been set for the edge.'''

class DirectedGraph:

    # The starting state in the `.att` format is represented by `0`.
    _STARTING_STATE = 0
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
            node = _get_or_create_node(current_state)

            # Add every edge to nodes in nodes dictionary.
            for input_symbol in transitions[current_state].keys():

                next_state, output_symbol, weight = transitions[current_state][input_symbol]
                next_node = _get_or_create_node(next_state)

                directed_edge = DirectedEdge(node, next_node, input_symbol, output_symbol, weight)

                nodes[current_state].transitions_out.append(directed_edge)
                next_node.transitions_in.append(directed_edge)

        self.start_state = nodes[DirectedGraph._STARTING_STATE]

    # This and the tests need to updated to accomodate multiple output I think.
    # TODO Check with Miikka.
    def traverse(self, input_string: str) -> str:
        return None
    