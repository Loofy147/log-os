# core/environment.py
"""
Defines the default global environment for the Log-Os interpreter.
This environment contains built-in procedures and standard library functions.
"""

import math
import operator as op

from .types import Symbol, List, Atom

class Environment(dict):
    """A dictionary with an outer scope."""
    def __init__(self, params=(), args=(), outer=None):
        super().__init__()
        self.update(zip(params, args))
        self.outer = outer

    def find(self, var: Symbol) -> 'Environment':
        """Finds the innermost environment where a variable is defined."""
        if var in self:
            return self
        elif self.outer is not None:
            return self.outer.find(var)
        else:
            raise NameError(f"Symbol '{var}' is not defined.")

def create_global_env() -> Environment:
    """Creates and returns the default global environment."""
    env = Environment()
    env.update({
        # Mathematical operators
        '+': op.add,
        '-': op.sub,
        '*': op.mul,
        '/': op.truediv,
        '>': op.gt,
        '<': op.lt,
        '>=': op.ge,
        '<=': op.le,
        '=': op.eq,

        # Core functions
        'abs': abs,
        'append': op.add,
        'apply': lambda proc, args: proc(*args),
        'begin': lambda *x: x[-1],
        'car': lambda x: x[0],
        'cdr': lambda x: x[1:],
        'cons': lambda x, y: [x] + y,
        'eq?': op.is_,
        'equal?': op.eq,
        'length': len,
        'list': lambda *x: list(x),
        'list?': lambda x: isinstance(x, list),
        'map': lambda proc, lst: list(map(proc, lst)),
        'max': max,
        'min': min,
        'not': op.not_,
        'null?': lambda x: x == [],
        'number?': lambda x: isinstance(x, (int, float)),
        'procedure?': callable,
        'round': round,
        'symbol?': lambda x: isinstance(x, Symbol),

        # Math constants
        'pi': math.pi,

        # Reflective functions (placeholders for now)
        'read-source': lambda f: print(f"Reading from {f}... Not implemented."),
        'write-source': lambda f, d: print(f"Writing to {f}... Not implemented."),
    })
    return env