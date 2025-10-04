# tests/test_evaluation.py

import pytest
from core.interpreter import evaluate
from core.environment import create_global_env, _metrics, _metrics_lock, L0_CACHE
from core.parser import parse, parse_stream
from core.types import Symbol
import time

@pytest.fixture(autouse=True)
def test_setup_teardown():
    """
    Fixture to set up and tear down the environment for each test.
    It clears metrics, caches, and other global state to ensure test isolation.
    """
    with _metrics_lock:
        _metrics.clear()
    L0_CACHE.clear()
    # Resetting the environment for each test is crucial for isolation.
    yield

@pytest.fixture
def lisp_eval_env():
    """
    Provides a LISP evaluation function and its corresponding environment,
    with kernel.l0 pre-loaded.
    """
    env = create_global_env(evaluate)

    # Define an evaluation function that uses this specific environment
    def evaluator(ast):
        return evaluate(ast, env)

    # Load kernel, which is foundational for almost all LISP code.
    with open("kernel.l0", 'r') as f:
        source = f.read()
        asts = parse_stream(source)
        for ast in asts:
            evaluator(ast)

    return evaluator, env

def run_lisp_file(lisp_eval, filepath: str):
    """Helper function to load and evaluate a LISP file."""
    ast = parse(f'(load "{filepath}")')
    lisp_eval(ast)

def test_contracts_l0(lisp_eval_env):
    """Tests the contracts system by running the LISP test suite."""
    lisp_eval, env = lisp_eval_env
    run_lisp_file(lisp_eval, "tests/test_contracts.l0")

def test_multimethods_l0_success(lisp_eval_env):
    """Tests the multimethod system's success cases by running the LISP test file."""
    lisp_eval, env = lisp_eval_env
    run_lisp_file(lisp_eval, "tests/test_multimethods.l0")

def test_multimethods_l0_error_on_no_method(lisp_eval_env):
    """
    Tests that the multimethod dispatcher returns a special symbol
    when no method is found (workaround for interpreter bug).
    """
    lisp_eval, env = lisp_eval_env

    # Load the multimethods library and the test file which defines the 'report-type' multimethod.
    run_lisp_file(lisp_eval, "stdlib/multimethods.l0")
    run_lisp_file(lisp_eval, "tests/test_multimethods.l0")

    # Call 'report-type' with a boolean (for which no method is defined).
    result = lisp_eval(parse("(report-type #f)"))

    # Assert that the result is the special error symbol.
    assert result == Symbol('*%no-method-found%*')

def test_stdlib_l0(lisp_eval_env):
    """
    Tests the standard library's 'count' generic function by directly
    loading dependencies and calling the function from Python.
    """
    lisp_eval, env = lisp_eval_env

    # Load the new systems one by one to isolate any syntax errors.
    run_lisp_file(lisp_eval, "stdlib/contracts.l0")
    run_lisp_file(lisp_eval, "stdlib/multimethods.l0")
    # This is the file that defines 'count'.
    run_lisp_file(lisp_eval, "stdlib/collections.l0")

    # Get a handle to the LISP 'count' function.
    count_fn = lisp_eval(Symbol('count'))

    # Test 'count' with a list.
    assert count_fn([1, 2, 3]) == 3
    assert count_fn([]) == 0

    # Test 'count' with a hash-map.
    # Note: We need to use Symbol for keys if they are symbols in LISP.
    test_map = {Symbol('a'): 1, Symbol('b'): 2}
    assert count_fn(test_map) == 2
    assert count_fn({}) == 0

def test_synapse_adaptive_behavior_directly(lisp_eval_env):
    """
    Tests the Project Synapse feedback loop by directly calling LISP functions from Python.
    This bypasses complex LISP script execution, targeting the core logic instead.
    """
    lisp_eval, env = lisp_eval_env

    # Load Synapse-specific libraries
    for filepath in ["stdlib/telemetry.l0", "stdlib/cost-model.l0", "stdlib/tuning.l0", "core/lisp/aware-evaluator.l0"]:
         run_lisp_file(lisp_eval, filepath)

    # 1. --- Get handles to the LISP functions we need to call ---
    compose_evaluator_fn = lisp_eval(Symbol('compose-aware-evaluator'))
    update_threshold_fn = lisp_eval(Symbol('update-threshold!'))
    get_metric_stats_fn = lisp_eval(Symbol('get-metric-stats'))

    # 2. --- Compose the Aware Evaluator ---
    aware_evaluator = compose_evaluator_fn()

    # 3. --- Define the simulated workload in Python ---
    # This is the equivalent of the (heavy-work) LISP function
    def heavy_work_py():
        time.sleep(0.02)
        return 42

    # This is the equivalent of the 'heavy-task' AST hash-map
    heavy_task_ast = {
        Symbol('features'): {Symbol('id'): Symbol('heavy-work')},
        Symbol('fn'): heavy_work_py
    }

    # 4. --- First Run (Cold Start) ---
    # The cost model should use its default prediction, resulting in a 'baseline' run.
    aware_evaluator(heavy_task_ast, env)

    # Assert that the evaluation mode was 'baseline'
    with _metrics_lock:
        eval_modes = [m['value'] for m in _metrics.get('eval.mode', [])]
        assert eval_modes == ['baseline'], f"First run should be 'baseline', but got {eval_modes}"

    # 5. --- Tune the System ---
    # Lower the JIT threshold to make the evaluator more aggressive.
    update_threshold_fn(Symbol('jit-threshold'), 1.0)

    # 6. --- Second Run (Warm Start) ---
    # The cost model now has data from the first run and should predict a high cost.
    # This high prediction should cross the newly lowered threshold, triggering a 'jit' run.
    aware_evaluator(heavy_task_ast, env)

    # 7. --- Final Assertions ---
    # Check that the full sequence of evaluation modes is correct and that JIT was triggered.
    with _metrics_lock:
        eval_modes = [m['value'] for m in _metrics.get('eval.mode', [])]
        assert eval_modes == ['baseline', 'jit'], \
            f"Expected evaluation modes to be ['baseline', 'jit'], but got {eval_modes}"

        jit_compiles = _metrics.get('jit.compiled', [])
        assert len(jit_compiles) == 1, \
            f"Expected exactly one JIT compilation, but found {len(jit_compiles)}"
        assert jit_compiles[0]['value'] == 1