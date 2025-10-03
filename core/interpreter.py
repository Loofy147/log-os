# core/interpreter.py
"""
The evaluator, or interpreter, is the heart of Log-Os. It takes an
AST (Abstract Syntax Tree) and an environment, and computes the result
of the expression.
"""

from .types import Symbol, List, Macro
from .environment import Environment
from .errors import LogosEvaluationError
from .parser import parse


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
        if len(args) not in (2, 3):
            raise LogosEvaluationError(f"if form expects 2 or 3 arguments, but got {len(args)}")

        test_expr = args[0]
        conseq_expr = args[1]
        alt_expr = args[2] if len(args) == 3 else None

        if evaluate(test_expr, env):
            return evaluate(conseq_expr, env)
        else:
            return evaluate(alt_expr, env) if alt_expr is not None else None

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
        # (lambda (params... [. rest]) body...)
        (params, *body) = args
        if not body:
            raise LogosEvaluationError("lambda form must have a body.")

        body_expr = body[0] if len(body) == 1 else [Symbol('begin')] + body

        # Handle variadic parameters
        rest_param = None
        fixed_params = params
        if Symbol('.') in params:
            dot_index = params.index(Symbol('.'))
            if dot_index != len(params) - 2:
                raise LogosEvaluationError("Syntax error: '.' in parameter list must be the second-to-last element.")

            fixed_params = params[:dot_index]
            rest_param = params[dot_index + 1]

        def lambda_func(*arguments):
            local_env = Environment(outer=env)
            if rest_param: # If it's a variadic function
                if len(arguments) < len(fixed_params):
                    raise LogosEvaluationError(f"Procedure expects at least {len(fixed_params)} arguments, got {len(arguments)}")
                local_env.update(zip(fixed_params, arguments))
                local_env[rest_param] = list(arguments[len(fixed_params):])
            else: # If it's a fixed-arity function
                if len(fixed_params) != len(arguments):
                    raise LogosEvaluationError(f"Procedure expects {len(fixed_params)} arguments, got {len(arguments)}")
                local_env.update(zip(fixed_params, arguments))

            return evaluate(body_expr, local_env)

        return lambda_func

    elif op == 'defun':
        # (defun name (params...) [docstring] body)
        (name, params, *body) = args
        # A docstring is a string literal, but not a Symbol
        if isinstance(body[0], str) and not isinstance(body[0], Symbol):
            body = body[1:]

        body_expr = body[0] if len(body) == 1 else [Symbol('begin')] + body
        env[name] = evaluate(['lambda', params, body_expr], env)
        return env[name]

    elif op == 'begin':
        # (begin expr1 expr2 ...)
        # Evaluates expressions sequentially and returns the last one.
        result = None
        for expr in args:
            result = evaluate(expr, env)
        return result

    elif op == 'and':
        # (and expr1 expr2 ...) - short-circuiting
        val = True
        for expr in args:
            val = evaluate(expr, env)
            if not val:
                return False
        return val

    elif op == 'or':
        # (or expr1 expr2 ...) - short-circuiting
        val = False
        for expr in args:
            val = evaluate(expr, env)
            if val:
                return True
        return val

    elif op == 'let':
        # (let ((var val) ...) body...)
        (bindings, *body) = args
        if not body:
            raise LogosEvaluationError("let form must have a body.")

        params = [b[0] for b in bindings]
        values = [b[1] for b in bindings]

        # If there's more than one expression in the body, wrap it in a 'begin'
        body_expr = body[0] if len(body) == 1 else [Symbol('begin')] + body

        lambda_expr = ['lambda', params, body_expr]
        eval_expr = [lambda_expr] + values
        return evaluate(eval_expr, env)

    elif op == 'load':
        # (load "filepath")
        (filepath_expr,) = args
        filepath = evaluate(filepath_expr, env)
        if not isinstance(filepath, str):
            raise LogosEvaluationError(f"load expected a string filepath, but got {type(filepath)}")

        with open(filepath) as f:
            source = f.read()

        # Wrap the file content in a 'begin' block to handle multiple expressions
        ast = parse(f"(begin {source})")
        return evaluate(ast, env)

    elif op == 'hash-map':
        # (hash-map key1 val1 key2 val2 ...)
        if len(args) % 2 != 0:
            raise LogosEvaluationError("hash-map requires an even number of arguments for key-value pairs.")

        hash_map = {}
        for i in range(0, len(args), 2):
            key = evaluate(args[i], env)
            value = evaluate(args[i+1], env)
            hash_map[key] = value
        return hash_map

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