# core/utils.py
"""
Shared utility functions for the Log-Os project.
"""
from .types import Symbol

def lisp_str(exp) -> str:
    """
    Converts a Python object back into a LISP-readable string.
    Symbols are unquoted, strings are double-quoted.
    """
    if isinstance(exp, list):
        return '(' + ' '.join(map(lisp_str, exp)) + ')'
    elif exp is True:
        return '#t'
    elif exp is False:
        return '#f'
    elif isinstance(exp, Symbol):
        return exp
    elif isinstance(exp, str):
        return f'"{exp}"'
    else:
        return str(exp)