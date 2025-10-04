import pytest
from core.interpreter import Interpreter
from core.environment import create_global_env
from core.parser import parse_stream
from core.errors import LogosError

@pytest.fixture(scope="function")
def bootstrapped_env():
    """
    Provides a tuple of (Interpreter, global_env) with the kernel pre-loaded.
    This fixture ensures that a fresh interpreter and a fully bootstrapped
    environment (with macros like 'let' and 'cond') are available for tests.
    """
    interpreter = Interpreter()
    env = create_global_env(interpreter)

    # Load the kernel to make macros available for testing
    try:
        with open("kernel.l0") as f:
            source = f.read()
        asts = parse_stream(source)
        interpreter.evaluate_stream(asts, env)

    except FileNotFoundError:
        pytest.fail("FATAL: kernel.l0 not found during test setup. The kernel is required for tests to run.")
    except LogosError as e:
        pytest.fail(f"FATAL: Error loading kernel.l0 during test setup: {e}")

    return interpreter, env