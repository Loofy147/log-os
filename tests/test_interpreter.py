# tests/test_interpreter.py

import pytest
from core.parser import parse
from core.interpreter import evaluate
from core.environment import create_global_env
from core.errors import LogosEvaluationError, LogosAssertionError
from core.types import Symbol


def test_eval_number(global_env):
    assert evaluate(parse("42"), global_env) == 42

def test_eval_simple_procedure(global_env):
    assert evaluate(parse("(+ 2 3)"), global_env) == 5
    assert evaluate(parse("(- 10 4)"), global_env) == 6

def test_eval_nested_procedure(global_env):
    assert evaluate(parse("(* (+ 2 3) 4)"), global_env) == 20

def test_eval_defvar(global_env):
    evaluate(parse("(defvar x 10)"), global_env)
    assert Symbol('x') in global_env
    assert global_env[Symbol('x')] == 10
    assert evaluate(parse("(+ x 5)"), global_env) == 15

def test_eval_if_true(global_env):
    assert evaluate(parse("(if (> 5 3) 1 2)"), global_env) == 1

def test_eval_if_false(global_env):
    assert evaluate(parse("(if (< 5 3) 1 2)"), global_env) == 2

def test_eval_if_with_booleans(global_env):
    assert evaluate(parse("(if #t 1 2)"), global_env) == 1
    assert evaluate(parse("(if #f 1 2)"), global_env) == 2

def test_eval_let_form(global_env):
    # Test single binding
    assert evaluate(parse("(let ((x 10)) (+ x 5))"), global_env) == 15
    # Test multiple bindings
    assert evaluate(parse("(let ((x 10) (y 20)) (+ x y))"), global_env) == 30
    # Test that let creates a new scope and doesn't pollute the parent
    evaluate(parse("(let ((z 100)) z)"), global_env)
    with pytest.raises(LogosEvaluationError):
        evaluate(parse("z"), global_env)

def test_eval_lambda_and_defun(global_env):
    evaluate(parse("(defun square (r) (* r r))"), global_env)
    assert evaluate(parse("(square 3)"), global_env) == 9

def test_eval_undefined_symbol(global_env):
    with pytest.raises(LogosEvaluationError):
        evaluate(parse("undefined_symbol"), global_env)

def test_eval_load(global_env):
    # The 'load_sample.l0' file defines 'loaded-var' and 'loaded-func'
    evaluate(parse('(load "tests/load_sample.l0")'), global_env)
    # Check that the variable is defined
    assert evaluate(parse("loaded-var"), global_env) == 42
    # Check that the function is defined and works
    assert evaluate(parse("(loaded-func 10)"), global_env) == 20

def test_eval_list_directory(global_env):
    # Check that list-directory returns a list of symbols for a known directory
    file_list = evaluate(parse('(list-directory "core")'), global_env)
    assert isinstance(file_list, list)
    assert Symbol('interpreter.py') in file_list
    assert Symbol('parser.py') in file_list

def test_eval_hash_map(global_env):
    # Create a hash-map
    evaluate(parse('(defvar my-map (hash-map "key1" 100 \'key2 #t))'), global_env)
    # Test getting values
    assert evaluate(parse('(hash-get my-map "key1")'), global_env) == 100
    assert evaluate(parse('(hash-get my-map \'key2)'), global_env) is True
    assert evaluate(parse('(hash-get my-map "non-existent")'), global_env) is None
    # Test setting a value
    evaluate(parse('(hash-set! my-map "key1" 200)'), global_env)
    assert evaluate(parse('(hash-get my-map "key1")'), global_env) == 200
    # Test setting a new key
    evaluate(parse('(hash-set! my-map \'new-key "new-value")'), global_env)
    assert evaluate(parse('(hash-get my-map \'new-key)'), global_env) == "new-value"

def test_eval_utility_functions(global_env):
    # Test member?
    assert evaluate(parse("(member? 2 '(1 2 3))"), global_env) is True
    assert evaluate(parse("(member? 4 '(1 2 3))"), global_env) is False

    # Test filter
    evaluate(parse("(defun greater-than-3 (n) (> n 3))"), global_env)
    assert evaluate(parse("(filter greater-than-3 '(1 2 3 4 5))"), global_env) == [4, 5]

    # Test ends-with?
    assert evaluate(parse('(ends-with? "hello.l0" ".l0")'), global_env) is True
    assert evaluate(parse('(ends-with? "hello.py" ".l0")'), global_env) is False

def test_eval_logical_operators(global_env):
    # Test 'and'
    assert evaluate(parse("(and #t #t)"), global_env) is True
    assert evaluate(parse("(and #t #f)"), global_env) is False
    assert evaluate(parse("(and #f (undefined-symbol))"), global_env) is False # short-circuit

    # Test 'or'
    assert evaluate(parse("(or #f #f)"), global_env) is False
    assert evaluate(parse("(or #t #f)"), global_env) is True
    assert evaluate(parse("(or #t (undefined-symbol))"), global_env) is True # short-circuit


# --- NEW TESTS FOR CORE ENHANCEMENTS ---

def test_eval_modulo_operator(global_env):
    """Tests the new % (modulo) operator."""
    assert evaluate(parse("(% 10 3)"), global_env) == 1
    assert evaluate(parse("(% 7 7)"), global_env) == 0

def test_eval_error_function(global_env):
    """Tests the (error ...) built-in function."""
    with pytest.raises(LogosEvaluationError, match="This is a test error"):
        evaluate(parse('(error "This is a test error")'), global_env)

def test_eval_assert_equal(global_env):
    """Tests the (assert-equal ...) built-in function."""
    # Success case
    assert evaluate(parse("(assert-equal (+ 5 5) 10)"), global_env) is True
    assert evaluate(parse("(assert-equal '() '())"), global_env) is True

    # Failure case
    with pytest.raises(LogosAssertionError, match="Assertion Failed: Expected 6, but got 5"):
        evaluate(parse("(assert-equal 5 6)"), global_env)

    with pytest.raises(LogosAssertionError, match=r"Assertion Failed: Expected \[1, 2, 4\], but got \[1, 2, 3\]"):
        evaluate(parse("(assert-equal '(1 2 3) '(1 2 4))"), global_env)

def test_eval_variadic_function(global_env):
    """Tests variadic function definition and invocation."""
    # Define a function that captures the rest of the arguments
    defun_source = "(defun my-func (a b . rest) rest)"
    evaluate(parse(defun_source), global_env)

    # Call with more than the fixed number of arguments
    call_source_1 = "(my-func 1 2 3 4 5)"
    result_1 = evaluate(parse(call_source_1), global_env)
    assert result_1 == [3, 4, 5]

    # Call with exactly the fixed number of arguments
    call_source_2 = "(my-func 1 2)"
    result_2 = evaluate(parse(call_source_2), global_env)
    assert result_2 == []

    # Test error on too few arguments
    with pytest.raises(LogosEvaluationError, match="Procedure expects at least 2 arguments, got 1"):
        evaluate(parse("(my-func 1)"), global_env)

def test_eval_quasiquote(global_env):
    """Tests the quasiquote ` and unquote ,/@ operators."""
    # The parser converts numeric literals to numbers, so quasiquote should preserve them as such.

    # Simple quasiquote with numbers and symbols
    assert evaluate(parse("`(1 b 3)"), global_env) == [1, Symbol('b'), 3]

    # With unquote
    evaluate(parse("(defvar x 10)"), global_env)
    assert evaluate(parse("`(1 ,x 3)"), global_env) == [1, 10, 3]

    # With unquote-splicing
    evaluate(parse("(defvar y '(2 3))"), global_env)
    assert evaluate(parse("`(1 ,@y 4)"), global_env) == [1, 2, 3, 4]

    # Nested quasiquote - should produce a partially evaluated AST
    evaluate(parse("(defvar z 5)"), global_env)
    # `(a ,,z) should expand to `(a ,5) which is the AST (quasiquote (a (unquote 5)))
    expected_ast = [Symbol('quasiquote'), [Symbol('a'), [Symbol('unquote'), 5]]]
    assert evaluate(parse("``(a ,,z)"), global_env) == expected_ast

    # Error case for unquote-splicing a non-list
    with pytest.raises(LogosEvaluationError, match="unquote-splicing must be used with a list"):
        evaluate(parse("`(1 ,@x 4)"), global_env)

def test_eval_defmacro(global_env):
    """Tests the defmacro special form and macro expansion."""
    # Define an 'unless' macro: (unless condition body...)
    macro_source = """
    (defmacro unless (condition . body)
      `(if (not ,condition)
           (begin ,@body)))
    """
    evaluate(parse(macro_source), global_env)

    # Test case 1: Condition is false, body should execute.
    # (unless #f (defvar macro-test-1 100))
    # -> (if (not #f) (begin (defvar macro-test-1 100)))
    # -> (if #t (defvar macro-test-1 100)) -> 100
    evaluate(parse("(unless #f (defvar macro-test-1 100))"), global_env)
    assert evaluate(parse("macro-test-1"), global_env) == 100

    # Test case 2: Condition is true, body should not execute.
    # (unless #t (defvar macro-test-2 200))
    # -> (if (not #t) (begin (defvar macro-test-2 200)))
    # -> (if #f (defvar macro-test-2 200)) -> None
    evaluate(parse("(unless #t (defvar macro-test-2 200))"), global_env)
    with pytest.raises(LogosEvaluationError):
        evaluate(parse("macro-test-2"), global_env)