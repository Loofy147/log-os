import pytest
from core.environment import create_global_env
from core.interpreter import evaluate
from core.parser import parse
from core.errors import LogosError

@pytest.fixture(scope="function")
def global_env():
    """
    Provides a global environment with the kernel pre-loaded.
    This fixture ensures that macros like 'let' and 'cond' are available
    for tests that need them.
    """
    env = create_global_env()

    # Load the kernel to make macros available for testing
    try:
        # We use parse and evaluate on a 'load' expression, just like the REPL.
        evaluate(parse('(load "kernel.l0")'), env)

    except FileNotFoundError:
        pytest.fail("FATAL: kernel.l0 not found during test setup. The kernel is required for tests to run.")
    except LogosError as e:
        pytest.fail(f"FATAL: Error loading kernel.l0 during test setup: {e}")

    return env