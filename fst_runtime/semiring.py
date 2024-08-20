from typing import Callable
import math

class Semiring[T]:

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
    

class CommutativeSemiring[T](Semiring[T]):
    ...
    

class BooleanSemiring(CommutativeSemiring[bool]):

    def __init__(self):

        super().__init__(
            add=lambda a, b: a or b,
            multiply=lambda a, b: a and b,
            additive_identity=False,
            multiplicative_identity=True,
        )


class LogSemiring(CommutativeSemiring[float]):
    '''Logarithmic Semiring'''

    def __init__(self):

        super().__init__(
            add=lambda a, b: -math.log(math.exp(-a) + math.exp(-b)),
            multiply=lambda a, b: a + b,
            additive_identity=float('inf'),
            multiplicative_identity= 0.0,
        )


class ProbabilitySemiring(CommutativeSemiring[float]):

    def __init__(self):

        super().__init__(
            add=lambda a, b: a + b,
            multiply=lambda a, b: a * b,
            additive_identity=0.0,
            multiplicative_identity=1.0
        )
    
    def add(self, a: float, b: float) -> float:

        if a < 0 or b < 0:
            raise ValueError("Negative number found when only non-negative real numbers are in the underlying set of the probability semiring.")

        return super().add(a, b)
    
    def multiply(self, a: float, b: float) -> float:

        if a < 0 or b < 0:
            raise ValueError("Negative number found when only non-negative real numbers are in the underlying set of the probability semiring.")
        
        return super().multiply(a, b)


class TropicalSemiring(CommutativeSemiring[float]):
    '''Min Tropical Semiring'''

    def __init__(self):

        super().__init__(
            add=min,
            multiply=lambda a, b: a + b,
            additive_identity=float('inf'),
            multiplicative_identity=0.0,
        )





