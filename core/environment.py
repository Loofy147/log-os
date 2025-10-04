# core/environment.py
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

    return env