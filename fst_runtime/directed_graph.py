from __future__ import annotations
import logging
from collections import defaultdict
import uuid
from pprint import pformat
import sys
import os
from . import logger

class DirectedEdge:

    NO_WEIGHT = -1

    def __init__(self, source_node: DirectedNode, target_node: DirectedNode, input_symbol: str, output_symbol: str, weight: float = -1):
        self.source_node: DirectedNode = source_node
        self.target_node: DirectedNode = target_node
        self.weight: float = weight
        self.input_symbol: str = input_symbol
        self.output_symbol: str = output_symbol

class DirectedNode:
    def __init__(self, id: int, is_accepting_state: bool):
        self.id: int = id
        self.is_accepting_state: bool = is_accepting_state
        self.transitions_in: list[DirectedEdge] = []
        self.transitions_out: list[DirectedEdge] = []

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

    def _create_graph(self, att_file_path: str):
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

        # Add every node to dictionary.
        for current_state in all_state_ids:
            try:
                node = nodes[current_state]
            except KeyError:
                node = DirectedNode(current_state, current_state in accepting_states)
                nodes[current_state] = node

            # Add every edge to nodes in nodes dictionary.
            for input_symbol in transitions[current_state].keys():
                next_state, output_symbol, weight = transitions[current_state][input_symbol]
                directed_edge = DirectedEdge(current_state, next_state, input_symbol, output_symbol, weight)
                nodes[current_state].transitions_out.append(directed_edge)

                try:
                    next_node = nodes[next_state]
                except:
                    next_node = DirectedNode(next_state, next_state in accepting_states)
                    nodes[next_state] = next_node

                next_node.transitions_in.append(directed_edge)

        self.start_state = nodes[DirectedGraph._STARTING_STATE]

    def traverse(self, input_string: str):
        return None