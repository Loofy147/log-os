# tests/test_parser.py

import pytest
from core.parser import parse
from core.types import Symbol
from core.errors import LogosSyntaxError

def test_parse_simple_expression():
    source = "(add 1 2)"
    expected_ast = [Symbol('add'), 1, 2]
    assert parse(source) == expected_ast

def test_parse_nested_expression():
    source = "(mul (add 1 2) 3)"
    expected_ast = [Symbol('mul'), [Symbol('add'), 1, 2], 3]
    assert parse(source) == expected_ast

def test_parse_with_floats():
    source = "(+ 1.5 2.5)"
    expected_ast = [Symbol('+'), 1.5, 2.5]
    assert parse(source) == expected_ast

def test_parse_booleans():
    source = "(if #t #f #t)"
    expected_ast = [Symbol('if'), True, False, True]
    assert parse(source) == expected_ast

def test_parse_empty_list():
    source = "()"
    expected_ast = []
    assert parse(source) == expected_ast

def test_parse_multiple_expressions_fails():
    # The new parser should only handle one top-level expression
    source = "(add 1 2) (mul 3 4)"
    with pytest.raises(LogosSyntaxError):
        parse(source)

def test_parse_syntax_error_unexpected_paren():
    with pytest.raises(LogosSyntaxError):
        parse(")")

def test_parse_syntax_error_unclosed_paren():
    with pytest.raises(LogosSyntaxError):
        parse("(add 1 2")