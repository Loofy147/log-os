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
    Parses a string of Log-Os source code into a list of expressions.
    """
    # 1. Remove comments
    source_code = '\n'.join(line.split(';', 1)[0] for line in source_code.splitlines())

    # 2. Tokenize
    source_code = source_code.replace('(', ' ( ').replace(')', ' ) ').replace("'", " ' ")
    tokens = source_code.split()

    # 3. Read all expressions from the token stream
    expressions = []
    while tokens:
        expressions.append(read_from_tokens(tokens))

    return expressions

def read_from_tokens(tokens: list):
    """
    Recursively reads an expression from a list of tokens.
    This is a robust, purely recursive implementation.
    """
    if not tokens:
        raise LogosSyntaxError("Unexpected EOF while reading tokens.")

    token = tokens.pop(0)

    if token == "'":
        return [Symbol('quote'), read_from_tokens(tokens)]
    elif token == '(':
        L = []
        while tokens[0] != ')':
            L.append(read_from_tokens(tokens))
            if not tokens:
                raise LogosSyntaxError("Unexpected EOF: missing ')'")
        tokens.pop(0)  # Pop off the closing ')'
        return L
    elif token == ')':
        raise LogosSyntaxError("Unexpected ')' encountered.")
    else:
        return atom(token)

def atom(token: str):
    """
    Converts a token to its appropriate Python type.
    Handles strings, booleans, integers, floats, and Symbols.
    """
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]
    elif token == '#t':
        return True
    elif token == '#f':
        return False
    else:
        try:
            return int(token)
        except ValueError:
            try:
                return float(token)
            except ValueError:
                return Symbol(token)