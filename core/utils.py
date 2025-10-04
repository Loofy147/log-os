# core/utils.py
"""
Shared utility functions for the Log-Os project.
"""
from .types import Symbol

def lisp_str(exp, escape_str=True) -> str:
    """
    Converts a Python object back into a LISP-readable string.
    Symbols are unquoted, strings are double-quoted by default.
    """
    if isinstance(exp, list):
        # Recursively call lisp_str, passing the escape_str parameter along.
        return '(' + ' '.join(map(lambda e: lisp_str(e, escape_str), exp)) + ')'
    elif exp is True:
        return '#t'
    elif exp is False:
        return '#f'
    elif isinstance(exp, Symbol):
        return exp
    elif isinstance(exp, str):
        # Only add quotes if escape_str is True.
        return f'"{exp}"' if escape_str else exp
    else:
        return str(exp)