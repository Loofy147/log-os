import pytest
from core.environment import create_global_env
from core.interpreter import evaluate
from core.parser import parse, parse_stream
from core.errors import LogosError

@pytest.fixture(scope="function")
def global_env():
    """
    Provides a global environment with the kernel pre-loaded.
    This fixture ensures that macros like 'let' and 'cond' are available
    for tests that need them.
    """
    # The 'evaluate' function is now passed to create the environment
    # to break a circular dependency.
    env = create_global_env(evaluate)

    # Load the kernel to make macros available for testing
    try:
        with open("kernel.l0") as f:
            source = f.read()
        asts = parse_stream(source)
        for ast in asts:
            evaluate(ast, env)

    except FileNotFoundError:
        pytest.fail("FATAL: kernel.l0 not found during test setup. The kernel is required for tests to run.")
    except LogosError as e:
        pytest.fail(f"FATAL: Error loading kernel.l0 during test setup: {e}")

    return env