import pytest
from core.environment import create_global_env
from core.interpreter import evaluate
from core.parser import parse_stream
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
        with open("kernel.l0") as f:
            kernel_source = f.read()

        asts = parse_stream(kernel_source)
        for ast in asts:
            evaluate(ast, env)

    except FileNotFoundError:
        # This allows tests to run even if the kernel is not yet created
        print("\nWarning: kernel.l0 not found for testing. Some tests may fail.")
    except LogosError as e:
        pytest.fail(f"FATAL: Error loading kernel.l0 during test setup: {e}")

    return env