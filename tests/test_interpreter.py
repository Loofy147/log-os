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