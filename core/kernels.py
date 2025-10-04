# core/kernels.py
"""
Evaluation Kernels for the Log-Os interpreter.

This module defines the Pluggable Evaluator Architecture. The central
idea is to replace a single, monolithic `evaluate` function with a
family of "kernel" objects, each representing a different evaluation
strategy. The interpreter can then switch between these kernels
dynamically, even under the control of the Log-Os program itself.
"""
from abc import ABC, abstractmethod

from .types import Symbol, List, Procedure
from .errors import LogosEvaluationError, LogosError
from .environment import Environment


class EvaluationKernel(ABC):
    """Abstract base class for all evaluation strategies."""

    def __init__(self, interpreter):
        self.interpreter = interpreter

    @abstractmethod
    def evaluate(self, x, env):
        """Evaluates an expression 'x' in a given environment 'env'."""
        pass


class BaselineKernel(EvaluationKernel):
    """
    The standard, recursive evaluation strategy. It does not provide
    tail-call optimization, but is simple, correct, and extensible.
    """
    def evaluate(self, x, env: Environment):
        if isinstance(x, Symbol):
            try:
                return env.find(x)[x]
            except NameError:
                raise LogosEvaluationError(f"Symbol '{x}' not found.")

        elif not isinstance(x, List):
            return x

        if not x:
            return []

        op, *args = x

        if op == 'quote':
            return args[0]

        if op == 'quasiquote':
            return self.interpreter.expand_quasiquote(args[0], env, level=1)

        if op == 'if':
            test_expr, conseq_expr, *alt_expr = args
            alt = alt_expr[0] if alt_expr else None
            return self.evaluate(conseq_expr, env) if self.evaluate(test_expr, env) else self.evaluate(alt, env)

        if op == 'defvar':
            (symbol, expr) = args
            value = self.evaluate(expr, env)
            global_env = env
            while global_env.outer:
                global_env = global_env.outer
            global_env[symbol] = value
            return value

        if op == 'defmacro':
            (name, params, *body) = args
            body_expr = body[0] if len(body) == 1 else [Symbol('begin')] + body
            env.macros[name] = {'params': params, 'body': body_expr}
            return None

        if op == 'set!':
            (symbol, expr) = args
            value = self.evaluate(expr, env)
            env.find(symbol)[symbol] = value
            return value

        if op == 'defun':
            (name, params, *body) = args
            body_expr = body[0] if len(body) == 1 else [Symbol('begin')] + body
            lambda_expr = [Symbol('lambda'), params, body_expr]
            return self.evaluate([Symbol('defvar'), name, lambda_expr], env)

        if op == 'push-kernel!':
            (kernel_expr,) = args
            kernel = self.evaluate(kernel_expr, env)
            if not isinstance(kernel, EvaluationKernel):
                raise LogosEvaluationError(f"push-kernel!: expected a kernel object, but got {type(kernel)}")
            self.interpreter.kernel_stack.append(kernel)
            return None

        if op == 'pop-kernel!':
            if len(self.interpreter.kernel_stack) <= 1:
                raise LogosEvaluationError("pop-kernel!: cannot pop the last kernel from the stack.")
            return self.interpreter.kernel_stack.pop()

        if op == 'lambda':
            (params, *body) = args
            body_expr = body[0] if len(body) == 1 else [Symbol('begin')] + body
            return Procedure(params, body_expr, env)

        if op == 'begin':
            result = None
            for expr in args:
                result = self.evaluate(expr, env)
            return result

        if op == 'try':
            try_expr, catch_clause = args
            if not isinstance(catch_clause, List) or not catch_clause or catch_clause[0] != Symbol('catch'):
                raise LogosEvaluationError("try form must be followed by a (catch err-var . body) clause.")
            _catch_op, err_var, *catch_body = catch_clause
            if not isinstance(err_var, Symbol):
                 raise LogosEvaluationError(f"catch variable must be a symbol, but got {type(err_var)}")
            try:
                return self.evaluate(try_expr, env)
            except LogosError as e:
                catch_env = Environment(outer=env)
                catch_env[err_var] = str(e)
                catch_body_expr = catch_body[0] if len(catch_body) == 1 else [Symbol('begin')] + catch_body
                return self.evaluate(catch_body_expr, catch_env)

        if op == 'and' or op == 'or':
            result = True if op == 'and' else False
            for expr in args:
                val = self.evaluate(expr, env)
                if op == 'and' and not val:
                    return False
                if op == 'or' and val:
                    return True
                result = val
            return result

        if op == 'load':
            filepath = self.evaluate(args[0], env)
            with open(filepath) as f:
                source = f.read()
            from .parser import parse_stream
            asts = parse_stream(source)
            result = None
            for ast in asts:
                result = self.evaluate(ast, env)
            return result

        if op == 'hash-map':
            hash_map = {}
            for i in range(0, len(args), 2):
                key = self.evaluate(args[i], env)
                value = self.evaluate(args[i+1], env)
                hash_map[key] = value
            return hash_map

        # --- Macro and Procedure Calls ---
        if isinstance(op, Symbol):
            macro_def_env = env.find_macro(op)
            if macro_def_env:
                macro = macro_def_env.macros[op]
                expansion_env = Environment(params=macro['params'], args=args, outer=env)
                expanded_ast = self.evaluate(macro['body'], expansion_env)
                return self.evaluate(expanded_ast, env)

        proc = self.evaluate(op, env)
        evaluated_args = [self.evaluate(arg, env) for arg in args]

        if isinstance(proc, Procedure):
            return self.evaluate(proc.body, Environment(proc.params, evaluated_args, proc.env))
        elif callable(proc):
            try:
                return proc(*evaluated_args)
            except TypeError as e:
                raise LogosEvaluationError(f"Error calling primitive '{op}': {e}")
        else:
            raise LogosEvaluationError(f"The expression '{x}' is not a valid function call.")


class CachingKernel(BaselineKernel):
    """
    An evaluation kernel that inherits from BaselineKernel and adds a
    memoization layer. It is specifically designed to cache the results of
    function calls, not special forms.
    """
    def __init__(self, interpreter):
        super().__init__(interpreter)
        self.cache = {}
        self.special_forms = {
            'quote', 'quasiquote', 'if', 'defvar', 'defmacro', 'set!', 'defun',
            'lambda', 'begin', 'try', 'load', 'push-kernel!', 'pop-kernel!'
        }

    def evaluate(self, x, env):
        if not isinstance(x, list) or not x or x[0] in self.special_forms:
            return super().evaluate(x, env)

        from .utils import lisp_str
        try:
            key = lisp_str(x)
        except Exception:
            return super().evaluate(x, env)

        if key in self.cache:
            return self.cache[key]

        result = super().evaluate(x, env)
        self.cache[key] = result
        return result