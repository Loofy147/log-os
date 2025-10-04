# core/interpreter.py
"""
The evaluator, or interpreter, is the heart of Log-Os. It takes an
AST (Abstract Syntax Tree) and an environment, and computes the result
of the expression. This file defines the main Interpreter class that
dispatches evaluation to different "kernels".
"""

from .types import Symbol, List
from .environment import Environment
from .errors import LogosEvaluationError, LogosError
from .kernels import BaselineKernel, CachingKernel


class Interpreter:
    def __init__(self):
        self.baseline_kernel = BaselineKernel(self)
        self.caching_kernel = CachingKernel(self)

        self.kernels = {
            Symbol('baseline'): self.baseline_kernel,
            Symbol('caching'): self.caching_kernel,
        }

        # The stack of active kernels. Evaluation always uses the top kernel.
        self.kernel_stack = [self.baseline_kernel]

    def evaluate_stream(self, asts, env):
        """Evaluates a stream of ASTs, returning the result of the last one."""
        result = None
        for ast in asts:
            result = self.evaluate(ast, env)
        return result

    def evaluate(self, x, env: Environment):
        """
        The main entry point for evaluation. It dispatches to the kernel
        currently at the top of the kernel_stack.
        """
        active_kernel = self.kernel_stack[-1]
        return active_kernel.evaluate(x, env)

    def expand_quasiquote(self, x, env, level):
        """
        Recursively expands a quasiquoted expression, handling nesting levels
        of unquote and unquote-splicing.
        """
        if not isinstance(x, List) or not x:
            return x

        op, *rest = x

        if op == Symbol('quasiquote'):
            return [Symbol('quasiquote')] + [self.expand_quasiquote(rest[0], env, level + 1)]

        if op == Symbol('unquote') or op == Symbol('unquote-splicing'):
            if level == 1:
                result = self.evaluate(rest[0], env)
                if op == Symbol('unquote-splicing'):
                    if not isinstance(result, List):
                        raise LogosEvaluationError("unquote-splicing must be used with a list.")
                    return [Symbol.SPLICE] + result
                return result
            else:
                return [op] + [self.expand_quasiquote(rest[0], env, level - 1)]

        processed_list = []
        for item in x:
            result = self.expand_quasiquote(item, env, level)
            if isinstance(result, List) and result and result[0] is Symbol.SPLICE:
                processed_list.extend(result[1:])
            else:
                processed_list.append(result)
        return processed_list