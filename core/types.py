# core/types.py
"""
Defines the core data types used within the Log-Os interpreter.
"""

class Symbol(str):
    """A LISP-style symbol, which is a distinct type from a string."""
    # A unique object to mark lists that need to be spliced.
    SPLICE = object()

class Procedure:
    """
    Represents a user-defined procedure (lambda). It captures the parameters,
    body, and the environment in which it was created (its closure).
    """
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env

class Macro:
    """Represents a macro, holding its parameters and body."""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env # The environment where the macro was defined

# An Atom is a Symbol, a number, a boolean, a string, or a hash-map.
Atom = (Symbol, int, float, str, bool, dict)

# A List is a nested structure of other Expressions.
# We use a forward reference here as List contains Expression.
List = list

# An Expression is the fundamental unit of code.
Expression = (Atom, List)