# core/parser.py
"""
The parser is responsible for turning a string of Log-Os source code
into its Abstract Syntax Tree (AST). Because Log-Os is a LISP, the AST
is simply a nested list of Python objects.
"""

import re
from .errors import LogosSyntaxError
from .types import Symbol

def tokenize(source_code: str) -> list:
    """
    Splits the source code into a list of tokens using a robust regex.
    """
    source_code = '\n'.join(line.split(';', 1)[0] for line in source_code.splitlines())
    # The regex now includes support for `,@`, ` ` `, and `,`
    token_regex = r',@|"[^"]*"|\'|`|,|\(|\)|#t|#f|[^\s\(\)]+'
    return re.findall(token_regex, source_code)

def parse(source_code: str):
    """
    Parses a string of Log-Os source code into a single expression (AST).
    """
    tokens = tokenize(source_code)
    if not tokens:
        raise LogosSyntaxError("Source code is empty or contains only comments.")

    ast = read_from_tokens(tokens)
    if tokens:
        raise LogosSyntaxError(f"Unexpected tokens after main expression: {tokens}")
    return ast

def read_from_tokens(tokens: list):
    """
    Recursively reads an expression from a list of tokens.
    """
    if not tokens:
        raise LogosSyntaxError("Unexpected EOF while reading tokens.")

    token = tokens.pop(0)

    if token == "'":
        return [Symbol('quote'), read_from_tokens(tokens)]
    elif token == '`':
        return [Symbol('quasiquote'), read_from_tokens(tokens)]
    elif token == ',':
        return [Symbol('unquote'), read_from_tokens(tokens)]
    elif token == ',@':
        return [Symbol('unquote-splicing'), read_from_tokens(tokens)]
    elif token == '(':
        L = []
        while tokens and tokens[0] != ')':
            L.append(read_from_tokens(tokens))

        if not tokens:
            raise LogosSyntaxError("Unexpected EOF: missing ')'")

        tokens.pop(0)  # Pop off the closing ')'
        return L
    elif token == ')':
        raise LogosSyntaxError("Unexpected ')' encountered.")
    else:
        return atom(token)

def parse_stream(source_code: str) -> list:
    """
    Parses a string of Log-Os source code containing multiple expressions
    into a list of ASTs.
    """
    tokens = tokenize(source_code)
    if not tokens:
        return []

    asts = []
    while tokens:
        asts.append(read_from_tokens(tokens))
    return asts


def atom(token: str):
    """
    Converts a token to its appropriate Python type.
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