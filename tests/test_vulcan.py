# tests/test_vulcan.py
"""
Tests for Project Vulcan: The Pluggable Evaluator Architecture.

This test file is the entry point for verifying the self-hosted
evaluation foundry. It loads a Lisp file (`test_foundry.l0`) that
contains the actual test logic written in Log-Os itself.
"""

import pytest
from core.parser import parse

def test_evaluation_foundry(bootstrapped_env):
    """
    Runs the Lisp-based test suite for the evaluation foundry.
    """
    interpreter, env = bootstrapped_env

    # Load and evaluate the Lisp test file.
    # The assertions are performed within the Lisp code itself.
    # If any assertion fails, the `(error ...)` function will be called,
    # which raises a LogosEvaluationError, failing the test.
    result = interpreter.evaluate(parse('(load "tests/test_foundry.l0")'), env)

    # The test file should evaluate to #t on success.
    assert result is True