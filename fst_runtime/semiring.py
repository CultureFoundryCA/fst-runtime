# pylint: disable=undefined-variable
# This is disabled because pylint isn't recognize the new generic syntax for python yet and can't figure out what "T" is.

'''
This module defines a semiring as well as several semirings commonly used with weighted FSTs.

Attributes
----------
Semiring[T] : class
    An abstract class that defines a semiring.

BooleanSemiring[bool] : class
    A semiring whose underlying set and operations are defined over the boolean values ``True`` and ``False``.

LogSemiring[float] : class
    A semiring whose underlying set of values are the reals with +/- infinity, with addition as logadd and
    multiplication as standard addition.

ProbabilitySemiring[float] : class
    This is the probability semiring that is defined on the non-negative reals and standard additiona and multiplication.

TropicalSemiring[float] : class
    The tropical semiring is defined on the reals with +/- infinity, where addition is the minimum and multiplication is standard addition.
'''

from abc import ABC, abstractmethod
import math
from typing import Callable, Any

class Semiring[T](ABC):
    """
    An abstract class that defines a semiring.

    Attributes
    ----------
    additive_identity : T
        The additive identity of the semiring.

    multiplicative_identity : T
        The multiplicative identity of the semiring.

    add : method
        The addition operation for the semiring.

    multiply : method
        The multiplication operation for the semiring.

    get_path_weight : method
        Computes the overall weight of a single path by multiplying the weights of all edges in the path.

    get_path_set_weight : method
        Computes the overall weight of a set of paths by adding the weights of individual paths.

    check_membership : abstract method
        This method ensures that the values provided to it are members of the underlying set of the semiring. Raises a ``ValueError`` if not.
    
    convert_string_into_domain : abstract method
        This takes the string representation of a value and converts it into the underlying domain of the semiring.

    Examples
    --------
    An example of initializing this object for the tropical semiring would be::
    
        class TropicalSemiring(Semiring[float]):
            def __init__(self) -> None:
                super().__init__(
                    add=min,
                    multiply=lambda a, b: a + b,
                    additive_identity=float('inf'),
                    multiplicative_identity=0.0
                )
        
    References
    ----------
    See this OpenFST paper for a relatively high-level discussion of weighted FSTs and semirings.
        https://www.openfst.org/twiki/pub/FST/FstBackground/ciaa.pdf

    Wikipedia discussion on semirings:
        https://en.wikipedia.org/wiki/Semiring

    See this paper for a more in-depth and technical weighted FST design discussion:
        https://www.cs.mun.ca/~harold/Courses/Old/Ling6800.W06/Diary/tcs.pdf

    See this textbook for the definitions of the different semirings used here, as well as the general
    mathematical underpinning of them, and their uses in/for FSTs:
        Lothaire, *Applied Combinatorics on Words* (Cambridge: Cambridge University Press, 2004), 200.
    """

    def __init__(
            self,
            add: Callable[[T, T], T],
            multiply: Callable[[T, T], T],
            additive_identity: T,
            multiplicative_identity: T
        ) -> None:
        """
        Initializes the semiring with the specified operations and identity elements.

        Parameters
        ----------
        add : Callable[[T, T], T]
            A function that defines the addition operation for the semiring.

        multiply : Callable[[T, T], T]
            A function that defines the multiplication operation for the semiring.

        additive_identity : T
            The identity element for the addition operation.

        multiplicative_identity : T
            The identity element for the multiplication operation.

        """

        self._add = add
        self._multiply = multiply
        self._additive_identity = additive_identity
        self._multiplicative_identity = multiplicative_identity
        
    @property
    def additive_identity(self) -> T:
        """
        The additive identity of the semiring.

        Returns
        -------
        T
            The additive identity.
        """

        return self._additive_identity
    
    @property
    def multiplicative_identity(self) -> T:
        """
        The multiplicative identity of the semiring.

        Returns
        -------
        T
            The multiplicative identity.
        """

        return self._multiplicative_identity
        
    def add(self, a: T, b: T) -> T:
        """
        Performs the addition operation of the semiring.

        Parameters
        ----------
        a : T
            The first operand.

        b : T
            The second operand.

        Returns
        -------
        T
            The result of the addition.

        Note
        -----
        Please note that this addition is not the standard "+" operation, but could be any associative, commutative binary operation
        that has an identity element **0**.
        """

        return self._add(a, b)
    
    def multiply(self, a: T, b: T) -> T:
        """
        Performs the multiplication operation of the semiring.

        Parameters
        ----------
        a : T
            The first operand.
            
        b : T
            The second operand.

        Returns
        -------
        T
            The result of the multiplication.

        Note
        -----
        Please note that this multiplication is not the standard "*" operation, but could be any associative binary operation
        that distributes over the defined addition with identity element **1** and that has **0** as an annhilator. Multiplication
        retains higher precedence over the defined addition.
        """

        return self._multiply(a, b)

    def get_path_weight(self, *path_weights: T) -> T:
        """
        Computes the overall weight of a single path by multiplying the weights of all edges in the path.

        Parameters
        ----------
        *path_weights : T
            Weights corresponding to the edges in a path.

        Returns
        -------
        T
            The overall weight of the path, computed as the product of the individual edge weights.

        References
        ----------
        Lothaire, *Applied Combinatorics on Words* (Cambridge: Cambridge University Press, 2004), 201.
        """

        overall_path_weight = self.multiplicative_identity

        for path_weight in path_weights:
            overall_path_weight = self.multiply(overall_path_weight, path_weight)

        return overall_path_weight

    def get_path_set_weight(self, *set_of_path_weights: T) -> T:
        """
        Computes the overall weight of a set of paths by adding the weights of individual paths.

        Parameters
        ----------
        *set_of_path_weights : T
            A list of weights corresponding to individual paths.

        Returns
        -------
        T
            The overall weight of the set of paths, computed as the sum of the individual path weights.

        References
        ----------
        Lothaire, *Applied Combinatorics on Words* (Cambridge: Cambridge University Press, 2004), 201.
        """

        overall_set_weight = self.additive_identity

        for path_weight in set_of_path_weights:
            overall_set_weight = self.add(overall_set_weight, path_weight)

        return overall_set_weight

    @abstractmethod
    def check_membership(self, *values: Any) -> bool:
        """
        Checks that the given values are members of the underlying set of the semiring.

        Parameters
        ---------
        *values : Any
            The values that will be checked to guarantee they are of the type of the underlying set of the semiring.

        Returns
        ------
        bool
            Whether or not every provided value is in the underlying set or not.
        """

    @abstractmethod
    def convert_string_into_domain(self, string_representation_of_value: str) -> T:
        """
        Returns the underlying value for a given string representation of a that value (i.e. as read in from a file).

        Parameters
        ----------
        string_representation_of_value: str
            This is the string representation of the value to be converted.

        Returns
        -------
        T
            The value converted into the underlying domain of the semiring.
        """
    

#region Concrete Semirings

class BooleanSemiring(Semiring[bool]):
    """
    A semiring whose underlying set and operations are defined over the boolean values ``True`` and ``False``.

    Attributes
    ----------
    check_membership : method
        Checks that all provided values are boolean.

    convert_string_into_domain : method
        Converts the string representation of a value into the ``bool`` type.

    Note
    -----
    The boolean semiring defines ``add`` as the ``or`` operator and ``multiply`` as the ``and`` operator.
    The additive identity of the semiring is ``False``, and the multiplicative idenity is ``True``.

    This is also apparently the smallest semiring that is not a ring.

    See Also
    --------
    Semiring : The base class of the ``BooleanSemiring`` with ``T = bool``.

    References
    ----------
    Wikipedia article on two-element boolean algebra:
        https://en.wikipedia.org/wiki/Two-element_Boolean_algebra
    """

    def __init__(self) -> None:

        super().__init__(
            add=lambda a, b: a or b,
            multiply=lambda a, b: a and b,
            additive_identity=False,
            multiplicative_identity=True,
        )

    def check_membership(self, *values: Any) -> bool:
        """
        Checks that all provided values are boolean.

        Parameters
        ----------
        *values : Any
            The values to check for boolean membership.

        Returns
        ------
        bool
            Whether or not every provided value is in the underlying set or not.
        """

        for value in values:
            if not isinstance(value, bool):
                return False
            
        return True
    
    def convert_string_into_domain(self, string_representation_of_value: str) -> bool:
        
        if string_representation_of_value == "True":
            return True
        
        if string_representation_of_value == "False":
            return False
        
        if value_as_num := int(string_representation_of_value) == 1:
            return True
        
        if value_as_num == 0:
            return False
        
        raise ValueError(f"Non-boolean weight found. Offending weight: {string_representation_of_value}")


class LogSemiring(Semiring[float]):
    """
    A semiring whose underlying set of values are the reals with +/- infinity, with addition as logadd and
    multiplication as standard addition.

    Attributes
    ----------
    check_membership : method
        Checks that all provided values are real numbers or +/- infinity.
    
    convert_string_into_domain : method
        Converts the string representation of a value into the ``float`` type.

    Note
    -----
    This is also known as the minimum logarithmic semiring, given the negation of the log and the exponents of e.

    This semiring defines ``add`` as ``-math.log(math.exp(-a) + math.exp(-b))`` and ``multiply`` as ``a + b``.
    It defines the additive identity as ``float('inf')``, and the multiplicative identity as ``0.0``.

    This ``add`` function is a smooth approximation of the minimum of the values ``a`` and ``b``. This sort of operation
    is known as the log-sum-exp trick, which allows for higher precision when doing floating-point arithmetic on large or small
    values by shifting the values into a domain that's better suited for floating-point precision. This sort of equation is often
    used in probability theory, as logarithms can have a bunch of benefits for calculations.

    See Also
    --------
    Semiring : The base class of the ``LogSemiring`` with ``T = float``.

    References
    ----------
    Wikipedia article on the LogSumExp function:
        https://en.wikipedia.org/wiki/LogSumExp

    Wikipedia article on the log semiring:
        https://en.wikipedia.org/wiki/Log_semiring

    Numpy has the maximum version of this function, see this and the Wikipedia article on the log semiring:
        https://numpy.org/doc/stable/reference/generated/numpy.logaddexp.html
    """

    def __init__(self) -> None:
        
        super().__init__(
            add=lambda a, b: -math.log(math.exp(-a) + math.exp(-b)),
            multiply=lambda a, b: a + b,
            additive_identity=float('inf'),
            multiplicative_identity=0.0,
        )

    def check_membership(self, *values: Any) -> bool:
        """
        Checks that all provided values are real numbers or +/- infinity.

        Parameters
        ----------
        *values : Any
            The values to check for real number membership.

        Returns
        ------
        bool
            Whether or not every provided value is in the underlying set or not.
        """
        for value in values:
            try:
                _ = float(value)
            except ValueError:
                return False
            
        return True

    def convert_string_into_domain(self, string_representation_of_value: str) -> float:
        return float(string_representation_of_value)


class ProbabilitySemiring(Semiring[float]):
    """
    This is the probability semiring that is defined on the non-negative reals and standard additiona and multiplication.

    Attributes
    ----------
    check_membership : method
        Checks that all provided values are non-negative real numbers.
    
    convert_string_into_domain : method
        Converts the string representation of a value into the ``float`` type.

    Note
    -----
    This semiring uses standard addition and multiplication, and is meant for managing weights that are probabilities.
    
    See Also
    --------
    Semiring : The base class of the ``ProbabilitySemiring`` with ``T = float``.

    """

    def __init__(self) -> None:
        
        super().__init__(
            add=lambda a, b: a + b,
            multiply=lambda a, b: a * b,
            additive_identity=0.0,
            multiplicative_identity=1.0
        )

    def check_membership(self, *values: Any) -> bool:
        """
        Checks that all provided values are non-negative real numbers.

        Parameters
        ----------
        *values : Any
            The values to check for membership in the non-negative reals.

        Returns
        ------
        bool
            Whether or not every provided value is in the underlying set or not.
        """

        for value in values:
            try:
                value = float(value)
            except ValueError:
                return False

            if value < 0 or value == float('inf'):
                return False
        
        return True

    def convert_string_into_domain(self, string_representation_of_value: str) -> float:
        return float(string_representation_of_value)
    

class TropicalSemiring(Semiring[float]):
    """
    The tropical semiring is defined on the reals with +/- infinity, where addition is the minimum and multiplication is standard addition.

    Attributes
    ----------
    check_membership : method
        Checks that all provided values are real numbers or +/- infinity.
    
    convert_string_into_domain : method
        Converts the string representation of a value into the ``float`` type.

    Note
    -----
    This is also known as the minimum tropical semiring for its use of ``min``, instead of ``max``, as the addition function.
    
    As mentioned, ``add`` is defined as ``min{a, b}``. Multiplication is defined as standard addition. The additive identity is ``float('inf')``.

    The way this works is that for a given output form, you may end up with a bunch of different paths that got you there. Each of those paths
    will have its own weight, and, because addition is ``min``, that means when you sum the paths together, the result you get is the lowest
    weight among paths that led to the output. This can be useful because some paths may be penalized for having maybe non-standard forms, etc.,
    but which lead to a perfectly valid output. We therefore only care about the minimum weight which is therefore the determiner of the
    validity/order of the output form. The rest of the weights can be thought of as superfluous.

    See Also
    --------
    Semiring : The base class of the ``TropicalSemiring`` with ``T = float``.

    References
    ----------
    The Wikipedia article on tropical semirings:
        https://en.wikipedia.org/wiki/Tropical_semiring
    """

    def __init__(self) -> None:

        super().__init__(
            add=min,
            multiply=lambda a, b: a + b,
            additive_identity=float('inf'),
            multiplicative_identity=0.0,
        )

    def check_membership(self, *values: Any) -> bool:
        """
        Checks that all provided values are real numbers or +/- infinity.

        Parameters
        ----------
        *values : Any
            The values to check for real number membership.
        
        Returns
        ------
        bool
            Whether or not every provided value is in the underlying set or not.
        """

        for value in values:
            try:
                _ = float(value)
            except ValueError:
                return False
            
        return True

    def convert_string_into_domain(self, string_representation_of_value: str) -> float:
        return float(string_representation_of_value)

#endregion
