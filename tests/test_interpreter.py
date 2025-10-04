# tests/test_interpreter.py

import pytest
from core.parser import parse
from core.errors import LogosEvaluationError, LogosAssertionError
from core.types import Symbol


def test_eval_number(bootstrapped_env):
    interpreter, env = bootstrapped_env
    assert interpreter.evaluate(parse("42"), env) == 42

def test_eval_simple_procedure(bootstrapped_env):
    interpreter, env = bootstrapped_env
    assert interpreter.evaluate(parse("(+ 2 3)"), env) == 5
    assert interpreter.evaluate(parse("(- 10 4)"), env) == 6

def test_eval_nested_procedure(bootstrapped_env):
    interpreter, env = bootstrapped_env
    assert interpreter.evaluate(parse("(* (+ 2 3) 4)"), env) == 20

def test_eval_defvar(bootstrapped_env):
    interpreter, env = bootstrapped_env
    interpreter.evaluate(parse("(defvar x 10)"), env)
    assert Symbol('x') in env
    assert env[Symbol('x')] == 10
    assert interpreter.evaluate(parse("(+ x 5)"), env) == 15

def test_eval_if_true(bootstrapped_env):
    interpreter, env = bootstrapped_env
    assert interpreter.evaluate(parse("(if (> 5 3) 1 2)"), env) == 1

def test_eval_if_false(bootstrapped_env):
    interpreter, env = bootstrapped_env
    assert interpreter.evaluate(parse("(if (< 5 3) 1 2)"), env) == 2

def test_eval_if_with_booleans(bootstrapped_env):
    interpreter, env = bootstrapped_env
    assert interpreter.evaluate(parse("(if #t 1 2)"), env) == 1
    assert interpreter.evaluate(parse("(if #f 1 2)"), env) == 2

def test_eval_let_form(bootstrapped_env):
    interpreter, env = bootstrapped_env
    # Test single binding
    assert interpreter.evaluate(parse("(let ((x 10)) (+ x 5))"), env) == 15
    # Test multiple bindings
    assert interpreter.evaluate(parse("(let ((x 10) (y 20)) (+ x y))"), env) == 30
    # Test that let creates a new scope and doesn't pollute the parent
    interpreter.evaluate(parse("(let ((z 100)) z)"), env)
    with pytest.raises(LogosEvaluationError):
        interpreter.evaluate(parse("z"), env)

def test_eval_lambda_and_defun(bootstrapped_env):
    interpreter, env = bootstrapped_env
    interpreter.evaluate(parse("(defun square (r) (* r r))"), env)
    assert interpreter.evaluate(parse("(square 3)"), env) == 9

def test_eval_undefined_symbol(bootstrapped_env):
    interpreter, env = bootstrapped_env
    with pytest.raises(LogosEvaluationError):
        interpreter.evaluate(parse("undefined_symbol"), env)

def test_eval_load(bootstrapped_env):
    interpreter, env = bootstrapped_env
    # The 'load_sample.l0' file defines 'loaded-var' and 'loaded-func'
    interpreter.evaluate(parse('(load "tests/load_sample.l0")'), env)
    # Check that the variable is defined
    assert interpreter.evaluate(parse("loaded-var"), env) == 42
    # Check that the function is defined and works
    assert interpreter.evaluate(parse("(loaded-func 10)"), env) == 20

def test_eval_list_directory(bootstrapped_env):
    interpreter, env = bootstrapped_env
    # Check that list-directory returns a list of symbols for a known directory
    file_list = interpreter.evaluate(parse('(list-directory "core")'), env)
    assert isinstance(file_list, list)
    assert Symbol('interpreter.py') in file_list
    assert Symbol('parser.py') in file_list

def test_eval_hash_map(bootstrapped_env):
    interpreter, env = bootstrapped_env
    # Create a hash-map
    interpreter.evaluate(parse('(defvar my-map (hash-map "key1" 100 \'key2 #t))'), env)
    # Test getting values
    assert interpreter.evaluate(parse('(hash-get my-map "key1")'), env) == 100
    assert interpreter.evaluate(parse('(hash-get my-map \'key2)'), env) is True
    assert interpreter.evaluate(parse('(hash-get my-map "non-existent")'), env) is None
    # Test setting a value
    interpreter.evaluate(parse('(hash-set! my-map "key1" 200)'), env)
    assert interpreter.evaluate(parse('(hash-get my-map "key1")'), env) == 200
    # Test setting a new key
    interpreter.evaluate(parse('(hash-set! my-map \'new-key "new-value")'), env)
    assert interpreter.evaluate(parse('(hash-get my-map \'new-key)'), env) == "new-value"

def test_eval_utility_functions(bootstrapped_env):
    interpreter, env = bootstrapped_env
    # Test member?
    assert interpreter.evaluate(parse("(member? 2 '(1 2 3))"), env) is True
    assert interpreter.evaluate(parse("(member? 4 '(1 2 3))"), env) is False

    # Test filter
    interpreter.evaluate(parse("(defun greater-than-3 (n) (> n 3))"), env)
    assert interpreter.evaluate(parse("(filter greater-than-3 '(1 2 3 4 5))"), env) == [4, 5]

    # Test ends-with?
    assert interpreter.evaluate(parse('(ends-with? "hello.l0" ".l0")'), env) is True
    assert interpreter.evaluate(parse('(ends-with? "hello.py" ".l0")'), env) is False

def test_eval_logical_operators(bootstrapped_env):
    interpreter, env = bootstrapped_env
    # Test 'and'
    assert interpreter.evaluate(parse("(and #t #t)"), env) is True
    assert interpreter.evaluate(parse("(and #t #f)"), env) is False
    assert interpreter.evaluate(parse("(and #f (undefined-symbol))"), env) is False # short-circuit

    # Test 'or'
    assert interpreter.evaluate(parse("(or #f #f)"), env) is False
    assert interpreter.evaluate(parse("(or #t #f)"), env) is True
    assert interpreter.evaluate(parse("(or #t (undefined-symbol))"), env) is True # short-circuit


# --- NEW TESTS FOR CORE ENHANCEMENTS ---

def test_eval_modulo_operator(bootstrapped_env):
    interpreter, env = bootstrapped_env
    """Tests the new % (modulo) operator."""
    assert interpreter.evaluate(parse("(% 10 3)"), env) == 1
    assert interpreter.evaluate(parse("(% 7 7)"), env) == 0

def test_eval_error_function(bootstrapped_env):
    interpreter, env = bootstrapped_env
    """Tests the (error ...) built-in function."""
    with pytest.raises(LogosEvaluationError, match="This is a test error"):
        interpreter.evaluate(parse('(error "This is a test error")'), env)

def test_eval_assert_equal(bootstrapped_env):
    interpreter, env = bootstrapped_env
    """Tests the (assert-equal ...) built-in function."""
    # Success case
    assert interpreter.evaluate(parse("(assert-equal (+ 5 5) 10)"), env) is True
    assert interpreter.evaluate(parse("(assert-equal '() '())"), env) is True

    # Failure case
    with pytest.raises(LogosAssertionError, match="Assertion Failed: Expected 6, but got 5"):
        interpreter.evaluate(parse("(assert-equal 5 6)"), env)

    with pytest.raises(LogosAssertionError, match=r"Assertion Failed: Expected \[1, 2, 4\], but got \[1, 2, 3\]"):
        interpreter.evaluate(parse("(assert-equal '(1 2 3) '(1 2 4))"), env)

def test_eval_variadic_function(bootstrapped_env):
    interpreter, env = bootstrapped_env
    """Tests variadic function definition and invocation."""
    # Define a function that captures the rest of the arguments
    defun_source = "(defun my-func (a b . rest) rest)"
    interpreter.evaluate(parse(defun_source), env)

    # Call with more than the fixed number of arguments
    call_source_1 = "(my-func 1 2 3 4 5)"
    result_1 = interpreter.evaluate(parse(call_source_1), env)
    assert result_1 == [3, 4, 5]

    # Call with exactly the fixed number of arguments
    call_source_2 = "(my-func 1 2)"
    result_2 = interpreter.evaluate(parse(call_source_2), env)
    assert result_2 == []

    # Test error on too few arguments
    with pytest.raises(LogosEvaluationError, match="Procedure expects at least 2 arguments, got 1"):
        interpreter.evaluate(parse("(my-func 1)"), env)