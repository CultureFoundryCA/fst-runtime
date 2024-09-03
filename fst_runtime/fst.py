"""
This module provides the main class ``Fst`` which defines a finite-state transducer (FST) in-memory as a directed graph.

Attributes
----------
Fst : class
    Defines an FST in-memory as a directed graph.

EPSILON : str
    The epsilon character as encoded in the AT&T ``.att`` FST format; this representation is the string: ``@0@``.
"""


#region Imports and Constants

from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field, replace
import os
import sys
from typing import Generator, Iterator, Any

from fst_runtime import logger
from fst_runtime.att_format_error import AttFormatError
from fst_runtime.semiring import Semiring
from fst_runtime.tokenize_input import tokenize_input_string

EPSILON: str = "@0@"
"""This is the epsilon character as encoded in the AT&T ``.att`` FST format."""

#endregion


#region Helper Classes

@dataclass
class FstOutput:
    """
    A dataclass for holding the output from a given node to another in an FST.

    Attributes
    ----------
    ouput_string : str
        This string represents the current state of the FST output; e.g. this could be "r", then "ru", then "run" as you walk through the FST.

    path_weight : Any
        This is the current weight of the path being walked. This value is computed via the semiring provided to the FST.

    """
    output_string: str
    """This string represents the current state of the FST output; e.g. this could be "r", then "ru", then "run" as you walk through the FST."""

    path_weight: Any
    """This is the current weight of the path being walked. This value is computed via the semiring provided to the FST."""


@dataclass
class _AttInputInfo:
    """
    Represents input information from the AT&T file format (``.att``) for a transition to a new state.

    Attributes
    ----------
    target_state_id : int
        The ID of the state in the FST that is being transitioned to.

    transition_output_symbol : str
        The symbol that is outputted over the transition.

    transition_weight : Any, optional
        The weight associated with a transition, should it have one.
    """

    target_state_id: int
    """The ID of the state in the FST that is being transitioned to."""

    transition_output_symbol: str
    """The symbol that is outputted over the transition."""

    transition_weight: Any = field(default=None)
    """The weight associated with a transition, should it have one."""

    def __iter__(self) -> Iterator[int | str | float]:
        """
        Defines an iterable for this object to allow for object unpacking.

        Yields
        ------
        int
            The ID of the state in the FST that is being transitioned to.
        str
            The symbol that is outputted over the transition.
        float
            The penalty weight of the transition.
        """
        yield self.target_state_id
        yield self.transition_output_symbol
        yield self.transition_weight


@dataclass
class _FstNode:
    """
    Represents a directed node in a graph that represents an FST.

    Attributes
    ----------
    id : int
        A unique ID given to each node for easier lookup.

    is_accepting_state : bool
        Indicates whether the current node is an accepting state of the FST.

    final_state_weight : Any
        Represents the weight of acceptance of this state if it is an accepting state.

    in_transitions : list[_FstEdge]
        Holds all the edges that lead to this node.

    out_transitions : list[_FstEdge]
        Holds all the edges that lead out of this node.
    """

    id: int
    """A unique ID is given to each node in order to allow for easier lookup of nodes."""

    is_accepting_state: bool
    """
    This boolean holds whether the current node is an accepting state of the FST.
    When we get to the end of our input string, if we are at an accepting state, that means
    that the input is valid according to the FST, and so it will then output a value accordingly.
    """

    final_state_weight: Any = field(default=None)
    """If this state is an accepting state, then there can be a weight to that acceptance. This value represents that weight."""

    in_transitions: list[_FstEdge] = field(default_factory=list)
    """This is a node in a directed graph, and this list holds all the edges that lead to this node."""

    out_transitions: list[_FstEdge] = field(default_factory=list)
    """This is a node in a directed graph, and this list holds all the edges that lead out of this node."""


@dataclass
class _FstEdge:
    """
    Represents a directed edge in a graph that represents an FST.

    Attributes
    ----------
    source_node : _FstNode
        The source node where the edge starts.

    target_node : _FstNode
        The target node where the edge ends.

    input_symbol : str
        The input symbol consumed by this edge in the FST.

    output_symbol : str
        The output symbol produced by this edge in the FST.

    weight : float, optional
        The weight that penalizes traversing this edge. Default is 0.
    """

    source_node: _FstNode
    """This is an edge in a directed graph, and so it leads from somewhere (source node) to somewhere (target node)."""

    target_node: _FstNode
    """This is an edge in a directed graph, and so it leads from somewhere (source node) to somewhere (target node)."""

    input_symbol: str
    """This edge is in an FST, and so it consumes input symbols and outputs output symbols."""

    output_symbol: str
    """This edge is in an FST, and so it consumes input symbols and outputs output symbols."""

    weight: Any = field(default=None)
    """This represents a weight on a transition in an FST. The values that this field can take are in the domain of the corresponding semiring."""

#endregion


class Fst:
    """
    Represents a finite-state transducer as a directed graph.

    Attributes
    ----------
    recursion_limit : int
        Sets the recursion limit for the generation/analysis functionality, to prevent epsilon cycles from running amok.

    multichar_symbols : set[str]
        A copy of the set of multi-character symbols defined in the FST.

    down_generation : method
        Generates wordforms from a lemma and sets of prefix and suffix tags.

    down_generations : method
        Generates wordforms from many lemmas and common sets of prefix and suffix tags.

    up_analysis : method
        Analyzes a wordform and returns any associated tagged lemmas of the wordform.

    up_analyses : method
        Analyzes many wordforms and returns their associated tagged lemmas of each wordform in a dictionary keyed to the wordform.
    """


    #region Variables and Initialization

    _STARTING_STATE = 0
    """
    The starting state in the ``.att`` format is represented by ``0`.
    This is the "top" of the graph, so when you query down, you start here and go down.
    Down is like walk+GER -> walking.
    """

    _ATT_DEFINES_UNWEIGHTED_ACCEPTING_STATE = 1
    """One input value on a line means that that line represents an accepting state in the ``.att`` file."""

    _ATT_DEFINES_WEIGHTED_ACCEPTING_STATE = 2
    """Two input values on a line indicates that the line represents an accepting state with a weight in the ``.att`` file."""

    _ATT_DEFINES_UNWEIGHTED_TRANSITION = 4
    """Four input values on a line mean that the line represents an unweighted transition in the ``.att`` file."""

    _ATT_DEFINES_WEIGHTED_TRANSITION = 5
    """Five input values on a line mean that the line represents a weighted transition in the ``.att`` file."""

    def __init__(self, att_file_path: str, *, semiring: Semiring | None = None, recursion_limit: int | None = None) -> None:
        """
        Initializes the FST via the provided ``.att`` file.

        Parameters
        ----------
        att_file_path : str
            The path to the ``.att`` file containing the FST description.

        semiring: Semiring | None, optional
            The semiring over which the weights in the FST are defined.

        recursion_limit : int | None, optional
            The recursion limit for the generation/analysis functionality. Default is ``None``, which leaves it as the python default of 1000.
        """

        if not att_file_path:
            logger.error("Failed to provide valid path to input file. Example: ``/path/to/fst.att``.")
            sys.exit(1)

        if not str(att_file_path).endswith('.att'):
            logger.error("Provided file path does not point to a ``.att`` file. Example: ``/path/to/fst.att``.")
            sys.exit(1)

        self._start_state: _FstNode = _FstNode(-1, False, [], [])
        """This is the entry point into the FST. This is functionally like the root of a tree (even though this is a graph, not a tree)."""

        self._accepting_states: dict[int, _FstNode] = {}
        """This dictionary holds all the accepting states of the FST."""

        self._multichar_symbols: set[str] = set()
        """This set represents all the multi-character symbols that have been defined in the FST."""

        self._semiring: Semiring | None = semiring
        """This holds the semiring used to perform weight arithmetic on paths in the FST."""

        self._recursion_limit: int | None = recursion_limit
        """This sets the recursion limit for the generation/analysis functionality, so that epsilon cycles don't run amok."""

        self._create_graph(att_file_path)

    @property
    def multichar_symbols(self) -> set[str]:
        """
        Public getter for the multichar_symbols variable.

        Returns
        -------
        set[str]
            A copy of the set of multi-character symbols.
        """
        return self._multichar_symbols.copy()
    
    @property
    def recursion_limit(self) -> int | None:
        """
        Public getter for the recursion_limit variable.

        Returns
        -------
        int
            The recursion limit that has been set. A value less than 1 represents that no recursion limit has been set,
            and so the current system recursion limit will be used (default for Python applications).
        """
        return self._recursion_limit

    @recursion_limit.setter
    def recursion_limit(self, new_recursion_limit: int | None) -> None:
        """
        Public setter for the recursion_limit variable.

        Parameters
        ----------
        new_recursion_limit : int
            The new value to set the recursion limit to.
        """
        self._recursion_limit = new_recursion_limit

    #endregion


    #region Graph Creation

    def _get_or_create_node(self, state_id: int, nodes: dict[int, _FstNode], accepting_states: dict[int, Any]) -> _FstNode:
        """
        Tries to get a node from the dictionary, and if it doesn't exist, creates it first, then returns it.

        Parameters
        ----------
        state_id : int
            The unique identifier for the state.

        nodes : dict[int, _FstNode]
            The dictionary containing all the nodes, keyed by their state IDs.

        accepting_states : dict[int, Any]
            A dictionary whose keys are the IDs of the accepting states, and whose values are the weights of those accepting states.

        Returns
        -------
        _FstNode
            The node corresponding to the given state ID.
        """
        try:
            node = nodes[state_id]
        except KeyError:
            is_accepting_state = state_id in accepting_states

            try:
                weight = accepting_states[state_id]
            except KeyError:
                weight = self._semiring.multiplicative_identity if self._semiring else None

            node = _FstNode(state_id, is_accepting_state, final_state_weight=weight)
            nodes[state_id] = node

            if is_accepting_state and node.id not in self._accepting_states:
                self._accepting_states[node.id] = node

        return node


    def _read_att_file_into_transitions(self, att_file_path: str) \
        -> tuple[dict[int, dict[str, list[_AttInputInfo]]], dict[int, Any]]: # pylint: disable=too-many-branches,too-many-statements
        """
        Reads in all the transition and state information from the file into the ``transitions`` object,
        and also saves the accepting states of the FST.

        Parameters
        ----------
        att_file_path : str
            The path to the ``.att`` file containing the FST description.

        Returns
        -------
        tuple[dict[int, dict[str, list[_AttInputInfo]]], dict[int, Any]]
            A tuple containing:
            - ``transitions`` : dict[int, dict[str, list[_AttInputInfo]]]
                The dictionary of transitions read from the ``.att`` file, keyed by state ID and input symbol.
            - ``accepting_states`` : dict[int, Any]
                A dictionary whose keys are accepting state IDs and whose values are the weight of the accepting state.

        Raises
        ------
        ValueError
            This exception is raised when trying to parse the states and weights into their respective types.
        """

        # See comment in ``_create_graph`` for what this object is.
        transitions: dict[int, dict[str, list[_AttInputInfo]]] = defaultdict(dict)
        accepting_states: dict[int, Any] = {}

        with open(att_file_path, encoding='utf-8') as att_file:

            # Parse file into FST graph object.
            for line in att_file:
                
                # Lines in the AT&T format are tab separated.
                # No .strip() in case whitespace character is an output. This is very important.
                att_line_items = line.replace('\n', '').split('\t')
                num_defined_items = len(att_line_items)

                # Unweighted accepting state read in only.
                if num_defined_items == Fst._ATT_DEFINES_UNWEIGHTED_ACCEPTING_STATE:
                    state_id = int(att_line_items[0])
                    weight = None if self._semiring is None else self._semiring.multiplicative_identity
                    accepting_states[state_id] = weight

                # Unweighted transition.
                elif num_defined_items == Fst._ATT_DEFINES_UNWEIGHTED_TRANSITION:
                    current_state, next_state, input_symbol, output_symbol = att_line_items

                    if len(input_symbol) > 1:
                        self._multichar_symbols.add(input_symbol)

                    if len(output_symbol) > 1:
                        self._multichar_symbols.add(output_symbol)

                    try:
                        next_state = int(next_state)
                    except ValueError:
                        raise

                    weight = None if self._semiring is None else self._semiring.multiplicative_identity
                    info = _AttInputInfo(next_state, output_symbol, weight)

                    try:
                        transitions[int(current_state)][input_symbol].append(info)
                    except KeyError:
                        transitions[int(current_state)][input_symbol] = [info]

                # Weighted accepting state.
                elif num_defined_items == Fst._ATT_DEFINES_WEIGHTED_ACCEPTING_STATE:
                    state_id, weight = att_line_items

                    state_id = int(state_id)

                    if self._semiring is not None:
                        weight = self._semiring.convert_string_into_domain(weight)
                    else:
                        weight = None

                    accepting_states[state_id] = weight

                # Weighted transition.
                elif num_defined_items == Fst._ATT_DEFINES_WEIGHTED_TRANSITION:
                    current_state, next_state, input_symbol, output_symbol, weight = att_line_items

                    if len(input_symbol) > 1:
                        self._multichar_symbols.add(input_symbol)
                    
                    if len(output_symbol) > 1:
                        self._multichar_symbols.add(output_symbol)

                    next_state = int(next_state)

                    if self._semiring is not None:
                        weight = self._semiring.convert_string_into_domain(weight)
                    else:
                        weight = None

                    info = _AttInputInfo(next_state, output_symbol, weight)

                    try:
                        transitions[int(current_state)][input_symbol].append(info)
                    except KeyError:
                        transitions[int(current_state)][input_symbol] = [info]

                # Invalid input line.
                else:
                    logger.error("Invalid line in %s. Offending line: %s", os.path.basename(att_file_path), line)
                    sys.exit(1)

        return transitions, accepting_states


    # This function is easier to read when not split up into more parts. Too many locals disabled for this reason.
    def _create_graph(self, att_file_path: str) -> None: # pylint: disable=too-many-locals
        """
        Create the graph that represents the FST from reading in the provided ``.att`` file.

        This method initializes the FST by reading transitions and accepting states from the
        specified file, creating all nodes and transitions, and setting the start state.

        Parameters
        ----------
        att_file_path : str
            The path to the ``.att`` file containing the FST description.

        Raises
        ------
        AttFormatError
            This error is raised if the FST is ill-defined according to the AT&T format.

        Note
        -----
        ``transitions`` is a dictionary whose key is the source state number as read in from the ``.att`` file
        (e.g., 22), and whose value is a dictionary. This child dictionary is keyed to the input symbol from 
        the ``.att`` file (e.g., 'k' or '+PLURAL'), and whose value is a class that contains the target state 
        number, the output of the transition, and the weight of that transition.
        """

        transitions, accepting_states = self._read_att_file_into_transitions(att_file_path)

        accepting_state_ids: set[int] = set(accepting_states.keys())
        transition_state_ids: set[int] = set(transitions.keys())
        all_state_ids: set[int] = set.union(accepting_state_ids, transition_state_ids)

        nodes: dict[int, _FstNode] = {}

        # For every state in the FST, create/get that as a _FstNode object
        for current_state in all_state_ids:
            current_node = self._get_or_create_node(current_state, nodes, accepting_states)

            # Then, for every transition that leads out from this node, get then next node, create the new transition as an _FstEdge object,
            # and add that transition to the current node's out transitions and the target node's in transitions.
            for input_symbol, att_inputs in transitions[current_state].items():
                for att_input in att_inputs:

                    next_state, output_symbol, weight = att_input
                    next_node = self._get_or_create_node(next_state, nodes, accepting_states) # type: ignore

                    directed_edge = _FstEdge(current_node, next_node, input_symbol, output_symbol, weight) # type: ignore

                    current_node.out_transitions.append(directed_edge)
                    next_node.in_transitions.append(directed_edge)

        # Set the start state.
        try:
            self._start_state = nodes[Fst._STARTING_STATE]
        except KeyError as key_error:
            raise AttFormatError("There must be a start state specified that has state number ``0` in the input ``.att`` file.") from key_error

    #endregion


    # region Down/Generation Methods

    def down_generations(
        self,
        lemmas: list[str],
        *,
        prefixes: list[list[str]] | None = None,
        suffixes: list[list[str]] | None = None
    ) -> dict[str, Generator[FstOutput]]:
        """
        Calls ``down_generation`` for each lemma and returns a dictionary keyed on each lemma.

        The values in the dictionary are generators of wordforms returned by the FST.

        Parameters
        ----------
        lemmas : list[str]
            The list of lemmas to process.

        prefixes : list[list[str]], optional
            A list of lists containing prefix sequences. Default is None.

        suffixes : list[list[str]], optional
            A list of lists containing suffix sequences. Default is None.

        Returns
        -------
        dict[str, Generator[str]]
            A dictionary where each key is a lemma and the value is a generator of wordforms generated by the FST.

        See Also
        --------
        down_generation : For more information on how each lemma is processed.
        """

        prefixes = [[EPSILON]] if prefixes is None else prefixes
        suffixes = [[EPSILON]] if suffixes is None else suffixes

        generated_forms = {}

        for lemma in lemmas:
            generated_forms[lemma] = self.down_generation(lemma, prefixes=prefixes, suffixes=suffixes)

        return generated_forms


    def down_generation(
        self,
        lemma: str,
        *,
        prefixes: list[list[str]] | None = None,
        suffixes: list[list[str]] | None = None
    ) -> Generator[FstOutput]:
        """
        Queries the FST in the down/generation direction.

        Parameters
        ----------
        lemma : str
            The lemma to process.

        prefixes : list[list[str]], optional
            A list of lists containing prefix sequences. Default is None.

        suffixes : list[list[str]], optional
            A list of lists containing suffix sequences. Default is None.

        Returns
        -------
        Generator[FstOutput]
            A generator of generated forms that are accepted by the FST along with their weights.

        Note
        -----
        When provided lists of prefixes and suffixes as well as the lemma, it fully permutes the tags based on the slots of the affixes. 
        For example, the lemma "wal" in English (for the lemma "walk"), with prefix tags ``[["+VERB"], ["+INF", "+PAST", "+GER", "+PRES"]]``. 
        Then, these would be fully permuted to "wal+VERB+INF", "wal+VERB+PAST", "wal+VERB+GER", and "wal+VERB+PRES"; likewise with any prefixes. 
        All of these constructions are then walked over the FST to see if we end at an accepting state. If so, the generated forms 
        (i.e., walk, walked, walking, walks) will be added to a list and returned.
        """
        
        prefixes = [[EPSILON]] if prefixes is None else prefixes
        suffixes = [[EPSILON]] if suffixes is None else suffixes

        permutations: list[list[str]] = prefixes + [[lemma]] + suffixes

        queries: list[str] = Fst._permute_tags(permutations)
        logger.debug('Queries created: %s', queries)

        yield from self._traverse_down(queries)


    @staticmethod
    def _permute_tags(parts: list[list[str]]) -> list[str]:
        """
        Recursively descends into the tags to create all permutations of the given tags in the given order.

        Parameters
        ----------
        parts : list[list[str]]
            A list of lists containing tag sequences to permute.

        Returns
        -------
        list[str]
            A list of all permutations of the given tags in the given order.

        Note
        -----
        This method generates all possible permutations of the tags by recursively descending through the provided lists of tags.
        """

        if not parts:
            return ['']

        # Remember: EPSILON in a slot mean that slot can be omitted for a construction.
        # Example: parts = [["dis", "re"], ["member"], ["ment", "ing"], ["s", EPSILON]]
        # First pass: head = ["dis", "re"], tail = [["member"], ["ment", "ing"], ["s", EPSILON]]
        # Second pass: head = ["member"], tail = [["ment", "ing"], ["s", EPSILON]]
        # Third pass: head = ["ment", "ing"], tail = [["s", EPSILON]]
        # Fourth pass: head = ["s", EPSILON], tail = [] <- base case reached
        # Fourth pass return: ['']
        # Third pass return: ["ments", "ment", "ings", "ing"] <- note the epsilon omissions here
        # Second pass return: ["memberments", "memberment", "memberings", "membering"]
        # First pass return: ["dismemberments", "dismemberment", "dismemberings", "dismembering",
        #                       "rememberments", "rememberment", "rememberings", "remembering"]
        # Having incorrect combinations like this is okay, like "rememberments", as they'll just return no results
        # from the final FST when you try to query it (i.e. ends up in an unaccepting state).
        head = parts[0]
        tail = Fst._permute_tags(parts[1:])
        result = []

        for prefix in head:
            for suffix in tail:
                if prefix == EPSILON:
                    result.append(suffix)
                else:
                    result.append(prefix + suffix)

        return result

    
    def _traverse_down(self, queries: list[str]) -> Generator[FstOutput]:
        """
        Handles all the queries down the FST and returns all the resulting outputs that were found.

        Parameters
        ----------
        queries : list[str]
            The list of queries to process down the FST.

        Returns
        -------
        Generator[FstOutput]
            A generator of all the resulting outputs that were found with their corresponding weights.
        """

        original_recursion_limit = 0
        
        # If the recursion limit has been set, the save the original value, and set it to the specified one.
        if self.recursion_limit is not None:
            original_recursion_limit = sys.getrecursionlimit()
            sys.setrecursionlimit(self.recursion_limit)

        for query in queries:
            results = self.__traverse_down(
                current_node=self._start_state,
                input_tokens=tokenize_input_string(query, self._multichar_symbols)
            )

            for result in results:
                yield replace(result, output_string=result.output_string.replace(EPSILON, ''))

        # Reset recursion limit before exiting the function.
        if self.recursion_limit is not None:
            sys.setrecursionlimit(original_recursion_limit)


    def __traverse_down(self, current_node: _FstNode, input_tokens: list[str]) -> Generator[FstOutput]: # pylint: disable=too-many-branches
        """
        Traverses down the FST beginning at an initial provided node.

        Parameters
        ----------
        current_node : _FstNode
            The current node in the recursion. Provide the FST's start state if calling this for the first time.

        input_tokens : list[str]
            The list of input tokens to process through the FST.

        Returns
        -------
        Generator[FstOutput]
            A generator of matches found during the traversal with their corresponding weights.

        Note
        -----
        This function walks through the FST, recursively finding matches that it builds up through the traversal.
        """

        current_token = input_tokens[0] if input_tokens else None

        for edge in current_node.out_transitions:

            # If the current transition is an epsilon transition, then consume no input and recurse.
            if edge.input_symbol == EPSILON:

                # Case: there are no more input tokens, but you have an epsilon transition to follow.
                # In this case, you follow the epsilon, and see if you're in an accepting state. If so,
                # then add the output of this transition to the matches and continue to the recursive step,
                # since there could be further epsilon transitions to follow.
                if not current_token and edge.target_node.is_accepting_state and edge.output_symbol:
                    path_weight = None

                    if self._semiring:
                        path_weight = self._semiring.get_path_weight(edge.weight, edge.target_node.final_state_weight)

                    yield FstOutput(edge.output_symbol, path_weight)

                recursive_results = self.__traverse_down(edge.target_node, input_tokens)

                try:
                    for result in recursive_results:
                        output_string = edge.output_symbol + result.output_string
                        path_weight = None

                        if self._semiring:
                            path_weight = self._semiring.get_path_weight(edge.weight, result.path_weight)
                        
                        yield FstOutput(output_string, path_weight)

                except RecursionError:
                    pass

            # If we have found an explicit match of the current token with the edge's input token, then we are going
            # to want to create the new input symbols for the next level of recursion by chopping off the current token,
            # and getting the resulting output of that recursion. Then, we'll want to loop over that result, and, since
            # we consumed an input token over this current transition, we add ``edge.output_symbol + result`` to the matches.
            elif current_token == edge.input_symbol:
                
                new_input_tokens = input_tokens[1:]

                if not new_input_tokens and edge.target_node.is_accepting_state:
                    path_weight = None

                    if self._semiring:
                        path_weight = self._semiring.get_path_weight(edge.weight, edge.target_node.final_state_weight)

                    yield FstOutput(edge.output_symbol, path_weight)

                recursive_results = self.__traverse_down(edge.target_node, new_input_tokens)

                try:
                    for result in recursive_results:
                        output_string = edge.output_symbol + result.output_string
                        path_weight = None

                        if self._semiring:
                            path_weight = self._semiring.get_path_weight(edge.weight, result.path_weight)
                        
                        yield FstOutput(output_string, path_weight)

                except RecursionError:
                    pass

    #endregion


    #region Up/Analysis Methods

    def up_analyses(self, wordforms: list[str]) -> dict[str, Generator[FstOutput]]:
        """
        Calls ``up_analysis`` for each wordform and returns a dictionary keyed on each wordform.

        The values in the dictionary are generators of tagged forms returned by the FST.

        Parameters
        ----------
        wordforms : list[str]
            The list of wordforms to process.

        Returns
        -------
        dict[str, Generator[FstOutput]]
            A dictionary where each key is a wordform and the value is a generator of tagged forms generated by the FST, along with their weights.

        See Also
        --------
        up_analysis : For more information on how each wordform is processed.
        """

        tagged_forms = {}

        for wordform in wordforms:
            tagged_forms[wordform] = self.up_analysis(wordform)

        return tagged_forms
    

    def up_analysis(self, wordform: str) -> Generator[FstOutput]:
        """
        Queries the FST up, or in the direction of analysis.

        Parameters
        ----------
        wordform : str
            The wordform to process.

        Returns
        -------
        Generator[FstOutput]
            A generator of tagged forms that could lead to the provided wordform, along with their weights.

        Note
        -----
        This function queries the FST in the direction of analysis by starting at the accepting states. Instead of looking at 
        the input symbols for a node and the out transitions, it looks at the output symbols of the node and the in transitions. 
        In this way, the FST becomes reversed. For example, ``walking -> wal+GER``. There can be several tagged forms that lead to 
        a single word. For instance, the word ``walk`` can have forms like ``wal+VERB+1Sg+Pres``, ``wal+VERB+2Sg+Pres``, etc., that lead 
        to its generation. All these tagged forms are aggregated and returned.

        This method starts at the accepting states and looks at the output symbols of the node and the in transitions,
        effectively reversing the FST. While down/generation generates forms from a lemma plus some tags, the up/analysis 
        direction takes a word form and generates the tagged forms that could lead to that particular word form.
        """

        original_recursion_limit = 0
        
        # If the recursion limit has been set, the save the original value, and set it to the specified one.
        if self.recursion_limit is not None:
            original_recursion_limit = sys.getrecursionlimit()
            sys.setrecursionlimit(self.recursion_limit)

        for accepting_state in self._accepting_states.values():
            recursive_results = self._traverse_up(accepting_state, wordform)

            # This reverses the final output as the string being returned from the recursion is backwards since we're going in the up direction.
            for result in recursive_results:
                yield replace(result, output_string=result.output_string[::-1].replace(EPSILON, ''))

        # Reset recursion limit before exiting the function.
        if self.recursion_limit is not None:
            sys.setrecursionlimit(original_recursion_limit)
        

    def _traverse_up(self, current_state: _FstNode, wordform: str) -> Generator[FstOutput]:
        """
        Handles the recursive walk through the FST.

        Parameters
        ----------
        current_state : _FstNode
            The current state node to start the traversal from.
            
        wordform : str
            The wordform to be processed during the traversal.
        
        Returns
        -------
        Generator[FstOutput]
            A generator of symbols outputted from the FST during the walk, along with their weights.

        Note
        -----
        This function recursively walks through the FST starting from the given state node.
        """
        
        current_char = wordform[-1] if wordform else None

        for edge in current_state.in_transitions:

            def yield_results(new_wordform: str, current_edge: _FstEdge) -> Generator[FstOutput]:
                
                recursive_results: Generator[FstOutput] = self._traverse_up(current_edge.source_node, new_wordform)
            
                try:
                    for result in recursive_results:
                        output_string = current_edge.input_symbol[::-1] + result.output_string
                        path_weight = None

                        if self._semiring:
                            path_weight = self._semiring.get_path_weight(current_edge.weight, result.path_weight)

                        yield FstOutput(output_string, path_weight)

                except RecursionError:
                    pass

            # If the current character matches the output symbol and takes you to the starting state, i.e. the end of the walk.
            if current_char == edge.output_symbol and edge.source_node.id == Fst._STARTING_STATE:

                new_wordform = wordform[:-1]

                # Since we're at the starting state, we check if there are any input characters left. If not, then we are at our base case.
                if not new_wordform:
                    # This reverses the symbol since we're going up instead of down.
                    yield FstOutput(edge.input_symbol[::-1], edge.weight)

                yield from yield_results(new_wordform, edge)

            # Otherwise, output symbol is epsilon, then consume no characters.
            elif edge.output_symbol == EPSILON:
                yield from yield_results(wordform, edge)

            # Otherwise, current character matches output character, so chop off the current character..
            elif current_char == edge.output_symbol:
                yield from yield_results(wordform[:-1], edge)

    #endregion
