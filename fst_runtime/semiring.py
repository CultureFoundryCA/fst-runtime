'''
This module defines a semiring as well as several commonly used semirings weighted FSTs.

Notes
-----
See this paper for a discussion on weighted FSTs and semirings:
    https://www.openfst.org/twiki/pub/FST/FstBackground/ciaa.pdf

See this paper for a more in-depth and technical weighted FST design discussion:
    https://www.cs.mun.ca/~harold/Courses/Old/Ling6800.W06/Diary/tcs.pdf
'''

from abc import ABC, abstractmethod
import math
from typing import Callable

class Semiring[T](ABC):

    def __init__(
            self,
            add: Callable[[T, T], T],
            multiply: Callable[[T, T], T],
            additive_identity: T,
            multiplicative_identity: T
        ):

        self._add = add
        self._multiply = multiply
        self._additive_identity = additive_identity
        self._multiplicative_identity = multiplicative_identity
        
    @property
    def additive_identity(self):
        return self._additive_identity
    
    @property
    def multiplicative_identity(self):
        return self._multiplicative_identity
        
    def add(self, a: T, b: T) -> T:
        return self._add(a, b)
    
    def multiply(self, a: T, b: T) -> T:
        return self._multiply(a, b)
    
    @abstractmethod
    def check_membership(self, *values: any) -> None:
        '''
        Checks that the given values are members of the underlying set of the semiring.

        Parameters
        ----------
        *values : any
            The values that will be checked to guarantee they are of the type of the underlying set of the semiring.

        Raises
        ------
        ValueError
            A value error is raised if any of the provided values don't belong to the underlying set of the semiring.
        '''

        raise ValueError("Cannot use abstract method directly.")
    

class BooleanSemiring(Semiring[bool]):

    def __init__(self):

        super().__init__(
            add=lambda a, b: a or b,
            multiply=lambda a, b: a and b,
            additive_identity=False,
            multiplicative_identity=True,
        )

    def check_membership(self, *values: any) -> None:

        for value in values:
            if not isinstance(value, bool):
                raise ValueError("The boolean semiring only supports boolean values.")
    
    @staticmethod
    def convert_value_to_boolean(value: int | float) -> bool:
        if value == 1:
            return True
        elif value == 0:
            return False
        else:
            raise ValueError("Only 0 and 1 are valid stand-ins for a boolean value.")
            
    @staticmethod
    def convert_values_to_boolean(*values: int | float) -> list[bool]:

        converted_values: list[bool] = []

        for value in values:
            converted_value = BooleanSemiring.convert_value_to_boolean(value)
            converted_values.append(converted_value)
        
        return converted_values
            

class LogSemiring(Semiring[float]):
    '''Min Logarithmic Semiring'''

    def __init__(self):

        super().__init__(
            add=lambda a, b: -math.log(math.exp(-a) + math.exp(-b)),
            multiply=lambda a, b: a + b,
            additive_identity=float('inf'),
            multiplicative_identity= 0.0,
        )

    def check_membership(self, *values: any) -> None:

        for value in values:
            try:
                _ = float(value)
            except ValueError as e:
                raise ValueError("The log semiring only supports the real numbers and +/- infinity.") from e


class ProbabilitySemiring(Semiring[float]):

    def __init__(self):

        super().__init__(
            add=lambda a, b: a + b,
            multiply=lambda a, b: a * b,
            additive_identity=0.0,
            multiplicative_identity=1.0
        )

    def check_membership(self, *values: any) -> None:
        
        error = ValueError("The probability semiring only supports the non-negative reals.")

        for value in values:
            try:
                value = float(value)
            except ValueError as e:
                raise error from e

            if value < 0 or value == float('inf'):
                raise error
    

class TropicalSemiring(Semiring[float]):
    '''Min Tropical Semiring'''

    def __init__(self):

        super().__init__(
            add=min,
            multiply=lambda a, b: a + b,
            additive_identity=float('inf'),
            multiplicative_identity=0.0,
        )

    def check_membership(self, *values: any) -> None:

        for value in values:
            try:
                _ = float(value)
            except ValueError as e:
                raise ValueError("The tropical semiring only supports the real numbers and +/- infinity.")
