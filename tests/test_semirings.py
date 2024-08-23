# pylint: disable=too-many-locals

'''This module executes tests on the four pre-defined, common semirings in the application.'''

import math
from fst_runtime.semiring import BooleanSemiring, LogSemiring, ProbabilitySemiring, TropicalSemiring

_SIGNIFICANT_PLACES = 8
'''
This value is used to set the number of significant digits to round decimal values to. This is used because of precision with my own
hand calculations vs the precision of the python math module, and to account for any possible small deviations manifesting from
doing floating-point arithmetic (such as getting the value 0.6000000000000001 instead of 0.6, which occurs in these tests).
'''

def test_boolean_semiring():
    '''Runs tests on the boolean semiring.'''

    semiring = BooleanSemiring()

    transition_weights_path1 = [True, True, False, True]
    transition_weights_path2 = [True, True, True]
    transition_weights_path3 = [False, False, False]

    # This operation will logical and the values in the list together.
    path1_weight = semiring.get_path_weight(transition_weights_path1)
    path2_weight = semiring.get_path_weight(transition_weights_path2)
    path3_weight = semiring.get_path_weight(transition_weights_path3)

    # ``True and True and False and True = False``.
    assert path1_weight is False

    # ``True and True and True = True``.
    assert path2_weight is True

    # ``False and False and False = False``.
    assert path3_weight is False

    path_set1 = [path1_weight, path2_weight, path3_weight]
    path_set2 = [path1_weight, path3_weight]
    path_set3_uncomputed_paths = [transition_weights_path1, transition_weights_path2, transition_weights_path3]

    path_set_weight1 = semiring.get_path_set_weight(path_set1)
    path_set_weight2 = semiring.get_path_set_weight(path_set2)
    path_set_weight3 = semiring.get_path_set_weight_for_uncomputed_path_weights(path_set3_uncomputed_paths)

    # ``False or True or False = True``.
    assert path_set_weight1 is True

    # ``False or False = False``.
    assert path_set_weight2 is False
    assert path_set_weight3 == path_set_weight1


def test_log_semiring():
    '''Runs tests on the log semiring.'''

    semiring = LogSemiring()

    transition_weights_path1 = [0.000000304, 0.2999928838, -1.9339999399, 1.0000000001]
    transition_weights_path2 = [0.00383, 0.5, 0.8]
    transition_weights_path3 = [0.1, 0.2, 0.3]

    # This operation will be standard addition, which is the multiplication operation in the log semiring.
    path1_weight = semiring.get_path_weight(transition_weights_path1)
    path2_weight = semiring.get_path_weight(transition_weights_path2)
    path3_weight = semiring.get_path_weight(transition_weights_path3)

    assert path1_weight == -0.6340067520000001
    assert path2_weight == 1.30383
    assert round(path3_weight, _SIGNIFICANT_PLACES) == 0.6

    path_set1 = [path1_weight, path2_weight, path3_weight]
    path_set2 = [path1_weight, path2_weight]
    path_set3_uncomputed_paths = [transition_weights_path1, transition_weights_path2, transition_weights_path3]

    # This operation will be ``f(x, y) = -ln(e^(-x) + e^(-y))`` which is the addition operation in the log semring.
    path_set_weight1 = semiring.get_path_set_weight(path_set1)
    path_set_weight2 = semiring.get_path_set_weight(path_set2)
    path_set_weight3 = semiring.get_path_set_weight_for_uncomputed_path_weights(path_set3_uncomputed_paths)

    # Recall that this log add is associative.
    # 1. ``-ln(e^(-(-0.6340067520000001)) + e^(-1.30383)) = -0.7685509`` <- plug this value into (2).
    # 2. ``-ln(e^(-(-0.7685509)) + e^(-0.6)) = -0.99526841``.
    log_add_expected_value = -math.log(math.exp(-path1_weight) + math.exp(-path2_weight))
    log_add_expected_value = -math.log(math.exp(-log_add_expected_value) + math.exp(-path3_weight))
    
    assert path_set_weight1 == log_add_expected_value
    assert round(path_set_weight1, _SIGNIFICANT_PLACES) == -0.99526841

    # ``-ln(e^(-(-0.6340067520000001) + e^(-1.30383)) = -0.76855089``.
    assert round(path_set_weight2, _SIGNIFICANT_PLACES) == -0.76855089
    assert path_set_weight3 == path_set_weight1

    
def test_probability_semiring():
    '''Run tests on the probability semiring.'''
    
    semiring = ProbabilitySemiring()

    transition_weights_path1 = [0.1, 0.5, 0.2, 0.2]
    transition_weights_path2 = [0.383, 0.5, 0.8]
    transition_weights_path3 = [0.1, 0.2, 0.3]
    transition_negative_weight = [0.1, 0.2, -0.4]

    # This operation will be standard multiplication.
    path1_weight = semiring.get_path_weight(transition_weights_path1)
    path2_weight = semiring.get_path_weight(transition_weights_path2)
    path3_weight = semiring.get_path_weight(transition_weights_path3)
    positive_values_in_semiring_domain = semiring.check_membership(*transition_weights_path1)
    negative_value_in_semiring_domain = semiring.check_membership(*transition_negative_weight)

    assert path1_weight == math.prod(transition_weights_path1)
    assert path2_weight == math.prod(transition_weights_path2)
    assert path3_weight == math.prod(transition_weights_path3)
    assert positive_values_in_semiring_domain is True
    assert negative_value_in_semiring_domain is False

    path_set1 = [path1_weight, path2_weight, path3_weight]
    path_set2 = [path1_weight, path2_weight]
    path_set3_uncomputed_paths = [transition_weights_path1, transition_weights_path2, transition_weights_path3]

    # This operation will be standard addition.
    path_set_weight1 = semiring.get_path_set_weight(path_set1)
    path_set_weight2 = semiring.get_path_set_weight(path_set2)
    path_set_weight3 = semiring.get_path_set_weight_for_uncomputed_path_weights(path_set3_uncomputed_paths)

    assert path_set_weight1 == sum(path_set1)
    assert path_set_weight2 == sum(path_set2)
    assert path_set_weight3 == path_set_weight1


def test_tropical_semiring():
    '''Run tests on the tropical semiring.'''
    
    semiring = TropicalSemiring()

    transition_weights_path1 = [0.1, 0.5, 0.2, 0.2]
    transition_weights_path2 = [0.4, 0.5, 0.8]
    transition_weights_path3 = [0.1, 0.2, -0.3]

    # This operation will be standard addition, which is the multiplication function of the tropical semiring.
    path1_weight = semiring.get_path_weight(transition_weights_path1)
    path2_weight = semiring.get_path_weight(transition_weights_path2)
    path3_weight = semiring.get_path_weight(transition_weights_path3)

    assert path1_weight == sum(transition_weights_path1)
    assert path2_weight == sum(transition_weights_path2)
    assert round(path3_weight, _SIGNIFICANT_PLACES) == round(sum(transition_weights_path3), _SIGNIFICANT_PLACES)

    path_set1 = [path1_weight, path2_weight, path3_weight]
    path_set2 = [path1_weight, path2_weight]
    path_set3_uncomputed_paths = [transition_weights_path1, transition_weights_path2, transition_weights_path3]

    # This operation will be ``min{x, y}``, which is the addition function of the tropical semiring.
    path_set_weight1 = semiring.get_path_set_weight(path_set1)
    path_set_weight2 = semiring.get_path_set_weight(path_set2)
    path_set_weight3 = semiring.get_path_set_weight_for_uncomputed_path_weights(path_set3_uncomputed_paths)

    assert round(path_set_weight1, _SIGNIFICANT_PLACES) == 0.0
    assert path_set_weight2 == 1.0
    assert path_set_weight3 == path_set_weight1
