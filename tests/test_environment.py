# tests/test_environment.py

import pytest
from core.environment import Environment, create_global_env
from core.errors import LogosEvaluationError
from core.types import Symbol

def test_env_creation():
    env = Environment(params=[Symbol('x'), Symbol('y')], args=[1, 2])
    assert env[Symbol('x')] == 1
    assert env[Symbol('y')] == 2

def test_env_find_local():
    env = Environment(params=[Symbol('x')], args=[10])
    found_env = env.find(Symbol('x'))
    assert found_env is env
    assert found_env[Symbol('x')] == 10

def test_env_find_outer():
    outer_env = Environment(params=[Symbol('x')], args=[10])
    inner_env = Environment(outer=outer_env)
    found_env = inner_env.find(Symbol('x'))
    assert found_env is outer_env
    assert found_env[Symbol('x')] == 10

def test_env_find_not_found():
    env = Environment()
    with pytest.raises(NameError):
        env.find(Symbol('non_existent_var'))

def test_create_global_env():
    global_env = create_global_env()
    assert Symbol('+') in global_env
    assert Symbol('car') in global_env
    assert Symbol('pi') in global_env
    # Check if a function works
    assert global_env[Symbol('+')](2, 3) == 5