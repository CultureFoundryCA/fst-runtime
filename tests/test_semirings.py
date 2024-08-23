from fst_runtime.semiring import *
import math

SIGNIFICANT_PLACES = 8
'''
This value is used to set the number of significant digits to round decimal values to. This is used because of precision with my own
hand calculations vs the precision of the python math module, and to account for any possible small deviations manifesting from
doing floating-point arithmetic (such as getting the value 0.6000000000000001 instead of 0.6, which occurs in these tests).
'''

def test_boolean_semiring():

    semiring = BooleanSemiring()

    transition_weights_of_path1 = [True, True, False, True]
    transition_weights_of_path2 = [True, True, True]
    transition_weights_of_path3 = [False, False, False]

    # This operation will logical and the values in the list together.
    path_weight1 = semiring.get_path_weight(transition_weights_of_path1)
    path_weight2 = semiring.get_path_weight(transition_weights_of_path2)
    path_weight3 = semiring.get_path_weight(transition_weights_of_path3)

    # ``True and True and False and True = False``.
    assert path_weight1 == False

    # ``True and True and True = True``.
    assert path_weight2 == True

    # ``False and False and False = False``.
    assert path_weight3 == False

    path_set1 = [path_weight1, path_weight2, path_weight3]
    path_set2 = [path_weight1, path_weight3]
    path_set3_uncomputed_paths = [transition_weights_of_path1, transition_weights_of_path2, transition_weights_of_path3]

    path_set_weight1 = semiring.get_path_set_weight(path_set1)
    path_set_weight2 = semiring.get_path_set_weight(path_set2)
    path_set_weight3 = semiring.get_path_set_weight_for_uncomputed_path_weights(path_set3_uncomputed_paths)

    # ``False or True or False = True``.
    assert path_set_weight1 == True

    # ``False or False = False``.
    assert path_set_weight2 == False
    assert path_set_weight3 == path_set_weight1


def test_log_semiring():

    semiring = LogSemiring()

    transition_weights_of_path1 = [0.000000304, 0.2999928838, -1.9339999399, 1.0000000001]
    transition_weights_of_path2 = [0.00383, 0.5, 0.8]
    transition_weights_of_path3 = [0.1, 0.2, 0.3]

    # This operation will be standard addition, which is the multiplication operation in the log semiring.
    path_weight1 = semiring.get_path_weight(transition_weights_of_path1)
    path_weight2 = semiring.get_path_weight(transition_weights_of_path2)
    path_weight3 = semiring.get_path_weight(transition_weights_of_path3)

    assert path_weight1 == -0.6340067520000001
    assert path_weight2 == 1.30383
    assert round(path_weight3, SIGNIFICANT_PLACES) == 0.6

    path_set1 = [path_weight1, path_weight2, path_weight3]
    path_set2 = [path_weight1, path_weight2]
    path_set3_uncomputed_paths = [transition_weights_of_path1, transition_weights_of_path2, transition_weights_of_path3]

    # This operation will be ``f(x, y) = -ln(e^(-x) + e^(-y))`` which is the addition operation in the log semring.
    path_set_weight1 = semiring.get_path_set_weight(path_set1)
    path_set_weight2 = semiring.get_path_set_weight(path_set2)
    path_set_weight3 = semiring.get_path_set_weight_for_uncomputed_path_weights(path_set3_uncomputed_paths)

    # Recall that this log add is associative.
    # 1. ``-ln(e^(-(-0.6340067520000001)) + e^(-1.30383)) = -0.7685509`` <- plug this value into (2).
    # 2. ``-ln(e^(-(-0.7685509)) + e^(-0.6)) = -0.99526841``.
    log_add_expected_value = -math.log(math.exp(-path_weight1) + math.exp(-path_weight2))
    log_add_expected_value = -math.log(math.exp(-log_add_expected_value) + math.exp(-path_weight3))
    
    assert path_set_weight1 == log_add_expected_value

    # ``-ln(e^(-(-0.6340067520000001) + e^(-1.30383)) = -0.76855089``.
    assert round(path_set_weight2, SIGNIFICANT_PLACES) == -0.76855089
    assert path_set_weight3 == path_set_weight1

    
def test_probability_semiring():
    
    semiring = ProbabilitySemiring()

    transition_weights_of_path1 = [0.1, 0.5, 0.2, 0.2]
    transition_weights_of_path2 = [0.383, 0.5, 0.8]
    transition_weights_of_path3 = [0.1, 0.2, 0.3]
    transition_negative_weight = [0.1, 0.2, -0.4]

    # This operation will be standard multiplication.
    path_weight1 = semiring.get_path_weight(transition_weights_of_path1)
    path_weight2 = semiring.get_path_weight(transition_weights_of_path2)
    path_weight3 = semiring.get_path_weight(transition_weights_of_path3)
    positive_values_in_semiring_domain = semiring.check_membership(*transition_weights_of_path1)
    negative_value_in_semiring_domain = semiring.check_membership(*transition_negative_weight)

    assert path_weight1 == math.prod(transition_weights_of_path1)
    assert path_weight2 == math.prod(transition_weights_of_path2)
    assert path_weight3 == math.prod(transition_weights_of_path3)
    assert positive_values_in_semiring_domain == True
    assert negative_value_in_semiring_domain == False

    path_set1 = [path_weight1, path_weight2, path_weight3]
    path_set2 = [path_weight1, path_weight2]
    path_set3_uncomputed_paths = [transition_weights_of_path1, transition_weights_of_path2, transition_weights_of_path3]

    # This operation will be standard addition.
    path_set_weight1 = semiring.get_path_set_weight(path_set1)
    path_set_weight2 = semiring.get_path_set_weight(path_set2)
    path_set_weight3 = semiring.get_path_set_weight_for_uncomputed_path_weights(path_set3_uncomputed_paths)

    assert path_set_weight1 == sum(path_set1)
    assert path_set_weight2 == sum(path_set2)
    assert path_set_weight3 == path_set_weight1


def test_tropical_semiring():
    ...
