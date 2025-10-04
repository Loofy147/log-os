# core/environment.py
"""
Defines the default global environment for the Log-Os interpreter.
This environment contains built-in procedures and standard library functions.
"""

import math
import operator as op
import functools
import os
import time

from .types import Symbol, List, Atom
from .errors import LogosEvaluationError, LogosAssertionError
from .types import Procedure

class Environment(dict):
    """A dictionary with an outer scope and a separate space for macros."""
    def __init__(self, params=(), args=(), outer=None):
        super().__init__()
        # Handle variadic parameters
        if Symbol('.') in params:
            dot_index = params.index(Symbol('.'))
            fixed_params = params[:dot_index]
            rest_param = params[dot_index + 1]

            if len(args) < len(fixed_params):
                raise LogosEvaluationError(f"Procedure expects at least {len(fixed_params)} arguments, got {len(args)}")

            self.update(zip(fixed_params, args))
            self[rest_param] = list(args[len(fixed_params):])
        else:
            if len(params) != len(args):
                raise LogosEvaluationError(f"Procedure expects {len(params)} arguments, got {len(args)}")
            self.update(zip(params, args))

        self.outer = outer
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

def create_global_env(interpreter) -> Environment:
    """
    Creates and returns the default global environment.
    The interpreter instance is passed in to allow primitives like `apply`
    to call back into the evaluation process.
    """
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
        Symbol('car'): lambda x: x[0],
        Symbol('cdr'): lambda x: x[1:],
        Symbol('cons'): lambda x, y: [x] + y,
        Symbol('eq?'): op.is_,
        Symbol('equal?'): op.eq,
        Symbol('length'): len,
        Symbol('list'): lambda *x: list(x),
        Symbol('list?'): lambda x: isinstance(x, list),
        Symbol('max'): max,
        Symbol('min'): min,
        Symbol('not'): op.not_,
        Symbol('null?'): lambda x: x == [],
        Symbol('number?'): lambda x: isinstance(x, (int, float)),
        Symbol('procedure?'): lambda p: callable(p) or isinstance(p, Procedure),
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

        # Utility functions
        Symbol('member?'): lambda item, lst: item in lst,
        Symbol('ends-with?'): lambda s, suffix: s.endswith(suffix),
    })

    # Primitives that need access to the interpreter
    def apply_proc(proc, args):
        if isinstance(proc, Procedure):
            return interpreter.evaluate(proc.body, Environment(proc.params, args, proc.env))
        elif callable(proc):
            return proc(*args)
        else:
            raise LogosEvaluationError(f"apply: expected a procedure, but got {type(proc)}")
    env[Symbol('apply')] = apply_proc

    def map_proc(proc, lst):
        return [apply_proc(proc, [item]) for item in lst]
    env[Symbol('map')] = map_proc

    def filter_proc(pred, lst):
        return [item for item in lst if apply_proc(pred, [item])]
    env[Symbol('filter')] = filter_proc

    # 'append' needs to be variadic, so we define it separately.
    def variadic_append(*lists):
        result = []
        for lst in lists:
            if not isinstance(lst, list):
                raise LogosEvaluationError(f"append: expected lists, but got {type(lst)}")
            result.extend(lst)
        return result
    env[Symbol('append')] = variadic_append

    # A simple unique symbol generator for macro hygiene
    gensym_counter = 0
    def gensym(prefix="G"):
        nonlocal gensym_counter
        gensym_counter += 1
        return Symbol(f"{prefix}{gensym_counter}")
    env[Symbol('gensym')] = gensym

    def print_proc(*args):
        """A simple print function for debugging."""
        print(*map(lisp_str, args))
        return None
    env[Symbol('print')] = print_proc

    def string_append_proc(*args):
        """Concatenates multiple values into a single string."""
        return "".join(map(lambda x: lisp_str(x, escape_str=False), args))
    env[Symbol('string-append')] = string_append_proc

    env[Symbol('current-time')] = time.time

    # Kernel management primitives
    def register_kernel(name, kernel_map):
        if not isinstance(name, Symbol):
            raise LogosEvaluationError(f"register-kernel!: name must be a symbol, but got {type(name)}")
        if not isinstance(kernel_map, dict):
            raise LogosEvaluationError(f"register-kernel!: kernel must be a hash-map, but got {type(kernel_map)}")
        interpreter.kernels[name] = kernel_map
        return name
    env[Symbol('register-kernel!')] = register_kernel

    def get_kernel(name):
        if not isinstance(name, Symbol):
            raise LogosEvaluationError(f"get-kernel: name must be a symbol, but got {type(name)}")
        return interpreter.kernels.get(name)
    env[Symbol('get-kernel')] = get_kernel

    return env