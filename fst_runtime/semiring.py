# pylint: disable=undefined-variable
# This is disabled because pylint isn't recognize the new generic syntax for python yet and can't figure out what "T" is.

'''
This module defines a semiring as well as several semirings commonly used with weighted FSTs.

Classes
-------
Semiring[T]
    An abstract class that defines a semiring.

BooleanSemiring[bool]
    A semiring whose underlying set and operations are defined over the boolean values ``True`` and ``False``.

LogSemiring[float]
    A semiring whose underlying set of values are the reals with +/- infinity, with addition as logadd and
    multiplication as standard addition.

ProbabilitySemiring[float]
    This is the probability semiring that is defined on the non-negative reals and standard additiona and multiplication.

Tropical Semiring[float]
    The tropical semiring is defined on the reals with +/- infinity, where addition is the minimum and multiplication is standard addition.

See Also
--------
See this OpenFST paper for a relatively high-level discussion of weighted FSTs and semirings.
    https://www.openfst.org/twiki/pub/FST/FstBackground/ciaa.pdf

Wikipedia discussion on semirings:
    https://en.wikipedia.org/wiki/Semiring

See this paper for a more in-depth and technical weighted FST design discussion:
    https://www.cs.mun.ca/~harold/Courses/Old/Ling6800.W06/Diary/tcs.pdf

See this textbook for the definitions of the different semirings used here, as well as the general
mathematical underpinning of them, and their uses in/for FSTs:
    Lothaire, *Applied Combinatorics on Words* (Cambridge: Cambridge University Press, 2004), 200.
'''

from abc import ABC, abstractmethod
import math
from typing import Callable, Iterable

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

    get_path_set_weight_for_uncomputed_path_weights : method
        Computes the overall weight of a set of paths by first calculating the weight of each path and then 
        summing these weights.

    check_membership : abstract method
        This method ensures that the values provided to it are members of the underlying set of the semiring. Raises a ``ValueError`` if not.

    Examples
    --------
    An example of initializing this object for the tropical semiring would be:
    
    ```
    class TropicalSemiring(Semiring[float]):
        def __init__(self) -> None:
            super().__init__(
                add=min,
                multiply=lambda a, b: a + b,
                additive_identity=float('inf'),
                multiplicative_identity=0.0
            )
    ```
        
    See Also
    --------
    See module-level documentation for a list of resources on semirings and weighted FSTs.
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

        Notes
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

        Notes
        -----
        Please note that this multiplication is not the standard "*" operation, but could be any associative binary operation
        that distributes over the defined addition with identity element **1** and that has **0** as an annhilator. Multiplication
        retains higher precedence over the defined addition.
        """

        return self._multiply(a, b)

    def get_path_weight(self, path_weights: Iterable[T]) -> T:
        """
        Computes the overall weight of a single path by multiplying the weights of all edges in the path.

        Parameters
        ----------
        path_weights : Iterable[T]
            A list of weights corresponding to the edges in a path.

        Returns
        -------
        T
            The overall weight of the path, computed as the product of the individual edge weights.

        See Also
        --------
        Lothaire, *Applied Combinatorics on Words* (Cambridge: Cambridge University Press, 2004), 201.
        """

        overall_path_weight = self.multiplicative_identity

        for path_weight in path_weights:
            overall_path_weight = self.multiply(overall_path_weight, path_weight)

        return overall_path_weight

    def get_path_set_weight(self, set_of_path_weights: Iterable[T]) -> T:
        """
        Computes the overall weight of a set of paths by adding the weights of individual paths.

        Parameters
        ----------
        set_of_path_weights : Iterable[T]
            A list of weights corresponding to individual paths.

        Returns
        -------
        T
            The overall weight of the set of paths, computed as the sum of the individual path weights.

        See Also
        --------
        Lothaire, *Applied Combinatorics on Words* (Cambridge: Cambridge University Press, 2004), 201.
        """

        overall_set_weight = self.additive_identity

        for path_weight in set_of_path_weights:
            overall_set_weight = self.add(overall_set_weight, path_weight)

        return overall_set_weight

    def get_path_set_weight_for_uncomputed_path_weights(self, set_of_paths: Iterable[Iterable[T]]) -> T:
        """
        Computes the overall weight of a set of paths by first calculating the weight of each path and then 
        summing these weights.

        Parameters
        ----------
        set_of_paths : Iterable[Iterable[T]]
            A list of paths, where each path is represented as a list of weights.

        Returns
        -------
        T
            The overall weight of the set of paths.

        See Also
        --------
        Lothaire, *Applied Combinatorics on Words* (Cambridge: Cambridge University Press, 2004), 201.
        """

        set_of_path_weights = [self.get_path_weight(path) for path in set_of_paths]
        return self.get_path_set_weight(set_of_path_weights)

    @abstractmethod
    def check_membership(self, *values: any) -> None:
        """
        Checks that the given values are members of the underlying set of the semiring.

        Parameters
        ----------
        *values : any
            The values that will be checked to guarantee they are of the type of the underlying set of the semiring.

        Raises
        ------
        ValueError
            A value error is raised if any of the provided values don't belong to the underlying set of the semiring.
        """

        raise ValueError("Cannot use abstract method directly.")
    

class BooleanSemiring(Semiring[bool]):
    """
    A semiring whose underlying set and operations are defined over the boolean values ``True`` and ``False``.

    Attributes
    ----------
    check_membership : method
        Checks that all provided values are boolean.

    convert_value_to_boolean : static method
        Converts an integer or float to a boolean if it is 0 or 1.

    convert values_to_boolean : static method
        Converts multiple integers or floats to boolean values.

    Notes
    -----
    The boolean semiring defines ``add`` as the ``or`` operator and ``multiply`` as the ``and`` operator.
    The additive identity of the semiring is ``False``, and the multiplicative idenity is ``True``.

    This is also apparently the smallest semiring that is not a ring.

    See Also
    --------
    For the base class API, please see ``Semiring[T]``.

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

    def check_membership(self, *values: any) -> None:
        """
        Checks that all provided values are boolean.

        Parameters
        ----------
        *values : any
            The values to check for boolean membership.

        Raises
        ------
        ValueError
            Raised if any value is not a boolean.
        """

        for value in values:
            if not isinstance(value, bool):
                raise ValueError("The boolean semiring only supports boolean values.")
    
    @staticmethod
    def convert_value_to_boolean(value: int | float) -> bool:
        """
        Converts an integer or float to a boolean if it is 0 or 1.

        Parameters
        ----------
        value : int | float
            The value to convert.

        Returns
        -------
        bool
            The boolean equivalent of the value.

        Raises
        ------
        ValueError
            Raised if the value is not 0 or 1.
        """

        if value == 1:
            return True
        
        if value == 0:
            return False
        
        raise ValueError("Only 0/0.0 and 1/1.0 are valid stand-ins for a boolean value.")
            
    @staticmethod
    def convert_values_to_boolean(*values: int | float) -> list[bool]:
        """
        Converts multiple integers or floats to boolean values.

        Parameters
        ----------
        *values : int | float
            The values to convert.

        Returns
        -------
        list[bool]
            A list of boolean values converted from the input.

        Raises
        ------
        ValueError
            Raised if a value is not 0 or 1.
        """

        converted_values: list[bool] = []

        for value in values:
            try:
                converted_value = BooleanSemiring.convert_value_to_boolean(value)
            except ValueError:
                raise

            converted_values.append(converted_value)
        
        return converted_values
            

class LogSemiring(Semiring[float]):
    """
    A semiring whose underlying set of values are the reals with +/- infinity, with addition as logadd and
    multiplication as standard addition.

    Attributes
    ----------
    check_membership : method
        Checks that all provided values are real numbers or +/- infinity.

    Notes
    -----
    For the base class API, please see ``Semiring[T]``.

    This is also known as the minimum logarithmic semiring, given the negation of the log and the exponents of e.

    This semiring defines ``add`` as ``-math.log(math.exp(-a) + math.exp(-b))`` and ``multiply`` as ``a + b``.
    It defines the additive identity as ``float('inf')``, and the multiplicative identity as ``0.0``.

    This ``add`` function is a smooth approximation of the minimum of the values ``a`` and ``b``. This sort of operation
    is known as the log-sum-exp trick, which allows for higher precision when doing floating-point arithmetic on large or small
    values by shifting the values into a domain that's better suited for floating-point precision. This sort of equation is often
    used in probability theory, as logarithms can have a bunch of benefits for calculations.

    This "smooth minimum" means that when values are close to each other, the value returned will be a kind of interpolation between the two.
    But, when values are far apart, the value returned will be much closer to the minimum value. That is, when ``a`` and ``b`` are far apart,
    then ``-ln(e^(-a) + e^(-b)) ≈ min{a, b}``.

    See Also
    --------
    For the base class API, please see ``Semiring[T]``.

    Wikipedia article on the LogSumExp function:
        https://en.wikipedia.org/wiki/LogSumExp

    Wikipedia article on the log semiring:
        https://en.wikipedia.org/wiki/Log_semiring
    """

    def __init__(self) -> None:
        
        super().__init__(
            add=lambda a, b: -math.log(math.exp(-a) + math.exp(-b)),
            multiply=lambda a, b: a + b,
            additive_identity=float('inf'),
            multiplicative_identity=0.0,
        )

    def check_membership(self, *values: any) -> None:
        """
        Checks that all provided values are real numbers or +/- infinity.

        Parameters
        ----------
        *values : any
            The values to check for real number membership.

        Raises
        ------
        ValueError
            If any value is not a real number or +/- infinity.
        """
        for value in values:
            try:
                _ = float(value)
            except ValueError as e:
                raise ValueError("The log semiring only supports the real numbers and +/- infinity.") from e


class ProbabilitySemiring(Semiring[float]):
    """
    This is the probability semiring that is defined on the non-negative reals and standard additiona and multiplication.

    Attributes
    ----------
    check_membership : method
        Checks that all provided values are non-negative real numbers.

    Notes
    -----
    This semiring uses standard addition and multiplication, and is meant for managing weights that are probabilities.
    
    See Also
    --------
    For the base class API, please see ``Semiring[T]``.
    """

    def __init__(self) -> None:
        
        super().__init__(
            add=lambda a, b: a + b,
            multiply=lambda a, b: a * b,
            additive_identity=0.0,
            multiplicative_identity=1.0
        )

    def check_membership(self, *values: any) -> None:
        """
        Checks that all provided values are non-negative real numbers.

        Parameters
        ----------
        *values : any
            The values to check for membership in the non-negative reals.

        Raises
        ------
        ValueError
            If any value is not a non-negative real number.
        """

        error = ValueError("The probability semiring only supports the non-negative reals.")

        for value in values:
            try:
                value = float(value)
            except ValueError as e:
                raise error from e

            if value < 0 or value == float('inf'):
                raise error
    

class TropicalSemiring(Semiring[float]):
    """
    The tropical semiring is defined on the reals with +/- infinity, where addition is the minimum and multiplication is standard addition.

    Attributes
    ----------
    check_membership : method
        Checks that all provided values are real numbers or +/- infinity.

    Notes
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
    For the base class API, please see ``Semiring[T]``.

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

    def check_membership(self, *values: any) -> None:
        """
        Checks that all provided values are real numbers or +/- infinity.

        Parameters
        ----------
        *values : any
            The values to check for real number membership.

        Raises
        ------
        ValueError
            If any value is not a real number or +/- infinity.
        """

        for value in values:
            try:
                _ = float(value)
            except ValueError as e:
                raise ValueError("The tropical semiring only supports the real numbers and +/- infinity.") from e
