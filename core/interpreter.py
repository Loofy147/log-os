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
from .types import List, Symbol


def expand_quasiquote(x, env, level):
    """
    Recursively expands a quasiquoted expression, handling nesting levels
    of unquote and unquote-splicing.
    """
    if not isinstance(x, List) or not x:
        return x

    op, *rest = x

    if op == Symbol('quasiquote'):
        # Nested quasiquote, increase nesting level and recurse
        return [Symbol('quasiquote')] + [expand_quasiquote(rest[0], env, level + 1)]

    if op == Symbol('unquote') or op == Symbol('unquote-splicing'):
        if level == 1:
            # This is the level to evaluate at.
            result = evaluate(rest[0], env)
            if op == Symbol('unquote-splicing'):
                if not isinstance(result, List):
                    raise LogosEvaluationError("unquote-splicing must be used with a list.")
                # Mark for splicing by the caller.
                return [Symbol.SPLICE] + result
            return result
        else:
            # Not our level, so reconstruct the form with a decremented level.
            return [op] + [expand_quasiquote(rest[0], env, level - 1)]

    # It's a regular list, so recurse through its items.
    processed_list = []
    for item in x:
        result = expand_quasiquote(item, env, level)
        # If the result is a list marked for splicing, flatten it into the current list.
        if isinstance(result, List) and result and result[0] is Symbol.SPLICE:
            processed_list.extend(result[1:])
        else:
            processed_list.append(result)
    return processed_list


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

    elif op == 'quasiquote':
        # (quasiquote expression)
        return expand_quasiquote(args[0], env, level=1)

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

    elif op == 'defmacro':
        # (defmacro name params . body)
        (name, params, *body) = args
        body_expr = body[0] if len(body) == 1 else [Symbol('begin')] + body
        # A macro is a procedure that transforms ASTs, created here as a lambda.
        macro_proc = evaluate([Symbol('lambda'), params, body_expr], env)
        env.macros[name] = macro_proc
        return None

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

    elif op == 'load':
        # (load "filepath")
        (filepath_expr,) = args
        filepath = evaluate(filepath_expr, env)
        if not isinstance(filepath, str):
            raise LogosEvaluationError(f"load expected a string filepath, but got {type(filepath)}")

        with open(filepath) as f:
            source = f.read()

        # Use parse_stream and evaluate each expression in the file's scope
        from .parser import parse_stream
        asts = parse_stream(source)
        result = None
        for ast in asts:
            result = evaluate(ast, env)
        return result

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
        # Check for macro expansion before procedure evaluation.
        if isinstance(op, Symbol):
            macro_env = env.find_macro(op)
            if macro_env:
                macro = macro_env.macros[op]
                # It's a macro. Expand it by calling its proc with unevaluated args.
                expanded_ast = macro(*args)
                # Evaluate the result of the expansion.
                return evaluate(expanded_ast, env)

        # It's a regular procedure call.
        proc = evaluate(op, env)
        if not callable(proc):
            raise LogosEvaluationError(f"'{op}' is not a procedure.")

        evaluated_args = [evaluate(arg, env) for arg in args]
        try:
            return proc(*evaluated_args)
        except TypeError as e:
            raise LogosEvaluationError(f"Error calling procedure '{op}': {e}")