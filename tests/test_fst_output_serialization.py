'''Tests the serialization of the FstOutput class.'''

import json
from fst_runtime.fst import Fst, FstOutput

def test_fst_output_serialization():
    '''Tests to make sure that the ``FstOutput`` object gets serialized and deserialized properly.'''

    fst = Fst('./tests/data/fst6_waabam.att')
    query_results: list[FstOutput] = list(fst.up_analysis('waabam'))

    assert len(query_results) > 0

    json_data = FstOutput.json_serialize_outputs(query_results)
    json_loaded = json.loads(str(json_data))

    assert len(json_loaded) == len(query_results)

    deserialized_object = FstOutput(json_loaded[0]['output_string'], json_loaded[0]['path_weight'], json_loaded[0]['input_string'])

    assert deserialized_object == query_results[0]

def test_empty_fst_output_serialization():
    '''Tests to make sure that if empty serialization data is passed to the serialization function, that it returns ``None``.'''

    fst = Fst('./tests/data/fst6_waabam.att')
    query_results = list(fst.up_analysis('hi my name is charlie im a unicorn'))
    json_data = FstOutput.json_serialize_outputs(query_results)

    assert json_data is None
