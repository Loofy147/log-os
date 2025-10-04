# core/environment.py
<<<<<< professional-overhaul
import math
import operator as op
from .types import Symbol

class Environment:
    """
    A class to represent the lexical environment for the interpreter,
    handling variable and macro scopes.
    """
    def __init__(self, outer=None):
        self.outer = outer
        self.vars = {}
        self.macros = {}

    def find(self, var):
        """
        Find the innermost environment where a variable is defined.
        Searches up the scope chain from the current environment.
        Returns the environment if found, otherwise None.
        """
        if var in self.vars:
            return self
        if self.outer is not None:
            return self.outer.find(var)
        return None

    def get(self, var):
        """
        Get the value of a variable from the environment.
        Raises a NameError if the variable is not found.
        """
        env_with_var = self.find(var)
        if env_with_var is None:
            raise NameError(f"'{var}' is not defined")
        return env_with_var.vars[var]

    def define(self, var, value):
        """
        Define a variable in the current environment.
        """
        self.vars[var] = value
        return value

    def set(self, var, value):
        """
        Set the value of an existing variable in the environment.
        Searches up the scope chain and updates the variable where it is found.
        Raises a NameError if the variable is not found.
        """
        env_with_var = self.find(var)
        if env_with_var is None:
            raise NameError(f"Cannot set! undefined variable '{var}'")
        env_with_var.vars[var] = value
        return value

    def update(self, other_dict):
        """Update the environment from another dictionary."""
        self.vars.update(other_dict)

    def define_macro(self, name, macro):
        """Define a macro in the current environment."""
        self.macros[name] = macro

    def find_macro(self, name):
        """
        Find the innermost environment where a macro is defined.
        Searches up the scope chain from the current environment.
        Returns the environment if found, otherwise None.
        """
        if name in self.macros:
            return self
        if self.outer is not None:
            return self.outer.find_macro(name)
        return None

def create_global_env(evaluate_fn):
    """
    Creates the global environment and populates it with
    primitive procedures.
    """
    env = Environment()

    # Mathematical functions
    env.vars.update(vars(math))
    env.vars.update({
        '+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv,
        '>': op.gt, '<': op.lt, '>=': op.ge, '<=': op.le, '=': op.eq,
        'abs': abs,
        'append': op.add,
        'apply': lambda f, args: f(*args),
        'begin': lambda *x: x[-1],
        'car': lambda x: x[0],
        'cdr': lambda x: x[1:],
        'cons': lambda x, y: [x] + y,
        'eq?': op.is_,
        'equal?': op.eq,
        'length': len,
        'list': lambda *x: list(x),
        'list?': lambda x: isinstance(x, list),
        'map': lambda f, x: list(map(f, x)),
        'max': max,
        'min': min,
        'not': op.not_,
        'null?': lambda x: x == [],
        'number?': lambda x: isinstance(x, (int, float)),
        'procedure?': callable,
        'round': round,
        'symbol?': lambda x: isinstance(x, Symbol)
    })

    # Add `eval` to the environment, using the passed-in evaluator
    env.define('eval', lambda expr: evaluate_fn(expr, env))
=======
"""
Defines the default global environment for the Log-Os interpreter.
This environment contains built-in procedures and standard library functions.
"""

import math
import operator as op
import functools
import os
import time
import random

from .types import Symbol, List, Atom
from .errors import LogosEvaluationError, LogosAssertionError

# Global state for orchestrator primitives
L0_CACHE = {}
L0_JIT_SEEN_ASTS = set()


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

def create_global_env(eval_func) -> Environment:
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
        Symbol('hash-get'): lambda h_map, key, default=None: h_map.get(key, default),
        Symbol('hash-set!'): lambda h_map, key, val: h_map.update({key: val}),

        # Orchestrator Primitives
        Symbol('interpret'): lambda ast, env: eval_func(ast, env),
        Symbol('current-time-ms'): lambda: time.time() * 1000,
        Symbol('random'): random.random,
        Symbol('gamma-sample'): lambda alpha: random.gammavariate(alpha, 1.0),
        Symbol('log'): math.log,
        Symbol('sqrt'): math.sqrt,
        Symbol('cos'): math.cos,
        Symbol('cache-get'): lambda key, default=None: L0_CACHE.get(key, default),
        Symbol('cache-put'): lambda key, value: L0_CACHE.update({key: value}) and value,
        Symbol('cache-has?'): lambda key: key in L0_CACHE,
        Symbol('jit-seen?'): lambda ast: lisp_str(ast) in L0_JIT_SEEN_ASTS,
        Symbol('jit-mark-seen'): lambda ast: L0_JIT_SEEN_ASTS.add(lisp_str(ast)),
        Symbol('simulate-jit-compile'): lambda ast: time.sleep(0.001), # Lightweight placeholder
        Symbol('cache-key'): lambda ast, env: lisp_str(ast),

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
>>>>>> main

    return env