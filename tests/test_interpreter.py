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