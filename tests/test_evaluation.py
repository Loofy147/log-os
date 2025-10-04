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
    Provides a LISP evaluation function and its corresponding environment.
    The environment is pre-loaded with kernel.l0 and all the Synapse libraries.
    """
    env = create_global_env(evaluate)

    # Define an evaluation function that uses this specific environment
    def evaluator(ast):
        return evaluate(ast, env)

    # Load kernel and all necessary Synapse project files
    for filepath in ["kernel.l0", "stdlib/telemetry.l0", "stdlib/cost-model.l0", "stdlib/tuning.l0", "core/lisp/aware-evaluator.l0"]:
        with open(filepath, 'r') as f:
            source = f.read()
            asts = parse_stream(source)
            for ast in asts:
                evaluator(ast)

    return evaluator, env

def test_synapse_adaptive_behavior_directly(lisp_eval_env):
    """
    Tests the Project Synapse feedback loop by directly calling LISP functions from Python.
    This bypasses complex LISP script execution, targeting the core logic instead.
    """
    lisp_eval, env = lisp_eval_env

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