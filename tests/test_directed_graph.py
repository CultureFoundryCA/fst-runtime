import os
import glob
import pytest
from fst_runtime.directed_graph import DirectedGraph

def read_pairs_file(pairs_file_path: str) -> list[tuple[str, str]]:
    pairs = []
    with open(pairs_file_path, 'r') as file:
        for line in file:
            input_string, expected_output_string = line.strip().split('\t')
            pairs.append((input_string, expected_output_string))
    return pairs

@pytest.mark.parametrize("att_file_path", glob.glob(os.path.join(os.path.dirname(__file__), 'data', '*.att')))
def test_graph_traversals(att_file_path: str):

    # Construct /path/to/basename.pairs from /path/to/basename.att.
    base_filename = os.path.splitext(os.path.basename(att_file_path))[0]
    pairs_file = os.path.join(os.path.dirname(att_file_path), f'{base_filename}.pairs')

    # Make sure that the constructed path actually exists.
    if not os.path.exists(pairs_file):
        raise ValueError(f"Could not find `.pairs` file for `{os.path.basename(att_file_path)}.")

    pairs = read_pairs_file(pairs_file)
    graph = DirectedGraph(att_file_path)

    # Loop through the input and ensure the output matches the expected output.
    for input_string, expected_output_string in pairs:
        output_string = graph.traverse(input_string)
        assert output_string == expected_output_string, f"Failed for {att_file_path} with input {input_string}"
