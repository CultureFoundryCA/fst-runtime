import pytest
from fst_runtime.directed_graph import DirectedGraph, DirectedNode, DirectedEdge

@pytest.fixture
def att_file_path_unweighted(tmp_path):
    att_file = tmp_path / "test1.att"

    # 0 1 a b
    # 1 2 b c
    # 2
    att_file.write_text("0\t1\ta\tb\n1\t2\tb\tc\n2\n")
    return att_file

@pytest.fixture
def att_file_path_weighted(tmp_path):
    att_file = tmp_path / "test2.att"
    
    # 0 1 a b 0.5
    # 1 2 b c 1.0
    # 2
    att_file.write_text("0\t1\ta\tb\t0.5\n1\t2\tb\tc\t1.0\n2\n")
    return att_file

def test_directed_graph_initialization_unweighted(att_file_path_unweighted):
    graph = DirectedGraph(att_file_path_unweighted)
    
    assert graph.start_state.id == 0
    assert len(graph.accepting_states) == 1
    assert graph.accepting_states[0] == 2
    
    node0 = graph.start_state
    node1 = node0.transitions_out[0].target_node
    node2 = node1.transitions_out[0].target_node
    
    assert node0.id == 0
    assert node1.id == 1
    assert node2.id == 2
    
    assert len(node0.transitions_out) == 1
    assert len(node1.transitions_out) == 1
    assert len(node2.transitions_out) == 0
    
    edge0 = node0.transitions_out[0]
    edge1 = node1.transitions_out[0]
    
    assert edge0.source_node == node0
    assert edge0.target_node == node1
    assert edge0.input_symbol == 'a'
    assert edge0.output_symbol == 'b'
    assert edge0.penalty_weight == DirectedEdge.NO_WEIGHT
    
    assert edge1.source_node == node1
    assert edge1.target_node == node2
    assert edge1.input_symbol == 'b'
    assert edge1.output_symbol == 'c'
    assert edge1.penalty_weight == DirectedEdge.NO_WEIGHT

def test_directed_graph_initialization_weighted(att_file_path_weighted):
    graph = DirectedGraph(att_file_path_weighted)
    
    assert graph.start_state.id == 0
    assert len(graph.accepting_states) == 1
    assert graph.accepting_states[0] == 2
    
    node0 = graph.start_state
    node1 = node0.transitions_out[0].target_node
    node2 = node1.transitions_out[0].target_node
    
    assert node0.id == 0
    assert node1.id == 1
    assert node2.id == 2
    
    assert len(node0.transitions_out) == 1
    assert len(node1.transitions_out) == 1
    assert len(node2.transitions_out) == 0
    
    edge0 = node0.transitions_out[0]
    edge1 = node1.transitions_out[0]
    
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
