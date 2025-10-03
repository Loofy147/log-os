# core/environment.py
"""
Defines the default global environment for the Log-Os interpreter.
This environment contains built-in procedures and standard library functions.
"""

import math
import operator as op
import functools
import os

from .types import Symbol, List, Atom
from .errors import LogosEvaluationError, LogosAssertionError

class Environment(dict):
    """A dictionary with an outer scope and a separate space for macros."""
    def __init__(self, params=(), args=(), outer=None):
        super().__init__()
        self.update(zip(params, args))
        self.outer = outer
        # Macros are stored separately to prevent them from being called as functions.
        self.macros = {}

    def find(self, var: Symbol) -> 'Environment':
        """Finds the innermost environment where a variable is defined."""
        if var in self:
            return self
        elif self.outer is not None:
            return self.outer.find(var)
        else:
            raise NameError(f"Symbol '{var}' is not defined.")

    def find_macro(self, var: Symbol) -> 'Environment':
        """Finds the innermost environment where a macro is defined."""
        if var in self.macros:
            return self
        elif self.outer is not None:
            return self.outer.find_macro(var)
        else:
            return None # Return None if macro is not found, not an error

from .parser import parse
from .utils import lisp_str

def create_global_env() -> Environment:
    """Creates and returns the default global environment."""
    env = Environment()
    env.update({
        # Mathematical operators
        Symbol('+'): lambda *args: sum(args),
        Symbol('-'): op.sub,
        Symbol('*'): lambda *args: functools.reduce(op.mul, args, 1),
        Symbol('/'): op.truediv,
        Symbol('>'): op.gt,
        Symbol('<'): op.lt,
        Symbol('>='): op.ge,
        Symbol('<='): op.le,
        Symbol('='): op.eq,
        Symbol('%'): op.mod,

        # Core functions
        Symbol('error'): lambda message: (_ for _ in ()).throw(LogosEvaluationError(message)),
        Symbol('assert-equal'): lambda actual, expected: (
            True if actual == expected
            else (_ for _ in ()).throw(LogosAssertionError(f"Assertion Failed: Expected {expected}, but got {actual}"))
        ),
        Symbol('abs'): abs,
        Symbol('apply'): lambda proc, args: proc(*args),
        Symbol('car'): lambda x: x[0],
        Symbol('cdr'): lambda x: x[1:],
        Symbol('cons'): lambda x, y: [x] + y,
        Symbol('eq?'): op.is_,
        Symbol('equal?'): op.eq,
        Symbol('length'): len,
        Symbol('list'): lambda *x: list(x),
        Symbol('list?'): lambda x: isinstance(x, list),
        Symbol('map'): lambda proc, lst: list(map(proc, lst)),
        Symbol('max'): max,
        Symbol('min'): min,
        Symbol('not'): op.not_,
        Symbol('null?'): lambda x: x == [],
        Symbol('number?'): lambda x: isinstance(x, (int, float)),
        Symbol('procedure?'): callable,
        Symbol('round'): round,
        Symbol('symbol?'): lambda x: isinstance(x, Symbol),

        # Math constants
        Symbol('pi'): math.pi,

        # Reflective I/O
        Symbol('read-source'): lambda filepath: parse(f"(begin {open(filepath).read()})"),
        Symbol('write-source'): lambda filepath, data: open(filepath, 'w').write(lisp_str(data)),
        Symbol('list-directory'): lambda path: [Symbol(item) for item in os.listdir(path)],

        # Hash-map functions
        Symbol('hash-get'): lambda h_map, key: h_map.get(key),
        Symbol('hash-set!'): lambda h_map, key, val: h_map.update({key: val}),

        # Utility functions
        Symbol('member?'): lambda item, lst: item in lst,
        Symbol('filter'): lambda pred, lst: list(filter(pred, lst)),
        Symbol('ends-with?'): lambda s, suffix: s.endswith(suffix),
    })
    # 'append' needs to be variadic, so we define it separately.
    def variadic_append(*lists):
        result = []
        for lst in lists:
            result.extend(lst)
        return result
    env[Symbol('append')] = variadic_append

    return env