# core/types.py
"""
Defines the core data types used within the Log-Os interpreter.
"""

# A Symbol is a variable name or function name.
Symbol = str

# An Atom is a Symbol or a number.
Atom = (Symbol, int, float)

# A List is a nested structure of other Expressions.
# We use a forward reference here as List contains Expression.
List = list

# An Expression is the fundamental unit of code.
Expression = (Atom, List)