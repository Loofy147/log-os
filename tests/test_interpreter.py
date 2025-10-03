# tests/test_interpreter.py

import pytest
from core.parser import parse
from core.interpreter import evaluate
from core.environment import create_global_env
from core.errors import LogosEvaluationError
from core.types import Symbol


@pytest.fixture
def global_env():
    return create_global_env()

def test_eval_number(global_env):
    assert evaluate(parse("42")[0], global_env) == 42

def test_eval_simple_procedure(global_env):
    assert evaluate(parse("(+ 2 3)")[0], global_env) == 5
    assert evaluate(parse("(- 10 4)")[0], global_env) == 6

def test_eval_nested_procedure(global_env):
    assert evaluate(parse("(* (+ 2 3) 4)")[0], global_env) == 20

def test_eval_defvar(global_env):
    evaluate(parse("(defvar x 10)")[0], global_env)
    assert Symbol('x') in global_env
    assert global_env[Symbol('x')] == 10
    assert evaluate(parse("(+ x 5)")[0], global_env) == 15

def test_eval_if_true(global_env):
    assert evaluate(parse("(if (> 5 3) 1 2)")[0], global_env) == 1

def test_eval_if_false(global_env):
    assert evaluate(parse("(if (< 5 3) 1 2)")[0], global_env) == 2

def test_eval_if_with_booleans(global_env):
    assert evaluate(parse("(if #t 1 2)")[0], global_env) == 1
    assert evaluate(parse("(if #f 1 2)")[0], global_env) == 2

def test_eval_let_form(global_env):
    # Test single binding
    assert evaluate(parse("(let ((x 10)) (+ x 5))")[0], global_env) == 15
    # Test multiple bindings
    assert evaluate(parse("(let ((x 10) (y 20)) (+ x y))")[0], global_env) == 30
    # Test that let creates a new scope and doesn't pollute the parent
    evaluate(parse("(let ((z 100)) z)")[0], global_env)
    with pytest.raises(LogosEvaluationError):
        evaluate(parse("z")[0], global_env)

def test_eval_lambda_and_defun(global_env):
    evaluate(parse("(defun square (r) (* r r))")[0], global_env)
    assert evaluate(parse("(square 3)")[0], global_env) == 9

def test_eval_undefined_symbol(global_env):
    with pytest.raises(LogosEvaluationError):
        evaluate(parse("undefined_symbol")[0], global_env)

def test_eval_load(global_env):
    # The 'load_sample.l0' file defines 'loaded-var' and 'loaded-func'
    evaluate(parse('(load "tests/load_sample.l0")')[0], global_env)
    # Check that the variable is defined
    assert evaluate(parse("loaded-var")[0], global_env) == 42
    # Check that the function is defined and works
    assert evaluate(parse("(loaded-func 10)")[0], global_env) == 20

def test_eval_list_directory(global_env):
    # Check that list-directory returns a list of symbols for a known directory
    file_list = evaluate(parse('(list-directory "core")')[0], global_env)
    assert isinstance(file_list, list)
    assert Symbol('interpreter.py') in file_list
    assert Symbol('parser.py') in file_list

def test_eval_hash_map(global_env):
    # Create a hash-map
    evaluate(parse('(defvar my-map (hash-map "key1" 100 \'key2 #t))')[0], global_env)
    # Test getting values
    assert evaluate(parse('(hash-get my-map "key1")')[0], global_env) == 100
    assert evaluate(parse('(hash-get my-map \'key2)')[0], global_env) is True
    assert evaluate(parse('(hash-get my-map "non-existent")')[0], global_env) is None
    # Test setting a value
    evaluate(parse('(hash-set! my-map "key1" 200)')[0], global_env)
    assert evaluate(parse('(hash-get my-map "key1")')[0], global_env) == 200
    # Test setting a new key
    evaluate(parse('(hash-set! my-map \'new-key "new-value")')[0], global_env)
    assert evaluate(parse('(hash-get my-map \'new-key)')[0], global_env) == "new-value"

def test_eval_utility_functions(global_env):
    # Test member?
    assert evaluate(parse("(member? 2 '(1 2 3))")[0], global_env) is True
    assert evaluate(parse("(member? 4 '(1 2 3))")[0], global_env) is False

    # Test filter
    evaluate(parse("(defun greater-than-3 (n) (> n 3))")[0], global_env)
    assert evaluate(parse("(filter greater-than-3 '(1 2 3 4 5))")[0], global_env) == [4, 5]

    # Test ends-with?
    assert evaluate(parse('(ends-with? "hello.l0" ".l0")')[0], global_env) is True
    assert evaluate(parse('(ends-with? "hello.py" ".l0")')[0], global_env) is False

def test_eval_logical_operators(global_env):
    # Test 'and'
    assert evaluate(parse("(and #t #t)")[0], global_env) is True
    assert evaluate(parse("(and #t #f)")[0], global_env) is False
    assert evaluate(parse("(and #f (undefined-symbol))")[0], global_env) is False # short-circuit

    # Test 'or'
    assert evaluate(parse("(or #f #f)")[0], global_env) is False
    assert evaluate(parse("(or #t #f)")[0], global_env) is True
    assert evaluate(parse("(or #t (undefined-symbol))")[0], global_env) is True # short-circuit

def test_eval_while_loop(global_env):
    evaluate(parse("(defvar i 0)")[0], global_env)
    evaluate(parse("(while (< i 5) (set! i (+ i 1)))")[0], global_env)
    assert evaluate(parse("i")[0], global_env) == 5