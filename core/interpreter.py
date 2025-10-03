# core/interpreter.py
"""
The evaluator, or interpreter, is the heart of Log-Os. It takes an
AST (Abstract Syntax Tree) and an environment, and computes the result
of the expression.
"""

from .types import Symbol, List
from .environment import Environment
from .errors import LogosEvaluationError

def evaluate(x, env: Environment):
    """
    Evaluates an expression in a given environment.
    """
    if isinstance(x, Symbol):
        # Variable reference
        try:
            return env.find(x)[x]
        except NameError:
            raise LogosEvaluationError(f"Symbol '{x}' not found.")

    elif not isinstance(x, List):
        # Constant literal (e.g., number)
        return x

    # At this point, x must be a List (S-expression)
    if not x:
        return [] # An empty list evaluates to itself

    op, *args = x

    # Special Forms (handle these before evaluating arguments)
    if op == 'quote':
        # (quote expression)
        return args[0]

    elif op == 'if':
        # (if test conseq alt)
        (test, conseq, alt) = args
        expr = (conseq if evaluate(test, env) else alt)
        return evaluate(expr, env)

    elif op == 'defvar':
        # (defvar symbol expr)
        (symbol, expr) = args
        env[symbol] = evaluate(expr, env)
        return env[symbol]

    elif op == 'set!':
        # (set! symbol expr)
        (symbol, expr) = args
        env.find(symbol)[symbol] = evaluate(expr, env)
        return env.find(symbol)[symbol]

    elif op == 'lambda':
        # (lambda (params...) body)
        (params, body) = args
        return lambda *arguments: evaluate(body, Environment(params, arguments, env))

    elif op == 'defun':
        # (defun name (params...) body) -- syntactic sugar for (defvar name (lambda ...))
        (name, params, body) = args
        env[name] = evaluate(['lambda', params, body], env)
        return env[name]

    elif op == 'let':
        # (let ((var val) ...) body) => ((lambda (vars...) body) vals...)
        (bindings, body) = args
        params = [b[0] for b in bindings]
        values = [b[1] for b in bindings]
        lambda_expr = ['lambda', params, body]
        eval_expr = [lambda_expr] + values
        return evaluate(eval_expr, env)

    else:
        # Procedure call
        proc = evaluate(op, env)
        if not callable(proc):
            raise LogosEvaluationError(f"'{op}' is not a procedure.")

        evaluated_args = [evaluate(arg, env) for arg in args]
        try:
            return proc(*evaluated_args)
        except TypeError as e:
            raise LogosEvaluationError(f"Error calling procedure '{op}': {e}")