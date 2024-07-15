# pylint: disable=protected-access,redefined-outer-name

"""
This module tests the graph creation process.

Functions
---------
test_directed_graph_initialization_unweighted
    Tests that all initialization of the graph from the file is done correctly for an unweighted FST.
test_directed_graph_initialization_weighted
    Tests that all initialization of the graph from the file is done correctly for a weighted FST.
"""


import pytest
from fst_runtime.fst import Fst, _FstEdge


@pytest.fixture
def _att_file_path_unweighted(tmp_path):
    """
    Provides a fixture of a simple unweighted FST.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary path for the test file. Provided automatically by Pytest.

    Returns
    -------
    pathlib.Path
        Path to the temporary unweighted FST file.
    """
    att_file = tmp_path / "test1.att"

    # 0 1 a b
    # 1 2 b c
    # 2
    att_file.write_text("0\t1\ta\tb\n1\t2\tb\tc\n2\n")
    return att_file


@pytest.fixture
def _att_file_path_weighted(tmp_path):
    """
    Provides a fixture of a simple weighted FST.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary path for the test file. Provided automatically by Pytest.

    Returns
    -------
    pathlib.Path
        Path to the temporary weighted FST file.
    """
    att_file = tmp_path / "test2.att"

    # 0 1 a b 0.5
    # 1 2 b c 1.0
    # 2
    att_file.write_text("0\t1\ta\tb\t0.5\n1\t2\tb\tc\t1.0\n2\n")
    return att_file


def test_directed_graph_initialization_unweighted(_att_file_path_unweighted):
    """
    Tests that the initialization of the graph from the file is done correctly for an unweighted FST.

    Parameters
    ----------
    _att_file_path_unweighted : pathlib.Path
        Path to the temporary unweighted FST file. Provided automatically by Pytest.
    """
    graph = Fst(_att_file_path_unweighted)

    assert graph._start_state.id == 0
    assert len(graph._accepting_states) == 1

    node0 = graph._start_state
    node1 = node0.out_transitions[0].target_node
    node2 = node1.out_transitions[0].target_node

    assert node0.id == 0
    assert node1.id == 1
    assert node2.id == 2

    assert len(node0.out_transitions) == 1
    assert len(node1.out_transitions) == 1
    assert len(node2.out_transitions) == 0

    edge0 = node0.out_transitions[0]
    edge1 = node1.out_transitions[0]

    assert edge0.source_node == node0
    assert edge0.target_node == node1
    assert edge0.input_symbol == 'a'
    assert edge0.output_symbol == 'b'
    assert edge0.penalty_weight == _FstEdge.NO_WEIGHT

    assert edge1.source_node == node1
    assert edge1.target_node == node2
    assert edge1.input_symbol == 'b'
    assert edge1.output_symbol == 'c'
    assert edge1.penalty_weight == _FstEdge.NO_WEIGHT


def test_directed_graph_initialization_weighted(_att_file_path_weighted):
    """
    Tests that all initialization of the graph from the file is done correctly for a weighted FST.

    Parameters
    ----------
    _att_file_path_weighted : pathlib.Path
        Path to the temporary weighted FST file. Provided automatically by Pytest.
    """
    graph = Fst(_att_file_path_weighted)

    assert graph._start_state.id == 0
    assert len(graph._accepting_states) == 1

    node0 = graph._start_state
    node1 = node0.out_transitions[0].target_node
    node2 = node1.out_transitions[0].target_node

    assert node0.id == 0
    assert node1.id == 1
    assert node2.id == 2

    assert len(node0.out_transitions) == 1
    assert len(node1.out_transitions) == 1
    assert len(node2.out_transitions) == 0

    edge0 = node0.out_transitions[0]
    edge1 = node1.out_transitions[0]

    assert edge0.source_node == node0
    assert edge0.target_node == node1
    assert edge0.input_symbol == 'a'
    assert edge0.output_symbol == 'b'
    assert edge0.penalty_weight == '0.5'

    assert edge1.source_node == node1
    assert edge1.target_node == node2
    assert edge1.input_symbol == 'b'
    assert edge1.output_symbol == 'c'
    assert edge1.penalty_weight == '1.0'
