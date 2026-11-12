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
from dataclasses import asdict, dataclass, field
from itertools import product as cartesian_product
import json
import os
import sys
from typing import Any, Generator, Iterable

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
    output_string : str
        The string that the FST outputted for the given input; e.g. "walking" for the input "wal+VERB+GER".

    path_weight : Any
        The weight of the path that was walked to get this output. This value is computed via the semiring provided to the FST.

    input_string : str, optional
        The input string that resulted in the given output.

    get_serialization_dictionary : method
        This method returns a dictionary represenatation of the fields of the dataclass to be used in object serialization.

    json_serialize_outputs : static method
        This method returns the json serialization of a collection of ``FstOutput``s in order to be returned from an API.

    """

    output_string: str
    """The string that the FST outputted for the given input; e.g. "walking" for the input "wal+VERB+GER"."""

    path_weight: Any
    """The weight of the path that was walked to get this output. This value is computed via the semiring provided to the FST."""

    input_string: str = 'uninitialized'
    """This is the string that was inputted into the FST that resulted in this output."""

    def get_serialization_dictionary(self) -> dict[str, Any]:
        '''
        Gets the dictionary representation of this object for use in i.e. json serialization.

        Returns
        -------
        dict[str, Any]
            The dictionary representation of this object. This is a copy, so changing it does not change this object.
        '''
        return asdict(self)

    def get_serialialization_dictionary(self) -> dict[str, Any]:
        '''
        Misspelled alias of ``get_serialization_dictionary``, kept so that existing callers keep working.

        Returns
        -------
        dict[str, Any]
            The dictionary representation of this object.
        '''
        return self.get_serialization_dictionary()

    @staticmethod
    def json_serialize_outputs(outputs: Iterable[FstOutput]) -> str | None:
        """
        This function returns creates the json-serialized string-representation of a collection of FstOutput objects.

        Parameters
        ----------
        outputs : Iterable[FstOutput]
            The outputs collection to be serialized.

        Returns
        -------
        str
            The json-serialized string-representation of the collection of outputs. Returns ``None`` when there is nothing to serialize.

        """
        values = [output.get_serialization_dictionary() for output in outputs]

        if not values:
            return None

        return json.dumps(values)


@dataclass
class _AttTransition:
    """
    Represents one transition line as read in from the AT&T file format (``.att``).

    Attributes
    ----------
    source_state_id : int
        The ID of the state in the FST that the transition leaves from.

    target_state_id : int
        The ID of the state in the FST that is being transitioned to.

    input_symbol : str
        The symbol that is consumed over the transition.

    output_symbol : str
        The symbol that is outputted over the transition.

    weight : Any, optional
        The weight associated with the transition, should it have one.
    """

    source_state_id: int
    """The ID of the state in the FST that the transition leaves from."""

    target_state_id: int
    """The ID of the state in the FST that is being transitioned to."""

    input_symbol: str
    """The symbol that is consumed over the transition."""

    output_symbol: str
    """The symbol that is outputted over the transition."""

    weight: Any = field(default=None)
    """The weight associated with the transition, should it have one."""


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

    weight : Any, optional
        The weight of traversing this edge. Its values are in the domain of the semiring provided to the FST.
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
        Limits how many transitions in a row can be followed without consuming any input, to prevent epsilon cycles from running amok.

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

    _ATT_ACCEPTING_STATE_ITEM_COUNTS = (1, 2)
    """A line in the ``.att`` file that defines an accepting state holds the state, and optionally the weight of accepting there."""

    _ATT_TRANSITION_ITEM_COUNTS = (4, 5)
    """
    A line in the ``.att`` file that defines a transition holds the source state, the target state, the input symbol,
    the output symbol, and optionally the weight of the transition.
    """

    def __init__(self, att_file_path: str | os.PathLike[str], *, semiring: Semiring | None = None, recursion_limit: int | None = None) -> None:
        """
        Initializes the FST via the provided ``.att`` file.

        Parameters
        ----------
        att_file_path : str | os.PathLike[str]
            The path to the ``.att`` file containing the FST description.

        semiring: Semiring | None, optional
            The semiring over which the weights in the FST are defined.

        recursion_limit : int | None, optional
            The most transitions in a row that a query may follow without consuming any input. Default is ``None``, which uses
            the interpreter's recursion limit (1000 unless it has been changed).

        Raises
        ------
        ValueError
            Raised when the provided path is empty or does not point to a ``.att`` file.

        AttFormatError
            Raised when the contents of the ``.att`` file are not valid.
        """

        if not att_file_path:
            raise ValueError("Failed to provide valid path to input file. Example: ``/path/to/fst.att``.")

        if not str(att_file_path).endswith('.att'):
            raise ValueError("Provided file path does not point to a ``.att`` file. Example: ``/path/to/fst.att``.")

        self._start_state: _FstNode = _FstNode(-1, False)
        """This is the entry point into the FST. This is functionally like the root of a tree (even though this is a graph, not a tree)."""

        self._accepting_states: dict[int, _FstNode] = {}
        """This dictionary holds all the accepting states of the FST."""

        self._multichar_symbols: set[str] = set()
        """This set represents all the multi-character symbols that have been defined in the FST."""

        self._semiring: Semiring | None = semiring
        """This holds the semiring used to perform weight arithmetic on paths in the FST."""

        self._recursion_limit: int | None = recursion_limit
        """This limits how many transitions in a row can be followed without consuming input, so that epsilon cycles don't run amok."""

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
        int | None
            The most transitions in a row that a query may follow without consuming any input. ``None`` means that the
            interpreter's recursion limit is used as that number.
        """
        return self._recursion_limit

    @recursion_limit.setter
    def recursion_limit(self, new_recursion_limit: int | None) -> None:
        """
        Public setter for the recursion_limit variable.

        Parameters
        ----------
        new_recursion_limit : int | None
            The new value to set the recursion limit to.
        """
        self._recursion_limit = new_recursion_limit

    #endregion


    #region Graph Creation

    def _parse_weight(self, weight_items: list[str]) -> Any:
        """
        Gets the weight for a line of the ``.att`` file.

        Parameters
        ----------
        weight_items : list[str]
            The items of the line that come after the required ones. This is empty when the line has no weight,
            and otherwise holds the string representation of the weight.

        Returns
        -------
        Any
            ``None`` if the FST has no semiring. Otherwise, the weight in the domain of the semiring, where a line
            without a weight gets the multiplicative identity.
        """

        if self._semiring is None:
            return None

        if not weight_items:
            return self._semiring.multiplicative_identity

        return self._semiring.convert_string_into_domain(weight_items[0])


    def _read_att_file(self, att_file_path: str | os.PathLike[str]) -> tuple[list[_AttTransition], dict[int, Any]]:
        """
        Reads in all the transitions and accepting states from the ``.att`` file.

        Parameters
        ----------
        att_file_path : str | os.PathLike[str]
            The path to the ``.att`` file containing the FST description.

        Returns
        -------
        tuple[list[_AttTransition], dict[int, Any]]
            A tuple containing:
            - ``transitions`` : list[_AttTransition]
                Every transition in the ``.att`` file, in the order they appear in the file.
            - ``accepting_states`` : dict[int, Any]
                A dictionary whose keys are accepting state IDs and whose values are the weight of the accepting state.

        Raises
        ------
        AttFormatError
            Raised when a line has the wrong number of items, or when a state or weight can't be parsed.
        """

        transitions: list[_AttTransition] = []
        accepting_states: dict[int, Any] = {}

        with open(att_file_path, encoding='utf-8') as att_file:

            for line_number, line in enumerate(att_file, start=1):

                if not line.strip():
                    continue

                # Lines in the AT&T format are tab separated.
                # No .strip() in case whitespace character is an output. This is very important.
                att_line_items = line.rstrip('\n').split('\t')
                num_defined_items = len(att_line_items)

                try:
                    if num_defined_items in Fst._ATT_ACCEPTING_STATE_ITEM_COUNTS:
                        accepting_states[int(att_line_items[0])] = self._parse_weight(att_line_items[1:])

                    elif num_defined_items in Fst._ATT_TRANSITION_ITEM_COUNTS:
                        source_state, target_state, input_symbol, output_symbol = att_line_items[:4]

                        transitions.append(_AttTransition(
                            int(source_state),
                            int(target_state),
                            input_symbol,
                            output_symbol,
                            self._parse_weight(att_line_items[4:])
                        ))

                    else:
                        raise ValueError(f"expected 1, 2, 4, or 5 tab-separated items but found {num_defined_items}")

                except ValueError as value_error:
                    raise AttFormatError(
                        f"Invalid line {line_number} in {os.path.basename(att_file_path)}: {line!r} ({value_error})."
                    ) from value_error

        return transitions, accepting_states


    def _create_graph(self, att_file_path: str | os.PathLike[str]) -> None:
        """
        Create the graph that represents the FST from reading in the provided ``.att`` file.

        This method initializes the FST by reading transitions and accepting states from the
        specified file, creating all nodes and transitions, and setting the start state.

        Parameters
        ----------
        att_file_path : str | os.PathLike[str]
            The path to the ``.att`` file containing the FST description.

        Raises
        ------
        AttFormatError
            This error is raised if the FST is ill-defined according to the AT&T format.
        """

        transitions, accepting_states = self._read_att_file(att_file_path)

        non_accepting_weight = None if self._semiring is None else self._semiring.multiplicative_identity
        nodes: dict[int, _FstNode] = {}

        def get_or_create_node(state_id: int) -> _FstNode:
            if state_id not in nodes:
                is_accepting_state = state_id in accepting_states
                weight = accepting_states[state_id] if is_accepting_state else non_accepting_weight
                nodes[state_id] = _FstNode(state_id, is_accepting_state, weight)

            return nodes[state_id]

        for state_id in accepting_states:
            self._accepting_states[state_id] = get_or_create_node(state_id)

        # Every transition becomes an edge that is held by both the node it leaves from and the node it leads to.
        for transition in transitions:
            source_node = get_or_create_node(transition.source_state_id)
            target_node = get_or_create_node(transition.target_state_id)

            edge = _FstEdge(source_node, target_node, transition.input_symbol, transition.output_symbol, transition.weight)

            source_node.out_transitions.append(edge)
            target_node.in_transitions.append(edge)

            for symbol in (transition.input_symbol, transition.output_symbol):
                if len(symbol) > 1:
                    self._multichar_symbols.add(symbol)

        # Set the start state.
        try:
            self._start_state = nodes[Fst._STARTING_STATE]
        except KeyError as key_error:
            raise AttFormatError("There must be a start state specified that has state number ``0` in the input ``.att`` file.") from key_error

    #endregion


    #region Shared Traversal Helpers

    def _multiply_weights(self, first_weight: Any, second_weight: Any) -> Any:
        """
        Multiplies two weights under the semiring of the FST.

        Parameters
        ----------
        first_weight : Any
            The weight of the earlier part of the path.

        second_weight : Any
            The weight of the later part of the path.

        Returns
        -------
        Any
            The product of the weights, or ``None`` if the FST has no semiring.
        """

        if self._semiring is None:
            return None

        return self._semiring.multiply(first_weight, second_weight)


    def _get_epsilon_run_limit(self) -> int:
        """
        Gets the most transitions in a row that a query may follow without consuming any input.

        Returns
        -------
        int
            The recursion limit of this FST if one was set, and otherwise the interpreter's recursion limit.
        """

        if self._recursion_limit is None:
            return sys.getrecursionlimit()

        return self._recursion_limit


    @staticmethod
    def _join_symbols(symbols: Iterable[str]) -> str:
        """
        Joins the symbols collected over a path into a single string, leaving out any epsilons.

        Parameters
        ----------
        symbols : Iterable[str]
            The symbols in the order they should appear in the string.

        Returns
        -------
        str
            The joined string.
        """
        return ''.join(symbol for symbol in symbols if symbol != EPSILON)

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
        dict[str, Generator[FstOutput]]
            A dictionary where each key is a lemma and the value is a generator of wordforms generated by the FST.

        See Also
        --------
        down_generation : For more information on how each lemma is processed.
        """

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
        The tags are given without the ``+`` that separates them, as that is added when the query is built.
        For example, the lemma "wal" in English (for the lemma "walk"), with suffix tags ``[["VERB"], ["INF", "PAST", "GER", "PRES"]]``.
        Then, these would be fully permuted to "wal+VERB+INF", "wal+VERB+PAST", "wal+VERB+GER", and "wal+VERB+PRES"; likewise with any prefixes.
        All of these constructions are then walked over the FST to see if we end at an accepting state. If so, the generated forms
        (i.e., walk, walked, walking, walks) are returned.

        If the FST has an epsilon cycle, the same form can be returned many times, once for each number of trips around the cycle
        up to the ``recursion_limit``.
        """

        prefixes = [[EPSILON]] if prefixes is None else prefixes
        suffixes = [[EPSILON]] if suffixes is None else suffixes

        for query in Fst._permute_tags(prefixes + [[lemma]] + suffixes):
            logger.debug('Query created: %s', query)
            yield from self._traverse_down(query)


    @staticmethod
    def _permute_tags(parts: list[list[str]], separator: str = '+') -> Generator[str]:
        """
        Creates all permutations of the given tags in the given order.

        Parameters
        ----------
        parts : list[list[str]]
            A list of lists containing tag sequences to permute.

        separator : str, optional
            The string placed between each of the parts. Default is ``+``.

        Returns
        -------
        Generator[str]
            A generator of all permutations of the given tags in the given order.

        Note
        -----
        One tag is taken from each of the lists, in order, and they are joined with the separator. Epsilons are left out.
        """

        for product in cartesian_product(*parts):
            yield separator.join(tag for tag in product if tag != EPSILON)


    def _traverse_down(self, query: str) -> Generator[FstOutput]:
        """
        Walks a single query down the FST and returns all the resulting outputs that were found.

        Parameters
        ----------
        query : str
            The query to process down the FST.

        Returns
        -------
        Generator[FstOutput]
            A generator of all the resulting outputs that were found with their corresponding weights.

        Note
        -----
        This is a depth-first walk that keeps its own stack rather than using recursion, so the length of the query is not
        limited by the interpreter's recursion limit. Each item on the stack is a partial path: the node it has reached, how many
        input tokens it has consumed, the output symbols and weight so far, and how many epsilon transitions it has just followed in a row.
        """

        input_tokens = tokenize_input_string(query, self._multichar_symbols)
        num_input_tokens = len(input_tokens)
        epsilon_run_limit = self._get_epsilon_run_limit()

        # The weight of a path that hasn't crossed any transitions yet is the multiplicative identity.
        stack: list[tuple[_FstNode, int, tuple[str, ...], Any, int]] = [
            (self._start_state, 0, (), None if self._semiring is None else self._semiring.multiplicative_identity, 0)
        ]

        while stack:
            current_node, num_consumed_tokens, output_symbols, path_weight, epsilon_run = stack.pop()

            # All the input has been consumed and we're at an accepting state, so this path is a match.
            if num_consumed_tokens == num_input_tokens and current_node.is_accepting_state:
                yield FstOutput(
                    Fst._join_symbols(output_symbols),
                    self._multiply_weights(path_weight, current_node.final_state_weight),
                    query
                )

            current_token = input_tokens[num_consumed_tokens] if num_consumed_tokens < num_input_tokens else None

            # Reversed so that the edges come off the stack in the order they're defined in.
            for edge in reversed(current_node.out_transitions):

                # An epsilon transition consumes no input.
                if edge.input_symbol == EPSILON:
                    if epsilon_run >= epsilon_run_limit:
                        continue

                    next_num_consumed_tokens = num_consumed_tokens
                    next_epsilon_run = epsilon_run + 1

                elif edge.input_symbol == current_token:
                    next_num_consumed_tokens = num_consumed_tokens + 1
                    next_epsilon_run = 0

                else:
                    continue

                stack.append((
                    edge.target_node,
                    next_num_consumed_tokens,
                    output_symbols + (edge.output_symbol,),
                    self._multiply_weights(path_weight, edge.weight),
                    next_epsilon_run
                ))

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

        While down/generation generates forms from a lemma plus some tags, the up/analysis direction takes a word form and
        generates the tagged forms that could lead to that particular word form.
        """

        for accepting_state in self._accepting_states.values():
            yield from self._traverse_up(accepting_state, wordform)


    def _traverse_up(self, accepting_state: _FstNode, wordform: str) -> Generator[FstOutput]:
        """
        Walks a wordform backwards through the FST from an accepting state to the start state.

        Parameters
        ----------
        accepting_state : _FstNode
            The accepting state to start the walk from.

        wordform : str
            The wordform to be processed during the walk.

        Returns
        -------
        Generator[FstOutput]
            A generator of the tagged forms that lead from the start state to the accepting state while outputting the wordform,
            along with their weights.

        Note
        -----
        This is a depth-first walk that keeps its own stack rather than using recursion. The wordform is consumed from its end,
        so each item on the stack is a partial path: the node it has reached, how much of the start of the wordform is still left
        to consume, the input symbols and weight so far, and how many epsilon transitions it has just followed in a row.
        """

        epsilon_run_limit = self._get_epsilon_run_limit()

        stack: list[tuple[_FstNode, int, tuple[str, ...], Any, int]] = [
            (accepting_state, len(wordform), (), accepting_state.final_state_weight, 0)
        ]

        while stack:
            current_node, remaining_length, input_symbols, path_weight, epsilon_run = stack.pop()

            # The whole wordform has been consumed and we're back at the start state, so this path is a match.
            if remaining_length == 0 and current_node is self._start_state:
                yield FstOutput(Fst._join_symbols(input_symbols), path_weight, wordform)

            # Reversed so that the edges come off the stack in the order they're defined in.
            for edge in reversed(current_node.in_transitions):

                # An epsilon output consumes none of the wordform.
                if edge.output_symbol == EPSILON or not edge.output_symbol:
                    if epsilon_run >= epsilon_run_limit:
                        continue

                    next_remaining_length = remaining_length
                    next_epsilon_run = epsilon_run + 1

                # The output symbol can be more than one character long, so compare it to the end of what's left of the wordform.
                elif wordform.endswith(edge.output_symbol, 0, remaining_length):
                    next_remaining_length = remaining_length - len(edge.output_symbol)
                    next_epsilon_run = 0

                else:
                    continue

                # We're walking backwards, so this edge comes before everything that has been collected so far.
                stack.append((
                    edge.source_node,
                    next_remaining_length,
                    (edge.input_symbol,) + input_symbols,
                    self._multiply_weights(edge.weight, path_weight),
                    next_epsilon_run
                ))

    #endregion
