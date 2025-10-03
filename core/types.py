# core/types.py
"""
Defines the core data types used within the Log-Os interpreter.
"""

class Symbol(str):
    """A LISP-style symbol, which is a distinct type from a string."""
    pass

# An Atom is a Symbol, a number, a boolean, or a string.
Atom = (Symbol, int, float, str, bool)

# A List is a nested structure of other Expressions.
# We use a forward reference here as List contains Expression.
List = list

# An Expression is the fundamental unit of code.
Expression = (Atom, List)