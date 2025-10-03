# core/parser.py
"""
The parser is responsible for turning a string of Log-Os source code
into its Abstract Syntax Tree (AST). Because Log-Os is a LISP, the AST
is simply a nested list of Python objects.
"""

from .errors import LogosSyntaxError
from .types import Symbol

def parse(source_code: str):
    """
    Parses a string containing Log-Os S-expressions into a Python list.
    Example: "(add 1 (mul 2 3))" -> ['add', 1, ['mul', 2, 3]]
    """
    # 1. Remove comments (anything after a semicolon)
    source_code = '\n'.join(line.split(';', 1)[0] for line in source_code.splitlines())

    # 2. Add spaces around parentheses and quotes for easier tokenization
    source_code = source_code.replace('(', ' ( ').replace(')', ' ) ').replace("'", " ' ")
    tokens = source_code.split()
    if not tokens:
        # This can happen if the source is only comments
        return []

    # 2. Read tokens recursively
    ast, _ = read_from_tokens(tokens)
    return ast

def read_from_tokens(tokens: list):
    """Recursively reads tokens to build the nested list structure."""
    if len(tokens) == 0:
        raise LogosSyntaxError("Unexpected EOF while reading.")

    token = tokens.pop(0)
    if token == "'":
        return [Symbol('quote'), read_from_tokens(tokens)[0]], 2
    elif token == '(':
        nested_list = []
        while tokens and tokens[0] != ')':
            sub_ast, _ = read_from_tokens(tokens)
            nested_list.append(sub_ast)

        if not tokens:
            raise LogosSyntaxError("Unexpected EOF: missing ')'")

        tokens.pop(0)  # Pop off ')'
        return nested_list, len(nested_list)
    elif token == ')':
        raise LogosSyntaxError("Unexpected ')'")
    else:
        return atom(token), 1

def atom(token: str):
    """
    Converts a token to its appropriate Python type.
    Handles integers, floats, booleans (#t/#f), strings, and Symbols.
    """
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]  # Return as a string literal
    if token == '#t':
        return True
    if token == '#f':
        return False
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)  # Return as a Symbol