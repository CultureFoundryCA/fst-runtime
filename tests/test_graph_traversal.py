import os
import pytest
from fst_runtime.directed_graph import DirectedGraph, EPSILON

# Define the path to the data folder
ATT_DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')

# Generate a list of file paths in the data folder
att_data_files = [os.path.join(ATT_DATA_FOLDER, filename)
              for filename
              in os.listdir(ATT_DATA_FOLDER)
              if filename.endswith('.att')
                and os.path.isfile(os.path.join(ATT_DATA_FOLDER, filename))]

# Define the parameterized test
# @pytest.mark.parametrize("att_data_file", att_data_files)
def test_down_traversal(att_data_file = '/home/parkhill/Documents/Coding/fst-runtime/tests/data/fst4.att'):
    graph = DirectedGraph(att_data_file)

    prefix_options = [[EPSILON]]
    stem = 'wal'
    suffix_options = [['+VERB'], ['+INF', '+GER', '+PAST', '+PRES']]

    results = graph.down_generation(prefix_options, stem, suffix_options)

    results = set(results)
    expected_results = {'walk', 'walks', 'walked', 'walking'}

    assert results == expected_results
