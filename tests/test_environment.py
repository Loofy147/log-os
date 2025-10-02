# tests/test_environment.py

import pytest
from core.environment import Environment, create_global_env
from core.errors import LogosEvaluationError

def test_env_creation():
    env = Environment(params=['x', 'y'], args=[1, 2])
    assert env['x'] == 1
    assert env['y'] == 2

def test_env_find_local():
    env = Environment(params=['x'], args=[10])
    found_env = env.find('x')
    assert found_env is env
    assert found_env['x'] == 10

def test_env_find_outer():
    outer_env = Environment(params=['x'], args=[10])
    inner_env = Environment(outer=outer_env)
    found_env = inner_env.find('x')
    assert found_env is outer_env
    assert found_env['x'] == 10

def test_env_find_not_found():
    env = Environment()
    with pytest.raises(NameError):
        env.find('non_existent_var')

def test_create_global_env():
    global_env = create_global_env()
    assert '+' in global_env
    assert 'car' in global_env
    assert 'pi' in global_env
    # Check if a function works
    assert global_env['+'](2, 3) == 5